import os
import sys
import wx
from wx import html
from time import time
from datetime import date, datetime

from Tribler.Main.vwxGUI.GuiUtility import GUIUtility
from Tribler.Core.API import *
from Tribler.__init__ import LIBRARYNAME
from Tribler.Core.Utilities.utilities import get_collected_torrent_filename
from Tribler.Subscriptions.rss_client import TorrentFeedThread
from Tribler.Core.CacheDB.sqlitecachedb import bin2str

from list_footer import *
from list_header import *
from list_body import *
from list_details import *

LISTCOLOR = '#E6E6E6'

class RemoteSearchManager:
    def __init__(self, list):
        self.list = list
        self.oldkeywords = ''
        self.data_channels = []
        
        self.guiutility = GUIUtility.getInstance()
        self.torrentsearch_manager = self.guiutility.torrentsearch_manager
        self.channelsearch_manager = self.guiutility.channelsearch_manager
        
    def refresh(self):
        [total_items, nrfiltered, data_files] = self.torrentsearch_manager.getHitsInCategory()
        [total_channels, self.data_channels] = self.channelsearch_manager.getChannelHits()
        
        keywords = ' '.join(self.torrentsearch_manager.searchkeywords['filesMode']) 
        self.list.SetNrResults(total_items, nrfiltered, total_channels, keywords)
        self.list.SetFF(self.guiutility.getFamilyFilter())
        
        if self.oldkeywords != keywords:
            self.list.Reset()
            self.oldkeywords = keywords
            
        self.list.SetData(data_files)
        
    def refresh_channel(self):
        [total_channels, self.data_channels] = self.channelsearch_manager.getChannelHits()
        keywords = ' '.join(self.torrentsearch_manager.searchkeywords['filesMode'])
        self.list.SetNrResults(None, None, total_channels, keywords)
    
    def downloadStarted(self, infohash):
        if self.list.InList(infohash):
            item = self.list.GetItem(infohash)
            torrent_details = item.GetExpandedPanel()
            torrent_details.ShowPanel(1)
            
    def torrentUpdated(self, infohash):
        if self.list.InList(infohash):
            data = self.torrentsearch_manager.torrent_db.getTorrent(infohash)
            self.list.RefreshData(infohash, data)

class LocalSearchManager:
    def __init__(self, list):
        self.list = list
        self.torrentsearch_manager = GUIUtility.getInstance().torrentsearch_manager 
        
    def refresh(self):
        [total_items, nrfiltered, data_files] = self.torrentsearch_manager.getHitsInCategory('libraryMode', sort="name")
        self.list.SetData(data_files)
        
class ChannelSearchManager:
    def __init__(self, list):
        self.list = list
        self.category = ''
        
        self.channelsearch_manager = GUIUtility.getInstance().channelsearch_manager

    def refresh(self, search_results = None):
        [total_items, data] = self.channelsearch_manager.getSubscriptions()
        favorites = data
        
        if search_results == None:
            if self.category == 'New':
                [total_items,data] = self.channelsearch_manager.getNewChannels()
                self.list.SetTitle('New Channels', total_items)
            elif self.category == 'Popular':
                [total_items,data] = self.channelsearch_manager.getPopularChannels()
                self.list.SetTitle('Popular Channels', total_items)
            elif self.category == 'All':
                [total_items,data] = self.channelsearch_manager.getAllChannels()
                self.list.SetTitle('All Channels', total_items)
            elif self.category == 'Favorites':
                self.list.SetTitle('Your Favorites', total_items)
        else:
            self.list.select_popular = False
            total_items = len(search_results)
            data = search_results
            
            keywords = ' '.join(self.channelsearch_manager.searchkeywords) 
            self.list.SetTitle('Search results for "%s"'%keywords, total_items)
        
        self.list.SetData(data, favorites)
        #self.list.SetFocus()
        
    def SetCategory(self, category):
        if category != self.category:
            self.category = category
            self.list.Reset()
            
            if category != 'searchresults':
                self.refresh()
        else:
            self.list.DeselectAll()
        
    def channelUpdated(self, permid):
        if self.list.ready:
            if self.list.InList(permid):
                data = self.channelsearch_manager.getChannel(permid)
                self.list.RefreshData(permid, data)
            elif self.category != 'searchresults':
                #Show new channel, but only if we are not showing search results
                self.refresh()

class ChannelManager():
    def __init__(self, list):
        self.list = list
        self.list.publisher_id = 0
        self.guiutility = GUIUtility.getInstance()
        self.channelsearch_manager = self.guiutility.channelsearch_manager
        self.torrentsearch_manager = self.guiutility.torrentsearch_manager
        
    def refresh(self, permid):
        self.list.Reset()
        vote = self.channelsearch_manager.getMyVote(permid)
        
        self.list.footer.SetStates(vote == -1, vote == 2)
        self.list.publisher_id = permid
        self.list.SetFF(self.guiutility.getFamilyFilter())
        self._refresh_list()
        
    def _refresh_list(self):
        [total_items, nrfiltered, torrentList]  = self.channelsearch_manager.getTorrentsFromPublisherId(self.list.publisher_id)
        torrentList = self.torrentsearch_manager.addDownloadStates(torrentList)
        
        if self.list.SetData(torrentList) < total_items: #some items are filtered by quickfilter (do not update total_items)
            self.list.SetNrResults(None, nrfiltered, None, None)
        else:
            self.list.SetNrResults(total_items, nrfiltered, None, None)
    
    def downloadStarted(self, infohash):
        if self.list.InList(infohash):
            item = self.list.GetItem(infohash)
            
            torrent_details = item.GetExpandedPanel()
            torrent_details.ShowPanel(1)

    def torrentUpdated(self, infohash):
        if self.list.InList(infohash):
            data = self.channelsearch_manager.getTorrentFromPublisherId(self.list.publisher_id, bin2str(infohash))
            self.list.RefreshData(infohash, data)
            
    def channelUpdated(self, permid):
        if self.list.publisher_id == permid:
            self._refresh_list()

class MyChannelManager():
    def __init__(self, list):
        self.list = list
        self.channelsearch_manager = GUIUtility.getInstance().channelsearch_manager
        self.my_permid = self.channelsearch_manager.channelcast_db.my_permid
        
    def refresh(self):
        nr_favorite = self.channelsearch_manager.channelcast_db.getSubscribersCount(bin2str(self.my_permid))
        [total_items, nr_filtered, torrentList] = self.channelsearch_manager.getTorrentsFromMyChannel()
        self.list.SetData(torrentList, nr_favorite)
        
    def RemoveItems(self, infohashes):
        for infohash in infohashes:
            self.channelsearch_manager.channelcast_db.deleteOwnTorrent(infohash)
        self.list.Reset()
        self.refresh()
        
    def RemoveAllItems(self):
        self.channelsearch_manager.channelcast_db.deleteTorrentsFromPublisherId(self.channelsearch_manager.channelcast_db.my_permid)
        self.list.Reset()
        self.refresh()

class List(wx.Panel):
    def __init__(self, columns, background, spacers = [0,0], singleSelect = False, showChange = False):
        """
        Column alignment:
        
        Text should usually be left-aligned, though if there are only a small number of possible values and 
        they are all short, then centre alignment can work well.
        
        Numbers should usually be right-aligned with each other.
        
        Numbers with decimal points should have the same number of digits to the right of the point. They 
        should be right-aligned (so the decimal points are all aligned).
        
        Numbers are right-aligned to make it easy to visually compare magnitudes. So in cases where the 
        magnitude is irrelevant (for example, listing the team numbers of football players) you could consider left- or centre-alignment.
        For the same reason, numbers representing magnitudes should use the same units. For example, Mac OS "helpfully" displays file sizes 
        in differing units (kB, MB). This makes it very easy to miss a 3MB file in a listing of 3kB files. If it were listed as 3000kB then it would stand out appropriately.
        
        Headings often look good if they are aligned the same as their data. You could consider alternatives such as centre-alignment, but 
        avoid situations where a column heading is not actually above the data in the column (e.g. a wide column with left-aligned header and right-aligned data).
        
        taken from: http://uxexchange.com/questions/2249/text-alignment-in-tables-legibility
        """
        
        self.columns = columns
        self.background = background
        self.spacers = spacers
        self.singleSelect = singleSelect
        self.showChange = showChange
        self.ready = False
        
        pre = wx.PrePanel()
        # the Create step is done by XRC. 
        self.PostCreate(pre)
        if sys.platform == 'linux2': 
            self.Bind(wx.EVT_SIZE, self.OnCreate)
        else:
            self.Bind(wx.EVT_WINDOW_CREATE, self.OnCreate)
    
    def OnCreate(self, event):
        if sys.platform == 'linux2': 
            self.Unbind(wx.EVT_SIZE)
        else:
            self.Unbind(wx.EVT_WINDOW_CREATE)
        
        wx.CallAfter(self._PostInit)
        event.Skip()
    
    def _PostInit(self):
        vSizer = wx.BoxSizer(wx.VERTICAL)

        self.guiutility = GUIUtility.getInstance()
        self.uelog = UserEventLogDBHandler.getInstance()
        
        self.header = self.CreateHeader()
        vSizer.Add(self.header, 0, wx.EXPAND)
        
        self.list = self.CreateList()
        listSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        #left and right borders
        leftLine = wx.Panel(self, size=(1,-1))
        leftLine.SetBackgroundColour(self.background)
        rightLine = wx.Panel(self, size=(1,-1))
        rightLine.SetBackgroundColour(self.background)
        
        listSizer.Add(leftLine, 0, wx.EXPAND)
        listSizer.Add(self.list, 1, wx.EXPAND)
        listSizer.Add(rightLine, 0, wx.EXPAND)
        vSizer.Add(listSizer, 1, wx.EXPAND)
        
        self.footer = self.CreateFooter()
        vSizer.Add(self.footer, 0, wx.EXPAND)
        
        self.SetSizer(vSizer)
        self.Layout()
        
        self.list.Bind(wx.EVT_SIZE, self.OnSize)
        self.ready = True
    
    def format_time(self, val):
        today = datetime.today()
        discovered = datetime.fromtimestamp(val)
        
        diff = today - discovered
        if diff.days > 0 or today.day != discovered.day:
            return discovered.strftime('%d-%m-%Y')
        return discovered.strftime('Today %H:%M')

    def format_size(self, val):
        size = (val/1048576.0)
        return "%.0f MB"%size
    
    def CreateHeader(self):
        return ListHeader(self, self.background, self.columns)
    
    def CreateList(self):
        return ListBody(self, self.background, self.columns, self.spacers[0], self.spacers[1], self.singleSelect, self.showChange)
    
    def CreateFooter(self):
        return ListFooter(self, self.background)
    
    def OnSize(self, event):
        diff = self.header.GetClientSize()[0] - self.list.GetClientSize()[0]
        self.header.SetSpacerRight(diff)
        self.footer.SetSpacerRight(diff)
        event.Skip()
        
    def OnSort(self, column, reverse):
        self.list.OnSort(column, reverse)
    
    def Reset(self):
        self.header.Reset()
        self.list.Reset()
        
        self.Layout()
    
    def OnExpand(self, item):
        pass
    
    def OnCollapse(self, item, panel):
        self.OnCollapseInternal(item)
        if panel:
            panel.Destroy()
            
    def OnCollapseInternal(self, item):
        pass
    
    def GetManager(self):
        pass
    
    def SetData(self, data):
        pass
    def RefreshData(self, key, data):
        pass
        
    def InList(self, key):
        if self.ready:
            return self.list.InList(key)
    
    def GetItem(self, key):
        if self.ready:
            return self.list.GetItem(key)
    
    def Focus(self):
        if self.ready:
            self.list.SetFocus()
        
    def ScrollToEnd(self, scroll_to_end):
        if self.ready:
            self.list.ScrollToEnd(scroll_to_end)
    
    def DeselectAll(self):
        self.list.DeselectAll()
        
    def Select(self, key, raise_event = True):
        self.list.Select(key, raise_event)
    
class SearchList(List):
    def __init__(self):
        self.guiutility = GUIUtility.getInstance()
        self.utility = self.guiutility.utility
        
        columns = [{'name':'Name', 'width': wx.LIST_AUTOSIZE, 'sortAsc': True, 'icon': 'tree'}, \
                   {'name':'Size', 'width': 70, 'style': wx.ALIGN_RIGHT, 'fmt': self.format_size}, \
                   #{'name':'Seeders', 'width': wx.LIST_AUTOSIZE_USEHEADER, 'style': wx.ALIGN_RIGHT, 'fmt': self.format}, \
                   #{'name':'Leechers', 'width': wx.LIST_AUTOSIZE_USEHEADER, 'style': wx.ALIGN_RIGHT, 'fmt': self.format}, \
                   {'type':'method', 'width': wx.LIST_AUTOSIZE_USEHEADER, 'method': self.CreateRatio, 'name':'Popularity'}, \
                   {'type':'method', 'width': -1, 'method': self.CreateDownloadButton}]
       
        List.__init__(self, columns, LISTCOLOR, [7,7], True)
    
    def GetManager(self):
        if getattr(self, 'manager', None) == None:
            self.manager = RemoteSearchManager(self) 
        return self.manager
    
    def CreateHeader(self):
        return SearchHeader(self, self.background, self.columns)

    def CreateFooter(self):
        footer = ChannelResultFooter(self, self.background)
        footer.SetEvents(self.OnChannelResults)
        return footer 
    
    def SetNrResults(self, nr, nr_filtered, nr_channels, keywords):
        if isinstance(nr, int):
            if nr == 0:
                self.header.SetTitle('No results for "%s"'%keywords)
            elif nr == 1:
                self.header.SetTitle('Got 1 result for "%s"'%keywords)
            else:
                self.header.SetTitle('Got %d results for "%s"'%(nr, keywords))
            self.total_results = nr
        
        if isinstance(nr_filtered, int):
            self.header.SetFiltered(nr_filtered)
            
        if isinstance(nr_channels, int):
            if nr_channels == 0:
                self.footer.SetMessage('No matching channels for "%s"'%keywords)
            elif nr_channels == 1:
                self.footer.SetMessage('Additionally, got 1 channel for "%s"'%keywords)
            else:
                self.footer.SetMessage('Additionally, got %d channels for "%s"'%(nr_channels, keywords))
            self.footer.EnableResults(nr_channels > 0)
        
    def SetFilteredResults(self, nr):
        if nr != self.total_results: 
            self.header.SetNrResults(nr)
        else:
            self.header.SetNrResults()
    
    def SetFF(self, family_filter):
        self.header.SetFF(family_filter)
    
    def toggleFamilyFilter(self):
        self.guiutility.toggleFamilyFilter()
        self.guiutility.dosearch()
        
        self.uelog.addEvent(message="SearchList: user toggled family filter", type = 2)  
    
    def SetData(self, data):
        if len(data) > 0:
            #data = [(file['infohash'],[file['name'], file['length'], file['num_seeders'], file['num_leechers']], file) for file in data]
            data = [(file['infohash'],[file['name'], file['length'], 0, 0], file) for file in data]
            return self.list.SetData(data)
        message =  'No torrents matching your query are found. \n'
        message += 'Try leaving Tribler running for a longer time to allow it to discover new torrents, or use less specific search terms.'
        if self.guiutility.getFamilyFilter():
            message += '\n\nAdditionally, you could disable the "Family Filter" by clicking on it.'
        self.list.ShowMessage(message)
        return 0
    
    def RefreshData(self, key, data):
        data = (data['infohash'],[data['name'], data['length'], 0, 0], data)
        self.list.RefreshData(key, data)
        
        item = self.list.GetItem(key)
        panel = item.GetExpandedPanel()
        if panel:
            panel.UpdateStatus()
    
    def CreateDownloadButton(self, parent, item):
        button = wx.Button(parent, -1, 'Download', style = wx.BU_EXACTFIT)
        button.item = item
        item.button = button
        
        if not item.original_data.get('ds',False):
            button.Bind(wx.EVT_MOUSE_EVENTS, self.OnDownload)
        else:
            button.Enable(False)
        return button

    def CreateRatio(self, parent, item):
        seeders = int(item.original_data['num_seeders'])
        leechers = int(item.original_data['num_leechers'])
        item.data[-2] = seeders + leechers
        
        control = SwarmHealth(parent)
        control.SetMinSize((self.columns[-2]['width'],7))
        control.SetBackgroundColour(wx.WHITE)
        control.SetRatio(seeders, leechers)
        if leechers < 0 and seeders < 0:
            control.SetToolTipString('popularity unknown')
        else:
            control.SetToolTipString('%s seeders, %s leechers'%(seeders,leechers))
        return control
        
    def OnDownload(self, event):
        if event.LeftUp():
            item = event.GetEventObject().item
            self.StartDownload(item.original_data)
        event.Skip()
        
    def StartDownload(self, torrent):
        if isinstance(self, SelectedChannelList):
            self.uelog.addEvent(message="Torrent: torrent download from channel", type = 2)
        else:
            self.uelog.addEvent(message="Torrent: torrent download from other", type = 2)
        
        self.guiutility.torrentsearch_manager.downloadTorrent(torrent)
        
    def OnChannelResults(self, event):
        manager = self.GetManager()
        self.guiutility.showChannelResults(manager.data_channels)
        
        self.uelog.addEvent(message="SearchList: user clicked to view channel results", type = 2)  
    
    def OnExpand(self, item):
        item.button.Hide()
        item.button.Refresh()
        return TorrentDetails(item, item.original_data)
    
    def OnCollapseInternal(self, item):
        item.button.Show()
        
    def OnFilter(self, keyword):
        self.header.FilterCorrect(self.list.FilterItems(keyword))
        
    def format(self, val):
        val = int(val)
        if val < 0:
            return "?"
        return str(val)
    
class LibaryList(List):
    def __init__(self):
        self.guiutility = GUIUtility.getInstance() 
        self.utility = self.guiutility.utility
        self.torrent_manager = self.guiutility.torrentsearch_manager

        columns = [{'name':'Name', 'width': wx.LIST_AUTOSIZE, 'sortAsc': True, 'icon': 'tree'}, \
                   {'type':'method', 'name':'Completion', 'width': 250, 'method': self.CreateProgress}, \
                   {'type':'method', 'name':'Connections', 'width': wx.LIST_AUTOSIZE_USEHEADER, 'method': self.CreateConnections, 'footer_style': wx.ALIGN_RIGHT}, \
                   {'type':'method', 'name':'Down', 'width': 70, 'method': self.CreateDown, 'fmt': self.utility.speed_format_new, 'footer_style': wx.ALIGN_RIGHT}, \
                   {'type':'method', 'name':'Up', 'width': 70, 'method': self.CreateUp, 'fmt': self.utility.speed_format_new, 'footer_style': wx.ALIGN_RIGHT}]
        
     
        List.__init__(self, columns, LISTCOLOR, [7,7], True)
    
    def GetManager(self):
        if getattr(self, 'manager', None) == None:
            self.manager = LocalSearchManager(self) 
        return self.manager
    
    def CreateHeader(self):
        header = ButtonHeader(self, self.background, self.columns)
        header.SetTitle('Library')
        header.SetEvents(self.OnResume, self.OnStop, self.OnDelete)
        return header
    
    def CreateFooter(self):
        footer = TotalFooter(self, self.background, self.columns)
        footer.SetTotal(0, 'Totals:')
        return footer
    
    def CreateUp(self, parent, item):
        up = wx.StaticText(parent, style = wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE, size=(70,-1))
        item.up = up
        
        if item.data[4]:
            up.SetLabel(self.utility.speed_format_new(item.data[4]))
        return up
        
    def CreateDown(self, parent, item):
        down = wx.StaticText(parent, style = wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE, size=(70,-1))
        item.down = down
        
        if item.data[3]:
            down.SetLabel(self.utility.speed_format_new(item.data[3]))
        return down
    
    def CreateProgress(self, parent, item):
        progressPanel = ProgressPanel(parent, item)
        progressPanel.SetMinSize((self.columns[1]['width'],-1))
        progressPanel.Layout()
        
        item.progressPanel = progressPanel
        return progressPanel
    
    def CreateConnections(self, parent, item):
        connections = wx.StaticText(parent, style = wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE, size=(self.columns[2]['width'],-1))
        item.connections = connections
        
        if item.data[2]:
            connections.SetLabel(str(item.data[2][0] + item.data[2][1]))
        return connections

    def OnExpand(self, item):
        playable = False
        delete = True
        
        if item.original_data.get('ds'):
            ds = item.original_data['ds']
            
            finished = ds.get_progress() == 1.0
            if finished: #finished download
                if ds.get_status() == DLSTATUS_SEEDING:
                    resume = False
                    stop = True
                else:
                    resume = True
                    stop = False
            elif ds.get_status() in (DLSTATUS_STOPPED, DLSTATUS_REPEXING): #stopped download
                resume = True
                stop = False
            else: #active download
                resume = False
                stop = True
        else: #inactive download
            progress = item.original_data.get('progress')
            finished = progress == 100
            
            resume = True
            stop = False
        
        self.header.SetStates(resume, stop, delete)
        return LibraryDetails(item, item.original_data)

    def OnCollapseInternal(self, item):
        self.header.SetStates(False, False, False)

    def OnPlay(self, event):
        item = self.list.GetExpandedItem()
        self.torrent_manager.playTorrent(item.original_data)
    
    def OnResume(self, event):
        item = self.list.GetExpandedItem()
        if item.original_data.get('ds'):
            ds = item.original_data['ds']
            ds.get_download().restart()
            
            self.header.SetStates(False, True, True)
        else:
            #TODO: start inactive item?
            pass
    
    def OnStop(self, event):
        item = self.list.GetExpandedItem()
        if item.original_data.get('ds'):
            ds = item.original_data['ds']
            ds.get_download().stop()
            
            self.header.SetStates(True, False, True)
            
    def OnDelete(self, event):
        item = self.list.GetExpandedItem()
        
        dlg = wx.Dialog(None, -1, 'Are you sure you want to remove this torrent?', style=wx.DEFAULT_DIALOG_STYLE, size=(400,200))
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        hSizer.Add(wx.StaticBitmap(dlg, -1, wx.ArtProvider.GetBitmap(wx.ART_QUESTION, wx.ART_MESSAGE_BOX)), 0, wx.RIGHT, 5)
        
        vSizer = wx.BoxSizer(wx.VERTICAL)
        vSizer.Add(wx.StaticText(dlg, -1, "Do you want to remove '%s'\nfrom your library or also from your computer?"%item.data[0]))
        
        bSizer = wx.StdDialogButtonSizer()
        bSizer.AddStretchSpacer()
        bSizer.Add(wx.Button(dlg, wx.ID_CANCEL))
        bSizer.Add(wx.Button(dlg, wx.ID_DEFAULT, 'Only delete from library'))
        bSizer.Add(wx.Button(dlg, wx.ID_DELETE, 'Also delete from computer'))
        vSizer.Add(bSizer, 0, wx.TOP|wx.EXPAND, 5)
        hSizer.Add(vSizer)
        
        border = wx.BoxSizer()
        border.Add(hSizer, 1, wx.ALL|wx.EXPAND, 10)
        dlg.Bind(wx.EVT_BUTTON, lambda event: dlg.EndModal(event.GetId()))
        dlg.SetSizerAndFit(border)
        dlg.Centre()
        buttonId = dlg.ShowModal()
        dlg.Destroy()
        
        if buttonId == wx.ID_DEFAULT:
            self.torrent_manager.deleteTorrent(item.original_data)
            self.header.SetStates(False, False, False) #nothing selected
            self.list.RemoveItem(item)
        elif buttonId == wx.ID_DELETE:
            self.torrent_manager.deleteTorrent(item.original_data, True)
            self.header.SetStates(False, False, False) #nothing selected
            self.list.RemoveItem(item)
        
        if self.list.IsEmpty():
            self.SetData([])
    
    def RefreshItems(self, dslist):
        if self.ready:
            totals = {2:0, 3:0, 4:0}
            
            nr_finished = 0
            nr_downloading = 0
            for ds in dslist:
                infohash = ds.get_download().get_def().get_infohash()
                if infohash in self.list.items:
                    item = self.list.items[infohash]
                    item.original_data['ds'] = ds
                else:
                    self.GetManager().refresh()
                    break
                    
            for infohash, item in self.list.items.iteritems():
                status = item.progressPanel.Update()
                if status == 1:
                    nr_downloading += 1
                elif status == 2:
                    nr_finished += 1
                
                totals[2] = totals[2] + item.data[2][0] + item.data[2][1]
                totals[3] = totals[3] + item.data[3]
                totals[4] = totals[4] + item.data[4]
                
                nr_connections = str(item.data[2][0] + item.data[2][1])
                if item.connections.GetLabel() != nr_connections:
                    item.connections.SetLabel(nr_connections)
                    item.connections.Refresh()
                
                down = self.utility.speed_format_new(item.data[3])
                if item.down.GetLabel() != down:
                    item.down.SetLabel(down)
                    item.down.Refresh()
                
                up = self.utility.speed_format_new(item.data[4])
                if item.up.GetLabel() != up:
                    item.up.SetLabel(up)
                    item.up.Refresh()
            
            if len(self.list.items) > 0:
                self.footer.SetTotal(0, str(len(self.list.items)) + " items (" +str(nr_finished) + " seeding, "+str(nr_downloading) + " downloading)")
            else:
                self.footer.SetTotal(0, "0 items")
            
            for key in totals.keys():
                self.footer.SetTotal(key, totals[key])
        
    def SetData(self, data):
        if len(data) > 0:
            data = [(file['infohash'], [file['name'], [0,0], None, None, None], file) for file in data]
            return self.list.SetData(data)
        message = "Currently not downloading any torrents.\n"
        message += "You can find torrents by using our integrated search, discover them using a channel or drag and drop a torrent file downloaded from an external source."
        self.list.ShowMessage(message)
        return 0

    def Show(self):
        List.Show(self)
        self.torrent_manager.add_download_state_callback(self.RefreshItems)
        
    def Hide(self):
        wx.Panel.Hide(self)
        self.torrent_manager.remove_download_state_callback(self.RefreshItems)
        
class ChannelList(List):
    def __init__(self):
        self.guiutility = GUIUtility.getInstance()
        self.utility = self.guiutility.utility
        
        columns = [{'name':'Name', 'width': wx.LIST_AUTOSIZE, 'icon': self.__favorite_icon, 'sortAsc': True}, \
                   {'name':'Latest Update', 'width': wx.LIST_AUTOSIZE_USEHEADER, 'fmt': self.format_time}, \
                   #{'name':'Popularity', 'width': wx.LIST_AUTOSIZE_USEHEADER, 'style': wx.ALIGN_RIGHT, 'fmt': self.__format}, \
                   {'type':'method', 'width': 75, 'method': self.CreatePopularity, 'name':'Popularity', 'defaultSorted': True}, \
                   {'name':'Torrents', 'width': wx.LIST_AUTOSIZE_USEHEADER, 'style': wx.ALIGN_RIGHT}]
        
        self.favorite = wx.Bitmap(os.path.join(self.utility.getPath(),LIBRARYNAME,"Main","vwxGUI","images","starEnabled.png"), wx.BITMAP_TYPE_ANY)
        self.normal = wx.Bitmap(os.path.join(self.utility.getPath(),LIBRARYNAME,"Main","vwxGUI","images","star.png"), wx.BITMAP_TYPE_ANY)
        self.mychannel = wx.Bitmap(os.path.join(self.utility.getPath(),LIBRARYNAME,"Main","vwxGUI","images","mychannel.png"), wx.BITMAP_TYPE_ANY)
        
        self.select_popular = True
        self.my_permid = bin2str(self.guiutility.channelsearch_manager.channelcast_db.my_permid)
        List.__init__(self, columns, '#D8E9F0', [7,7], showChange = True)
    
    def __favorite_icon(self, item):
        if item.original_data[0] == self.my_permid:
            return self.mychannel
        if item.original_data[0] in self.favorites:
            return self.favorite
        return self.normal
    
    def __format(self, val):
        val = int(val)
        if val <= 0:
            return "New"
        return str(val)
    
    def CreateHeader(self):
        return SubTitleHeader(self, self.background, self.columns)
    
    def CreatePopularity(self, parent, item):
        pop = int(item.data[2])
        if pop <= 0:
            ratio = wx.StaticText(parent, -1, "New", )
            ratio.SetMinSize((self.columns[2]['width'],-1))
            return ratio
        
        ratio = min(1, pop / 5.0)
        control = ChannelPopularity(parent, self.normal, self.favorite)
        control.SetMinSize((self.columns[2]['width'],15))
        control.SetBackgroundColour(wx.WHITE)
        control.SetVotes(ratio)
        control.SetToolTipString('%s users marked this channel as one of their favorites.'%pop)
        return control
    
    def OnExpand(self, item):
        if item.original_data[0] == self.my_permid:
            self.guiutility.frame.channelcategories.Select(5)
        else:
            self.guiutility.showChannel(item.GetColumn(0), item.original_data[0])
        return False
    
    def GetManager(self):
        if getattr(self, 'manager', None) == None:
            self.manager = ChannelSearchManager(self) 
        return self.manager

    def SetData(self, data, favorites):
        if len(data) > 0:
            self.favorites = [file[0] for file in favorites]
            
            data = [(file[0],[file[1], file[2], file[3], file[4]], file) for file in data]
            return self.list.SetData(data)
        
        self.list.ShowMessage('No channels are discovered for this category.')
        return 0
        
    def RefreshData(self, key, data):
        data = (data[0],[data[1], data[2], data[3], data[4]], data)
        self.list.RefreshData(key, data)
        
    def SetTitle(self, title, nr):
        self.header.SetTitle(title)
        if title == 'Popular Channels':
            self.header.SetSubTitle("Showing the %d most popular channels" % nr)
        elif title == 'Your Favorites':
            self.header.SetSubTitle("You marked %d channels as a favorite" % nr)
        elif title == 'New Channels':
            self.header.ShowSortedBy(1)
            self.header.SetSubTitle("Discovered %d new channels (no votes yet and updated within the last 2 months)"% nr)
        else:
            if nr == 1:
                self.header.SetSubTitle("Discovered %d channel" % nr)
            else:
                self.header.SetSubTitle("Discovered %d channels" % nr)
        
class SelectedChannelList(SearchList):
    def __init__(self):
        self.guiutility = GUIUtility.getInstance()
        self.utility = self.guiutility.utility
        self.channelsearch_manager = self.guiutility.channelsearch_manager 
        
        columns = [{'name':'Name', 'width': wx.LIST_AUTOSIZE, 'sortAsc': True, 'icon': 'tree'}, \
                   #{'name':'Created', 'width': -1, 'style': wx.ALIGN_RIGHT, 'fmt': self.__format_time},\
                   {'name':'Date Added', 'width': 85, 'fmt': self.format_time, 'defaultSorted': True}, \
                   {'name':'Size', 'width': 70, 'style': wx.ALIGN_RIGHT, 'fmt': self.format_size}, \
                   {'type':'method', 'width': wx.LIST_AUTOSIZE_USEHEADER, 'method': self.CreateRatio, 'name':'Popularity'}, \
                   #{'name':'Seeders', 'width': wx.LIST_AUTOSIZE_USEHEADER, 'style': wx.ALIGN_RIGHT, 'fmt': self.format}, \
                   #{'name':'Leechers', 'width': wx.LIST_AUTOSIZE_USEHEADER, 'style': wx.ALIGN_RIGHT, 'fmt': self.format}, \
                   {'type':'method', 'width': -1, 'method': self.CreateDownloadButton}]
        
        List.__init__(self, columns, LISTCOLOR, [7,7], True)
        
    def CreateHeader(self):
        header = ChannelHeader(self, self.background, self.columns)
        header.SetEvents(self.OnBack) 
        return header
   
    def CreateFooter(self):
        footer = ChannelFooter(self, self.background)
        footer.SetEvents(self.OnSpam, self.OnFavorite, self.OnRemoveVote)
        return footer
        
    def SetTitle(self, title):
        self.title = title
        self.header.SetTitle("%s's channel"%title)
    
    def SetDescription(self, description):
        self.header.SetDescription(description)
   
    def toggleFamilyFilter(self):
        self.guiutility.toggleFamilyFilter()
        self.guiutility.showChannel(self.title, self.publisher_id)
   
    def GetManager(self):
        if getattr(self, 'manager', None) == None:
            self.manager = ChannelManager(self) 
        return self.manager
    
    def SetData(self, data):
        data = [(file['infohash'],[file['name'], file['time_stamp'], file['length'], 0, 0], file) for file in data]
        return self.list.SetData(data)
    
    def SetNrResults(self, nr, nr_filtered, nr_channels, keywords):
        if isinstance(nr, int):
            self.total_results = nr
            if self.total_results == 1:
                self.header.SetSubTitle('Discovered %d torrent'%self.total_results)
            else:
                self.header.SetSubTitle('Discovered %d torrents'%self.total_results)
        
        SearchList.SetNrResults(self, None, nr_filtered, nr_channels, keywords)
    
    def RefreshData(self, key, data):
        data = (data['infohash'],[data['name'], data['time_stamp'], data['length'], 0, 0], data)
        self.list.RefreshData(key, data)
        
        item = self.list.GetItem(key)
        panel = item.GetExpandedPanel()
        if panel:
            panel.UpdateStatus()
    
    def OnExpand(self, item):
        panel = SearchList.OnExpand(self, item)
        panel.ShowChannelAd(False)
        return panel
        
    def OnRemoveVote(self, event):
        self.channelsearch_manager.remove_vote(self.publisher_id)
        self.footer.SetStates(False, False)
    
    def OnFavorite(self, event = None):
        self.channelsearch_manager.favorite(self.publisher_id)
        self.footer.SetStates(False, True)
        
        #Request all items from connected peers
        channelcast = BuddyCastFactory.getInstance().channelcast_core
        channelcast.updateAChannel(self.publisher_id)
        
    def OnSpam(self, event):
        dialog = wx.MessageDialog(None, "Are you sure you want to report %s's channel as spam?" % self.title, "Report spam", wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT)
        if dialog.ShowModal() == wx.ID_YES:
            self.channelsearch_manager.spam(self.publisher_id)
            self.footer.SetStates(True, False)
        dialog.Destroy()
    
    def OnBack(self, event):
        self.guiutility.GoBack()
        
    def StartDownload(self, torrent):
        states = self.footer.GetStates()
        if not states[1]:
            nrdownloaded = self.channelsearch_manager.getNrTorrentsDownloaded(self.publisher_id) + 1
            if  nrdownloaded > 1:
                dial = wx.MessageDialog(self, "You have now downloaded %d torrents from this Channel.\nMarking it as a favorite will make sure that you will always have to newest content.\nDo you want to mark this channel as one of your favorites now?"%nrdownloaded, 'Mark as Favorite?', wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
                if dial.ShowModal() == wx.ID_YES:
                    self.OnFavorite()
                    self.uelog.addEvent(message="ChannelList: user clicked yes to mark as favorite", type = 2)
                else:
                    self.uelog.addEvent(message="ChannelList: user clicked no to mark as favorite", type = 2)  
                dial.Destroy()
        SearchList.StartDownload(self, torrent)
        
class MyChannelList(List):
    def __init__(self):
        self.guiutility = GUIUtility.getInstance()
        self.utility = self.guiutility.utility
        
        columns = [{'name':'Name', 'width': wx.LIST_AUTOSIZE, 'icon': 'checkbox', 'sortAsc': True}, \
                   {'name':'Date Added', 'width': 85, 'fmt': self.format_time, 'defaultSorted': True}]
   
        List.__init__(self, columns, '#D8E9F0', [7,7])
      
    def CreateHeader(self):
        self.myheader = MyChannelHeader(self, self.background, self.columns)
        self.myheader.SetName(self.utility.session.get_nickname())
        return self.myheader
    
    def CreateList(self):
        return MyChannelTabs(self, self.background, self.columns, self.spacers, self.singleSelect)
    
    def CreateFooter(self):
        #small ugly hack to correct references
        self.header = self.list.header
        self.list = self.list.list
        
        #Return default footer
        return List.CreateFooter(self)
    
    def GetManager(self):
        if getattr(self, 'manager', None) == None:
            self.manager = MyChannelManager(self) 
        return self.manager
    
    def SetData(self, data, nr_favorites):
        data = [(file['infohash'],[file['name'],file['time_stamp']], file) for file in data]
        self.myheader.SetNrTorrents(len(data), nr_favorites)
        
        if len(data) > 0:
            return self.list.SetData(data)
        self.list.ShowMessage('You are currently not sharing any torrents in your channel.')
        return 0
    
    def ShowList(self):
        self.list.SetFocus()
    
    def OnExpand(self, item):
        subsupport = SubtitlesSupport.getInstance()
        if subsupport._registered:
            return MyChannelDetails(item, item.original_data, self.GetManager().my_permid)
        return True
    
    def OnRemoveAll(self, event):
        dlg = wx.MessageDialog(self, 'Are you sure you want to remove all torrents from your channel?', 'Remove torrents', wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT)
        if dlg.ShowModal() == wx.ID_YES:
            self.manager.RemoveAllItems()
        dlg.Destroy()
    
    def OnRemoveSelected(self, event):
        dlg = wx.MessageDialog(self, 'Are you sure you want to remove all selected torrents from your channel?', 'Remove torrents', wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT)
        if dlg.ShowModal() == wx.ID_YES:
            infohashes = [key for key,item in self.list.GetExpandedItems()]
            self.manager.RemoveItems(infohashes)
        dlg.Destroy()
        
class ChannelCategoriesList(List):
    def __init__(self):
        self.guiutility = GUIUtility.getInstance()
        self.utility = self.guiutility.utility
        columns = [{'width': wx.LIST_AUTOSIZE}]
    
        List.__init__(self, columns, LISTCOLOR, [7,7], True)
    
    def CreateHeader(self):
        title = TitleHeader(self, self.background, self.columns, 1, wx.FONTWEIGHT_NORMAL)
        title.SetTitle('Categories')
        return title
    
    def CreateList(self):
        return FixedListBody(self, self.background, self.columns, self.spacers[0], self.spacers[1], self.singleSelect)    
    
    def _PostInit(self):
        List._PostInit(self)
        self.list.SetData([(1,['Popular'],None), (2,['New'],None), (3,['Favorites'],None), (4,['All'],None), (5,['My Channel'],None)])
        self.SetMinSize((-1, self.GetBestSize()[1]))
        
        self.Select(1, False)
        wx.CallAfter(self.guiutility.showChannelCategory, 'Popular', False)
        
    def OnExpand(self, item):
        if item.data[0] in ['Popular','New','Favorites','All']:
            wx.CallAfter(self.guiutility.showChannelCategory, item.data[0])
            
        elif item.data[0] == 'My Channel':
            self.guiutility.ShowPage('mychannel')
        
        #Show highlight
        return True
    
    def GetSelectedCategory(self):
        category = self.list.GetExpandedItem()
        if category:
            return category.data[0]
        return ''

    def SetQuicktip(self, quicktip):
        self.quicktip = quicktip
    def Quicktip(self, html):
        html = '<font size=\'2\'><b>Quick Tip:</b> ' + html + '</font>' 
        self.quicktip.SetPage(html)