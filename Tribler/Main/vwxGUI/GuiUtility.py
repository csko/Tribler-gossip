# Written by Jelle Roozenburg, Maarten ten Brinke, Arno Bakker, Lucian Musat 
# see LICENSE.txt for license information

from Tribler.Category.Category import Category
from Tribler.Core.BuddyCast.buddycast import BuddyCastFactory
from Tribler.Core.CacheDB.SqliteCacheDBHandler import UserEventLogDBHandler
from Tribler.Core.CacheDB.sqlitecachedb import bin2str, str2bin
from Tribler.Core.Search.SearchManager import split_into_keywords
from Tribler.Core.Utilities.utilities import *
from Tribler.Core.simpledefs import *
from Tribler.Main.Utility.constants import *
from Tribler.Main.vwxGUI.SearchGridManager import TorrentManager, \
    ChannelSearchGridManager
from Tribler.Main.vwxGUI.bgPanel import *
from Tribler.Video.VideoPlayer import VideoPlayer
from Tribler.__init__ import LIBRARYNAME
from threading import Event, Thread
from time import time
from traceback import print_exc
from webbrowser import open_new
from wx import xrc
import random
import urllib
import webbrowser
import wx
import os






DEBUG = False


class GUIUtility:
    __single = None
    
    def __init__(self, utility = None, params = None):
        if GUIUtility.__single:
            raise RuntimeError, "GUIUtility is singleton"
        GUIUtility.__single = self 
        
        # do other init
        self.utility = utility
        self.vwxGUI_path = os.path.join(self.utility.getPath(), LIBRARYNAME, 'Main', 'vwxGUI')
        self.utility.guiUtility = self
        self.params = params
        self.frame = None

       # videoplayer
        self.videoplayer = VideoPlayer.getInstance()

        # current GUI page
        self.guiPage = 'home'
        # previous pages
        self.oldpage = []

        # port number
        self.port_number = None

        # firewall
        self.firewall_restart = False # ie Tribler needs to restart for the port number to be updated

        self.guiOpen = Event()
     
        self.mainColour = wx.Colour(216,233,240) # main color theme used throughout the interface      

        self.selectedColour = self.mainColour
        self.unselectedColour = wx.WHITE ## 102,102,102      
        self.unselectedColour2 = wx.WHITE ## 230,230,230       
        self.selectedColourPending = self.mainColour  ## 208,251,244
        self.bgColour = wx.Colour(102,102,102)

        # Recall improves by 20-25% by increasing the number of peers to query to 20 from 10 !
        self.max_remote_queries = 20    # max number of remote peers to query
        
        self.current_search_query = ''
    
    def getInstance(*args, **kw):
        if GUIUtility.__single is None:
            GUIUtility(*args, **kw)
        return GUIUtility.__single
    getInstance = staticmethod(getInstance)
    
    def register(self):
        self.torrentsearch_manager = TorrentManager.getInstance(self)
        self.channelsearch_manager = ChannelSearchGridManager.getInstance(self)
        
        self.torrentsearch_manager.connect()
        self.channelsearch_manager.connect()
    
    def ShowPlayer(self, show):
        if self.frame.videoparentpanel:
            if show:
                self.frame.videoparentpanel.Show()
            else:
                self.frame.videoparentpanel.Hide()
    
    def ShowPage(self, page, *args):
        if page == 'settings':
            xrcResource = os.path.join(self.vwxGUI_path, 'settingsDialog.xrc')
            res = xrc.XmlResource(xrcResource)
            dialog = res.LoadDialog(None, 'settingsDialog')
            dialog.Centre()
            dialog.ShowModal()
            dialog.Destroy()
        
        elif page != self.guiPage:
            self.oldpage.append(self.guiPage)
            if len(self.oldpage) > 3:
                self.oldpage.pop(0)
                
            self.frame.Freeze()
            
            if page == 'search_results':
                #Show animation
                if self.frame.top_bg.ag.IsPlaying():
                    self.frame.top_bg.ag.Show()
                
                #Show list
                self.frame.searchlist.Show()
            else:
                #Stop animation
                self.frame.top_bg.ag.Stop() # only calling Hide() on mac isnt sufficient 
                self.frame.top_bg.ag.Show(False)
                
                if sys.platform == 'win32':
                    self.frame.top_bg.Layout()
                
                if self.guiPage == 'search_results':
                    #Hide list
                    self.frame.searchlist.Show(False)
            
            if page == 'channels':
                selectedcat = self.frame.channelcategories.GetSelectedCategory()
                if selectedcat in ['Popular','New','Favorites','All', 'Updated'] or self.oldpage[:-1] == 'mychannel':
                    self.frame.channelselector.Show()
                    self.frame.channellist.Show()
                    self.frame.channelcategories.Quicktip('All Channels are ordered by popularity. Popularity is measured by the number of Tribler users which have marked this channel as favorite.')
                    
                elif selectedcat == 'My Channel' and self.guiPage != 'mychannel':
                    page = 'mychannel'
                else:
                    page = 'selectedchannel'
                    
            elif self.guiPage == 'channels':
                self.frame.channellist.Show(False)
                self.frame.channelselector.Show(False)
            
            if page == 'mychannel':
                self.frame.channelcategories.Quicktip('This is your channel, other Tribler users can find this channel by searching for your username')
                
                #Show list
                self.frame.managechannel.SetChannelId(self.channelsearch_manager.channelcast_db._channel_id)
                self.frame.managechannel.Show()
            elif self.guiPage == 'mychannel':
                self.frame.managechannel.Show(False)
                
            if page == 'managechannel':
                self.frame.managechannel.Show()
            elif self.guiPage == 'managechannel':
                self.frame.managechannel.Show(False)
            
            if page == 'selectedchannel':
                self.frame.selectedchannellist.Show()
            elif self.guiPage == 'selectedchannel':
                self.frame.selectedchannellist.Show(False)
                
                if page != 'playlist':
                    self.frame.selectedchannellist.Reset()
            
            if page == 'playlist':
                self.frame.playlist.Show()
            elif self.guiPage == 'playlist':
                self.frame.playlist.Show(False)
                
            if page == 'my_files':
                #Reload content
                self.frame.librarylist.GetManager().refresh()
                
                #Open infohash
                if args:
                    self.frame.librarylist.GetManager().expand(args[0])
                
                #Show list
                self.frame.librarylist.Show()
            elif self.guiPage == 'my_files':
                #Hide list
                self.frame.librarylist.Show(False)
            
            if page == 'home':
                self.frame.home.Show()
            elif self.guiPage == 'home':
                self.frame.home.Show(False)
            
            if page == 'stats':
                self.frame.stats.Show()
            elif self.guiPage == 'stats':
                self.frame.stats.Show(False)
            
            #show player on these pages
            if not self.useExternalVideo:
                if page in ['my_files', 'mychannel', 'selectedchannel', 'channels', 'search_results', 'playlist', 'managechannel']:
                    if self.guiPage not in ['my_files', 'mychannel', 'selectedchannel', 'channels', 'search_results', 'playlist', 'managechannel']:
                        self.ShowPlayer(True)
                else:
                    self.ShowPlayer(False)
            
            self.guiPage = page
            
            self.frame.Layout()
            self.frame.Thaw()
        
            #Set focus to page
            if page == 'search_results':
                self.frame.searchlist.Focus()
            elif page == 'channels':
                self.frame.channellist.Focus()
            elif page == 'selectedchannel':
                self.frame.selectedchannellist.Focus()
            elif page =='my_files':
                self.frame.librarylist.Focus()

    def GoBack(self, scrollTo = None):
        topage = self.oldpage.pop()
        
        if topage == 'channels':
            category = self.frame.channellist.GetManager().category
            categories = ['Popular','New','Favorites','All','My Channel', 'Updated']
            if category in categories:
                category = categories.index(category) + 1
                self.frame.channelcategories.Select(category, False)
        
        if topage == 'search_results':
            self.frame.top_bg.selectTab('results')
        elif topage in ['channels', 'selectedchannel', 'mychannel']:
            self.frame.top_bg.selectTab('channels')
        else:
            self.frame.top_bg.selectTab(topage)
        
        self.ShowPage(topage)
        self.oldpage.pop() #remove curpage from history
        
        if scrollTo:
            self.ScrollTo(scrollTo)
        
    def dosearch(self, input = None):
        if input == None:
            sf = self.frame.top_bg.searchField
            if sf is None:
                return
            
            input = sf.GetValue().strip()
            if input == '':
                return
        else:
            self.frame.top_bg.searchField.SetValue(input)
            
        if input.startswith("http://"):
            if self.frame.startDownloadFromUrl(str(input)):
                self.frame.top_bg.searchField.Clear()
                self.ShowPage('my_files')
            
        elif input.startswith("magnet:"):
            if self.frame.startDownloadFromMagnet(str(input)):
                self.frame.top_bg.searchField.Clear()
                self.ShowPage('my_files')
                
        else:
            wantkeywords = split_into_keywords(input)
            if len(' '.join(wantkeywords))  == 0:
                self.frame.top_bg.Notify('Please enter a search term', wx.ART_INFORMATION)
            else:
                self.frame.top_bg.StartSearch()
                
                self.current_search_query = wantkeywords
                if DEBUG:
                    print >>sys.stderr,"GUIUtil: searchFiles:", wantkeywords
                
                self.frame.searchlist.Freeze()
                self.frame.searchlist.Reset()
                self.ShowPage('search_results')
                
                #We now have to call thaw, otherwise loading message will not be shown.
                self.frame.searchlist.Thaw()
                
                #Peform local search
                self.torrentsearch_manager.setSearchKeywords(wantkeywords, 'filesMode')
                self.torrentsearch_manager.set_gridmgr(self.frame.searchlist.GetManager())
                
                self.channelsearch_manager.setSearchKeywords(wantkeywords)
                self.channelsearch_manager.set_gridmgr(self.frame.searchlist.GetManager())
                self.torrentsearch_manager.refreshGrid()
                
                #Start remote search
                #Arno, 2010-02-03: Query starts as Unicode
                q = u'SIMPLE '
                for kw in wantkeywords:
                    q += kw+u' '
                q = q.strip()
                
                self.utility.session.query_connected_peers(q, self.sesscb_got_remote_hits, self.max_remote_queries)
                
                if len(input) > 1: #do not perform remote channel search for single character inputs
                    q = 'CHANNEL k '
                    for kw in wantkeywords:
                        q += kw+' '
                    self.utility.session.query_connected_peers(q,self.sesscb_got_channel_hits)
                wx.CallLater(10000, self.CheckSearch, wantkeywords)
    
    def showChannelCategory(self, category, show = True):
        if show:
            self.frame.channellist.Freeze()
        
        manager = self.frame.channellist.GetManager()
        manager.SetCategory(category)
        
        if show:
            self.ShowPage('channels')
            self.frame.channellist.Thaw()
    
    def showChannel(self, channelname, channel_id):
        description_list = ["Marking a channel as your favorite will help to distribute it.", "If many Tribler users mark a channel as their favorite, it is considered popular."]
        self.frame.channelcategories.Quicktip(random.choice(description_list))
        
        self.ShowPage('selectedchannel')
        
        manager = self.frame.selectedchannellist.GetManager()
        manager.refresh(channel_id)
    
    def showChannelResults(self, data_channel):
        self.frame.top_bg.selectTab('channels')
        self.frame.channelcategories.DeselectAll()
        
        data = []
        for channel_id, channel_data in data_channel.iteritems():
            channel = self.channelsearch_manager.getChannel(channel_id)
            if channel:
                data.append(channel)
                
            else: #channel not found in local database (no torrents downloaded yet)
                channel_name = channel_data[0]
                subscribers = channel_data[1]
                nrtorrents = len(channel_data[2])
                
                if nrtorrents > 0:
                    max_timestamp = max([value[1] for _, value in channel_data[2].iteritems()])
                else:
                    max_timestamp = -1
                data.append([channel_id, channel_name, max_timestamp, subscribers, nrtorrents, 0, 0])
            
        def subscribe_latestupdate_sort(b, a):
            val = cmp(a[4], b[4])
            if val == 0:
                val = cmp(a[3], b[3])
            return val
        data.sort(subscribe_latestupdate_sort)
        
        manager = self.frame.channellist.GetManager()
        manager.SetCategory('searchresults')
        manager.refresh(data)
        
        self.ShowPage('channels')
    
    def showManageChannel(self, channel_id):
        self.frame.managechannel.SetChannelId(channel_id)
        self.ShowPage('managechannel')
    
    def showPlaylist(self, data):
        self.frame.playlist.Set(data)
        self.ShowPage('playlist')
        
    def OnList(self, goto_end, event = None):
        lists = {'channels': self.frame.channellist,'selectedchannel': self.frame.selectedchannellist ,'mychannel': self.frame.managechannel, 'search_results': self.frame.searchlist, 'my_files': self.frame.librarylist}
        if self.guiPage in lists and lists[self.guiPage].HasFocus():
            lists[self.guiPage].ScrollToEnd(goto_end)
        elif event:
            event.Skip()
    
    def ScrollTo(self, id):
        lists = {'channels': self.frame.channellist,'selectedchannel': self.frame.selectedchannellist ,'mychannel': self.frame.managechannel, 'search_results': self.frame.searchlist, 'my_files': self.frame.librarylist}
        if self.guiPage in lists:
            lists[self.guiPage].ScrollToId(id)
    
    def CheckSearch(self, wantkeywords):
        curkeywords, hits, filtered = self.torrentsearch_manager.getSearchKeywords('filesMode')
        if curkeywords == wantkeywords and (hits + filtered) == 0:
            uelog = UserEventLogDBHandler.getInstance()
            uelog.addEvent(message="Search: nothing found for query: "+" ".join(wantkeywords), type = 2)
     
    def sesscb_got_remote_hits(self,permid,query,hits):
        # Called by SessionCallback thread 

        if DEBUG:
            print >>sys.stderr,"GUIUtil: sesscb_got_remote_hits",len(hits)

        # 22/01/10 boudewijn: use the split_into_keywords function to
        # split.  This will ensure that kws is unicode and splits on
        # all 'splittable' characters
        kwstr = query[len('SIMPLE '):]
        kws = split_into_keywords(kwstr)

        wx.CallAfter(self.torrentsearch_manager.gotRemoteHits, permid, kws, hits)
        
    def sesscb_got_channel_hits(self, permid, query, hits):
        '''
        Called by SessionCallback thread from RemoteQueryMsgHandler.process_query_reply.
        
        @param permid: the peer who returnd the answer to the query
        @param query: the keywords of the query that originated the answer
        @param hits: the complete answer retruned by the peer
        '''
        # Called by SessionCallback thread 
        if DEBUG:
            print >>sys.stderr,"GUIUtil: sesscb_got_channel_hits",len(hits)
        
        # Let channelcast handle inserting items etc.
        channelcast = BuddyCastFactory.getInstance().channelcast_core
        listOfAdditions = channelcast.updateChannel(permid, query, hits)
        
        # 22/01/10 boudewijn: use the split_into_keywords function to
        # split.  This will ensure that kws is unicode and splits on
        # all 'splittable' characters
        kwstr = query[len("CHANNEL x "):]
        kws = split_into_keywords(kwstr)

        #Code that calls GUI
        # 1. Grid needs to be updated with incoming hits, from each remote peer
        # 2. Sorting should also be done by that function
        wx.CallAfter(self.channelsearch_manager.gotRemoteHits, permid, kws, listOfAdditions)

    #TODO: should be somewhere else
    def set_port_number(self, port_number):
        self.port_number = port_number
    def get_port_number(self):
        return self.port_number
    
    def toggleFamilyFilter(self, state = None):
         catobj = Category.getInstance()
         ff_enabled = not catobj.family_filter_enabled()
         #print 'Setting family filter to: %s' % ff_enabled
         if state is not None:
             ff_enabled = state    
         catobj.set_family_filter(ff_enabled)
        
    def getFamilyFilter(self):
        catobj = Category.getInstance()
        return catobj.family_filter_enabled()  
    
    def set_firewall_restart(self,b):
        self.firewall_restart = b
