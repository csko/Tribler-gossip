#!/usr/bin/python

#########################################################################
#
# Author : Choopan RATTANAPOKA, Jie Yang, Arno Bakker
#
# Description : Main ABC [Yet Another Bittorrent Client] python script.
#               you can run from source code by using
#               >python abc.py
#               need Python, WxPython in order to run from source code.
#
# see LICENSE.txt for license information
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
import urllib
original_open_https = urllib.URLopener.open_https
import M2Crypto
urllib.URLopener.open_https = original_open_https

# Arno, 2008-03-21: see what happens when we disable this locale thing. Gives
# errors on Vista in "Regional and Language Settings Options" different from 
# "English[United Kingdom]" 
#import locale
import signal
import commands
import pickle

try:
    import wxversion
    wxversion.select('2.8')
except:
    pass
import wx
from wx import xrc
#import hotshot

from threading import Thread, Event,currentThread,enumerate
from time import time, ctime, sleep
from traceback import print_exc, print_stack
from cStringIO import StringIO
import urllib
import webbrowser

from Tribler.Main.vwxGUI.MainFrame import MainFrame
from Tribler.Main.Utility.utility import Utility
from Tribler.Main.Utility.constants import * #IGNORE:W0611
import Tribler.Main.vwxGUI.font as font
from Tribler.Main.vwxGUI.GuiUtility import GUIUtility
import Tribler.Main.vwxGUI.updateXRC as updateXRC
from Tribler.Main.vwxGUI.TasteHeart import set_tasteheart_bitmaps
from Tribler.Main.vwxGUI.perfBar import set_perfBar_bitmaps
from Tribler.Main.vwxGUI.MainMenuBar import MainMenuBar
from Tribler.Main.vwxGUI.font import *
from Tribler.Main.vwxGUI.FriendsItemPanel import fs2text 
from Tribler.Main.Dialogs.GUITaskQueue import GUITaskQueue
from Tribler.Main.notification import init as notification_init
from Tribler.Category.Category import Category
from Tribler.Subscriptions.rss_client import TorrentFeedThread
from Tribler.Video.VideoPlayer import VideoPlayer
from Tribler.Web2.util.update import Web2Updater
from Tribler.Policies.RateManager import UserDefinedMaxAlwaysOtherwiseEquallyDividedRateManager
from Tribler.Policies.SeedingManager import GlobalSeedingManager
from Tribler.Utilities.Instance2Instance import *
from Tribler.Main.globals import DefaultDownloadStartupConfig,get_default_dscfg_filename

from Tribler.Core.API import *
from Tribler.Core.Utilities.utilities import show_permid
import Tribler.Core.CacheDB.friends as friends 

I2I_LISTENPORT = 57891
VIDEOHTTP_LISTENPORT = 6878

DEBUG = False
ALLOW_MULTIPLE = False
        

##############################################################
#
# Class : ABCApp
#
# Main ABC application class that contains ABCFrame Object
#
##############################################################
class ABCApp(wx.App):
    def __init__(self, x, params, single_instance_checker, installdir):
        self.params = params
        self.single_instance_checker = single_instance_checker
        self.installdir = installdir
        self.error = None
        self.last_update = 0
        self.update_freq = 0    # how often to update #peers/#torrents
        wx.App.__init__(self, x)
        
        
    def OnInit(self):
        try:
            self.utility = Utility(self.installdir)
            self.utility.app = self

            self.postinitstarted = False
            """
            Hanging self.OnIdle to the onidle event doesnot work under linux (ubuntu). The images in xrc files
            will not load in any but the filespanel.
            """
            #self.Bind(wx.EVT_IDLE, self.OnIdle)
            
        
            # Set locale to determine localisation
            #locale.setlocale(locale.LC_ALL, '')

            sys.stdout.write('Client Starting Up.\n')
            sys.stdout.write('Build: ' + self.utility.lang.get('build') + '\n')

            bm = wx.Bitmap(os.path.join(self.utility.getPath(),'Tribler','Images','splash.jpg'),wx.BITMAP_TYPE_JPEG)
            #s = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN
            #s = wx.SIMPLE_BORDER|wx.FRAME_NO_TASKBAR|wx.FRAME_FLOAT_ON_PARENT
            self.splash = wx.SplashScreen(bm, wx.SPLASH_CENTRE_ON_SCREEN|wx.SPLASH_TIMEOUT, 1000, None, -1)
            
            # Arno: Do heavy startup on GUI thread after splash screen has been
            # painted.
            self.splash.Show()
            "Replacement for self.Bind(wx.EVT_IDLE, self.OnIdle)"
            wx.CallAfter(self.PostInit)    
            return True
            
        except Exception,e:
            print_exc()
            self.error = e
            self.onError()
            return False

    def OnIdle(self,event=None):
        if not self.postinitstarted:
            self.postinitstarted = True
            wx.CallAfter(self.PostInit)
            # Arno: On Linux I sometimes have to move the mouse into the splash
            # for the rest of Tribler to start. H4x0r
            if event is not None:
                event.RequestMore(True)
                event.Skip()


    def PostInit(self):
        try:
            # On Linux: allow painting of splash screen first.
            wx.Yield()
            
            # Initialise fonts
            font.init()

            #tribler_init(self.utility.getConfigPath(),self.utility.getPath(),self.db_exception_handler)
            
            self.utility.postAppInit(os.path.join(self.installdir,'Tribler','Images','tribler.ico'))
            
            # H4x0r a bit
            set_tasteheart_bitmaps(self.utility.getPath())
            set_perfBar_bitmaps(self.utility.getPath())

            cat = Category.getInstance(self.utility.getPath())
            cat.init_from_main(self.utility)
            
            # Put it here so an error is shown in the startup-error popup
            # Start server for instance2instance communication
            self.i2is = Instance2InstanceServer(I2I_LISTENPORT,self.i2icallback) 
            self.i2is.start()

            # Fire up the VideoPlayer, it abstracts away whether we're using
            # an internal or external video player.
            playbackmode = self.utility.config.Read('videoplaybackmode', "int")
            self.videoplayer = VideoPlayer.getInstance(httpport=VIDEOHTTP_LISTENPORT)
            self.videoplayer.register(self.utility,preferredplaybackmode=playbackmode,closeextplayercallback=self.OnClosingVideoFrameOrExtPlayer)

            notification_init( self.utility )

            #
            # Read and create GUI from .xrc files
            #
            #self.frame = ABCFrame(-1, self.params, self.utility)
            self.guiUtility = GUIUtility.getInstance(self.utility, self.params)
            updateXRC.main([os.path.join(self.utility.getPath(),'Tribler','Main','vwxGUI')])
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

            self.menubar = MainMenuBar(self.frame,self.utility)
            self.frame.set_wxapp(self)

            # Make sure self.utility.frame is set
            self.startAPI()
            
            #self.frame.Refresh()
            #self.frame.Layout()
            self.frame.Show(True)
            self.setDBStats()
            
            self.Bind(wx.EVT_QUERY_END_SESSION, self.frame.OnCloseWindow)
            self.Bind(wx.EVT_END_SESSION, self.frame.OnCloseWindow)
            
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
            # Delay this so GUI has time to paint
            wx.CallAfter(self.loadSessionCheckpoint)
                        
            
        except Exception,e:
            print_exc()
            self.error = e
            self.onError()
            return False

        return True

    def startAPI(self):
        
        # Start Tribler Session
        state_dir = Session.get_default_state_dir()
        
        cfgfilename = Session.get_default_config_filename(state_dir)
        if DEBUG:
            print >>sys.stderr,"main: Session config",cfgfilename
        try:
            self.sconfig = SessionStartupConfig.load(cfgfilename)
        except:
            print_exc()
            self.sconfig = SessionStartupConfig()
            self.sconfig.set_state_dir(state_dir)
            # Set default Session params here
            torrcolldir = os.path.join(get_default_dest_dir(),STATEDIR_TORRENTCOLL_DIR)
            self.sconfig.set_torrent_collecting_dir(torrcolldir)
            self.sconfig.set_nat_detect(True)
            
            # rename old collected torrent directory
            try:
                old_collected_torrent_dir = os.path.join(state_dir, 'torrent2')
                if not os.path.exists(torrcolldir) and os.path.isdir(old_collected_torrent_dir):
                    os.rename(old_collected_torrent_dir, torrcolldir)
                    print >>sys.stderr,"main: Moved dir with old collected torrents to", torrcolldir
            except:
                print_exc()

        # 22/08/08 boudewijn: convert abc.conf to SessionConfig
        self.utility.convert__presession_4_1__4_2(self.sconfig)
        
        s = Session(self.sconfig)
        self.utility.session = s
        
        s.add_observer(self.sesscb_ntfy_reachable,NTFY_REACHABLE,[NTFY_INSERT])
        s.add_observer(self.sesscb_ntfy_activities,NTFY_ACTIVITIES,[NTFY_INSERT])
        s.add_observer(self.sesscb_ntfy_dbstats,NTFY_TORRENTS,[NTFY_INSERT])
        s.add_observer(self.sesscb_ntfy_dbstats,NTFY_PEERS,[NTFY_INSERT])
        s.add_observer(self.sesscb_ntfy_friends,NTFY_PEERS,[NTFY_UPDATE])

        # Load the default DownloadStartupConfig
        dlcfgfilename = get_default_dscfg_filename(s)
        try:
            defaultDLConfig = DefaultDownloadStartupConfig.load(dlcfgfilename)
        except:
            defaultDLConfig = DefaultDownloadStartupConfig.getInstance()
            #print_exc()
            defaultdestdir = os.path.join(get_default_dest_dir())
            defaultDLConfig.set_dest_dir(defaultdestdir)

        # 29/08/08 boudewijn: convert abc.conf to DefaultDownloadStartupConfig
        self.utility.convert__postsession_4_1__4_2(s, defaultDLConfig)

        s.set_coopdlconfig(defaultDLConfig)

        # Loading of checkpointed Downloads delayed to allow GUI to paint,
        # see loadSessionCheckpoint

        # Create global rate limiter
        self.ratelimiter = UserDefinedMaxAlwaysOtherwiseEquallyDividedRateManager()
        self.rateadjustcount = 0 
        maxup = self.utility.config.Read('maxuploadrate', "int")
        maxdown = self.utility.config.Read('maxdownloadrate', "int")
        maxupseed = self.utility.config.Read('maxseeduploadrate', "int")
        self.ratelimiter.set_global_max_speed(UPLOAD,maxup)
        self.ratelimiter.set_global_max_speed(DOWNLOAD,maxdown)
        self.ratelimiter.set_global_max_seedupload_speed(maxupseed)
        self.utility.ratelimiter = self.ratelimiter
 
# SelectiveSeeding _       
        self.seedingmanager = GlobalSeedingManager(self.utility.config.Read, self.utility.session)
        
        self.seedingcount = 0 
# _SelectiveSeeding

        # seeding stats crawling
        self.seeding_snapshot_count = 0
        self.seedingstats_settings = s.open_dbhandler(NTFY_SEEDINGSTATSSETTINGS).loadCrawlingSettings()
        self.seedingstats_enabled = self.seedingstats_settings[0][2]
        self.seedingstats_interval = self.seedingstats_settings[0][1]
        
        # Only allow updates to come in after we defined ratelimiter
        s.set_download_states_callback(self.sesscb_states_callback)
        
        # Load friends from friends.txt
        friends.init(s)
        
    def sesscb_states_callback(self,dslist):
        """ Called by SessionThread """
        wx.CallAfter(self.gui_states_callback,dslist)
        return(1.0, True)
        
    def gui_states_callback(self,dslist):
        """ Called by MainThread  """
        if DEBUG: print >>sys.stderr,"main: Stats:"
        #print >>sys.stderr,"main: Stats: NAT",self.utility.session.get_nat_type()
        try:
            # Pass DownloadStates to libaryView
            try:
                # Jelle: libraryMode only exists after user clicked button
                if self.guiUtility.standardOverview is not None:
                    mode = self.guiUtility.standardOverview.mode 
                    if mode == 'libraryMode' or mode == 'friendsMode':
                        # Also pass dslist to friendsView, for coopdl boosting info
                        modedata = self.guiUtility.standardOverview.data[mode]
                        gm = modedata['grid'].gridManager
                        gm.download_state_gui_callback(dslist)
            except KeyError:
                # Apparently libraryMode only has has a 'grid' key when visible
                print_exc()
                pass
            except AttributeError:
                print_exc()
            except:
                print_exc()
            
            # Restart other torrents when the single torrent that was
            # running in VOD mode is done
            currdlist = []
            for ds in dslist:
                currdlist.append(ds.get_download())
            vodd = self.videoplayer.get_vod_download()
            for ds in dslist:
                d = ds.get_download()
                if d == vodd and ds.get_status() == DLSTATUS_SEEDING:
                    self.restart_other_downloads(currdlist)
                    break
                            
            # Adjust speeds once every 4 seconds
            adjustspeeds = False
            if self.rateadjustcount % 4 == 0:
                adjustspeeds = True
            self.rateadjustcount += 1
    
            if adjustspeeds:
                self.ratelimiter.add_downloadstatelist(dslist)
                self.ratelimiter.adjust_speeds()
                
            # Update stats in lower right overview box
            self.guiUtility.refreshTorrentStats(dslist)
            
            # Upload overall upload states
            self.guiUtility.refreshUploadStats(dslist)
            
# SelectiveSeeding_
            # Apply seeding policy every 60 seconds, for performance
            applyseedingpolicy = False
            if self.seedingcount % 60 == 0:
                applyseedingpolicy = True
            self.seedingcount += 1
    
            if applyseedingpolicy:
                self.seedingmanager.apply_seeding_policy(dslist)
# _SelectiveSeeding
            
# Crawling Seeding Stats_
            if self.seedingstats_enabled == 1:
                snapshot_seeding_stats = False
                if self.seeding_snapshot_count % self.seedingstats_interval == 0:
                    snapshot_seeding_stats = True
                self.seeding_snapshot_count += 1
                
                if snapshot_seeding_stats:
                    bc_db = self.utility.session.open_dbhandler(NTFY_BARTERCAST)
                    reputation = bc_db.getMyReputation()
                    self.utility.session.close_dbhandler(bc_db)
                    
                    seedingstats_db = self.utility.session.open_dbhandler(NTFY_SEEDINGSTATS)
                    seedingstats_db.updateSeedingStats(self.utility.session.get_permid(), reputation, dslist, self.seedingstats_interval) 
                    self.utility.session.close_dbhandler(seedingstats_db)
# _Crawling Seeding Stats

        except:
            print_exc()

    def restart_other_downloads(self,currdlist):
        restartdlist = self.videoplayer.get_vod_postponed_downloads()
        self.videoplayer.set_vod_postponed_downloads([]) # restart only once
        for d in restartdlist:
            if d in currdlist:
                d.restart()


    def OnClosingVideoFrameOrExtPlayer(self):
        vodd = self.videoplayer.get_vod_download()
        if vodd is not None:
            if vodd.get_def().get_live():
                print >>sys.stderr,"main: OnClosingVideoFrameOrExtPlayer: vodd is live, stopping",vodd.get_def().get_name_as_unicode()
                vodd.stop()
            self.restart_other_downloads(self.utility.session.get_downloads())
        #else: playing Web2 video

    def loadSessionCheckpoint(self):
        # Load all other downloads
        # TODO: reset all saved DownloadConfig to new default?
        if self.params[0] != "":
            # There is something on the cmdline, start all stopped
            self.utility.session.load_checkpoint(initialdlstatus=DLSTATUS_STOPPED)
        else:
            self.utility.session.load_checkpoint()


    def sesscb_ntfy_dbstats(self,subject,changeType,objectID,*args):
        """ Called by SessionCallback thread """
        wx.CallAfter(self.setDBStats)
        # Test
        #if subject == NTFY_PEERS:
        #    self.frame.friendsmgr.sesscb_friendship_callback(objectID,{})
        
    def setDBStats(self):
        """ Set total # peers and torrents discovered """
        
        # Arno: GUI thread accessing database
        now = time.time()
        if now - self.last_update < self.update_freq:
            return  
        self.last_update = now
        peer_db = self.utility.session.open_dbhandler(NTFY_PEERS)
        npeers = peer_db.getNumberPeers()
        torrent_db = self.utility.session.open_dbhandler(NTFY_TORRENTS)
        nfiles = torrent_db.getNumberTorrents()
        if nfiles > 30 and npeers > 30:
            self.update_freq = 2
        # Arno: not closing db connections, assuming main thread's will be 
        # closed at end.
                
        self.frame.numberPersons.SetLabel('%d' % npeers)
        self.frame.numberFiles.SetLabel('%d' % nfiles)
        #print >> sys.stderr, "************>>>>>>>> setDBStats", npeers, nfiles
        
    def sesscb_ntfy_activities(self,subject,changeType,objectID,*args):
        # Called by SessionCallback thread
        #print >>sys.stderr,"main: sesscb_ntfy_activities called:",subject,"ct",changeType,"oid",objectID,"a",args
        wx.CallAfter(self.frame.setActivity,objectID,*args)
    
    def sesscb_ntfy_reachable(self,subject,changeType,objectID,msg):
        wx.CallAfter(self.frame.onReachable)


    def sesscb_ntfy_friends(self,subject,changeType,objectID,*args):
        """ Called by SessionCallback thread """
        if subject == NTFY_PEERS:
            peerdb = self.utility.session.open_dbhandler(NTFY_PEERS)
            peer = peerdb.getPeer(objectID)
            self.utility.session.close_dbhandler(peerdb)
        else:
            peer = None
        wx.CallAfter(self.gui_ntfy_friends,subject,changeType,objectID,args,peer)

    def gui_ntfy_friends(self,subject,changeType,objectID,args,peer):
        """ A change in friendship status, report via message window """
        if len(args) == 2:
            if args[0] == 'friend':
                fs = args[1]
                if fs != FS_I_INVITED and fs != FS_I_DENIED and fs != FS_NOFRIEND:
                    fstext = fs2text(fs)
                    if peer['name'] is None or peer['name'] == '':
                        name = show_permid_short(objectID)
                    else:
                        name = peer['name']
                    msg = name + u" " + fstext
                    wx.CallAfter(self.frame.setActivity,NTFY_ACT_NONE,msg)

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
        print >>sys.stderr,"main: ONEXIT"
        
        friends.done(self.utility.session)
        
        self.torrentfeed.shutdown()

        # Don't checkpoint, interferes with current way of saving Preferences,
        # see Tribler/Main/Dialogs/abcoption.py
        self.utility.session.shutdown(hacksessconfcheckpoint=False) 
        
        if not ALLOW_MULTIPLE:
            del self.single_instance_checker
        return 0
    
    def db_exception_handler(self,e):
        if DEBUG:
            print >> sys.stderr,"main: Database Exception handler called",e,"value",e.args,"#"
        try:
            if e.args[1] == "DB object has been closed":
                return # We caused this non-fatal error, don't show.
            if self.error is not None and self.error.args[1] == e.args[1]:
                return # don't repeat same error
        except:
            print >> sys.stderr, "main: db_exception_handler error", e, type(e)
            print_exc()
            #print_stack()
        self.error = e
        onerror_lambda = lambda:self.onError(source="The database layer reported:  ") 
        wx.CallAfter(onerror_lambda)
    
    def getConfigPath(self):
        return self.utility.getConfigPath()

    def startWithRightView(self):
        if self.params[0] != "":
            self.guiUtility.standardLibraryOverview()
 
 
    def i2icallback(self,cmd,param):
        """ Called by Instance2Instance thread """
        
        print >>sys.stderr,"main: Another instance called us with cmd",cmd,"param",param
        
        if cmd == 'START':
            torrentfilename = None
            if param.startswith('http:'):
                # Retrieve from web 
                f = tempfile.NamedTemporaryFile()
                n = urllib2.urlopen(url)
                data = n.read()
                f.write(data)
                f.close()
                n.close()
                torrentfilename = f.name
            else:
                torrentfilename = param
                
            # Switch to GUI thread
            start_download_lambda = lambda:self.frame.startDownload(torrentfilename)
            wx.CallAfter(start_download_lambda)
    
        
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
    if params is None:
        params = [""]
    
    if len(sys.argv) > 1:
        params = sys.argv[1:]
    
    # Create single instance semaphore
    # Arno: On Linux and wxPython-2.8.1.1 the SingleInstanceChecker appears
    # to mess up stderr, i.e., I get IOErrors when writing to it via print_exc()
    #
    if sys.platform != 'linux2':
        single_instance_checker = wx.SingleInstanceChecker("tribler-" + wx.GetUserId())
    else:
        single_instance_checker = DummySingleInstanceChecker("tribler-")

    if not ALLOW_MULTIPLE and single_instance_checker.IsAnotherRunning():
        #Send  torrent info to abc single instance
        if params[0] != "":
            torrentfilename = params[0]
            i2ic = Instance2InstanceClient(I2I_LISTENPORT,'START',torrentfilename)
    else:
        arg0 = sys.argv[0].lower()
        if arg0.endswith('.exe'):
            installdir = os.path.abspath(os.path.dirname(sys.argv[0]))
        else:
            installdir = os.getcwd()  
        # Arno: don't chdir to allow testing as other user from other dir.
        #os.chdir(installdir)

        # Launch first abc single instance
        app = ABCApp(0, params, single_instance_checker, installdir)
        configpath = app.getConfigPath()
        app.MainLoop()

    print "Client shutting down. Sleeping for a few seconds to allow other threads to finish"
    sleep(1)

    # This is the right place to close the database, unfortunately Linux has
    # a problem, see ABCFrame.OnCloseWindow
    #
    #if sys.platform != 'linux2':
    #    tribler_done(configpath)
    #os._exit(0)

if __name__ == '__main__':
    run()

