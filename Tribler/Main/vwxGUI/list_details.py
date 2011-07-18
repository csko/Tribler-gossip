import wx

import sys
import os
import time
import re
import shutil
from datetime import date, datetime

from Tribler.Core.API import *
from Tribler.Core.osutils import startfile
from Tribler.TrackerChecking.TorrentChecking import *
from Tribler.Video.Progress import ProgressBar
from Tribler.Main.vwxGUI.SearchGridManager import TorrentManager
from Tribler.Main.vwxGUI.GuiUtility import GUIUtility
from Tribler.Subscriptions.rss_client import TorrentFeedThread
from Tribler.Main.globals import DefaultDownloadStartupConfig
from Tribler.Main.vwxGUI.TopSearchPanel import TopSearchPanel
from Tribler.Core.CacheDB.sqlitecachedb import bin2str
from Tribler.Core.CacheDB.SqliteCacheDBHandler import UserEventLogDBHandler
from Tribler.Core.BuddyCast.buddycast import BuddyCastFactory
from Tribler.Core.Subtitles.SubtitlesSupport import SubtitlesSupport
from Tribler.Main.vwxGUI.tribler_topButton import LinkStaticText, SortedListCtrl, SelectableListCtrl

from list_header import ListHeader
from list_body import ListBody
from __init__ import *
from Tribler.Core.simpledefs import DLSTATUS_STOPPED

VLC_SUPPORTED_SUBTITLES = ['.cdg', '.idx', '.srt', '.sub', '.utf', '.ass', '.ssa', '.aqt', '.jss', '.psb', '.rt', '.smi']

class TorrentDetails(wx.Panel):
    def __init__(self, parent, torrent, compact=False):
        wx.Panel.__init__(self, parent)
        self.guiutility = GUIUtility.getInstance()
        self.uelog = UserEventLogDBHandler.getInstance()
        self.parent = parent
        self.torrent = torrent
        self.compact = compact
        self.type = None
        self.vod_log = None
        
        self.SetBackgroundColour(LIST_DESELECTED)
        vSizer = wx.BoxSizer(wx.VERTICAL)
        
        #Add messagePanel text
        self.messagePanel = wx.StaticText(self, -1, "Loading details, please wait.")
        vSizer.Add(self.messagePanel, 0, wx.ALIGN_CENTRE_HORIZONTAL|wx.ALL, 3)
        
        #Add details view
        self.details = wx.BoxSizer(wx.HORIZONTAL)
        vSizer.Add(self.details, 0, wx.EXPAND, 0)
        self.SetSizer(vSizer)
        self.Layout()
        
        self.isReady = False
        self.noChannel = False
        
        #Load torrent using guitaskqueue
        self.guiutility.frame.guiserver.add_task(self.loadTorrent, id = "TorrentDetails_loadTorrent")
        
    def loadTorrent(self):
        try:
            requesttype = self.guiutility.torrentsearch_manager.isTorrentPlayable(self.torrent, callback = self.showTorrent)
            if requesttype:
                #switch back to gui thread
                wx.CallAfter(self._showRequestType, requesttype)
        except wx.PyDeadObjectError:
            pass
    
    def _showRequestType(self, requesttype):
        try:
            self.messagePanel.SetLabel("Loading details, please wait.\nThe torrentfile is requested %s."%requesttype)
            
            self.Layout()
            self.parent.parent_list.OnChange()
        except wx.PyDeadObjectError:
            pass
    
    def showTorrent(self, torrent, information):
        #switch back to gui thread
        wx.CallAfter(self._showTorrent, torrent, information)
        
    def _showTorrent(self, torrent, information):
        try:
            self.torrent = torrent
            self.information = information
            ds = self.torrent.get('ds', None)
            
            self.Freeze()
            self.messagePanel.Show(False)
            
            self.notebook = wx.Notebook(self, style = wx.NB_NOPAGETHEME)
            self._addTabs(ds)
            self.details.Add(self.notebook, 6, wx.EXPAND)
            
            self.buttonPanel = wx.Panel(self)
            self.buttonPanel.SetBackgroundColour(LIST_DESELECTED)
            self.buttonSizer = wx.BoxSizer(wx.VERTICAL)
            
            self.ShowPanel()
            
            self.buttonPanel.SetSizer(self.buttonSizer)
            self.details.Add(self.buttonPanel, 4, wx.EXPAND|wx.LEFT|wx.RIGHT, 3)
            
            page0 = self.notebook.GetPage(0)
            bestHeight = page0.GetBestVirtualSize()[1]
            page0.SetMinSize((-1, bestHeight))
                    
            self.parent.parent_list.OnChange()
            self.Thaw()
            
            self.isReady = True
            self._Refresh(ds)
        except wx.PyDeadObjectError:
            pass
    
    def _create_tab(self, tabname, header = None):
        panel = wx.lib.scrolledpanel.ScrolledPanel(self.notebook, style = wx.VSCROLL)
        panel.SetBackgroundColour(self.notebook.GetThemeBackgroundColour())
        self.notebook.AddPage(panel, tabname)
        
        vSizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(vSizer)
        
        if header:
            header = wx.StaticText(panel, -1, header)
            font = header.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            header.SetFont(font)
            header.SetMinSize((1,-1))
            vSizer.Add(header, 0, wx.LEFT|wx.BOTTOM|wx.EXPAND, 3)
        
        return panel, vSizer
        
    def _add_row(self, parent, sizer, name, value, spacer = 10):
        if name:
            name = wx.StaticText(parent, -1, name)
            font = name.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            name.SetFont(font)
            sizer.Add(name, 0, wx.LEFT, spacer)
        
        if value:
            if isinstance(value, basestring):
                try:
                    value = wx.StaticText(parent, -1, unicode(value))
                except:
                    value = wx.StaticText(parent, -1, value.decode('utf-8','ignore'))
                value.SetMinSize((1,-1))
                sizer.Add(value, 0, wx.EXPAND|wx.LEFT, spacer)
            else:
                sizer.Add(value, 0, wx.LEFT, spacer)
        
        return name, value

    def _addTabs(self, ds):
        finished = self.torrent.get('progress', 0) == 100 or (ds and ds.get_progress() == 1.0)
    
        #Create torrent overview
        overview, torrentSizer = self._create_tab('Overview', 'Torrent Details')
        category = self.torrent['category']
        if isinstance(category,list):
            category = ', '.join(category)
        
        overviewColumns = {
            "Name": self.torrent['name'],
            "Type": category.capitalize(),
            "Uploaded": date.fromtimestamp(self.torrent['creation_date']).strftime('%Y-%m-%d'),
            "Filesize": self.guiutility.utility.size_format(self.torrent['length']) + " in " + str(len(self.information[2])) + " files",
        }
        
        if 'torrent_id' not in self.torrent:
            self.torrent['torrent_id'] = self.guiutility.torrentsearch_manager.torrent_db.getTorrentID(self.torrent['infohash'])
        
        swarmInfo = self.guiutility.torrentsearch_manager.getSwarmInfo(self.torrent['torrent_id'])
        if swarmInfo:
            _, seeders, leechers, last_check, _, _ = swarmInfo
        else:
            seeders = self.torrent.get('num_seeders', -1)
            leechers = self.torrent.get('num_leechers', -1)
            last_check = -1
        
        diff = time() - last_check
        if seeders <= 0 and leechers <= 0:
            overviewColumns["Status"] = "Unknown"
        else:
            overviewColumns["Status"] = "%s seeders, %s leechers (updated %s ago)"%(seeders,leechers,self.guiutility.utility.eta_value(diff, 2))
        
        if self.compact:
            vSizer = wx.FlexGridSizer(0, 6, 3, 3)
            vSizer.AddGrowableCol(1,4) #we give more space to name and status
            vSizer.AddGrowableCol(3,2)
            vSizer.AddGrowableCol(5,2)
            overviewColumnsOrder = ["Name", "Type", "Uploaded", "Status", "Filesize"]
        else:
            vSizer = wx.FlexGridSizer(0, 2, 3, 3)
            vSizer.AddGrowableCol(1)
            overviewColumnsOrder = ["Name", "Type", "Uploaded", "Filesize", "Status"]
        
        for column in overviewColumnsOrder:
            _, value = self._add_row(overview, vSizer, column, overviewColumns[column])
            if column == "Status":
                self.status = value
            
        torrentSizer.Add(vSizer, 1, wx.EXPAND)
        
        if diff > 1800: #force update if last update more than 30 minutes ago
            TorrentChecking(self.torrent['infohash']).start()
        overview.SetupScrolling(rate_y = 5)
        
        #Create filelist
        if len(self.information[2]) > 0:
            self.listCtrl = SortedListCtrl(self.notebook, 2)
            self.listCtrl.InsertColumn(0, 'Name')
            self.listCtrl.InsertColumn(1, 'Size', wx.LIST_FORMAT_RIGHT)
            self.listCtrl.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
            
            self.il = wx.ImageList(16,16)
            play_img = self.il.Add(wx.Bitmap(os.path.join(self.guiutility.vwxGUI_path, 'images', 'library_play.png'), wx.BITMAP_TYPE_ANY))
            file_img = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, size = (16,16)))
            self.listCtrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
            
            #Add files
            keywords = ' | '.join(self.guiutility.current_search_query)
            def sort_by_keywords(a, b):
                a_match = re.search(keywords, a[0].lower())
                b_match = re.search(keywords, b[0].lower())
                if a_match and not b_match:
                    return -1
                if b_match and not a_match:
                    return 1
                return cmp(a[0],b[0])
            
            self.information[2].sort(sort_by_keywords)
            for filename, size in self.information[2]:
                try:
                    pos = self.listCtrl.InsertStringItem(sys.maxint, filename)
                except:
                    try:
                        pos = self.listCtrl.InsertStringItem(sys.maxint, filename.decode('utf-8','ignore'))
                    except:
                        print >> sys.stderr, "Could not format filename", self.torrent['name']
                self.listCtrl.SetItemData(pos, pos)
                self.listCtrl.itemDataMap.setdefault(pos, [filename, size])
                
                size = self.guiutility.utility.size_format(size)
                self.listCtrl.SetStringItem(pos, 1, size)
                
                if filename in self.information[1]:
                    self.listCtrl.SetItemColumnImage(pos, 0, play_img)
                else:
                    self.listCtrl.SetItemColumnImage(pos, 0, file_img)
            
            self.listCtrl.setResizeColumn(0)
            self.listCtrl.SetMinSize((1,-1))
            self.listCtrl.SetColumnWidth(1, wx.LIST_AUTOSIZE) #autosize only works after adding rows
            self.notebook.AddPage(self.listCtrl, "Files")
        
        #Create subtitlelist
        if self.information[0]:
            curlang = []
            strlang = []
            
            subsupport = SubtitlesSupport.getInstance()
            if subsupport._registered:
                subs = subsupport.getSubtileInfosForInfohash(self.torrent['infohash'])
                if len(subs) > 0:
                    supportedLang = subsupport.langUtility.getLangSupported()

                    for channelid, dict in subs.iteritems():
                        for lang in dict.keys():
                            curlang.append((supportedLang[lang], channelid, dict[lang]))
                    curlang.sort()
                    strlang = [lang[0] for lang in curlang]
            
            internalSubs = []
            for filename, size in self.information[2]:
                root, extension = os.path.splitext(filename)
                if extension in VLC_SUPPORTED_SUBTITLES:
                    internalSubs.append(filename)
            internalSubs.sort()
            
            for filename in internalSubs:
                _, nicefilename = os.path.split(filename)
                strlang.append(nicefilename)
                curlang.append([filename])
                
            foundSubtitles = len(curlang) > 0
            
            subtitlePanel, vSizer = self._create_tab("Subtitles")
            vSizer.AddSpacer((-1, 3))
            
            if not finished:
                title = 'After you finished downloading this torrent you can select a subtitle'
            else:
                title = 'You can now select a subtitle'
            
            if foundSubtitles:
                title += ' found by Tribler or'
            title += ' specified by you to be used with our player.'
            self._add_row(subtitlePanel, vSizer, None, title, spacer = 3)
            
            vSizer.AddStretchSpacer()
            
            curlang.insert(0, ('','',''))
            strlang.insert(0, 'No subtitle')
            
            curlang.append(('','',''))
            strlang.append('Browse for a subtitle...')
                
            self.subtitleChoice = wx.Choice(subtitlePanel, choices = strlang)
            self.subtitleChoice.Bind(wx.EVT_CHOICE, self.OnSubtitle)
            self.subtitleChoice.Enable(False)
            self.subtitleChoice.items = curlang
              
            self.requestingSub = wx.StaticText(subtitlePanel)
            self.requestingSub.Show(False)
            
            self._add_row(subtitlePanel, vSizer, "Which subtitle do you want to use?", None, spacer = 3)
            
            vSizer.Add(self.subtitleChoice, 0, wx.ALIGN_RIGHT|wx.BOTTOM|wx.RIGHT, 3)
            vSizer.Add(self.requestingSub, 0, wx.ALIGN_RIGHT|wx.BOTTOM|wx.RIGHT, 3)
            
        
        #Create description
        if self.torrent.get('comment', 'None') != 'None' and self.torrent['comment'] != '':
            descriptionPanel, vSizer = self._create_tab("Description", "Comment")
            self._add_row(descriptionPanel, vSizer, None, self.torrent['comment'])
            descriptionPanel.SetupScrolling(rate_y = 5)
        
        #Create trackerlist
        if self.torrent.get('trackers', 'None') != 'None':
            tracker_list = []
            for trackers in self.torrent['trackers']:
                for tracker in trackers:
                    if tracker:
                        tracker_list.append(tracker)
                
            if len(tracker_list) > 0:
                trackerPanel, vSizer = self._create_tab("Trackers", "Trackers")
                for tracker in tracker_list:
                    self._add_row(trackerPanel, vSizer, None, tracker)
                trackerPanel.SetupScrolling(rate_y = 5)
    
    def ShowPanel(self, type = None):
        if getattr(self, 'buttonSizer', False):
            if type is None:
                type = 0
                
                #Decide which panel should be shown
                ds = self.torrent.get('ds', False)
                if ds:
                    if ds.get_progress() == 1.0:
                        type = 2
                    else:
                        type = 1
                else:
                    progress = self.torrent.get('progress', 0)
                    if progress == 100:
                        type = 2
                    elif progress > 0:
                        type = 1
            
            if type != self.type:    
                self.type = type
                
                self.buttonPanel.Freeze()
                self.buttonSizer.ShowItems(False)
                self.buttonSizer.DeleteWindows()
                self.buttonSizer.Clear()
            
                in_progress = finished = False
            
                if type == 2:
                    self.torrent['progress'] = 100
                    self._ShowDone()
                elif type == 1:
                    self._ShowDownloadProgress()
                else:
                    self._ShowTorrentDetails()
                
                if getattr(self.parent, 'button', False):
                    self.parent.button.Enable(not finished and not in_progress)
            
                self.buttonPanel.Show()
                self.buttonPanel.Layout()
                self.buttonPanel.Thaw()
        else:
            #Additionally called by database event, thus we need to check if sizer exists(torrent is downloaded).
            wx.CallAfter(self.ShowPanel, type)
        
    def ShowChannelAd(self, show):
        if self.isReady:
            self.channeltext.Show(show)
        else:
            self.noChannel = True

    def _ShowTorrentDetails(self):
        header = wx.StaticText(self.buttonPanel, -1, "Liking what you see?")
        header.SetMinSize((1,-1))
        font = header.GetFont()
        font.SetPointSize(font.GetPointSize()+1)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(font)
        self.buttonSizer.Add(header, 0, wx.ALL|wx.EXPAND, 3)
        subtitle = wx.StaticText(self.buttonPanel, -1, "Click download or play to enjoy this torrent.")
        subtitle.SetMinSize((1, -1))
        self.buttonSizer.Add(subtitle, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 3)
        
        self.buttonSizer.AddStretchSpacer()
        
        download_play_sizer = wx.BoxSizer(wx.HORIZONTAL)
        download = wx.Button(self.buttonPanel, -1, "Download")
        download.SetToolTipString('Start downloading this torrent.')
        download.Bind(wx.EVT_BUTTON, self.OnDownload)
        
        play = wx.Button(self.buttonPanel, -1, "Play")
        play.SetToolTipString('Start playing this torrent.')
        play.Bind(wx.EVT_BUTTON, self.OnPlay)
        
        if not self.information[0]:
            play.Disable()
        
        download_play_sizer.Add(download)
        download_play_sizer.Add(wx.StaticText(self.buttonPanel, -1, "or"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.LEFT|wx.RIGHT, 3)
        download_play_sizer.Add(play)
        self.buttonSizer.Add(download_play_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)
        
        self.buttonSizer.AddStretchSpacer()
        
        if not self.noChannel:
            #prefer local channel result
            channel = self.guiutility.channelsearch_manager.getChannelForTorrent(self.torrent['infohash'])
            if channel is None:
                if 'channel_permid' in self.torrent and self.torrent['channel_permid'] != '':
                    channel = (self.torrent['channel_permid'], self.torrent['channel_name'], self.torrent['subscriptions'], {})
            
            if channel is not None:
                if channel[0] == bin2str(self.guiutility.utility.session.get_permid()):
                    label = "This torrent is part of your Channel."
                    tooltip = "Open your Channel."
                else:
                    label = "Click to see more from %s's Channel."%channel[1]
                    tooltip = "Click to go to %s's Channel."%channel[1]
                
                self.channeltext = LinkStaticText(self.buttonPanel, label)
                self.channeltext.SetToolTipString(tooltip)
                self.channeltext.SetMinSize((1, -1))
                self.channeltext.channel = channel
                self.channeltext.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
                self.channeltext.target = 'channel'
                self.buttonSizer.Add(self.channeltext, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL|wx.EXPAND, 3)
    
    def _ShowDownloadProgress(self):
        #Header
        self.downloadText = wx.StaticText(self.buttonPanel, -1, "You are downloading this torrent")
        font = self.downloadText.GetFont()
        font.SetPointSize(font.GetPointSize()+1)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.downloadText.SetFont(font)
        self.buttonSizer.Add(self.downloadText, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 3)
        
        if not isinstance(self, LibraryDetails):
            library = LinkStaticText(self.buttonPanel, "Open library")
            library.SetToolTipString("Open library")
            library.target = 'my_files'
            library.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
            self.buttonSizer.Add(library, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 3)
        
        self.buttonSizer.AddStretchSpacer()
        
        if not isinstance(self, LibraryDetails):
            #Progress
            header = wx.StaticText(self.buttonPanel, -1, "Current progress")
            font = header.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            header.SetFont(font)
            self.buttonSizer.Add(header, 0, wx.ALL, 3)
            class tmp_object():
                def __init__(self, data, original_data):
                    self.data = data
                    self.original_data = original_data
            self.item = tmp_object(['',[0,0],[0,0],0,0],self.torrent)
            self.progressPanel = ProgressPanel(self.buttonPanel, self.item, ProgressPanel.ETA_EXTENDED)
            self.buttonSizer.Add(self.progressPanel, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 3)
        
        #Optional stream button
        if self.information[0]:
            self.playSpacer = self.buttonSizer.AddStretchSpacer()
            self.play = wx.Panel(self.buttonPanel)
            self.play.SetBackgroundColour(LIST_DESELECTED)
            vSizer = wx.BoxSizer(wx.VERTICAL)
            
            header = wx.StaticText(self.play, -1, "Impatient?")
            font = header.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            header.SetFont(font)
            vSizer.Add(header, 0, wx.ALL, 3)
            
            play = LinkStaticText(self.play, "Start playing this torrent now")
            play.SetToolTipString('Start playing this torrent.')
            play.Bind(wx.EVT_LEFT_DOWN, self.OnPlay)
            vSizer.Add(play, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 3)
            self.play.SetSizer(vSizer)
            self.buttonSizer.Add(self.play, 0,wx.EXPAND, 3)
            
        if isinstance(self, LibraryDetails):
            self.vod_log = wx.StaticText(self.buttonPanel)
            self.vod_log.SetMinSize((1,-1))
            self.vod_log.Hide()
            
            self.buttonSizer.Add(self.vod_log, 0, wx.EXPAND, 3)
        else:
            self.vod_log = None
        
        self.guiutility.library_manager.add_download_state_callback(self.OnRefresh)
    
    def _ShowDone(self):
        header = wx.StaticText(self.buttonPanel, -1, "This torrent has finished downloading.")
        header.SetMinSize((1,-1))
        font = header.GetFont()
        font.SetPointSize(font.GetPointSize()+1)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(font)
        self.buttonSizer.Add(header, 0, wx.ALL|wx.EXPAND, 3)
        
        self.buttonSizer.AddStretchSpacer()
        
        play = wx.Button(self.buttonPanel, -1, "Play")
        play.SetToolTipString('Start playing this torrent.')
        play.Bind(wx.EVT_BUTTON, self.OnPlay)
        
        if not self.information[0]:
            play.Disable()
        
        explore_play_sizer = wx.BoxSizer(wx.HORIZONTAL)
        explore = wx.Button(self.buttonPanel, -1, "Explore Files")
        explore.SetToolTipString('Explore the files of this torrent.')
        explore.Bind(wx.EVT_BUTTON, self.OnExplore)
        
        explore_play_sizer.Add(explore)
        explore_play_sizer.Add(wx.StaticText(self.buttonPanel, -1, "or"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.LEFT|wx.RIGHT, 3)
        explore_play_sizer.Add(play)
        self.buttonSizer.Add(explore_play_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)
        self.buttonSizer.AddStretchSpacer()
        
        if not self.noChannel:
            channel = self.guiutility.channelsearch_manager.getChannelForTorrent(self.torrent['infohash'])
            if channel is None or channel[0] != bin2str(self.guiutility.utility.session.get_permid()):
                header = wx.StaticText(self.buttonPanel, -1, "Did you enjoy this torrent?")
                font = header.GetFont()
                font.SetWeight(wx.FONTWEIGHT_BOLD)
                header.SetFont(font)
                header.SetMinSize((1,-1))
                self.buttonSizer.Add(header, 0, wx.ALL|wx.EXPAND, 3)
                
                if channel:
                    channeltext = LinkStaticText(self.buttonPanel, "Click to see more from %s's Channel."%channel[1])
                    channeltext.SetToolTipString("Click to go to %s's Channel."%channel[1])
                    channeltext.target = 'channel'
                    channeltext.channel = channel
                    channeltext.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
                    self.buttonSizer.Add(channeltext, 0, wx.ALL|wx.EXPAND, 3)
                
                    mychannel = LinkStaticText(self.buttonPanel, "Or spread it using your channel")
                else:
                    mychannel = LinkStaticText(self.buttonPanel, "Spread it using your channel")
                    
                mychannel.Bind(wx.EVT_LEFT_DOWN, self.OnMyChannel)
                mychannel.SetToolTipString('Add this torrent to your channel.')
                self.buttonSizer.Add(mychannel, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 3)
            else:
                header = wx.StaticText(self.buttonPanel, -1, "You are sharing this torrent in your channel")
                font = header.GetFont()
                font.SetWeight(wx.FONTWEIGHT_BOLD)
                header.SetFont(font)
                header.SetMinSize((1,-1))
                self.buttonSizer.Add(header, 0, wx.ALL|wx.EXPAND, 3)
                
                channeltext = LinkStaticText(self.buttonPanel, "Open your channel")
                channeltext.SetToolTipString("Click to go to your Channel.")
                channeltext.target = 'channel'
                channeltext.channel = channel
                channeltext.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
                self.buttonSizer.Add(channeltext, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 3)
             
        if getattr(self, 'subtitleChoice', None):
            self.subtitleChoice.Enable(True)
        if getattr(self, 'subtitleBrowse', None):
            self.subtitleBrowse.Enable(True)
            self.removeSubtitle.Enable(True)
    
    def _GetPath(self, file = None):
        ds = self.torrent.get('ds', False)
        if ds:
            destdirs = ds.get_download().get_dest_files()
            if file:
                for filenameintorrent, path in destdirs:
                    if filenameintorrent == file:
                        return path
                    
            return os.path.commonprefix([os.path.split(path)[0] for _,path in destdirs])
    
    def OnExplore(self, event):
        path = self._GetPath()
        if path:
            startfile(path)
                
    def OnDownload(self, event):
        self.parent.parent_list.parent_list.StartDownload(self.torrent)
        
        button = event.GetEventObject()
        button.Enable(False)
        wx.CallLater(5000, button.Enable, True)
        
    def OnPlay(self, event):
        play = event.GetEventObject()
        playable_files = self.information[1]
        
        if len(playable_files) > 1: #Create a popup
            playable_files.sort()
            dialog = wx.SingleChoiceDialog(self, 'Tribler currently only supports playing one file at a time.\nSelect the file you want to play?', 'Which file do you want to play?',playable_files)
            
            (_, selected_file) = max([(size, filename) for filename, size in self.information[2] if filename in self.information[1]])
            if self.notebook.GetSelection() == 1: #If currentpage is files
                selected = self.listCtrl.GetFirstSelected()
                if selected != -1 and self.listCtrl.GetItemText(selected) in playable_files:
                    selected_file = self.listCtrl.GetItemText(selected)
             
            if selected_file in playable_files:
                dialog.SetSelection(playable_files.index(selected_file))
                
            if dialog.ShowModal() == wx.ID_OK:
                response = dialog.GetStringSelection()
                
                self.guiutility.library_manager.playTorrent(self.torrent, response)
                
                if self.noChannel:
                    self.uelog.addEvent(message="Torrent: torrent play from channel", type = 2)
                else:
                    self.uelog.addEvent(message="Torrent: torrent play from other", type = 2)       
            dialog.Destroy()
        elif len(playable_files) == 1:
            self.guiutility.library_manager.playTorrent(self.torrent)
            
            if self.noChannel:
                self.uelog.addEvent(message="Torrent: torrent play from channel", type = 2)
            else:
                self.uelog.addEvent(message="Torrent: torrent play from other", type = 2)   
            
        play.Enable(False)
        wx.CallLater(5000, play.Enable, True)
    
    def OnDoubleClick(self, event):
        selected = self.listCtrl.GetFirstSelected()
        playable_files = self.information[1]
            
        if selected != -1:
            selected_file = self.listCtrl.GetItemText(selected)
            if selected_file in playable_files:
                self.guiutility.library_manager.playTorrent(self.torrent, selected_file)
            elif self.torrent.get('progress',0) == 100: #not playable
                file = self._GetPath(selected_file)
                if os.path.isfile(file):
                    startfile(file)
    
    def _ToggleSubtitleChoice(self, showChoice = None):
        if not showChoice:
            showChoice = not self.subtitleChoice.IsShown()
        
        self.subtitleChoice.Show(showChoice)
        self.requestingSub.Show(not showChoice)
        self.requestingSub.sizer.Layout()
                   
    def OnSubtitle(self, event):
        selected = self.subtitleChoice.GetSelection()
        nrItems =self.subtitleChoice.GetCount()
        
        if selected == 0 or selected == wx.NOT_FOUND:
            self.RemoveSubtitle()
            
        elif selected == nrItems - 1:
            self.OnSubtitleBrowse(event)
            
        else:
            if len(self.subtitleChoice.items[selected]) > 1:
                (lang, channelid, subtitleinfo) = self.subtitleChoice.items[selected]
                
                self.requestingSub.SetLabel('Requesting subtitle from peers...')
                self._ToggleSubtitleChoice(False)
                                
                subsupport = SubtitlesSupport.getInstance()
                subsupport.retrieveSubtitleContent(channelid, self.torrent['infohash'], subtitleinfo, self.OnRetrieveSubtitle)
                
                def subTimeout():
                    if self.requestingSub.IsShown():
                        self.requestingSub.SetLabel('Request failed, no peer responded with subtitle')
                        wx.CallLater(3000, self._ToggleSubtitleChoice, True)
                wx.CallLater(10000, subTimeout)
            else:
                file = self._GetPath(self.subtitleChoice.items[selected][0])
                self.uelog.addEvent(message="Subtitles: user choose a internal subtitle", type = 2)
                self.SetSubtitle(file)
    
    def OnRetrieveSubtitle(self, subtitleinfo):
        self.SetSubtitle(subtitleinfo.getPath())
        self.uelog.addEvent(message="Subtitles: user retrieved a subtitle", type = 2)
        self.requestingSub.SetLabel('Got subtitle from peers')
        wx.CallLater(3000, self._ToggleSubtitleChoice, True)
            
    def OnSubtitleBrowse(self, event):
        wildcard = "*" + ";*".join(VLC_SUPPORTED_SUBTITLES)
        wildcard = "Subtitles (%s) | %s"%(wildcard, wildcard)
        
        dlg = wx.FileDialog(self, 'Please select your subtitle.', wildcard = wildcard, style = wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.uelog.addEvent(message="Subtitles: user choose his own subtitle", type = 2)
            
            file = dlg.GetPath()
            self.SetSubtitle(file)
        dlg.Destroy()
        
    def SetSubtitle(self, file):
        _, ext = os.path.splitext(file)
        if ext.lower() in VLC_SUPPORTED_SUBTITLES:
            #get largest playable file
            (size, filename) = max([(size, filename) for filename, size in self.information[2] if filename in self.information[1]])
            
            filename = os.path.join(self._GetPath(), filename[0:filename.rfind(".")] + ext)
            shutil.copy(file, filename)
        
    def RemoveSubtitle(self, event = None):
        (size, filename) = max([(size, filename) for filename, size in self.information[2] if filename in self.information[1]])
        if filename[0:filename.rfind(".")] + ".srt" not in self.information[2]: #only actually remove this subtitle if it not in the .torrent
            filename = os.path.join(self._GetPath(), filename[0:filename.rfind(".")] + ".srt")
            if os.path.isfile(filename):
                os.remove(filename)
    
    def OnClick(self, event):
        label = event.GetEventObject().GetParent()
        if label.target == 'my_files':
            self.guiutility.frame.top_bg.selectTab('my_files')
            self.guiutility.ShowPage('my_files', self.torrent['infohash'])
        else:
            self.guiutility.frame.top_bg.selectTab('channels')
            
            channel = label.channel
            if channel[0] == bin2str(self.guiutility.utility.session.get_permid()):
                self.guiutility.ShowPage('mychannel')
            else:
                if self.torrent.get('channel_permid', '') == channel[0] and 'query_permids' in self.torrent:
                    channelcast = BuddyCastFactory.getInstance().channelcast_core
                    channelcast.updateAChannel(channel[0], self.torrent['query_permids'])
                    
                self.guiutility.showChannel(channel[1], channel[0])    
    
    def OnMyChannel(self, event):
        torrent_dir = self.guiutility.utility.session.get_torrent_collecting_dir()
        torrent_filename = os.path.join(torrent_dir, self.torrent['torrent_file_name'])
        
        torrentfeed = TorrentFeedThread.getInstance()
        torrentfeed.addFile(torrent_filename)
        self.guiutility.Notify('New torrent added to My Channel', wx.ART_INFORMATION)
        self.uelog.addEvent(message="MyChannel: manual add from library", type = 2)
    
    def UpdateStatus(self):
        if 'torrent_id' not in self.torrent:
            self.torrent['torrent_id'] = self.guiutility.torrentsearch_manager.torrent_db.getTorrentID(self.torrent['infohash'])
        
        swarmInfo = self.guiutility.torrentsearch_manager.getSwarmInfo(self.torrent['torrent_id'])
        if swarmInfo:
            self.torrent['num_seeders'] = swarmInfo[1]
            self.torrent['num_leechers'] = swarmInfo[2]
            self.torrent['last_check'] = swarmInfo[3]
            wx.CallAfter(self.ShowStatus)
    
    def ShowStatus(self):
        diff = time() - self.torrent['last_check']
        if self.torrent['num_seeders'] < 0 and self.torrent['num_leechers'] < 0:
            self.status.SetLabel("Unknown")
        else:
            self.status.SetLabel("%s seeders, %s leechers (current)"%(self.torrent['num_seeders'], self.torrent['num_leechers']))
           
    def OnRefresh(self, dslist):
        found = False
        
        for ds in dslist:
            infohash = ds.get_download().get_def().get_infohash()
            if infohash == self.torrent['infohash']:
                self._Refresh(ds)
                found = True
                break
        
        if not found:
            self.guiutility.library_manager.remove_download_state_callback(self.OnRefresh)
            self.ShowPanel()
            
    def _Refresh(self, ds):
        self.torrent['ds'] = ds
        if ds:
            self.torrent['progress'] = int(ds.get_progress() * 100)
        elif 'progress' not in self.torrent:
            self.torrent['progress'] = 0
                    
        if self.torrent['progress'] < 100:
            if getattr(self, 'progressPanel', False) and ds:
                self.item.original_data['ds'] = ds
                self.progressPanel.Update()
            
            if not ds or ds.get_status() == DLSTATUS_STOPPED:
                label = 'Download is stopped'
                
                if self.vod_log:
                    self.vod_log.Hide()
            elif ds.is_vod():
                label = 'You are streaming this torrent'
                if getattr(self, 'play', False):
                    self.play.Hide()
                    self.playSpacer.Show(False)
                    self.buttonPanel.Layout()
                
                if ds.vod_status_msg:
                    vod_log = ds.vod_status_msg.replace(". ", ".\n")
                    if self.vod_log and self.vod_log.GetLabel() != vod_log:
                        self.vod_log.SetLabel(vod_log)
                        self.vod_log.Refresh()
                        
                        if not self.vod_log.IsShown():
                            self.vod_log.Show()
                        self.buttonPanel.Layout()
            else:
                label = 'You are downloading this torrent'
            
            if getattr(self,'downloadText', False) and self.downloadText.GetLabel() != label:
                self.downloadText.SetLabel(label)
                self.downloadText.Refresh()
            self.buttonPanel.Show()
            
        else:
            self.guiutility.library_manager.remove_download_state_callback(self.OnRefresh)
            self.ShowPanel(2)
            
    def __del__(self):
        self.guiutility.library_manager.remove_download_state_callback(self.OnRefresh)

class LibraryDetails(TorrentDetails):
    def _showRequestType(self, requesttype):
        pass
    
    def _addTabs(self, ds):
        TorrentDetails._addTabs(self, ds)
        peersPanel = wx.Panel(self.notebook)
        vSizer = wx.BoxSizer(wx.VERTICAL)
         
        self.peerList = SelectableListCtrl(peersPanel, 4, style = wx.LC_REPORT|wx.LC_NO_HEADER, tooltip = False)
        self.peerList.InsertColumn(0, 'IP-address')
        self.peerList.InsertColumn(1, 'Traffic', wx.LIST_FORMAT_RIGHT)
        self.peerList.InsertColumn(2, 'State', wx.LIST_FORMAT_RIGHT)
        self.peerList.InsertColumn(3, 'ID', wx.LIST_FORMAT_RIGHT)
        self.peerList.setResizeColumn(0)
        self.peerList.SetToolTipString("States:\nO\toptimistic unchoked\nUI\tgot interested\nUC\tupload chocked\nUQ\tgot request\nDI\tsend interested\nDC\tdownload chocked\nS\tis snubbed\nL\tOutgoing connection\nR\tIncoming connection")
        vSizer.Add(self.peerList, 1, wx.EXPAND)
        
        finished = self.torrent.get('progress', 0) == 100 or (ds and ds.get_progress() == 1.0)
        if not finished:
            hSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.availability = wx.StaticText(peersPanel)
            self._add_row(peersPanel, hSizer, 'Availability', self.availability, spacer = 3)
            vSizer.Add(hSizer, 0, wx.EXPAND)
        else:
            self.availability = None

        peersPanel.SetSizer(vSizer)
        self.notebook.AddPage(peersPanel, "Peers")
    
    def _Refresh(self, ds):
        TorrentDetails._Refresh(self, ds)
        
        #register callback for peerlist update
        self.guiutility.library_manager.add_download_state_callback(self.OnRefresh)
        
        self.peerList.Freeze()
        def downsort(a, b):
            if a['downrate'] != b['downrate']:
                return a['downrate'] - b['downrate']
            return a['uprate'] - b['uprate']
        
        index = 0
        if ds:
            peers = ds.get_peerlist()
            peers.sort(downsort, reverse = True)
            
            for peer_dict in peers:
                peer_name = peer_dict['ip'] + ':%d @ %d%%'%(peer_dict['port'], peer_dict['completed']*100.0)
                if index < self.peerList.GetItemCount():
                    self.peerList.SetStringItem(index, 0, peer_name)
                else:
                    self.peerList.InsertStringItem(index, peer_name)
                
                traffic = ""
                traffic += self.guiutility.utility.speed_format_new(peer_dict['downrate']) + u"\u2193 "
                traffic += self.guiutility.utility.speed_format_new(peer_dict['uprate']) + u"\u2191"
                self.peerList.SetStringItem(index, 1, traffic.strip())
                
                state = ""
                if peer_dict['optimistic']:
                    state += "O,"
                if peer_dict['uinterested']:
                    state += "UI,"
                if peer_dict['uchoked']:
                    state += "UC,"
                if peer_dict['uhasqueries']:
                    state += "UQ,"
                if peer_dict['dinterested']:
                    state += "DI,"
                if peer_dict['dchoked']:
                    state += "DC,"
                if peer_dict['snubbed']:
                    state += "S,"
                state += peer_dict['direction']
                self.peerList.SetStringItem(index, 2, state)
                
                try:
                    self.peerList.SetStringItem(index, 3, peer_dict['extended_version'])
                except:
                    try:
                        self.peerList.SetStringItem(index, 3, peer_dict['extended_version'].decode('utf-8','ignore'))
                    except:
                        print >> sys.stderr, "Could not format peer client version"
                
                index += 1
                
            if self.availability:
                self.availability.SetLabel("%.2f"%ds.get_availability())
            
        if index == 0:
            self.peerList.DeleteAllItems()
            self.peerList.InsertStringItem(index, "Not connected to any peers")
        else:
            while index < self.peerList.GetItemCount():
                self.peerList.DeleteItem(index)
                index += 1
        
        self.peerList.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.peerList.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        self.peerList.SetColumnWidth(3, wx.LIST_AUTOSIZE)
        self.peerList._doResize()
        self.peerList.Thaw()

class ProgressPanel(wx.Panel):
    #eta style
    ETA_DEFAULT = 1
    ETA_EXTENDED = 2
    
    def __init__(self, parent, item, style = ETA_DEFAULT):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(LIST_DESELECTED)
        self.item = item
        self.style = style
        guiutility = GUIUtility.getInstance()
        self.utility = guiutility.utility

        self.pb = ProgressBar(self)
        self.status = wx.StaticText(self)
        vSizer = wx.BoxSizer(wx.VERTICAL)
        vSizer.AddStretchSpacer()
        vSizer.Add(self.pb, 0, wx.EXPAND)
        vSizer.Add(self.status, 0, wx.EXPAND)
        
        vSizer.AddStretchSpacer()
        
        self.SetSizer(vSizer)
        self.Update()
        
    def Update(self, ds = None):
        #return_val, 0 == inactive, 1 == incomplete, 2 == complete/seeding
        return_val = 0
        
        if ds == None:
            ds = self.item.original_data.get('ds', None)
        
        if ds != None:
            progress = ds.get_progress()
            seeds, peers = ds.get_num_seeds_peers()
            
            dls = ds.get_current_speed('down')*1024
            uls = ds.get_current_speed('up')*1024
            
            eta = ds.get_eta()
            status = ds.get_status()
        else:
            progress = self.item.original_data.get('progress', 0) / 100.0
            seeds = peers = None
            dls = uls = 0
            
            eta = ''
            status = DLSTATUS_STOPPED
        
        if seeds == None:
            seeds = 0
        if peers == None:
            peers = 0
            
        progress = max(0, min(1, progress)) #progress has to be between 0 and 1
         
        self.item.data[2] = [seeds, peers]
        self.item.data[3] = dls
        self.item.data[4] = uls
            
        finished = progress == 1.0
        if finished:
            eta = "Completed"
            if status == DLSTATUS_SEEDING:
                eta += ", seeding"
                return_val = 2
            elif status == DLSTATUS_REPEXING:
                eta += ", repexing"
            else:
                eta += ", inactive"
        else:
            if status in [DLSTATUS_WAITING4HASHCHECK, DLSTATUS_HASHCHECKING]:
                eta = 'Checking'
            
            elif status == DLSTATUS_DOWNLOADING:
                sizestr = ''
                size = self.item.original_data.get('length', False)
                if size:
                    size_progress = size*progress
                    
                    def format_size(bytes):
                        if bytes > 1073741824:
                            return self.utility.size_format(bytes, 1)
                        return self.utility.size_format(bytes, 0)
                    sizestr = '%s/%s (%0.1f%%)'%(format_size(size_progress), format_size(size), progress*100) 
                    
                eta = self.utility.eta_value(eta, truncate=2)
                if eta == '' or eta.find('unknown') != -1:
                    eta = sizestr
                else:
                    eta = sizestr + ' - ' + eta
                
                return_val = 1
            else:
                eta = 'Incomplete, inactive (%0.1f%%)'%(progress*100)
            
        if self.style == ProgressPanel.ETA_EXTENDED:
            if status == DLSTATUS_SEEDING:
                upSpeed = " @ " +self.utility.speed_format_new(uls)
                eta += upSpeed
            elif status == DLSTATUS_DOWNLOADING:
                dlSpeed = " @ " +self.utility.speed_format_new(dls)
                eta += dlSpeed
        
        #Update eta
        if self.status.GetLabel() != eta:
            self.status.SetLabel(eta)
            self.status.Refresh()
            
            if not status in [DLSTATUS_WAITING4HASHCHECK, DLSTATUS_ALLOCATING_DISKSPACE, DLSTATUS_HASHCHECKING, DLSTATUS_STOPPED]:
                havedigest = ds.get_pieces_complete()
            else:
                havedigest = None
            
            #Update graph
            if finished:
                self.pb.reset(colour=2) # Show as complete
            elif havedigest:
                self.pb.set_pieces(havedigest)
            elif progress > 0:
                self.pb.setNormalPercentage(progress) # Show as having some
            else:
                self.pb.reset(colour=0) # Show as having none
            self.pb.Refresh()
            
        return return_val
    
class MyChannelTabs(wx.Panel):
    def __init__(self, parent, background, columns, spacers, singleSelect):
        self.parent = parent
        self.torrentfeed = TorrentFeedThread.getInstance()
        self.torrentfeed.addCallback(self.OnRssItem)
        self.guiutility = GUIUtility.getInstance()
        self.uelog = UserEventLogDBHandler.getInstance()
        
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(background)
        
        notebook = wx.Notebook(self, style = wx.NB_NOPAGETHEME)
        notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnChange)
        #overview page
        text =  """
        <p>
            This is your channel.
        </p>
        <p>
            You can use your channel to spread torrents to other Tribler users.<br />
            If your channel provides other Tribler users with original or popular content, then they might mark your channel as one of their favorites.<br />
            This will help to promote your channel, because the number of users which have marked a channel as one of their favorites is used to calculate popularity.
            Additionally, when another Tribler user marks your channel as a favorite they help you distribute all the .torrent files.
        </p>
        <p>
            Currently <em>three</em> options exist to spread torrents. Two of them, periodically importing .torrents from an rss feed and manually adding .torrent files, are available from the 'Manage' tab. <br />
            The third option is available from the torrentview after completely downloading a torrent and allows you to add a torrent to your channel with a single click.
        </p>
                """
        overviewpage = wx.Panel(notebook)
        overviewpage.SetBackgroundColour(LIST_DESELECTED)
        overviewtext = self.createHtml(overviewpage, text)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(overviewtext, 1, wx.EXPAND)
        overviewpage.SetSizer(hSizer)
        notebook.AddPage(overviewpage, "Overview")
        
        #shared files page
        filespage = wx.Panel(notebook)
        filespage.SetBackgroundColour(LIST_DESELECTED)
        self.header = ListHeader(filespage, columns, 0)
        self.list = ListBody(filespage, filespage, columns, spacers[0], spacers[1], singleSelect)
        self.list.SetBackgroundColour(background)
        
        #small onexpand hack
        filespage.OnExpand = self.parent.OnExpand
        filespage.OnCollapse = self.parent.OnCollapse
        filespage.OnSort = self.parent.OnSort
        
        """
        Disabled delete, does not actually work (purely local)
        listbuttons = wx.Panel(filespage)
        listbuttons.SetBackgroundColour(LIST_DESELECTED)
        removesel = wx.Button(listbuttons, -1, "Remove Selected")
        removesel.Bind(wx.EVT_BUTTON, self.parent.OnRemoveSelected)
        removeall = wx.Button(listbuttons, -1, "Remove All")
        removeall.Bind(wx.EVT_BUTTON, self.parent.OnRemoveAll)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.AddStretchSpacer()
        hSizer.Add(removesel, 0, wx.ALL, 3)
        hSizer.Add(removeall, 0, wx.ALL, 3)
        listbuttons.SetSizer(hSizer)
        """
        
        vSizer = wx.BoxSizer(wx.VERTICAL)
        vSizer.Add(self.header, 0, wx.EXPAND)
        vSizer.Add(self.list, 1, wx.EXPAND)
        #vSizer.Add(listbuttons, 0, wx.EXPAND)
        filespage.SetSizer(vSizer)
        notebook.AddPage(filespage, "Shared torrents")
        
        #manage page
        self.managepage = wx.Panel(notebook)
        self.managepage.SetBackgroundColour(LIST_DESELECTED)
        vSizer = wx.BoxSizer(wx.VERTICAL)
        
        #intro
        text =  """
        <p>
            Here you can manage your channel.
        </p>
        <p>
            Rss feeds are periodically checked for new .torrent files. For each item in the rss feed a .torrent file should be present in either:
            <ul>
            <li>The link element</li>
            <li>A src attribute</li>
            <li>A url attribute</li>
            </ul>
        </p>
                """
        self.manageText = self.createHtml(self.managepage, text)
        vSizer.Add(self.manageText, 0, wx.EXPAND)
        
        #rss
        self.gridSizer = wx.FlexGridSizer(0, 2, 3)
        self.gridSizer.AddGrowableCol(1)
        self.gridSizer.AddGrowableRow(0)
        
        self.BuildRssPanel(self.managepage, self.gridSizer)
        vSizer.Add(self.gridSizer, 1, wx.EXPAND|wx.ALL, 10)
        self.managepage.SetSizer(vSizer)
        
        notebook.AddPage(self.managepage, "Manage")
        boxSizer = wx.BoxSizer(wx.HORIZONTAL)
        boxSizer.Add(notebook, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(boxSizer)
        
        self.Layout()
    
    def BuildRssPanel(self, parent, sizer):
        sizer.Add(self.createHeader(parent, "Current rss-feeds:","(which are periodically checked)"))
        
        rssSizer = wx.BoxSizer(wx.VERTICAL)
        urls = self.torrentfeed.getUrls("active")
        if len(urls) > 0:
            rssPanel = wx.lib.scrolledpanel.ScrolledPanel(parent)
            rssPanel.SetBackgroundColour(LIST_DESELECTED)
            
            urlSizer = wx.FlexGridSizer(0, 2, 0, 5)
            urlSizer.AddGrowableCol(0)
            for url in urls:
                rsstext = wx.StaticText(rssPanel, -1, url.replace('&', '&&'))
                rsstext.SetMinSize((1,-1))
                
                deleteButton = wx.Button(rssPanel, -1, "Delete")
                deleteButton.url = url
                deleteButton.text = rsstext
                deleteButton.Bind(wx.EVT_BUTTON, self.OnDeleteRss)
                
                urlSizer.Add(rsstext, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
                urlSizer.Add(deleteButton, 0, wx.ALIGN_RIGHT)
            
            rssPanel.SetMinSize((-1, 50))
            rssPanel.SetSizer(urlSizer)
            rssPanel.SetupScrolling(rate_y = 5)
            rssSizer.Add(rssPanel, 1, wx.EXPAND)
            
            refresh = wx.Button(parent, -1, "Refresh all rss-feeds")
            refresh.Bind(wx.EVT_BUTTON, self.OnRefreshRss)
            rssSizer.Add(refresh, 0, wx.ALIGN_RIGHT | wx.TOP, 3)
        else:
            rssSizer.Add(wx.StaticText(parent, -1, "No rss feeds are being monitored."))
            
        #add-rss
        rssSizer.Add(wx.StaticText(parent, -1, "Add an rss-feed:"), 0, wx.TOP, 3)
        addSizer = wx.BoxSizer(wx.HORIZONTAL)
        url = wx.TextCtrl(parent)
        addButton = wx.Button(parent, -1, "Add")
        addButton.url = url
        addButton.Bind(wx.EVT_BUTTON, self.OnAddRss)
        addSizer.Add(url, 1 , wx.ALIGN_CENTER_VERTICAL)
        addSizer.Add(addButton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5)
        rssSizer.Add(addSizer, 0, wx.EXPAND, 10)
        sizer.Add(rssSizer, 1, wx.EXPAND|wx.LEFT|wx.TOP|wx.BOTTOM, 10)
        
        #manual
        sizer.Add(self.createHeader(parent, "Manually import a .torrent file:","(downloaded from another source)"), 0, wx.EXPAND)
        browseButton = wx.Button(parent, -1, "Browse for .torrent files")
        browseButton.Bind(wx.EVT_BUTTON, self.OnManualAdd)
        browseButton2 = wx.Button(parent, -1, "Browse for a directory")
        browseButton2.Bind(wx.EVT_BUTTON, self.OnManualDirAdd)
        
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(browseButton)
        hSizer.Add(browseButton2, 0, wx.LEFT, 5)
        sizer.Add(hSizer, 0, wx.ALIGN_RIGHT|wx.LEFT|wx.TOP, 10)
    
    def RebuildRssPanel(self):
        self.gridSizer.ShowItems(False)
        self.gridSizer.Clear()
        
        self.BuildRssPanel(self.managepage, self.gridSizer)
        self.managepage.Layout()
    
    def createHtml(self, parent, text):
        html = wx.html.HtmlWindow(parent)
        html.SetPage(text)
        return html
    
    def createHeader(self, parent, title, subtitle):
        title = wx.StaticText(parent, -1, title)
        font = title.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(font)
        vSizer = wx.BoxSizer(wx.VERTICAL)
        vSizer.Add(title)
        vSizer.Add(wx.StaticText(parent, -1, subtitle))
        return vSizer
    
    def OnChange(self, event):
        page = event.GetSelection()
        if page == 1:
            self.parent.ShowList()
            self.parent.ScrollToEnd(False)
        elif page == 2:
            self.manageText.SetMinSize((-1,self.manageText.GetVirtualSize()[1]))
            self.managepage.Layout()
        event.Skip()
    
    def OnAddRss(self, event):
        item = event.GetEventObject()
        url = item.url.GetValue().strip()
        if len(url) > 0:
            self.torrentfeed.addURL(url)
            self.RebuildRssPanel()
            
            self.uelog.addEvent(message="MyChannel: rssfeed added", type = 2)
        
    def OnDeleteRss(self, event):
        item = event.GetEventObject()
        
        self.torrentfeed.deleteURL(item.url)
        self.RebuildRssPanel()
        
        self.uelog.addEvent(message="MyChannel: rssfeed removed", type = 2)
    
    def OnRefreshRss(self, event):
        self.torrentfeed.refresh()
        
        button = event.GetEventObject()
        button.Enable(False)
        wx.CallLater(5000, button.Enable, True)
        
        self.uelog.addEvent(message="MyChannel: rssfeed refreshed", type = 2)
        
    def OnManualAdd(self, event):
        dlg = wx.FileDialog(self,"Choose .torrent file", wildcard = "BitTorrent file (*.torrent) |*.torrent", style = wx.DEFAULT_DIALOG_STYLE|wx.FD_MULTIPLE)
        
        path = DefaultDownloadStartupConfig.getInstance().get_dest_dir() + os.sep
        dlg.SetPath(path)
        if dlg.ShowModal() == wx.ID_OK:
            files = dlg.GetPaths()
            self._import_torrents(files)
            
            self.uelog.addEvent(message="MyChannel: manual import files", type = 2)
            
    def OnManualDirAdd(self, event):
        dlg = wx.DirDialog(self,"Choose a directory containing the .torrent files", style = wx.wx.DD_DIR_MUST_EXIST)
        
        path = DefaultDownloadStartupConfig.getInstance().get_dest_dir() + os.sep
        dlg.SetPath(path)
        
        if dlg.ShowModal() == wx.ID_OK and os.path.isdir(dlg.GetPath()):
            full_files = []
            files = os.listdir(dlg.GetPath())
            for file in files:
                full_files.append(os.path.join(dlg.GetPath(), file))
            self._import_torrents(full_files)
            
            self.uelog.addEvent(message="MyChannel: manual import directory", type = 2)
    
    def _import_torrents(self, files):
        nr_imported = 0
        for file in files:
            if file.endswith(".torrent"):
                self.torrentfeed.addFile(file)
                nr_imported += 1
        
        if nr_imported > 0:
            self.parent.manager.OnNewTorrent()
            if nr_imported == 1:
                self.guiutility.Notify('New torrent added to My Channel', wx.ART_INFORMATION)
            else:
                self.guiutility.Notify('Added %d torrents to your Channel'%nr_imported, wx.ART_INFORMATION)
    
    def OnRssItem(self, rss_url, infohash, torrent_data):
        #this is called from another non-gui thread, thus we wrap it using wx.callafter
        self.parent.GetManager()
        wx.CallAfter(self.parent.manager.OnNewTorrent)

class MyChannelDetails(wx.Panel):
    def __init__(self, parent, torrent, my_permid):
        self.parent = parent
        self.torrent = torrent
        self.my_permid = my_permid
        
        self.uelog = UserEventLogDBHandler.getInstance()
        self.guiutility = GUIUtility.getInstance()

        self.subsupport = SubtitlesSupport.getInstance()
        self.supportedLang = self.subsupport.langUtility.getLangSupported()
        self.supportedLangFull = self.supportedLang.values()
        self.supportedLangFull.sort()
        
        wx.Panel.__init__(self, parent)
        
        self.borderSizer = wx.BoxSizer()
        self.SetSizer(self.borderSizer)
        
        self.SetBackgroundColour(LIST_DESELECTED)
        self.guiutility.torrentsearch_manager.isTorrentPlayable(self.torrent, callback = self.showTorrent)
    
    def showTorrent(self, torrent, information):
        wx.CallAfter(self._showTorrent, torrent, information)
        
    def _showTorrent(self, torrent, information):
        notebook = wx.Notebook(self, style = wx.NB_NOPAGETHEME)
        listCtrl = SortedListCtrl(notebook, 2)
        listCtrl.InsertColumn(0, 'Name')
        listCtrl.InsertColumn(1, 'Size', wx.LIST_FORMAT_RIGHT)
            
        self.il = wx.ImageList(16,16)
        play_img = self.il.Add(wx.Bitmap(os.path.join(self.guiutility.vwxGUI_path, 'images', 'library_play.png'), wx.BITMAP_TYPE_ANY))
        file_img = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, size = (16,16)))
        listCtrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
            
        for filename, size in information[2]:
            try:
                pos = listCtrl.InsertStringItem(sys.maxint, filename)
            except:
                try:
                    pos = listCtrl.InsertStringItem(sys.maxint, filename.decode('utf-8','ignore'))
                except:
                    print >> sys.stderr, "Could not format filename", torrent['name']
            listCtrl.SetItemData(pos, pos)
            listCtrl.itemDataMap.setdefault(pos, [filename, size])
            
            size = self.guiutility.utility.size_format(size)
            listCtrl.SetStringItem(pos, 1, size)
            
            if filename in information[1]:
                listCtrl.SetItemColumnImage(pos, 0, play_img)
            else:
                listCtrl.SetItemColumnImage(pos, 0, file_img)
            
        listCtrl.setResizeColumn(0)
        listCtrl.SetMinSize((1,-1))
        listCtrl.SetColumnWidth(1, wx.LIST_AUTOSIZE) #autosize only works after adding rows
        notebook.AddPage(listCtrl, "Files")
        
        if self.subsupport._registered and information[0]:
            self.subtitles = wx.Panel(notebook)
            self.vSizer = wx.BoxSizer(wx.VERTICAL)
            self.subtitles.SetSizer(self.vSizer)
            notebook.AddPage(self.subtitles, "Subtitles")
            self.AddSubs()
        
        self.borderSizer.Add(notebook, 1, wx.EXPAND)
        self.Layout()
        self.parent.parent_list.OnChange()
    
    def AddSubs(self):
        self.vSizer.ShowItems(False)
        self.vSizer.DeleteWindows()
        self.vSizer.Clear()
        
        currentsubs = self.subsupport.getSubtitleInfos(self.my_permid, self.torrent['infohash'])
        if len(currentsubs) > 0:
            header = wx.StaticText(self.subtitles, -1, "Current Subtitles")
            font = header.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            header.SetFont(font)
            self.vSizer.Add(header, 0, wx.BOTTOM, 3)
            
            curlang = [self.supportedLang[langkey] for langkey in currentsubs.keys()]
            curlang.sort()
            for lang in curlang:
                self.vSizer.Add(wx.StaticText(self.subtitles, -1, lang), 0, wx.LEFT, 6)
        else:
            header = wx.StaticText(self.subtitles, -1, "No subtitles added to this .torrent.")
            font = header.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            header.SetFont(font)
            self.vSizer.Add(header)
        
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(wx.StaticText(self.subtitles, -1, "Add a subtitle to this .torrent"), 0, wx.ALIGN_CENTER_VERTICAL)
        hSizer.AddStretchSpacer()
        button = wx.Button(self.subtitles, -1, "Browse")
        button.Bind(wx.EVT_BUTTON, self.OnClick)
        hSizer.Add(button)
        self.vSizer.Add(hSizer, 0, wx.EXPAND)
        self.vSizer.Layout()
    
    def OnClick(self, event):
        dlg = wx.FileDialog(self,"Choose .srt file", wildcard = "SubRip file (*.srt) |*.srt", style = wx.DEFAULT_DIALOG_STYLE)
        
        path = DefaultDownloadStartupConfig.getInstance().get_dest_dir() + os.sep
        dlg.SetPath(path)
        if dlg.ShowModal() == wx.ID_OK:
            file = dlg.GetPath()
            dlg.Destroy()
            
            dlg = wx.SingleChoiceDialog(self, 'Choose a language for this subtitle?', 'Language?',self.supportedLangFull)
            if dlg.ShowModal() == wx.ID_OK:
                lang = dlg.GetStringSelection()
                for key, value in self.supportedLang.iteritems():
                    if value == lang:
                        self.subsupport.publishSubtitle(self.torrent['infohash'], key, file)
                        self.uelog.addEvent(message="MyChannel: new subtitle added", type = 2)
                        self.AddSubs()
                        
                        self.parent.parent_list.OnChange()
                        break
        dlg.Destroy()
    
class SwarmHealth(wx.Panel):
    def __init__(self, parent, bordersize = 0, size = wx.DefaultSize):
        wx.Panel.__init__(self, parent, size = size, style = wx.NO_BORDER)
        self.bordersize = bordersize
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
    
    def SetRatio(self, seeders, leechers):
        ratio = 0
        pop = 0
        
        self.blue = 0
        if leechers <= 0 and seeders <= 0:
            self.barwidth = 0
            
            self.green = 0
            self.red = 0
        else:
            if leechers == 0:
                ratio = sys.maxint
            elif seeders == 0:
                ratio = 0
            else:
                ratio = seeders/(leechers*1.0)
            
            if ratio == 0:
                self.barwidth = 1
                self.green = 0
                self.red = 0
            else:
                pop = seeders + leechers
                if pop > 0:
                    self.barwidth = min(max(math.log(pop*4,10) * 2, 1) / 10.0, 1) #let it max at 25k population
                else:
                    self.barwidth = 1
                
                self.green = max(0, min(255, 125 + (ratio * 130)))
                self.red = max(0, min(255, 125 + ((1 - ratio) * 130)))
        self.Refresh()
        
        if self.barwidth == 0:
            tooltip = 'Unknown swarmsize and seeder to leecher ratio.'
        else:
            if pop < 10:
                tooltip = 'A small swarm'
            elif pop < 500:
                tooltip = 'A medium-sized swarm'
            else:
                tooltip = 'A large swarm'
            
            if ratio == 0:
                tooltip += ', with no seeders.'
            elif ratio < 0.3:
                tooltip += ', with much more leechers than seeders.'
            elif ratio < 1:
                tooltip += ', with more leechers than seeders.'
            elif ratio == sys.maxint:
                tooltip += ', with only seeders.'
            else:
                tooltip += ', with more seeders than leechers.'
        self.SetToolTipString(tooltip)
        
    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        
        width, height = self.GetClientSize()
        width -= self.bordersize * 2
        width -= 1
        width -= width % 10
        width += 1
        
        xpos = (self.GetClientSize()[0] - width) / 2
            
        dc.SetPen(wx.Pen(self.GetParent().GetForegroundColour()))
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.DrawRectangle(xpos, 0, width, height)
                
        dc.SetPen(wx.TRANSPARENT_PEN)
        
        dc.SetBrush(wx.Brush((self.red, self.green, self.blue), wx.SOLID))
        
        if self.barwidth > 0:
            dc.DrawRectangle(xpos + 1, 1,  self.barwidth * (width - 2), height-2)
        
        if self.green > 0 or self.red > 0:
            dc.SetPen(wx.WHITE_PEN)
            for i in range(1,10):
                x = xpos + (width/10) * i
                dc.DrawLine(x, 1, x, height - 1)
        
        dc.SetPen(wx.BLACK_PEN)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(xpos, 0, width, height)

    def OnEraseBackground(self, event):
        pass
    
class ChannelPopularity(wx.Panel):
    def __init__(self, parent, background, bitmap, bordersize = 0, size = wx.DefaultSize):
        wx.Panel.__init__(self, parent, size = size, style = wx.NO_BORDER)
        self.background = background
        self.bitmap = bitmap
        self.bordersize = bordersize
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
    
    def SetVotes(self, votes):
        self.votes = votes
        self.Refresh()
    
    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        
        bitmapWidth, bitmapHeight = self.bitmap.GetSize()
        
        width, height = self.GetClientSize()
        width -= self.bordersize * 2
        width = min(width, 5 * bitmapWidth)
        
        xpos = self.bordersize
        ypos = (height - bitmapHeight) / 2

        for i in range(5):
            dc.DrawBitmap(self.background, xpos + (i * bitmapWidth), ypos, True)

        dc.SetClippingRegion(xpos, ypos, width * self.votes, bitmapHeight)
        for i in range(5):
            dc.DrawBitmap(self.bitmap, xpos + (i * bitmapWidth), ypos, True)
    
    def OnEraseBackground(self, event):
        pass
