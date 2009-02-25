# Written by Arno Bakker, Choopan RATTANAPOKA, Jie Yang
# see LICENSE.txt for license information
""" Base class for Player and Plugin Background process. See swarmplayer.py """

#
# TODO: set 'download_slice_size' to 32K, such that pieces are no longer
# downloaded in 2 chunks. This particularly avoids a bad case where you
# kick the source: you download chunk 1 of piece X
# from lagging peer and download chunk 2 of piece X from source. With the piece
# now complete you check the sig. As the first part of the piece is old, this
# fails and we kick the peer that gave us the completing chunk, which is the 
# source.
#
# Note that the BT spec says: 
# "All current implementations use 2 15 , and close connections which request 
# an amount greater than 2 17." http://www.bittorrent.org/beps/bep_0003.html
#
# So it should be 32KB already. However, the BitTorrent (3.4.1, 5.0.9), 
# BitTornado and Azureus all use 2 ** 14 = 16KB chunks.

import os
import sys
import time
from sets import Set

from threading import enumerate,currentThread,RLock
from traceback import print_exc

if sys.platform == "darwin":
    # on Mac, we can only load VLC/OpenSSL libraries
    # relative to the location of tribler.py
    os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))
try:
    import wxversion
    wxversion.select('2.8')
except:
    pass
import wx

from Tribler.__init__ import LIBRARYNAME
from Tribler.Core.API import *
from Tribler.Policies.RateManager import UserDefinedMaxAlwaysOtherwiseEquallyDividedRateManager
from Tribler.Utilities.Instance2Instance import *

from Tribler.Player.systray import PlayerTaskBarIcon
from Tribler.Player.Reporter import Reporter
from Tribler.Player.UtilityStub import UtilityStub

DEBUG = False
RATELIMITADSL = False

DISKSPACE_LIMIT = 5L * 1024L * 1024L * 1024L  # 5 GB
DEFAULT_MAX_UPLOAD_SEED_WHEN_SEEDING = 75 # KB/s

class BaseApp(wx.App,InstanceConnectionHandler):
    def __init__(self, redirectstderrout, appname, params, single_instance_checker, installdir, i2iport, sport):
        self.appname = appname
        self.params = params
        self.single_instance_checker = single_instance_checker
        self.installdir = installdir
        self.i2iport = i2iport
        self.sport = sport
        self.error = None
        self.s = None
        self.tbicon = None
        
        self.downloads_in_vodmode = Set() # Set of playing Downloads, one for SP, many for Plugin
        self.ratelimiter = None
        self.ratelimit_update_count = 0
        self.playermode = DLSTATUS_DOWNLOADING
        self.getpeerlistcount = 2 # for research Reporter
        self.shuttingdown = False
        
        InstanceConnectionHandler.__init__(self,self.i2ithread_readlinecallback)
        wx.App.__init__(self, redirectstderrout)

        
    def OnInitBase(self):
        """ To be wrapped in a OnInit() method that returns True/False """
        
        # Normal startup
        # Read config
        state_dir = Session.get_default_state_dir('.'+self.appname)
        
        self.utility = UtilityStub(self.installdir,state_dir)
        self.utility.app = self
        print >>sys.stderr,self.utility.lang.get('build')
        self.iconpath = os.path.join(self.installdir,LIBRARYNAME,'Images',self.appname+'Icon.ico')
        self.logopath = os.path.join(self.installdir,LIBRARYNAME,'Images',self.appname+'Logo.png')

        
        # Start server for instance2instance communication
        self.i2is = Instance2InstanceServer(self.i2iport,self) 


        # The playerconfig contains all config parameters that are not
        # saved by checkpointing the Session or its Downloads.
        self.load_playerconfig(state_dir)

        # Install systray icon
        # Note: setting this makes the program not exit when the videoFrame
        # is being closed.
        
        self.tbicon = PlayerTaskBarIcon(self,self.iconpath)

        
        # Start Tribler Session
        cfgfilename = Session.get_default_config_filename(state_dir)
        
        if DEBUG:
            print >>sys.stderr,"main: Session config",cfgfilename
        try:
            self.sconfig = SessionStartupConfig.load(cfgfilename)
        except:
            print_exc()
            self.sconfig = SessionStartupConfig()
            self.sconfig.set_state_dir(state_dir)
            
            self.sconfig.set_listen_port(self.sport)    
            self.sconfig.set_overlay(False)
            self.sconfig.set_megacache(False)

        self.s = Session(self.sconfig)
        self.s.set_download_states_callback(self.sesscb_states_callback)

        self.reporter = Reporter( self.sconfig )

        if RATELIMITADSL:
            self.ratelimiter = UserDefinedMaxAlwaysOtherwiseEquallyDividedRateManager()
            self.ratelimiter.set_global_max_speed(DOWNLOAD,400)
            self.ratelimiter.set_global_max_speed(UPLOAD,90)


        # Arno: For extra robustness, ignore any errors related to restarting
        try:
            # Load all other downloads in cache, but in STOPPED state
            self.s.load_checkpoint(initialdlstatus=DLSTATUS_STOPPED)
        except:
            print_exc()

        # Start remote control
        self.i2is.start()


    def start_download(self,tdef,dlfile):
        """ Start download of torrent tdef and play video file dlfile from it """
        
        # Free diskspace, if needed
        destdir = self.get_default_destdir()
        if not os.access(destdir,os.F_OK):
            os.mkdir(destdir)

        # Arno: For extra robustness, ignore any errors related to restarting
        # TODO: Extend code such that we can also delete files from the 
        # disk cache, not just Downloads. This would allow us to keep the
        # parts of a Download that we already have, but that is being aborted
        # by the user by closing the video window. See remove_playing_*
        try:
            if not self.free_up_diskspace_by_downloads(tdef.get_infohash(),tdef.get_length([dlfile])):
                print >>sys.stderr,"main: Not enough free diskspace, ignoring"
        except:
            print_exc()
        
        # Setup how to download
        dcfg = DownloadStartupConfig()
        
        # Delegate processing to VideoPlayer
        dcfg.set_video_event_callback(self.sesscb_vod_event_callback)
        dcfg.set_video_events(self.get_supported_vod_events())

        dcfg.set_dest_dir(destdir)
        
        if tdef.is_multifile_torrent():
            dcfg.set_selected_files([dlfile])
        
        # Arno: 2008-7-15: commented out, just stick with old ABC-tuned 
        # settings for now
        #dcfg.set_max_conns_to_initiate(300)
        #dcfg.set_max_conns(300)
        
        
        # Stop all non-playing, see if we're restarting one
        infohash = tdef.get_infohash()
        newd = None
        for d in self.s.get_downloads():
            if d.get_def().get_infohash() == infohash:
                # Download already exists.
                # One safe option is to remove it (but not its downloaded content)
                # so we can start with a fresh DownloadStartupConfig. However,
                # this gives funky concurrency errors and could prevent a
                # Download from starting without hashchecking (as its checkpoint
                # was removed) 
                # Alternative is to set VOD callback, etc. at Runtime:
                print >>sys.stderr,"main: Reusing old duplicate Download",`infohash`
                newd = d
            if d not in self.downloads_in_vodmode:
                d.stop()

        self.s.lm.h4xor_reset_init_conn_counter()

        # ARNOTODO: does this work with Plugin's duplicate download facility?

        self.playermode = DLSTATUS_DOWNLOADING
        if newd is None:
            print >>sys.stderr,"main: Starting new Download",`infohash`
            newd = self.s.start_download(tdef,dcfg)
        else:
            newd.set_video_event_callback(self.sesscb_vod_event_callback)
            newd.set_video_events(self.get_supported_vod_events())

            if tdef.is_multifile_torrent():
                newd.set_selected_files([dlfile])
            print >>sys.stderr,"main: Restarting existing Download",`infohash`
            newd.restart()

        self.downloads_in_vodmode.add(newd)

        print >>sys.stderr,"main: Saving content to",newd.get_dest_files()
        return newd


    def sesscb_vod_event_callback(self):
        pass
        
    def get_supported_vod_events(self):
        pass


    #
    # DownloadCache
    #
    def free_up_diskspace_by_downloads(self,infohash,needed):
        
        if DEBUG:
            print >> sys.stderr,"main: free_up: needed",needed,DISKSPACE_LIMIT
        if needed > DISKSPACE_LIMIT:
            # Not cleaning out whole cache for bigguns
            if DEBUG:
                print >> sys.stderr,"main: free_up: No cleanup for bigguns"
            return True 
        
        inuse = 0L
        timelist = []
        dlist = self.s.get_downloads()
        for d in dlist:
            hisinfohash = d.get_def().get_infohash()
            if infohash == hisinfohash:
                # Don't delete the torrent we want to play
                continue
            destfiles = d.get_dest_files()
            if DEBUG:
                print >> sys.stderr,"main: free_up: Downloaded content",`destfiles`
            
            dinuse = 0L
            for (filename,savepath) in destfiles:
                stat = os.stat(savepath)
                dinuse += stat.st_size
            inuse += dinuse
            timerec = (stat.st_ctime,dinuse,d)
            timelist.append(timerec)
            
        if inuse+needed < DISKSPACE_LIMIT:
            # Enough available, done.
            if DEBUG:
                print >> sys.stderr,"main: free_up: Enough avail",inuse
            return True
        
        # Policy: remove oldest till sufficient
        timelist.sort()
        if DEBUG:
            print >> sys.stderr,"main: free_up: Found",timelist,"in dest dir"
        
        got = 0L
        for ctime,dinuse,d in timelist:
            print >> sys.stderr,"main: free_up: Removing",`d.get_def().get_name_as_unicode()`,"to free up diskspace, t",ctime
            self.s.remove_download(d,removecontent=True)
            got += dinuse
            if got > needed:
                return True
        # Deleted all, still no space:
        return False
        
        
    #
    # Process periodically reported DownloadStates
    #
    def sesscb_states_callback(self,dslist):
        """ Called by Session thread """
        # Arno: delegate to GUI thread. This makes some things (especially
        #access control to self.videoFrame easier
        #self.gui_states_callback(dslist)
        
        # Arno: we want the prebuf stats every second, and we want the
        # detailed peerlist, needed for research stats. Getting them every
        # second may be too expensive, so get them every 10.
        #
        self.getpeerlistcount += 1
        getpeerlist = (self.getpeerlistcount % 10) == 0
        haspeerlist =  (self.getpeerlistcount % 10) == 1
        
        wx.CallAfter(self.gui_states_callback,dslist,haspeerlist)
        
        #print >>sys.stderr,"main: SessStats:",self.getpeerlistcount,getpeerlist,haspeerlist
        return (1.0,getpeerlist) 

    def gui_states_callback(self,dslist,haspeerlist):
        """ Called by *GUI* thread.
        CAUTION: As this method is called by the GUI thread don't to any 
        time-consuming stuff here! """
        
        #print >>sys.stderr,"main: Stats:"
        if self.shuttingdown:
            return ([],0,0)
        
        # See which Download is currently playing
        playermode = self.playermode

        totalspeed = {}
        totalspeed[UPLOAD] = 0.0
        totalspeed[DOWNLOAD] = 0.0
        totalhelping = 0

        # When not playing, display stats for all Downloads and apply rate control.
        if playermode == DLSTATUS_SEEDING:
            for ds in dslist:
                print >>sys.stderr,"main: Stats: Seeding: %s %.1f%% %s" % (dlstatus_strings[ds.get_status()],100.0*ds.get_progress(),ds.get_error())
            self.ratelimit_callback(dslist)
            
        # Calc total dl/ul speed and find DownloadStates for playing Downloads
        playing_dslist = []
        for ds in dslist:
            if ds.get_download() in self.downloads_in_vodmode:
                playing_dslist.append(ds)
            elif playermode == DLSTATUS_DOWNLOADING:
                print >>sys.stderr,"main: Stats: Waiting: %s %.1f%% %s" % (dlstatus_strings[ds.get_status()],100.0*ds.get_progress(),ds.get_error())
            
            for dir in [UPLOAD,DOWNLOAD]:
                totalspeed[dir] += ds.get_current_speed(dir)
            totalhelping += ds.get_num_peers()

        # Report statistics on all downloads to research server, every 10 secs
        if haspeerlist:
            try:
                for ds in dslist:
                    self.reporter.report_stat(ds)
            except:
                print_exc()

        # Set systray icon tooltip. This has limited size on Win32!
        txt = self.appname+'\n\n'
        txt += 'DL: %.1f\n' % (totalspeed[DOWNLOAD])
        txt += 'UL:   %.1f\n' % (totalspeed[UPLOAD])
        txt += 'Helping: %d\n' % (totalhelping)
        #print >>sys.stderr,"main: ToolTip summary",txt
        self.OnSetSysTrayTooltip(txt)
        
        # No playing Downloads        
        if len(playing_dslist) == 0:
            return ([],0,0)
        elif DEBUG and playermode == DLSTATUS_DOWNLOADING:
            for ds in playing_dslist:
                print >>sys.stderr,"main: Stats: DL: %s %.1f%% %s dl %.1f ul %.1f n %d" % (dlstatus_strings[ds.get_status()],100.0*ds.get_progress(),ds.get_error(),ds.get_current_speed(DOWNLOAD),ds.get_current_speed(UPLOAD),ds.get_num_peers())

        # If we're done playing we can now restart any previous downloads to 
        # seed them.
        if playermode != DLSTATUS_SEEDING:
            playing_seeding_count = 0
            for ds in playing_dslist:
                 if ds.get_status() == DLSTATUS_SEEDING:
                    playing_seeding_count += 1
            if len(playing_dslist) == playing_seeding_count: 
                    self.restart_other_downloads()

        # cf. 25 Mbps cap to reduce CPU usage and improve playback on slow machines
        # Arno: on some torrents this causes VLC to fail to tune into the video
        # although it plays audio???
        #ds.get_download().set_max_speed(DOWNLOAD,1500)
        
        return (playing_dslist,totalhelping,totalspeed) 


    def OnSetSysTrayTooltip(self,txt):         
        if self.tbicon is not None:
            self.tbicon.set_icon_tooltip(txt)

    #
    # Download Management
    #
    def restart_other_downloads(self):
        """ Called by GUI thread """
        if self.shuttingdown:
            return
        print >>sys.stderr,"main: Restarting other downloads"
        self.playermode = DLSTATUS_SEEDING
        self.ratelimiter = UserDefinedMaxAlwaysOtherwiseEquallyDividedRateManager()
        self.set_ratelimits()

        dlist = self.s.get_downloads()
        for d in dlist:
            if d not in self.downloads_in_vodmode:
                d.set_mode(DLMODE_NORMAL) # checkpointed torrents always restarted in DLMODE_NORMAL, just make extra sure
                d.restart() 


    def remove_downloads_in_vodmode_if_not_complete(self):
        print >>sys.stderr,"main: Removing playing download if not complete"
        for d in self.downloads_in_vodmode:
            d.set_state_callback(self.sesscb_remove_playing_callback)
        
    def sesscb_remove_playing_callback(self,ds):
        """ Called by SessionThread """
        
        print >>sys.stderr,"main: sesscb_remove_playing_callback: status is",dlstatus_strings[ds.get_status()],"progress",ds.get_progress()
        
        d = ds.get_download()
        name = d.get_def().get_name()
        if (ds.get_status() == DLSTATUS_DOWNLOADING and ds.get_progress() >= 0.9) or ds.get_status() == DLSTATUS_SEEDING:
            pass
            print >>sys.stderr,"main: sesscb_remove_playing_callback: KEEPING",`name`            
        else:
            print >>sys.stderr,"main: sesscb_remove_playing_callback: REMOVING",`name`
            wx.CallAfter(self.remove_playing_download,d)
        
        return (-1.0,False)
        

    def remove_playing_download(self,d):
        """ Called by MainThread """
        if self.s is not None:
            print >>sys.stderr,"main: Removing incomplete download",`d.get_def().get_name_as_unicode()`
            try:
                self.s.remove_download(d,removecontent=True)
                self.downloads_in_vodmode.remove(d)
            except:
                print_exc()


    #
    # Rate limiter
    #
    def set_ratelimits(self):
        uploadrate = float(self.playerconfig['total_max_upload_rate'])
        print >>sys.stderr,"main: set_ratelimits: Setting max upload rate to",uploadrate
        self.ratelimiter.set_global_max_speed(UPLOAD,uploadrate)
        self.ratelimiter.set_global_max_seedupload_speed(uploadrate)

    def ratelimit_callback(self,dslist):
        """ When the player is in seeding mode, limit the used upload to
        the limit set by the user via the options menu. 
        Called by *GUI* thread """
        if self.ratelimiter is None:
            return

        # Adjust speeds once every 4 seconds
        adjustspeeds = False
        if self.ratelimit_update_count % 4 == 0:
            adjustspeeds = True
        self.ratelimit_update_count += 1
        
        if adjustspeeds:
            self.ratelimiter.add_downloadstatelist(dslist)
            self.ratelimiter.adjust_speeds()


    #
    # Player config file
    # 
    def load_playerconfig(self,state_dir):
        self.playercfgfilename = os.path.join(state_dir,'playerconf.pickle')
        self.playerconfig = None
        try:
            f = open(self.playercfgfilename,"rb")
            self.playerconfig = pickle.load(f)
            f.close()
        except:
            print_exc()
            self.playerconfig = {}
            self.playerconfig['total_max_upload_rate'] = DEFAULT_MAX_UPLOAD_SEED_WHEN_SEEDING # KB/s

    def save_playerconfig(self):
        try:
            f = open(self.playercfgfilename,"wb")
            pickle.dump(self.playerconfig,f)
            f.close()
        except:
            print_exc()
            
    def set_playerconfig(self,key,value):
        self.playerconfig[key] = value
        
        if key == 'total_max_upload_rate':
            try:
                self.set_ratelimits()
            except:
                print_exc()
    
    def get_playerconfig(self,key):
        return self.playerconfig[key]


    #
    # Shutdown
    #
    def OnExit(self):
        print >>sys.stderr,"main: ONEXIT"
        self.shuttingdown = True
        self.remove_downloads_in_vodmode_if_not_complete()

        # To let Threads in Session finish their business before we shut it down.
        time.sleep(2) 
        
        if self.s is not None:
            self.s.shutdown()
        
        if self.tbicon is not None:
            self.tbicon.RemoveIcon()
            self.tbicon.Destroy()

        ts = enumerate()
        for t in ts:
            print >>sys.stderr,"main: ONEXIT: Thread still running",t.getName(),"daemon",t.isDaemon()
        
        self.ExitMainLoop()

    
    def clear_session_state(self):
        """ Try to fix apps by doing hard reset. Called from systray menu """
        try:
            self.videoplayer.stop_playback()
        except:
            print_exc()
        try:
            if self.s is not None:
                dlist = self.s.get_downloads()
                for d in dlist:
                    self.s.remove_download(d,removecontent=True)
        except:
            print_exc()
        time.sleep(1) # give network thread time to do stuff
        try:
                dldestdir = self.get_default_destdir()
                shutil.rmtree(dldestdir,True) # ignore errors
        except:
            print_exc()
        try:
                dlcheckpointsdir = os.path.join(self.s.get_state_dir(),STATEDIR_DLPSTATE_DIR)
                shutil.rmtree(dlcheckpointsdir,True) # ignore errors
        except:
            print_exc()
        try:
                cfgfilename = os.path.join(self.s.get_state_dir(),STATEDIR_SESSCONFIG)
                os.remove(cfgfilename)
        except:
            print_exc()

        self.s = None # HARD EXIT
        #self.OnExit()
        sys.exit(0) # DIE HARD 4.0


    def show_error(self,msg):
        dlg = wx.MessageDialog(None, msg, self.appname+" Error", wx.OK|wx.ICON_ERROR)
        result = dlg.ShowModal()
        dlg.Destroy()
        
    
    def get_default_destdir(self):
        return os.path.join(self.s.get_state_dir(),'downloads')

    #
    # InstanceConnectionHandler
    #
    def i2ithread_readlinecallback(self,ic,cmd):    
        pass
    
