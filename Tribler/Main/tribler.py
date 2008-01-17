#!/usr/bin/python

#########################################################################
#
# Author : Choopan RATTANAPOKA, Jie Yang, Arno Bakker
#
# Description : Main ABC [Yet Another Bittorrent Client] python script.
#               you can run from source code by using
#               >python abc.py
#               need Python, WxPython in order to run from source code.
#########################################################################

# Arno: M2Crypto overrides the method for https:// in the
# standard Python libraries. This causes msnlib to fail and makes Tribler
# freakout when "http://www.tribler.org/version" is redirected to
# "https://www.tribler.org/version/" (which happened during our website
# changeover) Until M2Crypto 0.16 is patched I'll restore the method to the
# original, as follows.
#
# This must be done in the first python file that is started.
#

import os,sys

if sys.platform == "darwin":
    # on Mac, we can only load VLC/OpenSSL libraries
    # relative to the location of tribler.py
    os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))

import urllib
original_open_https = urllib.URLopener.open_https
import M2Crypto
urllib.URLopener.open_https = original_open_https

import locale
import signal
import wx, commands
from wx import xrc
#import hotshot


from threading import Thread, Event,currentThread,enumerate
from time import time, ctime, sleep
from traceback import print_exc, print_stack
from cStringIO import StringIO
import urllib

from Tribler.Utilities.interconn import ServerListener, ClientPassParam


if (sys.platform == 'win32'):
    from Dialogs.regdialog import RegCheckDialog

from Tribler.Main.Utility.utility import Utility
from Tribler.Main.Utility.constants import * #IGNORE:W0611

from Tribler.Core.BitTornado.__init__ import product_name
from safeguiupdate import DelayedInvocation,FlaglessDelayedInvocation
import webbrowser
import Tribler.Main.vwxGUI.font as font
from Tribler.Main.vwxGUI.GuiUtility import GUIUtility
import Tribler.Main.vwxGUI.updateXRC as updateXRC
from Tribler.Video.VideoPlayer import VideoPlayer,return_feasible_playback_modes,PLAYBACKMODE_INTERNAL
from Tribler.Video.VideoServer import VideoHTTPServer
from Tribler.Main.Dialogs.GUIServer import GUIServer
from Tribler.Main.vwxGUI.TasteHeart import set_tasteheart_bitmaps
from Tribler.Main.vwxGUI.perfBar import set_perfBar_bitmaps
from Tribler.Main.Dialogs.BandwidthSelector import BandwidthSelector
from Tribler.Subscriptions.rss_client import TorrentFeedThread
from Tribler.Core.simpledefs import *
from Tribler.Core.DecentralizedTracking import mainlineDHT
from Tribler.Core.DecentralizedTracking.rsconvert import RawServerConverter
from Tribler.Core.DecentralizedTracking.mainlineDHTChecker import mainlineDHTChecker

from Tribler.Main.notification import init as notification_init
from Tribler.Main.vwxGUI.font import *
from Tribler.Web2.util.update import Web2Updater

from Tribler.Core.CacheDB.CacheDBHandler import BarterCastDBHandler
from Tribler.Core.Overlay.permid import permid_for_user
from Tribler.Core.simpledefs import *
from Tribler.Core.Session import Session
from Tribler.Core.APIImplementation.miscutils import NamedTimer
from Tribler.Core.SessionConfig import SessionStartupConfig
from Tribler.Policies.RateManager import UserDefinedMaxAlwaysOtherwiseEquallyDividedRateManager
import Tribler.Category.Category
DEBUG = False
ALLOW_MULTIPLE = False
start_time = 0
start_time2 = 0


################################################################
#
# Class: FileDropTarget
#
# To enable drag and drop for ABC list in main menu
#
################################################################
class FileDropTarget(wx.FileDropTarget): 
    def __init__(self, utility):
        # Initialize the wsFileDropTarget Object 
        wx.FileDropTarget.__init__(self) 
        # Store the Object Reference for dropped files 
        self.utility = utility
      
    def OnDropFiles(self, x, y, filenames):
        for filename in filenames:
            self.utility.queue.addtorrents.AddTorrentFromFile(filename)
        return True



# Custom class loaded by XRC
class ABCFrame(wx.Frame, DelayedInvocation):
    def __init__(self, *args):
        if len(args) == 0:
            pre = wx.PreFrame()
            # the Create step is done by XRC.
            self.PostCreate(pre)
            self.Bind(wx.EVT_WINDOW_CREATE, self.OnCreate)
        else:
            wx.Frame.__init__(self, args[0], args[1], args[2], args[3])
            self._PostInit()
        
    def OnCreate(self, event):
        self.Unbind(wx.EVT_WINDOW_CREATE)
        wx.CallAfter(self._PostInit)
        event.Skip()
        return True
    
    def _PostInit(self):
        # Do all init here
        self.guiUtility = GUIUtility.getInstance()
        self.utility = self.guiUtility.utility
        self.params = self.guiUtility.params
        self.utility.frame = self
        
        title = self.utility.lang.get('title') + \
                " " + \
                self.utility.lang.get('version')
        
        # Get window size and position from config file
        size, position = self.getWindowSettings()
        style = wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN
        
        self.SetSize(size)
        self.SetPosition(position)
        self.SetTitle(title)
        tt = self.GetToolTip()
        if tt is not None:
            tt.SetTip('')
        
        #wx.Frame.__init__(self, None, ID, title, position, size, style = style)
        
        self.doneflag = Event()
        DelayedInvocation.__init__(self)

        dragdroplist = FileDropTarget(self.utility)
        self.SetDropTarget(dragdroplist)

        self.tbicon = None

        # Arno: see ABCPanel
        #self.abc_sb = ABCStatusBar(self,self.utility)
        #self.SetStatusBar(self.abc_sb)

        """
        # Add status bar
        statbarbox = wx.BoxSizer(wx.HORIZONTAL)
        self.sb_buttons = ABCStatusButtons(self,self.utility)
        statbarbox.Add(self.sb_buttons, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        self.abc_sb = ABCStatusBar(self,self.utility)
        statbarbox.Add(self.abc_sb, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
        #colSizer.Add(statbarbox, 0, wx.ALL|wx.EXPAND, 0)
        self.SetStatusBar(statbarbox)
        """
        
        
        try:
            self.SetIcon(self.utility.icon)
        except:
            pass

        # Don't update GUI as often when iconized
        self.GUIupdate = True

        # Start the scheduler before creating the ListCtrl
        #self.utility.queue  = ABCScheduler(self.utility)
        #self.window = ABCPanel(self)
        #self.abc_sb = self.window.abc_sb
        
        
        #self.oldframe = ABCOldFrame(-1, self.params, self.utility)
        #self.oldframe.Refresh()
        #self.oldframe.Layout()
        #self.oldframe.Show(True)
        
        self.window = self.GetChildren()[0]
        self.window.utility = self.utility
        
        """
        self.list = ABCList(self.window)
        self.list.Show(False)
        self.utility.list = self.list
        print self.window.GetName()
        self.window.list = self.list
        self.utility.window = self.window
        """
        #self.window.sb_buttons = ABCStatusButtons(self,self.utility)
        
        #self.utility.window.postponedevents = []
        
        # Menu Options
        ############################
        #menuBar = ABCMenuBar(self)
        #if sys.platform == "darwin":
        #    wx.App.SetMacExitMenuItemId(wx.ID_CLOSE)
        #self.SetMenuBar(menuBar)
        
        #self.tb = ABCToolBar(self) # new Tribler gui has no toolbar
        #self.SetToolBar(self.tb)
        
        self.buddyFrame = None
        self.fileFrame = None
        self.buddyFrame_page = 0
        self.buddyFrame_size = (800, 500)
        self.buddyFrame_pos = None
        self.fileFrame_size = (800, 500)
        self.fileFrame_pos = None
        
        # Menu Events 
        ############################

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
#        self.Bind(wx.EVT_MENU, self.OnMenuExit, id = wx.ID_CLOSE)

        # leaving here for the time being:
        # wxMSW apparently sends the event to the App object rather than
        # the top-level Frame, but there seemed to be some possibility of
        # change
        self.Bind(wx.EVT_QUERY_END_SESSION, self.OnCloseWindow)
        self.Bind(wx.EVT_END_SESSION, self.OnCloseWindow)
        
        try:
            self.tbicon = ABCTaskBarIcon(self)
        except:
            pass
        self.Bind(wx.EVT_ICONIZE, self.onIconify)
        self.Bind(wx.EVT_SET_FOCUS, self.onFocus)
        self.Bind(wx.EVT_SIZE, self.onSize)
        self.Bind(wx.EVT_MAXIMIZE, self.onSize)
        #self.Bind(wx.EVT_IDLE, self.onIdle)
        
        # Start up the controller
        #self.utility.controller = ABCLaunchMany(self.utility)
        #self.utility.controller.start()
        self.startAPI()
        
        # Start up mainline DHT
        # Arno: do this in a try block, as khashmir gives a very funky
        # error when started from a .dmg (not from cmd line) on Mac. In particular
        # it complains that it cannot find the 'hex' encoding method when
        # hstr.encode('hex') is called, and hstr is a string?!
        #
#        try:
#            rsconvert = RawServerConverter(self.utility.controller.get_rawserver())
#            mainlineDHT.init('', self.utility.listen_port, self.utility.getConfigPath(),rawserver=rsconvert)
#            # Create torrent-liveliness checker based on DHT
#            c = mainlineDHTChecker.getInstance()
#            c.register(mainlineDHT.dht)
#        except:
#            print_exc()

        # Give GUI time to set up stuff
        wx.Yield()

        #if server start with params run it
        #####################################
        
        if DEBUG:
            print >>sys.stderr,"abc: wxFrame: params is",self.params
        
        if self.params[0] != "":
            success, msg, ABCTorrentTemp = self.utility.queue.addtorrents.AddTorrentFromFile(self.params[0],caller=CALLER_ARGV)

        #self.utility.queue.postInitTasks(self.params)

        if self.params[0] != "":
            # Update torrent.list, but after having read the old list of torrents, otherwise we get interference
            ABCTorrentTemp.torrentconfig.writeSrc(False)
            self.utility.torrentconfig.Flush()

        self.videoFrame = None
        feasible = return_feasible_playback_modes(self.utility.getPath())
        if PLAYBACKMODE_INTERNAL in feasible:
            # This means vlc is available
            from Tribler.Video.EmbeddedPlayer import VideoFrame
            self.videoFrame = VideoFrame(self)

            #self.videores = xrc.XmlResource("Tribler/vwxGUI/MyPlayer.xrc")
            #self.videoframe = self.videores.LoadFrame(None, "MyPlayer")
            #self.videoframe.Show()
            
            videoplayer = VideoPlayer.getInstance()
            videoplayer.set_parentwindow(self.videoFrame)
        else:
            videoplayer = VideoPlayer.getInstance()
            videoplayer.set_parentwindow(self)

        sys.stdout.write('GUI Complete.\n')

        self.Show(True)
        
        
        # Just for debugging: add test permids and display top 5 peers from which the most is downloaded in bartercastdb
        bartercastdb = BarterCastDBHandler.getInstance()
        mypermid = bartercastdb.my_permid
        
        if DEBUG:
            
            top = bartercastdb.getTopNPeers(5)['top']
    
            print 'My Permid: ', permid_for_user(mypermid)
            
            print 'Top 5 BarterCast peers:'
            print '======================='
    
            i = 1
            for (permid, up, down) in top:
                print '%2d: %15s  -  %10d up  %10d down' % (i, bartercastdb.getName(permid), up, down)
                i += 1
        
        
        # Check to see if ABC is associated with torrents
        #######################################################
        if (sys.platform == 'win32'):
            if self.utility.config.Read('associate', "boolean"):
                if self.utility.regchecker and not self.utility.regchecker.testRegistry():
                    dialog = RegCheckDialog(self)
                    dialog.ShowModal()
                    dialog.Destroy()

        self.checkVersion()

    def startAPI(self):
        sscfg = SessionStartupConfig()
        sscfg.set_install_dir(self.utility.getPath())
        #sscfg.set_state_dir('/tmp/state_dir')
        if sys.platform == 'win32':
            s = Session()
        else:
            s = Session(sscfg)
            
        print 'config_dir: %s' % s.get_state_dir()
        self.utility.session = s
        r = UserDefinedMaxAlwaysOtherwiseEquallyDividedRateManager()
        r.set_global_max_speed(DOWNLOAD,100)
        
    def checkVersion(self):
        t = NamedTimer(2.0, self._checkVersion)
        t.start()
        
    def _checkVersion(self):
        my_version = self.utility.getVersion()
        try:
            curr_status = urllib.urlopen('http://tribler.org/version').readlines()
            line1 = curr_status[0]
            if len(curr_status) > 1:
                self.update_url = curr_status[1].strip()
            else:
                self.update_url = 'http://tribler.org'
            _curr_status = line1.split()
            self.curr_version = _curr_status[0]
            if self.newversion(self.curr_version, my_version):
                # Arno: we are a separate thread, delegate GUI updates to MainThread
                self.upgradeCallback()
            
            # Also check new version of web2definitions for youtube etc. search
            Web2Updater(self.utility).checkUpdate()
        except Exception,e:
            print >> sys.stderr, "Tribler: Version check failed", ctime(time()), str(e)
            #print_exc()
            
    def newversion(self, curr_version, my_version):
        curr = curr_version.split('.')
        my = my_version.split('.')
        if len(my) >= len(curr):
            nversion = len(my)
        else:
            nversion = len(curr)
        for i in range(nversion):
            if i < len(my):
                my_v = int(my[i])
            else:
                my_v = 0
            if i < len(curr):
                curr_v = int(curr[i])
            else:
                curr_v = 0
            if curr_v > my_v:
                return True
            elif curr_v < my_v:
                return False
        return False

    def upgradeCallback(self):
        self.invokeLater(self.OnUpgrade)    
        # TODO: warn multiple times?
    
    def OnUpgrade(self, event=None):
        self.setActivity(NTFY_ACT_NEW_VERSION)
        guiserver = GUIServer.getInstance()
        guiserver.add_task(self.upgradeCallback,10.0)

    def onFocus(self, event = None):
        if event is not None:
            event.Skip()
        #self.window.getSelectedList(event).SetFocus()
        
    def setGUIupdate(self, update):
        oldval = self.GUIupdate
        self.GUIupdate = update
        
        if self.GUIupdate and not oldval:
            # Force an update of all torrents
            for torrent in self.utility.torrents["all"]:
                torrent.updateColumns()
                torrent.updateColor()


    def taskbarCallback(self):
        self.invokeLater(self.onTaskBarActivate,[])


    #######################################
    # minimize to tray bar control
    #######################################
    def onTaskBarActivate(self, event = None):
        self.Iconize(False)
        self.Show(True)
        self.Raise()
        
        if self.tbicon is not None:
            self.tbicon.updateIcon(False)

        #self.window.list.SetFocus()

        # Resume updating GUI
        self.setGUIupdate(True)

    def onIconify(self, event = None):
        # This event handler is called both when being minimalized
        # and when being restored.
        if DEBUG:
            if event is not None:
                print  >> sys.stderr,"abc: onIconify(",event.Iconized()
            else:
                print  >> sys.stderr,"abc: onIconify event None"
        if event.Iconized():                                                                                                               
            if (self.utility.config.Read('mintray', "int") > 0
                and self.tbicon is not None):
                self.tbicon.updateIcon(True)
                self.Show(False)

            # Don't update GUI while minimized
            self.setGUIupdate(False)
        else:
            self.setGUIupdate(True)
        if event is not None:
            event.Skip()

    def onSize(self, event = None):
        # Arno: On Windows when I enable the tray icon and then change
        # virtual desktop (see MS DeskmanPowerToySetup.exe)
        # I get a onIconify(event.Iconized()==True) event, but when
        # I switch back, I don't get an event. As a result the GUIupdate
        # remains turned off. The wxWidgets wiki on the TaskBarIcon suggests
        # catching the onSize event. 
        
        if DEBUG:
            if event is not None:
                print  >> sys.stderr,"abc: onSize:",self.GetSize()
            else:
                print  >> sys.stderr,"abc: onSize: None"
        self.setGUIupdate(True)
        if event is not None:
            if event.GetEventType() == wx.EVT_MAXIMIZE:
                self.window.SetClientSize(self.GetClientSize())
            event.Skip()
        

        # Refresh subscreens
        self.refreshNeeded = True
        self.guiUtility.refreshOnResize()
        
    def onIdle(self, event = None):
        """
        Only refresh screens (especially detailsPanel) when resizes are finished
        This gives less flickering, but doesnt look pretty, so i commented it out
        """
        if self.refreshNeeded:
            self.guiUtility.refreshOnResize()
            self.refreshNeeded = False
        
    def getWindowSettings(self):
        width = self.utility.config.Read("window_width")
        height = self.utility.config.Read("window_height")
        try:
            size = wx.Size(int(width), int(height))
        except:
            size = wx.Size(710, 400)

        x = self.utility.config.Read("window_x")
        y = self.utility.config.Read("window_y")
        if (x == "" or y == ""):
            #position = wx.DefaultPosition

            # On Mac, the default position will be underneath the menu bar, so lookup (top,left) of
            # the primary display
            primarydisplay = wx.Display(0)
            dsize = primarydisplay.GetClientArea()
            position = dsize.GetTopLeft()

            # Decrease size to fit on screen, if needed
            width = min( size.GetWidth(), dsize.GetWidth() )
            height = min( size.GetHeight(), dsize.GetHeight() )
            size = wx.Size( width, height )
        else:
            position = wx.Point(int(x), int(y))

        return size, position     
        
    def saveWindowSettings(self):
        width, height = self.GetSizeTuple()
        x, y = self.GetPositionTuple()
        self.utility.config.Write("window_width", width)
        self.utility.config.Write("window_height", height)
        self.utility.config.Write("window_x", x)
        self.utility.config.Write("window_y", y)

        self.utility.config.Flush()
       
    ##################################
    # Close Program
    ##################################
               
    def OnCloseWindow(self, event = None):
        if event != None:
            nr = event.GetEventType()
            lookup = { wx.EVT_CLOSE.evtType[0]: "EVT_CLOSE", wx.EVT_QUERY_END_SESSION.evtType[0]: "EVT_QUERY_END_SESSION", wx.EVT_END_SESSION.evtType[0]: "EVT_END_SESSION" }
            if nr in lookup: nr = lookup[nr]
            print "Closing due to event ",nr
            print >>sys.stderr,"Closing due to event ",nr
        else:
            print "Closing untriggered by event"
        
        # Don't do anything if the event gets called twice for some reason
        if self.utility.abcquitting:
            return

        # Check to see if we can veto the shutdown
        # (might not be able to in case of shutting down windows)
        if event is not None:
            try:
                if event.CanVeto() and self.utility.config.Read('confirmonclose', "boolean") and not event.GetEventType() == wx.EVT_QUERY_END_SESSION.evtType[0]:
                    dialog = wx.MessageDialog(None, self.utility.lang.get('confirmmsg'), self.utility.lang.get('confirm'), wx.OK|wx.CANCEL)
                    result = dialog.ShowModal()
                    dialog.Destroy()
                    if result != wx.ID_OK:
                        event.Veto()
                        return
            except:
                data = StringIO()
                print_exc(file = data)
                sys.stderr.write(data.getvalue())
                pass
            
        self.utility.abcquitting = True
        self.GUIupdate = False
        
        self.guiUtility.guiOpen.clear()
        
        # Close the Torrent Maker
        #self.utility.actions[ACTION_MAKETORRENT].closeWin()

        if False:
            try:
                self.utility.webserver.stop()
            except:
                data = StringIO()
                print_exc(file = data)
                sys.stderr.write(data.getvalue())
                pass

#        try:
#            # tell scheduler to close all active thread
#            self.utility.queue.clearScheduler()
#        except:
#            data = StringIO()
#            print_exc(file = data)
#            sys.stderr.write(data.getvalue())
#            pass

        try:
            # Restore the window before saving size and position
            # (Otherwise we'll get the size of the taskbar button and a negative position)
            self.onTaskBarActivate()
            self.saveWindowSettings()
        except:
            #print_exc(file=sys.stderr)
            print_exc()

        try:
            if self.buddyFrame is not None:
                self.buddyFrame.Destroy()
            if self.fileFrame is not None:
                self.fileFrame.Destroy()
            if self.videoFrame is not None:
                self.videoFrame.Destroy()
        except:
            pass

        #self.oldframe.Destroy()

        try:
            if self.tbicon is not None:
                self.tbicon.RemoveIcon()
                self.tbicon.Destroy()
            self.Destroy()
        except:
            data = StringIO()
            print_exc(file = data)
            sys.stderr.write(data.getvalue())
            pass

        # Arno: at the moment, Tribler gets a segmentation fault when the
        # tray icon is always enabled. This SEGV occurs in the wx mainloop
        # which is entered as soon as we leave this method. Hence I placed
        # tribler_done() here, so the database are closed properly
        # before the crash.
        #
        # Arno, 2007-02-28: Preferably this should be moved to the main 
        # run() method below, that waits a while to allow threads to finish.
        # Ideally, the database should still be open while they finish up.
        # Because of the crash problem with the icontray this is the safer
        # place.
        #
        # Arno, 2007-08-10: When a torrentfile is passed on the command line,
        # the client will crash just after this point due to unknown reasons
        # (it even does it when we don't look at the cmd line args at all!)
        # Hence, for safety, I close the DB here already. 
        #if sys.platform == 'linux2':
        #
        
        #tribler_done(self.utility.getConfigPath())            
        
        if DEBUG:    
            print >>sys.stderr,"abc: OnCloseWindow END"

        if not DEBUG:
            ts = enumerate()
            for t in ts:
                print >>sys.stderr,"abc: Thread still running",t.getName(),"daemon",t.isDaemon()



    def onWarning(self,exc):
        msg = self.utility.lang.get('tribler_startup_nonfatalerror')
        msg += str(exc.__class__)+':'+str(exc)
        dlg = wx.MessageDialog(None, msg, self.utility.lang.get('tribler_warning'), wx.OK|wx.ICON_WARNING)
        result = dlg.ShowModal()
        dlg.Destroy()

    def onUPnPError(self,upnp_type,listenport,error_type,exc=None,listenproto='TCP'):

        if error_type == 0:
            errormsg = unicode(' UPnP mode '+str(upnp_type)+' ')+self.utility.lang.get('tribler_upnp_error1')
        elif error_type == 1:
            errormsg = unicode(' UPnP mode '+str(upnp_type)+' ')+self.utility.lang.get('tribler_upnp_error2')+unicode(str(exc))+self.utility.lang.get('tribler_upnp_error2_postfix')
        elif error_type == 2:
            errormsg = unicode(' UPnP mode '+str(upnp_type)+' ')+self.utility.lang.get('tribler_upnp_error3')
        else:
            errormsg = unicode(' UPnP mode '+str(upnp_type)+' Unknown error')

        msg = self.utility.lang.get('tribler_upnp_error_intro')
        msg += listenproto+' '
        msg += str(listenport)
        msg += self.utility.lang.get('tribler_upnp_error_intro_postfix')
        msg += errormsg
        msg += self.utility.lang.get('tribler_upnp_error_extro') 

        dlg = wx.MessageDialog(None, msg, self.utility.lang.get('tribler_warning'), wx.OK|wx.ICON_WARNING)
        result = dlg.ShowModal()
        dlg.Destroy()

    def onReachable(self,event=None):
        """ Called by GUI thread """
        if self.firewallStatus is not None:
            self.firewallStatus.setToggled(True)
            tt = self.firewallStatus.GetToolTip()
            if tt is not None:
                tt.SetTip(self.utility.lang.get('reachable_tooltip'))


    def setActivity(self,type,msg=u''):
    
        if currentThread().getName() != "MainThread":
            print  >> sys.stderr,"abc: setActivity thread",currentThread().getName(),"is NOT MAIN THREAD"
            print_stack()
    
        if type == NTFY_ACT_NONE:
            prefix = u''
            msg = u''
        elif type == NTFY_ACT_UPNP:
            prefix = self.utility.lang.get('act_upnp')
        elif type == NTFY_ACT_REACHABLE:
            prefix = self.utility.lang.get('act_reachable')
        elif type == NTFY_ACT_GET_EXT_IP_FROM_PEERS:
            prefix = self.utility.lang.get('act_get_ext_ip_from_peers')
        elif type == NTFY_ACT_MEET:
            prefix = self.utility.lang.get('act_meet')
        elif type == NTFY_ACT_GOT_METADATA:
            prefix = self.utility.lang.get('act_got_metadata')
        elif type == NTFY_ACT_RECOMMEND:
            prefix = self.utility.lang.get('act_recommend')
        elif type == NTFY_ACT_DISK_FULL:
            prefix = self.utility.lang.get('act_disk_full')   
        elif type == NTFY_ACT_NEW_VERSION:
            prefix = self.utility.lang.get('act_new_version')   
        if msg == u'':
            text = prefix
        else:
            text = unicode( prefix+u' '+msg)
            
        if DEBUG:
            print  >> sys.stderr,"abc: Setting activity",`text`,"EOT"
        self.messageField.SetLabel(text)

    def set_player_status(self,s):
        """ Called by VideoServer when using an external player """
        pass


##############################################################
#
# Class : ABCApp
#
# Main ABC application class that contains ABCFrame Object
#
##############################################################
class ABCApp(wx.App,FlaglessDelayedInvocation):
    def __init__(self, x, params, single_instance_checker, abcpath):
        global start_time, start_time2
        start_time2 = time()
        #print "[StartUpDebug]----------- from ABCApp.__init__ ----------Tribler starts up at", ctime(start_time2), "after", start_time2 - start_time
        self.params = params
        self.single_instance_checker = single_instance_checker
        self.abcpath = abcpath
        self.error = None
        wx.App.__init__(self, x)
        
    def OnInit(self):
        try:
            self.utility = Utility(self.abcpath)
            self.utility.app = self
            # Set locale to determine localisation
            locale.setlocale(locale.LC_ALL, '')

            sys.stdout.write('Client Starting Up.\n')
            sys.stdout.write('Build: ' + self.utility.lang.get('build') + '\n')
            
            bm = wx.Bitmap(os.path.join(self.utility.getPath(),'Tribler','Images','splash.jpg'),wx.BITMAP_TYPE_JPEG)
            #s = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN
            #s = wx.SIMPLE_BORDER|wx.FRAME_NO_TASKBAR|wx.FRAME_FLOAT_ON_PARENT
            self.splash = wx.SplashScreen(bm, wx.SPLASH_CENTRE_ON_SCREEN|wx.SPLASH_TIMEOUT, 1000, None, -1)
            
            wx.CallAfter(self.PostInit)
            return True
            
        except Exception,e:
            print_exc()
            self.error = e
            self.onError()
            return False


    def PostInit(self):
        try:
            
            # Initialise fonts
            font.init()

            #tribler_init(self.utility.getConfigPath(),self.utility.getPath(),self.db_exception_handler)
            
            self.utility.postAppInit()
            
            # Singleton for executing tasks that are too long for GUI thread and
            # network thread
            self.guiserver = GUIServer.getInstance()
            self.guiserver.register()
    
            print 'Doing tribler.postinit'
            # H4x0r a bit
            set_tasteheart_bitmaps(self.utility.getPath())
            set_perfBar_bitmaps(self.utility.getPath())
    
            # Put it here so an error is shown in the startup-error popup
            self.serverlistener = ServerListener(self.utility)
            
            
                
            # Start single instance server listenner
            ############################################
            self.serverthread   = Thread(target = self.serverlistener.start)
            self.serverthread.setDaemon(True)
            self.serverthread.setName("SingleInstanceServer"+self.serverthread.getName())
            self.serverthread.start()
    
            self.videoplayer = VideoPlayer.getInstance()
            self.videoplayer.register(self.utility)
            self.videoserver = VideoHTTPServer.getInstance()
            self.videoserver.background_serve()

            notification_init( self.utility )

            #
            # Read and create GUI from .xrc files
            #
            #self.frame = ABCFrame(-1, self.params, self.utility)
            self.guiUtility = GUIUtility.getInstance(self.utility, self.params)
            updateXRC.main([os.path.join(self.utility.getPath(),'vwxGUI')])
            self.res = xrc.XmlResource(os.path.join(self.utility.getPath(),'Tribler', 'Main','vwxGUI','MyFrame.xrc'))
            self.guiUtility.xrcResource = self.res
            self.frame = self.res.LoadFrame(None, "MyFrame")
            self.guiUtility.frame = self.frame
            self.guiUtility.scrollWindow = xrc.XRCCTRL(self.frame, "level0")
            self.guiUtility.mainSizer = self.guiUtility.scrollWindow.GetSizer()
            self.frame.topBackgroundRight = xrc.XRCCTRL(self.frame, "topBG3")
            self.guiUtility.scrollWindow.SetScrollbars(1,1,1024,768)
            self.guiUtility.scrollWindow.SetScrollRate(15,15)
            self.frame.mainButtonPersons = xrc.XRCCTRL(self.frame, "mainButtonPersons")


            self.frame.numberPersons = xrc.XRCCTRL(self.frame, "numberPersons")
            numperslabel = xrc.XRCCTRL(self.frame, "persons")
            self.frame.numberFiles = xrc.XRCCTRL(self.frame, "numberFiles")
            numfileslabel = xrc.XRCCTRL(self.frame, "files")
            self.frame.messageField = xrc.XRCCTRL(self.frame, "messageField")
            self.frame.firewallStatus = xrc.XRCCTRL(self.frame, "firewallStatus")
            tt = self.frame.firewallStatus.GetToolTip()
            if tt is not None:
                tt.SetTip(self.utility.lang.get('unknownreac_tooltip'))
            
            if sys.platform == "linux2":
                self.frame.numberPersons.SetFont(wx.Font(9,FONTFAMILY,FONTWEIGHT,wx.NORMAL,False,FONTFACE))
                self.frame.numberFiles.SetFont(wx.Font(9,FONTFAMILY,FONTWEIGHT,wx.NORMAL,False,FONTFACE))
                self.frame.messageField.SetFont(wx.Font(9,FONTFAMILY,FONTWEIGHT,wx.NORMAL,False,FONTFACE))
                numperslabel.SetFont(wx.Font(9,FONTFAMILY,FONTWEIGHT,wx.NORMAL,False,FONTFACE))
                numfileslabel.SetFont(wx.Font(9,FONTFAMILY,FONTWEIGHT,wx.NORMAL,False,FONTFACE))
            """
            searchfilebut = xrc.XRCCTRL(self.frame, "bt257cC")
            searchfilebut.Bind(wx.EVT_LEFT_UP, self.guiUtility.buttonClicked)
            searchpersbut = xrc.XRCCTRL(self.frame, "bt258cC")
            searchpersbut.Bind(wx.EVT_LEFT_UP, self.guiUtility.buttonClicked)     
            
            self.frame.searchtxtctrl = xrc.XRCCTRL(self.frame, "tx220cCCC")
            """
            
            #self.frame.Refresh()
            #self.frame.Layout()
            self.frame.Show(True)
#===============================================================================
#            global start_time2
#            current_time = time()
#            print "\n\n[StartUpDebug]-----------------------------------------"
#            print "[StartUpDebug]"
#            print "[StartUpDebug]----------- from ABCApp.OnInit ----------Tribler frame is shown after", current_time-start_time2
#            print "[StartUpDebug]"
#            print "[StartUpDebug]-----------------------------------------\n\n"
#===============================================================================
            
            # GUI start
            # - load myFrame 
            # - load standardGrid
            # - gui utility > button mainButtonFiles = clicked
        

            self.Bind(wx.EVT_QUERY_END_SESSION, self.frame.OnCloseWindow)
            self.Bind(wx.EVT_END_SESSION, self.frame.OnCloseWindow)
            
            
            #asked = self.utility.config.Read('askeduploadbw', 'boolean')
            asked = True
            if not asked:
                dlg = BandwidthSelector(self.frame,self.utility)
                result = dlg.ShowModal()
                if result == wx.ID_OK:
                    ulbw = dlg.getUploadBandwidth()
                    self.utility.config.Write('maxuploadrate',ulbw)
                    self.utility.config.Write('maxseeduploadrate',ulbw)
                    self.utility.config.Write('askeduploadbw','1')
                dlg.Destroy()

            # Arno, 2007-05-03: wxWidgets 2.8.3.0 and earlier have the MIME-type for .bmp 
            # files set to 'image/x-bmp' whereas 'image/bmp' is the official one.
            try:
                bmphand = None
                hands = wx.Image.GetHandlers()
                for hand in hands:
                    #print "Handler",hand.GetExtension(),hand.GetType(),hand.GetMimeType()
                    if hand.GetMimeType() == 'image/x-bmp':
                        bmphand = hand
                        break
                #wx.Image.AddHandler()
                if bmphand is not None:
                    bmphand.SetMimeType('image/bmp')
            except:
                # wx < 2.7 don't like wx.Image.GetHandlers()
                print_exc()
            
            # Must be after ABCLaunchMany is created
            self.torrentfeed = TorrentFeedThread.getInstance()
            self.torrentfeed.register(self.utility)
            self.torrentfeed.start()
            
            #print "DIM",wx.GetDisplaySize()
            #print "MM",wx.GetDisplaySizeMM()

            wx.CallAfter(self.startWithRightView)            
            
        except Exception,e:
            print_exc()
            self.error = e
            self.onError()
            return False

        return True

    def onError(self,source=None):
        # Don't use language independence stuff, self.utility may not be
        # valid.
        msg = "Unfortunately, Tribler ran into an internal error:\n\n"
        if source is not None:
            msg += source
        msg += str(self.error.__class__)+':'+str(self.error)
        msg += '\n'
        msg += 'Please see the FAQ on www.tribler.org on how to act.'
        dlg = wx.MessageDialog(None, msg, "Tribler Fatal Error", wx.OK|wx.ICON_ERROR)
        result = dlg.ShowModal()
        print_exc()
        dlg.Destroy()

    def MacOpenFile(self,filename):
        self.utility.queue.addtorrents.AddTorrentFromFile(filename)

    def OnExit(self):
        
        self.torrentfeed.shutdown()
        mainlineDHT.deinit()
        
        if not ALLOW_MULTIPLE:
            del self.single_instance_checker
        ClientPassParam("Close Connection")
        return 0
    
    def db_exception_handler(self,e):
        if DEBUG:
            print >> sys.stderr,"abc: Database Exception handler called",e,"value",e.args,"#"
        try:
            if e.args[1] == "DB object has been closed":
                return # We caused this non-fatal error, don't show.
            if self.error is not None and self.error.args[1] == e.args[1]:
                return # don't repeat same error
        except:
            print >> sys.stderr, "abc: db_exception_handler error", e, type(e)
            print_exc()
            #print_stack()
        self.error = e
        self.invokeLater(self.onError,[],{'source':"The database layer reported: "})
    
    def getConfigPath(self):
        return self.utility.getConfigPath()

    def startWithRightView(self):
        if self.params[0] != "":
            self.guiUtility.standardLibraryOverview()
    
    
        
class DummySingleInstanceChecker:
    
    def __init__(self,basename):
        pass

    def IsAnotherRunning(self):
        "Uses pgrep to find other tribler.py processes"
        # If no pgrep available, it will always start tribler
        progressInfo = commands.getoutput('pgrep -fl "tribler\.py" | grep -v pgrep')
        numProcesses = len(progressInfo.split('\n'))
        if DEBUG:
            print 'ProgressInfo: %s, num: %d' % (progressInfo, numProcesses)
        return numProcesses > 1
                
        
##############################################################
#
# Main Program Start Here
#
##############################################################
def run(params = None):
    global start_time
    start_time = time()
    if params is None:
        params = [""]
    
    if len(sys.argv) > 1:
        params = sys.argv[1:]
    
    # Create single instance semaphore
    # Arno: On Linux and wxPython-2.8.1.1 the SingleInstanceChecker appears
    # to mess up stderr, i.e., I get IOErrors when writing to it via print_exc()
    #
    # TEMPORARILY DISABLED on Linux
    if sys.platform != 'linux2':
        single_instance_checker = wx.SingleInstanceChecker("tribler-" + wx.GetUserId())
    else:
        single_instance_checker = DummySingleInstanceChecker("tribler-")

    #print "[StartUpDebug]---------------- 1", time()-start_time
    if not ALLOW_MULTIPLE and single_instance_checker.IsAnotherRunning():
        #Send  torrent info to abc single instance
        ClientPassParam(params[0])
        #print "[StartUpDebug]---------------- 2", time()-start_time
    else:
        arg0 = sys.argv[0].lower()
        if arg0.endswith('.exe'):
            abcpath = os.path.abspath(os.path.dirname(sys.argv[0]))
        else:
            abcpath = os.getcwd()  
        # Arno: don't chdir to allow testing as other user from other dir.
        #os.chdir(abcpath)

        # Launch first abc single instance
        app = ABCApp(0, params, single_instance_checker, abcpath)
        configpath = app.getConfigPath()
#        print "[StartUpDebug]---------------- 3", time()-start_time
        app.MainLoop()

        print "Client shutting down. Sleeping for a few seconds to allow other threads to finish"
        sleep(4)

        # This is the right place to close the database, unfortunately Linux has
        # a problem, see ABCFrame.OnCloseWindow
        #
        #if sys.platform != 'linux2':
        #    tribler_done(configpath)
        os._exit(0)

if __name__ == '__main__':
    run()

