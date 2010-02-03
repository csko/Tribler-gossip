# Written by Jelle Roozenburg, Maarten ten Brinke, Arno Bakker, Lucian Musat 
# see LICENSE.txt for license information

import wx, os
from wx import xrc
from traceback import print_exc
from threading import Event, Thread
import urllib
import webbrowser
from webbrowser import open_new

from time import time

from Tribler.Core.simpledefs import *
from Tribler.Core.Utilities.utilities import *
from Tribler.Core.Search.SearchManager import split_into_keywords

from Tribler.TrackerChecking.TorrentChecking import TorrentChecking
#from Tribler.Subscriptions.rss_client import TorrentFeedThread
from Tribler.Category.Category import Category
from Tribler.Main.Dialogs.makefriends import MakeFriendsDialog, InviteFriendsDialog
from Tribler.Main.vwxGUI.bgPanel import *
from Tribler.Main.vwxGUI.GridState import GridState
from Tribler.Main.vwxGUI.SearchGridManager import TorrentSearchGridManager, ChannelSearchGridManager, PeerSearchGridManager
from Tribler.Main.Utility.constants import *
from Tribler.Main.vwxGUI.UserDownloadChoice import UserDownloadChoice

from Tribler.Video.VideoPlayer import VideoPlayer
from fontSizes import *

from Tribler.__init__ import LIBRARYNAME


DEBUG = False


class GUIUtility:
    __single = None
    
    def __init__(self, utility = None, params = None):
        if GUIUtility.__single:
            raise RuntimeError, "GUIUtility is singleton"
        GUIUtility.__single = self 
        # do other init
        self.xrcResource = None
        self.utility = utility
        self.vwxGUI_path = os.path.join(self.utility.getPath(), LIBRARYNAME, 'Main', 'vwxGUI')
        self.utility.guiUtility = self
        self.params = params
        self.frame = None
        self.selectedMainButton = None
        self.standardOverview = None
        self.standardDetails = None
        self.reachable = False
        self.DELETE_TORRENT_ASK = True
        self.DELETE_TORRENT_ASK_OLD = True
        self.DELETE_TORRENT_PREF = 1 # 1 : from Library
                                     # 2 : from Library and Harddisk


        self.fakeButton = None
        self.realButton = None

       # videoplayer
        self.videoplayer = VideoPlayer.getInstance()

        # current GUI page
        self.guiPage = None

        # standardGrid
        self.standardGrid = None
 

        # port number
        self.port_number = None

        # utf8
        if sys.platform == 'darwin':
            self.utf8 = ""
        else:
            self.utf8 = "UTF-8"


        # search mode
        self.search_mode = 'files' # 'files' or 'channels'


        # first channel search
        self.firstchannelsearch = True

        # page Title
        self.pageTitle = None


        # number subsciptions
        self.nb_subscriptions = None


        # firewall
        self.firewall_restart = False # ie Tribler needs to restart for the port number to be updated



        # Arno: 2008-04-16: I want to keep this for searching, as an extension
        # of the standardGrid.GridManager
        self.torrentsearch_manager = TorrentSearchGridManager.getInstance(self)
        self.channelsearch_manager = ChannelSearchGridManager.getInstance(self)
        self.peersearch_manager = PeerSearchGridManager.getInstance(self)
        
        self.guiOpen = Event()
        
       
        self.gridViewMode = 'thumbnails' 
        self.thumbnailViewer = None
#        self.standardOverview = standardOverview()
        
        self.selectedColour = wx.Colour(216,233,240) ## 155,200,187
        self.unselectedColour = wx.Colour(255,255,255) ## 102,102,102      
        self.unselectedColour2 = wx.Colour(255,255,255) ## 230,230,230       
        self.unselectedColourDownload = wx.Colour(198,226,147)        
        self.unselectedColour2Download = wx.Colour(190,209,139)
        self.selectedColourDownload = wx.Colour(145,173,78)
        self.selectedColourPending = wx.Colour(216,233,240)  ## 208,251,244
        self.triblerRed = wx.Colour(255, 51, 0)
        self.bgColour = wx.Colour(102,102,102)
        self.darkTextColour = wx.Colour(51,51,51)
        
        # Recall improves by 20-25% by increasing the number of peers to query to 20 from 10 !
        self.max_remote_queries = 20    # max number of remote peers to query
        self.remote_search_threshold = 20    # start remote search when results is less than this number

        self.user_download_choice = UserDownloadChoice.get_singleton()
    
    def getInstance(*args, **kw):
        if GUIUtility.__single is None:
            GUIUtility(*args, **kw)
        return GUIUtility.__single
    getInstance = staticmethod(getInstance)

    def buttonClicked(self, event):
        "One of the buttons in the GUI has been clicked"
        self.frame.SetFocus()

        event.Skip(True) #should let other handlers use this event!!!!!!!
            
        name = ""
        obj = event.GetEventObject()
        
        print 'tb > name of object that is clicked = %s' % obj.GetName()

        try:
            name = obj.GetName()
        except:
            print >>sys.stderr,'GUIUtil: Error: Could not get name of buttonObject: %s' % obj
        
        if DEBUG:
            print >>sys.stderr,'GUIUtil: Button clicked %s' % name
            #print_stack()
        
        
        if name == 'moreFileInfo':
            self.standardFileDetailsOverview()
        elif name == 'moreFileInfoPlaylist':
            self.standardFileDetailsOverview()
#            self.standardPlaylistOverview()
        elif name == 'more info >': 
            self.standardPersonDetailsOverview()                      
        elif name == 'backButton':            
            self.standardStartpage() 
            
        elif name == 'All popular files':            
            self.standardFilesOverview()  ##
            
        elif name == 'viewThumbs' or name == 'viewList':
#            print 'currentpanel = %s' % self.standardOverview.currentPanel.GetName()
#            self.viewThumbs = xrc.XRCCTRL(self.frame, "viewThumbs")
#            self.viewList = xrc.XRCCTRL(self.frame, "viewList")  
            
            grid = self.standardOverview.data[self.standardOverview.mode].get('grid')
            if name == 'viewThumbs':
                self.viewThumbs.setSelected(True)
                self.viewList.setSelected(False)                
                grid.onViewModeChange(mode='thumbnails')
                self.gridViewMode = 'thumbnails'
            elif name == 'viewList':
                self.viewThumbs.setSelected(False)
                self.viewList.setSelected(True)                
                grid.onViewModeChange(mode='list')               
                self.gridViewMode = 'list'

        elif name.lower().find('detailstab') > -1:
            self.detailsTabClicked(name)
        elif name == 'refresh':
            self.refreshTracker()
        elif name == "addAsFriend" or name == 'deleteFriend':
            self.standardDetails.addAsFriend()

        elif name in ['save','save_big', 'save_medium']: 
            self.standardDetails.download()
        elif name == 'addFriend':
            #print >>sys.stderr,"GUIUtil: buttonClicked: parent is",obj.GetParent().GetName()
            dialog = MakeFriendsDialog(obj,self.utility)
            ret = dialog.ShowModal()
            dialog.Destroy()
        elif name == 'inviteFriends':
            self.emailFriend(event)
            #else:
            #    print >>sys.stderr,"GUIUtil: buttonClicked: dlbooster: Torrent is None"
            
        elif name == 'browse':
            self.standardOverview.currentPanel.sendClick(event)

        elif (name == 'edit' or name == "top10Sharers" or name.startswith('bgPanel')) and obj.GetParent().GetName() == "profileOverview":
            self.standardOverview.currentPanel.sendClick(event)
            self.detailsTabClicked(name) #a panel was clicked in the profile overview and this is the most elegant so far method of informing the others
        elif name == "takeMeThere0" : #a button to go to preferences was clicked
            panel_name = self.standardDetails.currentPanel.GetName()
            if panel_name == "profileDetails_Files":
                #self.utility.actions[ACTION_PREFERENCES].action()
                self.utility.actions[ACTION_PREFERENCES].action(openname=self.utility.lang.get('triblersetting'))
                self.selectData(self.standardDetails.getData())
            if panel_name == "profileDetails_Download":
                #self.utility.actions[ACTION_PREFERENCES].action(openname=self.utility.lang.get('triblersetting'))
                self.utility.actions[ACTION_PREFERENCES].action(openname=self.utility.lang.get('videosetting'))
                self.selectData(self.standardDetails.getData())
            elif panel_name == "profileDetails_Presence":
                self.emailFriend(event)
                #self.mainButtonClicked( 'mainButtonPersons', self.frame.mainButtonPersons)
            #generate event to change page -> this should be done as a parameter to action because is modal
            #event = wx.TreeEvent(wx.EVT_TREE_ITEM_ACTIVATED)
            #wx.PostEvent()
        elif name == "takeMeThere1": #switch to another view
            panel_name = self.standardDetails.currentPanel.GetName()
            if panel_name == "profileDetails_Download":
                self.emailFriend(event)
                #self.mainButtonClicked( 'mainButtonPersons', self.frame.mainButtonPersons)
            if panel_name == "profileDetails_Presence": 
                URL = 'http://www.tribler.org/'
                webbrowser.open(URL)  
            else:
                print >>sys.stderr,'GUIUtil: A button was clicked, but no action is defined for: %s' % name
                
        elif name == "takeMeThere2": #switch to another view
            panel_name = self.standardDetails.currentPanel.GetName()
            if panel_name == "profileDetails_Download":
                URL = 'http://www.tribler.org/'
                webbrowser.open(URL)                
        elif name == 'subscribe':
            self.subscribe()
        elif name == 'firewallStatus':
            self.firewallStatusClick()
        elif name == 'options':            
            self.standardDetails.rightMouseButton(event)
        elif name == 'viewModus':            
            self.onChangeViewModus()
        elif name == 'searchClear':
            # this has to be a callafter to avoid segmentation fault
            # otherwise the panel with the event generating button is destroyed
            # in the execution of the event.
            self.clearSearch()
                        
            wx.CallAfter(self.standardOverview.toggleSearchDetailsPanel, False)
        elif name == 'familyfilter':
            catobj = Category.getInstance()
            ff_enabled = not catobj.family_filter_enabled()
            print 'Setting family filter to: %s' % ff_enabled
            ccatobj.set_family_filter(ff_enabled)
            self.familyButton.setToggled()
#            obj.setToggled(ff_enabled)
            for filtername in ['filesFilter', 'libraryFilter']:
                filterCombo = xrc.XRCCTRL(self.frame, filtername)
                if filterCombo:
                    filterCombo.refresh()

        elif name == 'familyFilterOn' or name == 'familyFilterOff': ## not used anymore
            if ((self.familyButtonOn.isToggled() and name == 'familyFilterOff') or
                (self.familyButtonOff.isToggled() and name == 'familyFilterOn')):

                catobj = Category.getInstance()
                ff_enabled = not catobj.family_filter_enabled()
                print 'Setting family filter to: %s' % ff_enabled
                catobj.set_family_filter(ff_enabled)
                self.familyButtonOn.setToggled()
                self.familyButtonOff.setToggled()
#                obj.setToggled(ff_enabled)
                for filtername in ['filesFilter', 'libraryFilter']:
                    filterCombo = xrc.XRCCTRL(self.frame, filtername)
                    if filterCombo:
                        filterCombo.refresh()

        elif name == 'playAdd' or name == 'play' or name == 'playAdd1' or name == 'play1':   
            playableFiles = self.standardOverview.data['fileDetailsMode']['panel'].selectedFiles[:]
            
            if name == 'play' or name == 'play1':
                self.standardDetails.addToPlaylist(name = '', add=False)
            
            for p in playableFiles:
                if p != '':
                    self.standardDetails.addToPlaylist(name = p.GetLabel(), add=True)

        elif name == 'advancedFiltering':    
            if self.filterStandard.visible:
                self.filterStandard.Hide()
                self.filterStandard.visible = False
                self.standardOverview.GetParent().Layout()
                #                self.frame.Refresh()
            else:
                self.filterStandard.Show()
                self.filterStandard.visible = True
                self.standardOverview.GetParent().Layout()
                #                self.frame.Refresh()

        elif name == 'fake':    
            self.realButton.setState(False) # disabled real button
            # TODO: write code for positive code

        elif name == 'real':    
            self.fakeButton.setState(False) # disable fake button
            # TODO: write code for positive code



        elif name == 'remove':

            ##if self.DELETE_TORRENT_ASK:
            ##    xrcResource = os.path.join(self.vwxGUI_path, 'deleteTorrent.xrc')
            ##    res = xrc.XmlResource(xrcResource)
            ##    self.dialogFrame = res.LoadFrame(None, "torrentDialog")
 
                #self.dialogFrame.SetFocus()
            ##    self.dialogFrame.Centre()
            ##    self.dialogFrame.Show(True)

            ##    self.dialogFrame.Library = xrc.XRCCTRL(self.dialogFrame,c "Library") 
            ##    self.dialogFrame.LibraryHardDisk = xrc.XRCCTRL(self.dialogFrame, "LibraryHardDisk") 
            ##    self.dialogFrame.Cancel = xrc.XRCCTRL(self.dialogFrame, "Cancel") 
            ##    self.dialogFrame.checkbox = xrc.XRCCTRL(self.dialogFrame, "checkBox")


            ##    self.dialogFrame.Library.Bind(wx.EVT_BUTTON, self.LibraryClicked)
            ##    self.dialogFrame.LibraryHardDisk.Bind(wx.EVT_BUTTON, self.HardDiskClicked)
            ##    self.dialogFrame.Cancel.Bind(wx.EVT_BUTTON, self.CancelClicked)
            ##    self.dialogFrame.checkbox.Bind(wx.EVT_CHECKBOX, self.checkboxClicked)



            ##elif self.DELETE_TORRENT_PREF == 1: 
            ##   self.onDeleteTorrentFromLibrary()
            ##else:
            ##   self.onDeleteTorrentFromDisk()
            self.onDeleteTorrentFromDisk() # default behaviour for preview 1
            

 


        ##elif name == 'settings':
        ##    self.settingsOverview()


        ##elif name == 'my_files':
        ##    self.standardLibraryOverview()

        elif name == 'edit':
            self.standardOverview.currentPanel.sendClick(event)
            self.detailsTabClicked(name)

             
        elif DEBUG:
            print >> sys.stderr, 'GUIUtil: A button was clicked, but no action is defined for: %s' % name
                
        
#    def mainButtonClicked(self, name, button):
#        "One of the mainbuttons in the top has been clicked"
#        
#        if not button.isSelected():
#            if self.selectedMainButton:
#                self.selectedMainButton.setSelected(False)
#            button.setSelected(True)
#            self.selectedMainButton = button
#
#        if name == 'mainButtonStartpage':
#            self.standardStartpage()
#        if name == 'mainButtonStats':
#            self.standardStats()
#        elif name == 'mainButtonFiles':
#            self.standardFilesOverview()
#        elif name == 'mainButtonPersons':
#            self.standardPersonsOverview()
#        elif name == 'mainButtonProfile':
#            self.standardProfileOverview()
#        elif name == 'mainButtonLibrary':
#            self.standardLibraryOverview()
#        elif name == 'mainButtonFriends':
#            self.standardFriendsOverview()
#        elif name == 'mainButtonRss':
#            self.standardSubscriptionsOverview()
#        elif name == 'mainButtonFileDetails':
#            self.standardFileDetailsOverview()
##            print 'tb debug> guiUtility button press ready'
#        elif name == 'mainButtonPersonDetails':
#            self.standardPersonDetailsOverview()
#        elif name == 'mainButtonMessages':
#            self.standardMessagesOverview()
#        elif DEBUG:
#            print >>sys.stderr,"GUIUtil: MainButtonClicked: unhandled name",name

    def setSearchMode(self, search_mode):
        if search_mode not in ('files', 'channels'):
            return
        self.search_mode = search_mode

    

    def LibraryClicked(self, event):
        self.DELETE_TORRENT_ASK_OLD = self.DELETE_TORRENT_ASK
        self.DELETE_TORRENT_PREF = 1
        self.dialogFrame.Close()
        self.standardOverview.Refresh()
        wx.CallAfter(self.onDeleteTorrentFromLibrary)
         
    def HardDiskClicked(self, event):
        self.DELETE_TORRENT_ASK_OLD = self.DELETE_TORRENT_ASK
        self.DELETE_TORRENT_PREF = 2
        self.dialogFrame.Close()
        self.standardOverview.Refresh()
        wx.CallAfter(self.onDeleteTorrentFromDisk)
        

    def CancelClicked(self, event):
        self.DELETE_TORRENT_ASK = self.DELETE_TORRENT_ASK_OLD
        self.dialogFrame.Close()
        self.standardOverview.Refresh()

    def checkboxClicked(self, event):
        self.DELETE_TORRENT_ASK = not self.DELETE_TORRENT_ASK 


    def set_port_number(self, port_number):
        self.port_number = port_number

    def get_port_number(self):
        return self.port_number



    def toggleFamilyFilter(self, state = None):
        catobj = Category.getInstance()
        ff_enabled = not catobj.family_filter_enabled()
        print 'Setting family filter to: %s' % ff_enabled
        if state is not None:
            ff_enabled = state    
        catobj.set_family_filter(ff_enabled)
      
        if sys.platform == 'win32':
            self.frame.top_bg.familyfilter.setToggled(ff_enabled)
        else:
            if ff_enabled:
                self.frame.top_bg.familyfilter.SetLabel('Family Filter:ON')
            else:
                self.frame.top_bg.familyfilter.SetLabel('Family Filter:OFF')
        #obj.setToggled(ff_enabled)
        for filtername in ['filesFilter', 'libraryFilter']:
            filterCombo = xrc.XRCCTRL(self.frame, filtername)
            if filterCombo:
                filterCombo.refresh()
        
 


    def standardStartpage(self, filters = ['','']):
        ##self.frame.pageTitle.SetLabel('START PAGE')               
        filesDetailsList = []
        self.standardOverview.setMode('startpageMode')

    def standardStats(self, filters = ['','']):
        self.frame.pageTitle.SetLabel('STATS')               
#        filesDetailsList = []
        self.standardOverview.setMode('statsMode')
            
    def standardFilesOverview(self):
        self.guiPage = 'search_results'
        if self.frame.top_bg.ag.IsPlaying():
            self.frame.top_bg.ag.Show() 

        if sys.platform != 'darwin':
            self.frame.videoframe.show_videoframe()
        self.frame.videoparentpanel.Show()            

        if self.frame.videoframe.videopanel.vlcwin.is_animation_running():
            self.frame.videoframe.videopanel.vlcwin.show_loading()
            
        #self.frame.channelsDetails.reinitialize()
        self.frame.channelsDetails.Hide()



        self.frame.top_bg.results.SetForegroundColour((0,105,156))
        self.frame.top_bg.channels.SetForegroundColour((255,51,0))
        self.frame.top_bg.settings.SetForegroundColour((255,51,0))
        self.frame.top_bg.my_files.SetForegroundColour((255,51,0))

        self.frame.top_bg.results.SetFont(wx.Font(FONT_SIZE_PAGE_OVER, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))
        self.frame.top_bg.channels.SetFont(wx.Font(FONT_SIZE_PAGE, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))
        self.frame.top_bg.settings.SetFont(wx.Font(FONT_SIZE_PAGE, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))
        self.frame.top_bg.my_files.SetFont(wx.Font(FONT_SIZE_PAGE, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))

        self.frame.top_bg.search_results.Show()

        if sys.platform == 'win32':
            self.frame.top_bg.Refresh()

        self.showPager(True)
        if sys.platform == "linux2":
            self.frame.pagerPanel.SetMinSize((634,20))
        elif sys.platform == 'darwin':
            self.frame.pagerPanel.SetMinSize((634,20))
        else:
            self.frame.pagerPanel.SetMinSize((635,20))


        self.standardOverview.setMode('filesMode')

        try:
            if self.standardDetails:
                self.standardDetails.setMode('filesMode', None)
        except:
            pass


        
    def channelsOverview(self, erase=False):
        if self.guiPage != 'search_results':
            if sys.platform == 'darwin':
                self.frame.top_bg.ag.Stop()
            self.frame.top_bg.ag.Hide()
        elif self.frame.top_bg.ag.IsPlaying():
            self.frame.top_bg.ag.Show() 
            
        if erase:
            self.frame.channelsDetails.reinitialize(force=True)
            self.frame.top_bg.indexMyChannel = -1

        self.frame.channelsDetails.Show()
        if self.guiPage == 'search_results':
            self.frame.top_bg.channels.SetForegroundColour((255,51,0))
            self.frame.top_bg.results.SetForegroundColour((0,105,156))
            self.frame.top_bg.channels.SetFont(wx.Font(FONT_SIZE_PAGE, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))
            self.frame.top_bg.results.SetFont(wx.Font(FONT_SIZE_PAGE_OVER, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))
            self.frame.top_bg.search_results.Show()
        elif self.guiPage == 'channels':
            self.frame.top_bg.channels.SetForegroundColour((0,105,156))
            self.frame.top_bg.results.SetForegroundColour((255,51,0))
            self.frame.top_bg.channels.SetFont(wx.Font(FONT_SIZE_PAGE_OVER, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))
            self.frame.top_bg.results.SetFont(wx.Font(FONT_SIZE_PAGE, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))
            self.frame.top_bg.search_results.Hide()

        self.frame.top_bg.settings.SetForegroundColour((255,51,0))
        self.frame.top_bg.my_files.SetForegroundColour((255,51,0))

        self.frame.top_bg.settings.SetFont(wx.Font(FONT_SIZE_PAGE, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))
        self.frame.top_bg.my_files.SetFont(wx.Font(FONT_SIZE_PAGE, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))

        self.frame.top_bg.Refresh()



        if sys.platform != 'darwin':
            self.frame.videoframe.show_videoframe()
        self.frame.videoparentpanel.Show()

        self.showPager(False)



        self.frame.Layout()

        t1 = time()

        self.standardOverview.setMode('channelsMode')
        

        t2 = time()
        if DEBUG: 
            print >> sys.stderr , "channelsMode" , t2 -t1



    def loadInformation(self, mode, sort, erase = False):
        """ Loads the information in a specific mode """
        if erase:
            self.standardOverview.getGrid().clearAllData()
        gridState = GridState(mode, 'all', sort)
        self.standardOverview.filterChanged(gridState)



    def settingsOverview(self):
        self.guiPage = 'settings' 
        if sys.platform == 'darwin':
            self.frame.top_bg.ag.Stop() # only calling Hide() on mac isnt sufficient 
        self.frame.top_bg.ag.Hide()
        if sys.platform == 'win32':
            self.frame.top_bg.Layout()

        self.frame.channelsDetails.Hide()
                
        self.frame.top_bg.results.SetForegroundColour((255,51,0))
        self.frame.top_bg.channels.SetForegroundColour((255,51,0))
        self.frame.top_bg.settings.SetForegroundColour((0,105,156))
        self.frame.top_bg.my_files.SetForegroundColour((255,51,0))

        self.frame.top_bg.results.SetFont(wx.Font(FONT_SIZE_PAGE, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))
        self.frame.top_bg.channels.SetFont(wx.Font(FONT_SIZE_PAGE, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))
        self.frame.top_bg.settings.SetFont(wx.Font(FONT_SIZE_PAGE_OVER, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))
        self.frame.top_bg.my_files.SetFont(wx.Font(FONT_SIZE_PAGE, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))


        self.frame.videoframe.hide_videoframe()
        self.frame.videoparentpanel.Hide()            

        if sys.platform == 'darwin':
            self.frame.videoframe.videopanel.vlcwin.stop_animation()

        self.showPager(False)

        if self.frame.top_bg.search_results.GetLabel() != '':
            self.frame.top_bg.search_results.Hide()
        self.frame.Layout()
        self.standardOverview.setMode('settingsMode')


    def showPager(self, b):
        self.frame.pagerPanel.Show(b)
        self.frame.BL.Show(b)
        self.frame.BR.Show(b)
        self.frame.pagerPanel.Refresh()
        self.frame.standardPager.Refresh()
        

    def standardLibraryOverview(self, filters = None, refresh=False):
        
        setmode = refresh
        if self.guiPage != 'my_files':
            self.guiPage = 'my_files' 
            if sys.platform == 'darwin':
                self.frame.top_bg.ag.Stop()
            self.frame.top_bg.ag.Hide()
            self.frame.top_bg.results.SetForegroundColour((255,51,0))
            self.frame.top_bg.channels.SetForegroundColour((255,51,0))
            self.frame.top_bg.settings.SetForegroundColour((255,51,0))
            self.frame.top_bg.my_files.SetForegroundColour((0,105,156))
            self.frame.top_bg.results.SetFont(wx.Font(FONT_SIZE_PAGE, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))
            self.frame.top_bg.channels.SetFont(wx.Font(FONT_SIZE_PAGE, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))
            self.frame.top_bg.settings.SetFont(wx.Font(FONT_SIZE_PAGE, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))
            self.frame.top_bg.my_files.SetFont(wx.Font(FONT_SIZE_PAGE_OVER, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, self.utf8))

            self.frame.channelsDetails.Hide()

            if sys.platform != 'darwin':
                self.frame.videoframe.show_videoframe()
            self.frame.videoparentpanel.Show()


            if self.frame.top_bg.search_results.GetLabel() != '':
                self.frame.top_bg.search_results.Hide()
            self.frame.top_bg.Layout()
            
            if sys.platform == "linux2":
                self.frame.pagerPanel.SetMinSize((634,20))
            elif sys.platform == 'darwin':
                self.frame.pagerPanel.SetMinSize((634,20))
            else:
                self.frame.pagerPanel.SetMinSize((635,20))

            self.showPager(True)
           
            setmode = True
            
        if setmode:
            self.standardOverview.setMode('libraryMode',refreshGrid=refresh)
            self.loadInformation('libraryMode', "name", erase=False)

            if sys.platform != 'darwin':
                wx.CallAfter(self.frame.videoframe.show_videoframe)
            
        self.standardDetails.setMode('libraryMode')

        wx.CallAfter(self.frame.standardPager.Show,self.standardOverview.getGrid().getGridManager().get_total_items()>0)


        
    def standardSubscriptionsOverview(self):
        self.frame.pageTitle.SetLabel('SUBSCRIPTIONS')       
        self.standardOverview.setMode('subscriptionsMode')
        gridState = GridState('subscriptionMode', 'all', 'name')
        self.standardOverview.filterChanged(gridState)
        self.standardDetails.setMode('subscriptionsMode')
    
    def standardFileDetailsOverview(self, filters = ['','']):               
        filesDetailsList = []
        self.standardOverview.setMode('fileDetailsMode')
#        print 'tb > self.standardOverview.GetSize() 1= %s ' % self.standardOverview.GetSize()
#        print 'tb > self.frame = %s ' % self.frame.GetSize()
        
        frameSize = self.frame.GetSize()
#        self.standardOverview.SetMinSize((1000,2000))
#        self.scrollWindow.FitInside()
#        print 'tb > self.standardOverview.GetSize() 2= %s ' % self.standardOverview.GetSize()
#        self.scrollWindow.SetScrollbars(1,1,1024,2000)
        
##        self.scrollWindow.SetScrollbars(1,1,frameSize[0],frameSize[1])
#        self.standardOverview.SetSize((-1, 2000))
#        print 'tb > self.standardOverview.GetSize() = %s' % self.standardOverview.GetSize()
#        self.standardOverview.filterChanged(filters)
#        self.standardDetails.setMode('fileDetails')
    def standardPlaylistOverview(self, filters = ['','']):               
        filesDetailsList = []
        self.standardOverview.setMode('playlistMode')
        

    def standardPersonDetailsOverview(self, filters = ['','']):               
        filesDetailsList = []
        self.standardOverview.setMode('personDetailsMode')
         
    def standardMessagesOverview(self):
        if DEBUG:
            print >>sys.stderr,'GUIUtil: standardMessagesOverview: Not yet implemented;'
  
            
    def initStandardOverview(self, standardOverview):
        "Called by standardOverview when ready with init"
        self.standardOverview = standardOverview
#        self.standardFilesOverview(filters = ['all', 'seeder'])


        self.standardStartpage()
        self.standardOverview.Show(True)
        wx.CallAfter(self.refreshOnResize)
        

        self.gridViewMode = 'list'
        
        #self.filterStandard.Hide() ## hide the standardOverview at startup
        
        # Family filter initialized from configuration file
        catobj = Category.getInstance()
        print >> sys.stderr , "FAMILY FILTER :" , self.utility.config.Read('family_filter', "boolean")

        
    def initFilterStandard(self, filterStandard):
        self.filterStandard = filterStandard
        self.advancedFiltering = xrc.XRCCTRL(self.frame, "advancedFiltering")
            
     
    def getOverviewElement(self):
        """should get the last selected item for the current standard overview, or
        the first one if none was previously selected"""
        firstItem = self.standardOverview.getFirstItem()
        return firstItem
        
    def initStandardDetails(self, standardDetails):
        "Called by standardDetails when ready with init"
        self.standardDetails = standardDetails
        firstItem = self.standardOverview.getFirstItem()
        self.standardDetails.setMode('filesMode', firstItem)        
        self.guiOpen.set()
        
    def deleteSubscription(self,subscrip):
        self.standardOverview.loadSubscriptionData()
        self.standardOverview.refreshData()
    
    def addTorrentAsHelper(self):
        if self.standardOverview.mode == 'libraryMode':
            self.standardOverview.filterChanged(None)
            #self.standardOverview.refreshData()
    
    def selectData(self, data):
        "User clicked on item. Has to be selected in detailPanel"
        self.standardDetails.setData(data)
        self.standardOverview.updateSelection()
        
    def selectTorrent(self, torrent):
        "User clicked on torrent. Has to be selected in detailPanel"
        self.standardDetails.setData(torrent)
        self.standardOverview.updateSelection()

    def selectPeer(self, peer_data):
        "User clicked on peer. Has to be selected in detailPanel"
        self.standardDetails.setData(peer_data)
        self.standardOverview.updateSelection()

    def selectSubscription(self, sub_data):
        "User clicked on subscription. Has to be selected in detailPanel"
        self.standardDetails.setData(sub_data)
        self.standardOverview.updateSelection()
            
    def detailsTabClicked(self, name):
        "A tab in the detailsPanel was clicked"
        self.standardDetails.tabClicked(name)
        
    def refreshOnResize(self):
#        print 'tb > REFRESH ON RESIZE'
#        print self.standardOverview.GetContainingSizer().GetItem(0)

#        self.standardOverview.GetContainingSizer().GetItem(self.standardOverview).SetProportion(1)
#        self.standardOverview.SetProportion(1)
        try:
            if DEBUG:
                print >>sys.stderr,'GuiUtility: explicit refresh'
            self.mainSizer.FitInside(self.frame)
            self.standardDetails.Refresh()
            self.frame.topBackgroundRight.Refresh()
            self.frame.topBackgroundRight.GetSizer().Layout()
            self.frame.topBackgroundRight.GetContainingSizer().Layout()
            self.updateSizeOfStandardOverview()
            self.standardDetails.Layout()
            self.standardDetail.GetContainingSizer.Layout()
            self.standardOverview.Refresh()
            
        except:
            pass # When resize is done before panels are loaded: no refresh
    
    def updateSizeOfStandardOverview(self):
        print 'tb > SetProportion'
        self.standardOverview.SetProportion(1)
        
        
        if self.standardOverview.gridIsAutoResizing():
            #print 'size1: %d, size2: %d' % (self.frame.GetClientSize()[1], self.frame.window.GetClientSize()[1])
            margin = 10
            newSize = (-1, #self.scrollWindow.GetClientSize()[1] - 
                           self.frame.GetClientSize()[1] - 
                               100 - # height of top bar
                               self.standardOverview.getPager().GetSize()[1] -
                               margin)
        else:
            newSize = self.standardOverview.GetSize()
                    
        #print 'ClientSize: %s, virtual : %s' % (str(self.scrollWindow.GetClientSize()), str(self.scrollWindow.GetVirtualSize()))
        #print 'Position: %s' % str(self.standardOverview.GetPosition())
        self.standardOverview.SetSize(newSize)
        self.standardOverview.SetMinSize(newSize)
        self.standardOverview.SetMaxSize(newSize)            
        #print 'Overview is now: %s' % str(self.standardOverview.GetSize())
        self.standardOverview.GetContainingSizer().Layout()
            
    def refreshTracker(self):
        torrent = self.standardDetails.getData()
        if not torrent:
            return
        if DEBUG:
            print >>sys.stderr,'GUIUtility: refresh ' + repr(torrent.get('content_name', 'no_name'))
        if torrent:
            check = TorrentChecking(torrent['infohash'])
            check.start()
            
            
    def refreshTorrentStats(self,dslist):
        """ Called from ABCApp by MainThread to refresh statistics of downloading torrents"""
        pass
        ##try:
        ##    if self.guiOpen.isSet():
        ##        self.standardDetails.refreshTorrentStats(dslist)
        ##except:
        ##    print_exc()
    
    def refreshUploadStats(self, dslist):
        pass
        ##try:
        ##    if self.guiOpen.isSet():
        ##        self.standardDetails.refreshUploadStats(dslist)
        ##except:
        ##    print_exc()
   
    def emailFriend(self, event):
        ip = self.utility.config.Read('bind')
        if ip is None or ip == '':
            ip = self.utility.session.get_external_ip()
        mypermid = self.utility.session.get_permid()

        permid_txt = self.utility.lang.get('permid')+": "+show_permid(mypermid)
        ip_txt = self.utility.lang.get('ipaddress')+": "+ip

        port = self.utility.session.get_listen_port()
        port_txt = self.utility.lang.get('portnumber')+" "+str(port)

        subject = self.utility.lang.get('invitation_subject')
        invitation_body = self.utility.lang.get('invitation_body')
        invitation_body = invitation_body.replace('\\n', '\n')
        invitation_body += ip_txt + '\n\r'
        invitation_body += port_txt + '\n\r'
        invitation_body += permid_txt + '\n\r\n\r\n\r'
       
        if sys.platform == "darwin":
            body = invitation_body.replace('\\r','')
            body = body.replace('\r','')
        else:
            body = urllib.quote(invitation_body)
        mailToURL = 'mailto:%s?subject=%s&body=%s'%('', subject, body)
        try:
            webbrowser.open(mailToURL)
        except:
            text = invitation_body.split("\n")
            InviteFriendsDialog(text)

    def get_nat_type(self, callback=None):
        return self.utility.session.get_nat_type(callback=callback)



    def dosearch(self):
        sf = self.frame.top_bg.searchField
        if sf is None:
            return
        input = sf.GetValue().strip()
        if input == '':
            return

        if self.search_mode == 'files':
            self.searchFiles('filesMode', input)
        else:
            self.searchChannels('channelsMode', input)
     


    def searchFiles(self, mode, input):
        wantkeywords = split_into_keywords(input)
        if DEBUG:
            print >>sys.stderr,"GUIUtil: searchFiles:", wantkeywords

        self.torrentsearch_manager.setSearchKeywords(wantkeywords, mode)
        self.torrentsearch_manager.set_gridmgr(self.standardOverview.getGrid().getGridManager())
        #print "******** gui uti searchFiles", wantkeywords

        self.frame.channelsDetails.Hide()
        self.frame.channelsDetails.mychannel = False

        self.standardOverview.setMode('filesMode')

        self.frame.standardOverview.SetMinSize((300,490)) # 476

        self.showPager(True)
        if sys.platform == "linux2":
            self.frame.pagerPanel.SetMinSize((626,20))
        elif sys.platform == 'darwin':
            self.frame.pagerPanel.SetMinSize((674,21))
        else:
            self.frame.pagerPanel.SetMinSize((626,20))



        self.standardOverview.getGrid().clearAllData()
        gridstate = GridState('filesMode', 'all', 'rameezmetric')
        self.standardOverview.filterChanged(gridstate)
 
        #
        # Query the peers we are connected to
        #
        q = 'SIMPLE '
        for kw in wantkeywords:
            q += kw+' '
            
        self.utility.session.query_connected_peers(q,self.sesscb_got_remote_hits,self.max_remote_queries)
        self.standardOverview.setSearchFeedback('remote', False, 0, wantkeywords,self.frame.top_bg.search_results)
                



    def searchChannels(self, mode, input):
        wantkeywords = split_into_keywords(input)
        if DEBUG:
            print >>sys.stderr,"GUIUtil: searchChannels:", wantkeywords
        self.channelsearch_manager.setSearchKeywords(wantkeywords, mode)

        ##### GUI specific code

        if self.standardOverview.getMode != 'channelsMode':
            self.standardOverview.setMode('channelsMode')

        self.standardOverview.setSearchFeedback('channels', False, -1, self.channelsearch_manager.searchkeywords[mode])

        grid2 = self.standardOverview.getGrid(2)
        grid2.Hide()
        grid = self.standardOverview.getGrid()
        grid.gridManager.blockedRefresh=True

        grid.gridManager.resizeGrid(grid)
        grid.gridManager.blockedRefresh=False


        self.frame.top_bg.indexMyChannel=-1

        self.frame.channelsDetails.Show()
        self.frame.channelsDetails.mychannel = False
        if not self.frame.channelsDetails.isEmpty():
            self.frame.channelsDetails.reinitialize()
        self.showPager(False)
        wx.GetApp().Yield()
        self.loadInformation('channelsMode', 'name', erase=True)

        
        if mode == 'channelsMode':
            q = 'CHANNEL k:'
            for kw in wantkeywords:
                q += kw+' '
            
            self.utility.session.query_connected_peers(q,self.sesscb_got_channel_hits)
            ##### GUI specific code




    def complete(self, term):
        """autocompletes term."""
        completion = self.utility.session.open_dbhandler(NTFY_TERM).getTermsStartingWith(term, num=1)
        if completion:
            return completion[0][len(term):]
        # boudewijn: may only return unicode compatible strings. While
        # "" is unicode compatible it is better to return u"" to
        # indicate that it must be unicode compatible.
        return u""

    def sesscb_got_remote_hits(self,permid,query,hits):
        # Called by SessionCallback thread 

        if DEBUG:
            print >>sys.stderr,"GUIUtil: sesscb_got_remote_hits",len(hits)

        # 22/01/10 boudewijn: use the split_into_keywords function to
        # split.  This will ensure that kws is unicode and splits on
        # all 'splittable' characters
        kwstr = query[len('SIMPLE '):]
        kws = split_into_keywords(kwstr)

        wx.CallAfter(self.torrentsearch_manager.gotRemoteHits,permid,kws,hits,self.standardOverview.getMode())
        
    def sesscb_got_channel_hits(self,permid,query,hits):
        # Called by SessionCallback thread 
        if DEBUG:
            print >>sys.stderr,"GUIUtil: sesscb_got_channel_hits",len(hits)

        # 22/01/10 boudewijn: use the split_into_keywords function to
        # split.  This will ensure that kws is unicode and splits on
        # all 'splittable' characters
        kwstr = query[len("CHANNEL x:"):]
        kws = split_into_keywords(kwstr)

        records = []
        for k,v in hits.items():
            records.append((v['publisher_id'],v['publisher_name'],v['infohash'],v['torrenthash'],v['torrentname'],v['time_stamp'],k))


        if DEBUG:
            print >> sys.stderr , "CHANNEL HITS" , records



        #Code that calls GUI
        # 1. Grid needs to be updated with incoming hits, from each remote peer
        # 2. Sorting should also be done by that function
        wx.CallAfter(self.channelsearch_manager.gotRemoteHits,permid,kws,records,self.standardOverview.getMode())
        

    def stopSearch(self):
        self.frame.go.setToggled(False)
        self.frame.top_bg.createBackgroundImage()
        self.frame.top_bg.Refresh()
        self.frame.top_bg.Update()
        self.frame.search.SetFocus()
        mode = self.standardOverview.getMode() 
        if mode == 'filesMode' or mode == 'libraryMode':
            self.torrentsearch_manager.stopSearch()
        if mode == 'personsMode' or mode == 'friendsMode':
            self.peersearch_manager.stopSearch()
        
    def clearSearch(self):
        mode = self.standardOverview.getMode()
        self.standardOverview.data[mode]['search'].Clear()
        if mode == 'filesMode'  or mode == 'libraryMode':
            self.torrentsearch_manager.setSearchKeywords([],mode)
            gridState = self.standardOverview.getFilter().getState()
            if not gridState or not gridState.isValid():
                gridState = GridState(mode, 'all', 'num_seeders')
            if DEBUG:
                print >> sys.stderr, 'GUIUtil: clearSearch, back to: %s' % gridState
            self.standardOverview.filterChanged(gridState)
        if mode == 'personsMode'  or mode == 'friendsMode':
            self.peersearch_manager.setSearchKeywords([],mode)
            gridState = GridState(mode, 'all', 'last_connected', reverse=False)
            self.standardOverview.filterChanged(gridState)
        
    def searchPersons(self, mode, input):
        wantkeywords = split_into_keywords(input)
        if DEBUG:
            print >>sys.stderr,"GUIUtil: searchPersons:", wantkeywords

        self.peersearch_manager.setSearchKeywords(wantkeywords, mode)
        self.peersearch_manager.set_gridmgr(self.standardOverview.getGrid().getGridManager())
        #print "******** gui uti searchFiles", wantkeywords
        gridstate = GridState(self.standardOverview.mode, 'all', 'last_connected')
        self.standardOverview.filterChanged(gridstate)
   

    def OnSearchKeyDown(self,event):
        
        keycode = event.GetKeyCode()
        #if event.CmdDown():
        #print "OnSearchKeyDown: keycode",keycode
        if keycode == wx.WXK_RETURN:
            self.frame.Hide()
            self.standardFilesOverview()
            self.dosearch()
        else:
            event.Skip()     

    def OnSubscribeKeyDown(self,event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN:
            self.subscribe()
        event.Skip()     

    def OnSubscribeMouseAction(self,event):
        obj = event.GetEventObject()

        # TODO: smarter behavior
        obj.SetSelection(-1,-1)
        event.Skip()


    """
    def subscribe(self):
        rssurlctrl = self.standardOverview.getRSSUrlCtrl()
        url = rssurlctrl.GetValue()
        if not url:
            return
        if not "://" in url:
            url = "http://" + url

        if DEBUG:
            print >>sys.stderr,"GUIUtil: subscribe:",url
        try:
            stream = urllib2.urlopen(url)
            stream.close()
        except Exception,e:
            dlg = wx.MessageDialog(self.standardOverview, "Could not resolve URL:\n\n"+str(e), 'Tribler Warning',wx.OK | wx.ICON_WARNING)
            result = dlg.ShowModal()
            dlg.Destroy()
            return
        
        torrentfeed = TorrentFeedThread.getInstance()
        torrentfeed.addURL(url)
        self.standardOverview.loadSubscriptionData()
        self.standardOverview.refreshData()
    """

    def set_firewall_restart(self,b):
        self.firewall_restart = b


    def firewallStatusClick(self,event=None):
        title = self.utility.lang.get('tribler_information')
        if self.firewall_restart:
            type = wx.ICON_WARNING
            msg = self.utility.lang.get('restart_tooltip')
        elif self.isReachable():
            type = wx.ICON_INFORMATION
            msg = self.utility.lang.get('reachable_tooltip')
        else:
            type = wx.ICON_INFORMATION
            msg = self.utility.lang.get('connecting_tooltip')
            
        dlg = wx.MessageDialog(None, msg, title, wx.OK|type)
        result = dlg.ShowModal()
        dlg.Destroy()

    def OnSearchMouseAction(self,event):
        sf = self.standardOverview.getSearchField()
        if sf is None:
            return

        eventType = event.GetEventType()
        #print 'event: %s, double: %s, leftup: %s' % (eventType, wx.EVT_LEFT_DCLICK, wx.EVT_LEFT_UP)
        #print 'value: "%s", 1: "%s", 2: "%s"' % (sf.GetValue(), self.utility.lang.get('filesdefaultsearchweb2txt'),self.utility.lang.get('filesdefaultsearchtxt')) 
        if event.LeftDClick() or \
           ( event.LeftUp() and sf.GetValue() in [self.utility.lang.get('filesdefaultsearchweb2txt'),self.utility.lang.get('filesdefaultsearchtxt')]):
            ##print 'select'
            sf.SetSelection(-1,-1)
            
        if not event.LeftDClick():
            event.Skip()

    def getSearchField(self,mode=None):
        return self.standardOverview.getSearchField(mode=mode)
   
    def isReachable(self):
        return self.utility.session.get_externally_reachable()
   
   
    def onChangeViewModus(self):
        # clicked on changemodus button in title bar of overviewPanel
        changeViewModus = wx.Menu() 
        self.utility.makePopup(changeViewModus, None, 'rChangeViewModusThumb', type="checkitem", status="active")
        self.utility.makePopup(changeViewModus, None, 'rChangeViewModusList', type="checkitem") 
        return (changeViewMouse)
        
        
        
    def OnRightMouseAction(self,event):
        # called from  "*ItemPanel" or from "standardDetails"
        item = self.standardDetails.getData()
        if not item:
            if DEBUG:
                print >>sys.stderr,'GUIUtil: Used right mouse menu, but no item in DetailWindow'
            return
        
        rightMouse = wx.Menu()        

        
        
        if self.standardOverview.mode == "filesMode" and not item.get('myDownloadHistory', False):
            self.utility.makePopup(rightMouse, None, 'rOptions')
            if item.get('web2'):
                self.utility.makePopup(rightMouse, self.onDownloadOpen, 'rPlay')
            else:
                #self.utility.makePopup(rightMouse, self.onRecommend, 'rRecommend')        
                #if secret:
                self.utility.makePopup(rightMouse, self.onDownloadOpen, 'rDownloadOpenly')
                #else:
                #self.utility.makePopup(rightMouse, self.onDownloadSecret, 'rDownloadSecretly')
            
            # if in library:
        elif self.standardOverview.mode == "libraryMode" or item.get('myDownloadHistory'):
            #self.utility.makePopup(rightMouse, self.onRecommend, 'rRecommend')        
            #rightMouse.AppendSeparator()
            self.utility.makePopup(rightMouse, None, 'rLibraryOptions')
            self.utility.makePopup(rightMouse, self.onOpenFileDest, 'rOpenfilename')
            self.utility.makePopup(rightMouse, self.onOpenDest, 'rOpenfiledestination')
            self.utility.makePopup(rightMouse, self.onDeleteTorrentFromLibrary, 'rRemoveFromList')
            self.utility.makePopup(rightMouse, self.onDeleteTorrentFromDisk, 'rRemoveFromListAndHD') 
            #rightMouse.AppendSeparator()
            #self.utility.makePopup(rightMouse, self.onAdvancedInfoInLibrary, 'rAdvancedInfo')
        elif self.standardOverview.mode == "personsMode" or self.standardOverview.mode == "friendsMode":     
            self.utility.makePopup(rightMouse, None, 'rOptions')
            fs = item.get('friend') 
            if fs == FS_MUTUAL or fs == FS_I_INVITED:
                self.utility.makePopup(rightMouse, self.onChangeFriendStatus, 'rRemoveAsFriend')
                self.utility.makePopup(rightMouse, self.onChangeFriendInfo, 'rChangeInfo')
            else:
                self.utility.makePopup(rightMouse, self.onChangeFriendStatus, 'rAddAsFriend')
            
            # if in friends:
##            if self.standardOverview.mode == "friendsMode":
##                rightMouse.AppendSeparator()
##                self.utility.makePopup(rightMouse, None, 'rFriendsOptions')
##                self.utility.makePopup(rightMouse, None, 'rSendAMessage')
        elif self.standardOverview.mode == "subscriptionsMode":
            event.Skip()
##            self.utility.makePopup(rightMouse, None, 'rOptions')
##            self.utility.makePopup(rightMouse, None, 'rChangeSubscrTitle')
##            self.utility.makePopup(rightMouse, None, 'rRemoveSubscr')
            

        
        return (rightMouse)
        #self.PopupMenu(rightMouse, (-1,-1))  
        
# ================== actions for rightMouse button ========================================== 
    def onOpenFileDest(self, event = None):
        # open File
        self.onOpenDest(event, openFile=True)
  
    def onOpenDest(self, event = None, openFile=False):
        # open Destination
        item = self.standardDetails.getData()
        state = item.get('ds')
        
        if state:
            dest = state.get_download().get_dest_dir()
            if openFile:
                destfiles = state.get_download().get_dest_files()
                if len(destfiles) == 1:
                    dest = destfiles[0][1]
            if sys.platform == 'darwin':
                dest = 'file://%s' % dest
            
            print >> sys.stderr,"GUIUtil: onOpenDest",dest
            complete = True
            # check if destination exists
            assert dest is not None and os.access(dest, os.R_OK), 'Could not retrieve destination'
            try:
                t = Thread(target = open_new, args=(str(dest),))
                t.setName( "FilesOpenNew"+t.getName() )
                t.setDaemon(True)
                t.start()
            except:
                print_exc()
                
        elif DEBUG:
            print >>sys.stderr,'GUIUtil: onOpenFileDest failed: no torrent selected'
            
    def onDeleteTorrentFromDisk(self, event = None):
        item = self.standardDetails.getData()
        
        if item.get('ds'):
            self.utility.session.remove_download(item['ds'].get_download(),removecontent = True)
            self.user_download_choice.remove_download_state(item['ds'].get_download().get_def().get_infohash())
            
        self.standardOverview.removeTorrentFromLibrary(item)
        #wx.CallAfter(self.frame.standardPager.Show,self.standardOverview.getGrid().getGridManager().get_total_items()>0)



                
    def onDeleteTorrentFromLibrary(self, event = None):
        item = self.standardDetails.getData()
        
        if item.get('ds'):
            self.utility.session.remove_download(item['ds'].get_download(),removecontent = False)
            
        self.standardOverview.removeTorrentFromLibrary(item)
    

    def onAdvancedInfoInLibrary(self, event = None):
        # open torrent details frame
        item = self.standardDetails.getData()
        abctorrent = item.get('abctorrent')
        if abctorrent:
            abctorrent.dialogs.advancedDetails(item)
            
        event.Skip()
        
    def onModerate(self, event = None):
        if DEBUG:
            print >>sys.stderr,'GUIUtil: ---tb--- Moderate event'
            print >>sys.stderr,event
        # todo
        event.Skip()
    
    def onRecommend(self, event = None):
        # todo
        event.Skip()
   
    def onDownloadOpen(self, event = None):
        self.standardDetails.download()
        event.Skip()
    
    def onDownloadSecret(self, event = None):
        self.standardDetails.download(secret=True)
        event.Skip()
        
    def onChangeFriendStatus(self, event = None):
        self.standardDetails.addAsFriend()
        event.Skip()

    def onChangeFriendInfo(self, event = None):
        item = self.standardDetails.getData()       
        dialog = MakeFriendsDialog(self.frame,self.utility, item)
        ret = dialog.ShowModal()
        dialog.Destroy()
        event.Skip()
        
       
    def getGuiElement(self, name):
        if not self.elements.has_key(name) or not self.elements[name]:
            return None
        return self.elements[name]
    


    
# =========END ========= actions for rightMouse button ==========================================
    
    def superRefresh(self, sizer):
        print 'supersizer to the rescue'
        for item in sizer.GetChildren():
            if item.IsSizer():
                self.superRefresh(item.GetSizer())
                item.GetSizer().Layout()
            elif item.IsWindow():
                item.GetWindow().Refresh()
