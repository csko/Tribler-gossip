# Written by Jelle Roozenburg, Maarten ten Brinke, Arno Bakker, Lucian Musat 
# see LICENSE.txt for license information

import wx, os
from wx import xrc
from traceback import print_exc
from threading import Event, Thread
import urllib
import webbrowser
import random
from webbrowser import open_new

from time import time

from Tribler.Core.simpledefs import *
from Tribler.Core.Utilities.utilities import *
from Tribler.Core.Search.SearchManager import split_into_keywords
from Tribler.Core.CacheDB.sqlitecachedb import bin2str, str2bin
from Tribler.Category.Category import Category
from Tribler.Main.vwxGUI.SearchGridManager import TorrentManager, ChannelSearchGridManager
from Tribler.Main.vwxGUI.bgPanel import *
from Tribler.Main.Utility.constants import *
from Tribler.Core.BuddyCast.buddycast import BuddyCastFactory


from Tribler.Video.VideoPlayer import VideoPlayer
from Tribler.__init__ import LIBRARYNAME


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
        self.guiPage = None

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
    
    def ShowPage(self, page):
        if page == 'settings':
            xrcResource = os.path.join(self.vwxGUI_path, 'settingsDialog.xrc')
            res = xrc.XmlResource(xrcResource)
            dialog = res.LoadDialog(None, 'settingsDialog')
            dialog.Centre()
            dialog.ShowModal()
            dialog.Destroy()
        
        elif page != self.guiPage:
            self.oldpage = self.guiPage
            self.frame.Freeze()
            
            #show channel selector on these pages
            if page in ['channels','selectedchannel','mychannel']:
                if self.oldpage not in ['channels','selectedchannel','mychannel']:
                    self.frame.channelselector.Show()
            else:
                self.frame.channelselector.Hide()
            
            if page == 'search_results':
                #Show animation
                if self.frame.top_bg.ag.IsPlaying():
                    self.frame.top_bg.ag.Show()
                
                #Show list
                self.frame.searchlist.Show()
            else:
                #Stop animation
                self.frame.top_bg.ag.Stop() # only calling Hide() on mac isnt sufficient 
                self.frame.top_bg.ag.Hide()
                
                if sys.platform == 'win32':
                    self.frame.top_bg.Layout()
                
                #Hide list
                self.frame.searchlist.Hide()
            
            if page == 'channels':
                selectedcat = self.frame.channelcategories.GetSelectedCategory()
                if selectedcat in ['Popular','New','Favorites','All'] or self.oldpage == 'mychannel':
                    self.frame.channellist.Show()
                    self.frame.channelcategories.Quicktip('All Channels are ordered by popularity. Popularity is measured by the number of Tribler users which have marked this channel as favorite.')
                elif selectedcat == 'My Channel' and self.oldpage != 'mychannel':
                    page = 'mychannel'
                else:
                    page = 'selectedchannel'
            else:
                self.frame.channellist.Hide()
            
            if page == 'mychannel':
                #Reload content
                self.frame.mychannel.Reset()
                self.frame.mychannel.GetManager().refresh()
                self.frame.channelcategories.Quicktip('This is your channel, other Tribler users can find this channel by searching for your username')
                
                #Show list
                self.frame.mychannel.Show()
            else:
                self.frame.mychannel.Hide()
            
            if page == 'selectedchannel':
                self.frame.selectedchannellist.Show()
                self.frame.channelcategories.DeselectAll()
            else:
                self.frame.selectedchannellist.Hide()
                self.frame.selectedchannellist.Reset()
                
            if page == 'my_files':
                #Show list
                self.frame.librarylist.Show()
                
                #Reload content
                self.frame.librarylist.GetManager().refresh()
            else:
                #Hide list
                self.frame.librarylist.Hide()
            
            if page == 'home':
                self.frame.home.Show()
            else:
                self.frame.home.Hide()
            
            if page == 'stats':
                self.frame.stats.Show()
            else:
                self.frame.stats.Hide()
            
            #show player on these pages
            if not self.useExternalVideo:
                if page in ['my_files', 'mychannel', 'selectedchannel', 'channels', 'search_results']:
                    if self.oldpage not in ['my_files', 'mychannel', 'selectedchannel', 'channels', 'search_results']:
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
            elif page == 'mychannel':
                self.frame.mychannel.Focus()
            elif page =='my_files':
                self.frame.librarylist.Focus()
                
    def GoBack(self):
        if self.oldpage == 'channels':
            category = self.frame.channellist.GetManager().category
            categories = ['Popular','New','Favorites','All','My Channel']
            if category in categories:
                category = categories.index(category) + 1
                self.frame.channelcategories.Select(category, False)
        
        if self.oldpage == 'search_results':
            self.frame.top_bg.selectTab('results')
        elif self.oldpage in ['channels', 'selectedchannel', 'mychannel']:
            self.frame.top_bg.selectTab('channels')
        else:
            self.frame.top_bg.selectTab(self.oldpage)
        self.ShowPage(self.oldpage)
        
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
            
        self.frame.top_bg.StartSearch()
        
        wantkeywords = split_into_keywords(input)
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
        
        q = 'CHANNEL k '
        for kw in wantkeywords:
            q += kw+' '
        self.utility.session.query_connected_peers(q,self.sesscb_got_channel_hits)
    
    def showChannelCategory(self, category, show = True):
        if show:
            self.frame.channellist.Freeze()
        
        manager = self.frame.channellist.GetManager()
        manager.SetCategory(category)
        
        if show:
            self.ShowPage('channels')
            self.frame.channellist.Thaw()
    
    def showChannel(self, channelname, channel_permid):
        self.frame.selectedchannellist.Reset()
        self.frame.selectedchannellist.SetTitle(channelname)
        
        description_list = ["Marking a channel as your favorite will help to distribute it.", "If many Tribler users mark a channel as their favorite, it is considered popular."]
        self.frame.channelcategories.Quicktip(random.choice(description_list))
        
        self.ShowPage('selectedchannel')
        
        manager = self.frame.selectedchannellist.GetManager()
        manager.refresh(channel_permid)
    
    def showChannelResults(self, data_channel):
        self.frame.top_bg.selectTab('channels')
        self.frame.channelcategories.DeselectAll()
        
        data = []
        for permid in data_channel.keys():
            data.append(self.channelsearch_manager.getChannel(permid))
            
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
        
    def OnList(self, goto_end, event = None):
        lists = {'channels': self.frame.channellist,'selectedchannel': self.frame.selectedchannellist ,'mychannel': self.frame.mychannel, 'search_results': self.frame.searchlist, 'my_files': self.frame.librarylist}
        if self.guiPage in lists and lists[self.guiPage].HasFocus():
            lists[self.guiPage].ScrollToEnd(goto_end)
        elif event:
            event.Skip()
        
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
        wx.CallAfter(self.channelsearch_manager.gotRemoteHits,permid,kws,listOfAdditions)

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
