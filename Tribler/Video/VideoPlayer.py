# Written by Arnfo Bakker
# see LICENSE.txt for license information
import sys
import os
import wx
import re
import urllib
from threading import currentThread,Event
from traceback import print_exc,print_stack
import urlparse

from Tribler.Video.VideoServer import VideoHTTPServer,VideoRawVLCServer
from Tribler.Video.Progress import ProgressBar,BufferInfo, ProgressInf
from Tribler.Core.Utilities.unicode import unicode2str,bin2unicode
from utils import win32_retrieve_video_play_command,win32_retrieve_playcmd_from_mimetype,quote_program_path,videoextdefaults
from Tribler.Core.simpledefs import *

DEBUG = True

PLAYBACKMODE_INTERNAL = 0
PLAYBACKMODE_EXTERNAL_DEFAULT = 1
PLAYBACKMODE_EXTERNAL_MIME = 2

OTHERTORRENTS_STOP_RESTART = 0
OTHERTORRENTS_STOP = 1
OTHERTORRENTS_CONTINUE = 2

USE_VLC_RAW_INTERFACE = False


class VideoPlayer:
    
    __single = None
    
    def __init__(self,httpport=6880):
        if VideoPlayer.__single:
            raise RuntimeError, "VideoPlayer is singleton"
        VideoPlayer.__single = self
        self.videoframe = None
        self.extprogress = None
        self.vod_download = None
        self.playbackmode = None
        self.alwaysinternalplayback = False
        self.vod_postponed_downloads = []

        if not USE_VLC_RAW_INTERFACE:
            # Start HTTP server for serving video to player widget
            self.videohttpserv = VideoHTTPServer.getInstance(httpport) # create
            self.videohttpserv.background_serve()
            self.videohttpserv.register(self.videohttpserver_error_callback,self.videohttpserver_set_status_callback)

        # Must create the instance here, such that it won't get garbage collected
        self.videoserv = VideoRawVLCServer.getInstance()

        
    def getInstance(*args, **kw):
        if VideoPlayer.__single is None:
            VideoPlayer(*args, **kw)
        return VideoPlayer.__single
    getInstance = staticmethod(getInstance)
        
    def register(self,utility,alwaysinternalplayback=False):
        
        self.utility = utility # TEMPARNO: make sure only used for language strings

        self.alwaysinternalplayback = alwaysinternalplayback
        self.determine_playbackmode()

    def set_videoframe(self,videoframe):
        self.videoframe = videoframe


    def play_file(self,dest):
        """ Play video file from disk """
        if DEBUG:
            print >>sys.stderr,"videoplay: Playing file from disk",dest

        (prefix,ext) = os.path.splitext(dest)
        [mimetype,cmd] = self.get_video_player(ext,dest)
        
        if DEBUG:
            print >>sys.stderr,"videoplay: play_file: cmd is",cmd
        
        self.launch_video_player(cmd)

    def play_file_via_httpserv(self,dest):
        """ Play a file via our internal HTTP server. Needed when the user
        selected embedded VLC as player and the filename contains Unicode
        characters.
        """ 
        if DEBUG:
            print >>sys.stderr,"videoplay: Playing file with Unicode filename via HTTP"

        videoserver = VideoHTTPServer.getInstance()
        
        (prefix,ext) = os.path.splitext(dest)
        videourl = self.create_url(videoserver,'/'+os.path.basename(prefix+ext))
        [mimetype,cmd] = self.get_video_player(ext,videourl)

        stream = open(dest,"rb")
        stats = os.stat(dest)
        length = stats.st_size
        streaminfo = {'mimetype':mimetype,'stream':stream,'length':length}
        videoserv.set_inputstream(streaminfo)
        
        self.launch_video_player(cmd)


 
    def play_url(self,url):
        """ Play video file from network or disk """
        if DEBUG:
            print >>sys.stderr,"videoplay: Playing file from url",url
        
        self.determine_playbackmode()
        
        t = urlparse.urlsplit(url)
        dest = t[2]
        
        # VLC will play .flv files, but doesn't like the URLs that YouTube uses,
        # so quote them
        if self.playbackmode != PLAYBACKMODE_INTERNAL:
            if sys.platform == 'win32':
                x = [t[0],t[1],t[2],t[3],t[4]]
                n = urllib.quote(x[2])
                if DEBUG:
                    print >>sys.stderr,"videoplay: play_url: OLD PATH WAS",x[2],"NEW PATH",n
                x[2] = n
                n = urllib.quote(x[3])
                if DEBUG:
                    print >>sys.stderr,"videoplay: play_url: OLD QUERY WAS",x[3],"NEW PATH",n
                x[3] = n
                url = urlparse.urlunsplit(x)
            elif url[0] != '"' and url[0] != "'":
                # to prevent shell escape problems
                # TODO: handle this case in escape_path() that now just covers spaces
                url = "'"+url+"'" 

        (prefix,ext) = os.path.splitext(dest)
        [mimetype,cmd] = self.get_video_player(ext,url)
        
        if DEBUG:
            print >>sys.stderr,"videoplay: play_url: cmd is",cmd
        
        self.launch_video_player(cmd)


    def play_stream(self,streaminfo):
        if DEBUG:
            print >>sys.stderr,"videoplay: play_stream"

        self.determine_playbackmode()

        if self.playbackmode == PLAYBACKMODE_INTERNAL:
            if USE_VLC_RAW_INTERFACE:
                # Play using direct callbacks from the VLC C-code
                self.launch_video_player(None,streaminfo=streaminfo)
            else:
                # Play via internal HTTP server
                self.videohttpserv.set_inputstream(streaminfo)
                url = self.create_url(self.videohttpserv,'/')

                self.launch_video_player(url)
        else:
            # External player, play stream via internal HTTP server
            self.videohttpserv.set_inputstream(streaminfo)
            url = self.create_url(self.videohttpserv,'/')

            [mimetype,cmd] = self.get_video_player(None,url,mimetype=streaminfo['mimetype'])
            self.launch_video_player(cmd)


    def launch_video_player(self,cmd,streaminfo=None):
        if self.playbackmode == PLAYBACKMODE_INTERNAL:

            if streaminfo is None:
                # Play URL from network or disk
                self.videoframe.get_videopanel().Load(cmd)
            else:
                # Play using direct callbacks from the VLC C-code
                self.videoframe.get_videopanel().Load('raw:',streaminfo=streaminfo)

            self.videoframe.show_videoframe()
            self.videoframe.get_videopanel().StartPlay()
        else:
            # Launch an external player
            # Play URL from network or disk
            self.exec_video_player(cmd)


    def stop_playback(self,reset=False):
        if self.playbackmode == PLAYBACKMODE_INTERNAL:
            self.videoframe.get_videopanel().Stop()
            if reset:
                self.videoframe.get_videopanel().Reset()



    def play(self,ds):
        """ Used by Tribler Main """
        self.determine_playbackmode()
        
        d = ds.get_download()
        tdef = d.get_def()
        videofiles = d.get_dest_files(exts=videoextdefaults)
        
        if len(videofiles) == 0:
            print >>sys.stderr,"main: No video files found! Let user select"
            # Let user choose any file
            videofiles = d.get_dest_files(exts=None)
            
        selectedinfilename = None
        selectedoutfilename= None
        if len(videofiles) > 1:
            infilenames = []
            for infilename,diskfilename in videofiles:
                infilenames.append(infilename)
            selectedinfilename = self.ask_user_to_select_video(infilenames)
            if selectedinfilename is None:
                print >>sys.stderr,"main: User selected no video"
                return
            for infilename,diskfilename in videofiles:
                if infilename == selectedinfilename:
                    selectedoutfilename = diskfilename
        else:
            selectedinfilename = videofiles[0][0]
            selectedoutfilename = videofiles[0][1]

        complete = ds.get_status() == DLSTATUS_SEEDING

        bitrate = tdef.get_bitrate(selectedinfilename)
        if bitrate is None and not complete:
            video_analyser_path = self.utility.config.Read('videoanalyserpath')
            if not os.access(video_analyser_path,os.F_OK):
                self.onError(self.utility.lang.get('videoanalysernotfound'),video_analyser_path,self.utility.lang.get('videoanalyserwhereset'))
                return

        # The VLC MediaControl API's playlist_add_item() doesn't accept unicode filenames.
        # So if the file to play is unicode we play it via HTTP. The alternative is to make
        # Tribler save the data in non-unicode filenames.
        #
        flag = self.playbackmode == PLAYBACKMODE_INTERNAL and not self.is_ascii_filename(selectedoutfilename)
        
        if complete:
            if flag:
                self.play_file_via_httpserv(selectedoutfilename)
            else:
                self.play_file(selectedoutfilename)
        else:
            self.play_vod(ds,selectedinfilename)


    def play_vod(self,ds,infilename):
        """ Called by GUI thread when clicking "Play ASAP" button """

        d = ds.get_download()
        tdef = d.get_def()
        # For multi-file torrent: when the user selects a different file, play that
        oldselectedfile = None
        if not tdef.get_live() and ds.is_vod():
            oldselectedfiles = d.get_selected_files()
            oldselectedfile = oldselectedfiles[0] # Should be just one
        
        # 1. (Re)Start torrent in VOD mode
        switchfile = (oldselectedfile is not None and oldselectedfile != infilename) 
        if not ds.is_vod() or switchfile or tdef.get_live():
            
            if switchfile:
                if self.playbackmode == PLAYBACKMODE_INTERNAL:
                    self.videoframe.get_videopanel().Reset()
            
            [proceed,othertorrents] = self.warn_user(ds,infilename)
            if not proceed:
                # User bailing out
                return

            if DEBUG:
                print >>sys.stderr,"videoplay: Enabling VOD on torrent",`d.get_def().get_name()`

            activetorrents = self.utility.session.get_downloads()
            
            if DEBUG:
                for d2 in activetorrents:
                    print >>sys.stderr,"videoplay: other torrents: Currently active is",`d2.get_def().get_name()`
            
            if othertorrents == OTHERTORRENTS_STOP or othertorrents == OTHERTORRENTS_STOP_RESTART:
                for d2 in activetorrents:
                    d2.stop()
            else:
                d.stop()
                
            if othertorrents == OTHERTORRENTS_STOP_RESTART:
                if d in activetorrents:
                    activetorrents.remove(d)
                # TODO: REACTIVATE TORRENTS WHEN DONE. 
                # ABCTorrentTemp.set_previously_active_torrents(activetorrents)
                self.set_vod_postponed_downloads(activetorrents)

            # Restart download
            d.set_video_start_callback(self.sesscb_vod_event_callback)
            if d.get_def().is_multifile_torrent():
                d.set_selected_files([infilename])
            print >>sys.stderr,"main: Restarting existing Download",`ds.get_download().get_def().get_infohash()`
            self.set_vod_download(d)
            d.restart()


    def start_and_play(self,tdef,dscfg):
        """ Called by GUI thread when Tribler started with live or video torrent on cmdline """

        if not tdef.get_live():
            videofiles = tdef.get_files(exts=videoextdefaults)
            if len(videofiles) > 1:
                selectedinfilename = self.ask_user_to_select_video(videofiles)
                if selectedinfilename is None:
                    print >>sys.stderr,"main: User selected no video"
                    return None
            else:
                selectedinfilename = videofiles[0]
    
            dscfg.set_selected_files([selectedinfilename])
        else:
            selectedinfilename = tdef.get_name()
            
        othertorrents = OTHERTORRENTS_STOP_RESTART
        activetorrents = self.utility.session.get_downloads()
        
        if DEBUG:
            for d2 in activetorrents:
                print >>sys.stderr,"videoplay: other torrents: Currently active is",`d2.get_def().get_name()`
        
        if othertorrents == OTHERTORRENTS_STOP or othertorrents == OTHERTORRENTS_STOP_RESTART:
            for d2 in activetorrents:
                d2.stop()
            
        if othertorrents == OTHERTORRENTS_STOP_RESTART:
            self.set_vod_postponed_downloads(activetorrents)

        # Restart download
        dscfg.set_video_start_callback(self.sesscb_vod_event_callback)
        print >>sys.stderr,"videoplay: Starting new VOD/live Download",`tdef.get_name()`
        
        d = self.utility.session.start_download(tdef,dscfg)
        self.set_vod_download(d)
        return d
        
    
    def sesscb_vod_event_callback(self,d,event,params):
        """ Called by the Session when the content of the Download is ready
         
        Called by Session thread """
        print >>sys.stderr,"VideoPlayer: sesscb_vod_event_callback called",currentThread().getName(),"###########################################################",params["mimetype"]
        wx.CallAfter(self.gui_vod_event_callback,d,event,params)

    def gui_vod_event_callback(self,d,event,params):
        """ Also called by SwarmPlayer """

        print >>sys.stderr,"VideoPlayer: gui_vod_event:",event
        if event == "start":
            filename = params["filename"]
            mimetype = params["mimetype"]
            stream   = params["stream"]
            length   = params["size"]

            if filename:
                self.play_file(filename)
            else:
                blocksize = d.get_def().get_piece_length()
                streaminfo = {'mimetype':mimetype,'stream':stream,'length':length,'blocksize':blocksize}
                self.play_stream(streaminfo)
        elif event == "pause":
            if self.playbackmode == PLAYBACKMODE_INTERNAL:
                self.videoframe.videopanel.Pause()
        elif event == "resume":
            if self.playbackmode == PLAYBACKMODE_INTERNAL:
                self.videoframe.videopanel.Play()


    def ask_user_to_select_video(self,videofiles):
        dlg = VideoChooser(self.videoframe,self.utility,videofiles,title='Tribler',expl='Select which file to play')
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            index = dlg.getChosenIndex()
            filename = videofiles[index]
        else:
            filename = None
        dlg.Destroy()
        return filename

    def is_ascii_filename(self,filename):
        if isinstance(filename,str):
            return True
        try:
            filename.encode('ascii','strict')
            return True
        except:
            print_exc()
            return False

    def warn_user(self,ds,infilename):
        dlg = VODWarningDialog(self.videoframe,self.utility,ds,infilename)
        result = dlg.ShowModal()
        othertorrents = dlg.get_othertorrents()
        dlg.Destroy()
        return [result == wx.ID_OK,othertorrents]

    def create_url(self,videoserver,upath):
        schemeserv = 'http://127.0.0.1:'+str(videoserver.get_port())
        asciipath = unicode2str(upath)
        return schemeserv+urllib.quote(asciipath)



    def get_video_player(self,ext,videourl,mimetype=None):

        video_player_path = self.utility.config.Read('videoplayerpath')
        if DEBUG:
            print >>sys.stderr,"videoplay: Default player is",video_player_path

        if mimetype is None:
            if sys.platform == 'win32':
                # TODO: Use Python's mailcap facility on Linux to find player
                [mimetype,playcmd] = win32_retrieve_video_play_command(ext,videourl)
                if DEBUG:
                    print >>sys.stderr,"videoplay: Win32 reg said playcmd is",playcmd
                    
            if mimetype is None:
                if ext == '.avi':
                    mimetype = 'video/avi'
                elif ext == '.mpegts':
                    mimetype = 'video/mp2t'
                else:
                    mimetype = 'video/mpeg'
        else:
            if sys.platform == 'win32':
                [mimetype,playcmd] = win32_retrieve_playcmd_from_mimetype(mimetype,videourl)

        if self.playbackmode == PLAYBACKMODE_INTERNAL:
            print >>sys.stderr,"videoplay: using internal player"
            return [mimetype,videourl]
        elif self.playbackmode == PLAYBACKMODE_EXTERNAL_MIME and sys.platform == 'win32':
            if playcmd is not None:
                cmd = 'start /B "TriblerVideo" '+playcmd
                return [mimetype,cmd]

        if DEBUG:
            print >>sys.stderr,"videoplay: Defaulting to default player",video_player_path
        qprogpath = quote_program_path(video_player_path)
        #print >>sys.stderr,"videoplay: Defaulting to quoted prog",qprogpath
        if qprogpath is None:
            return [None,None]
        qvideourl = self.escape_path(videourl)
        playcmd = qprogpath+' '+qvideourl
        if sys.platform == 'win32':
            cmd = 'start /B "TriblerVideo" '+playcmd
        elif sys.platform == 'darwin':
            cmd = 'open -a '+playcmd
        else:
            cmd = playcmd
        print >>sys.stderr,"videoplay: using external user-defined player by executing ",cmd
        return [mimetype,cmd]



    def exec_video_player(self,cmd):
        if DEBUG:
            print >>sys.stderr,"videoplay: Command is @"+cmd+"@"
        # I get a weird problem on Linux. When doing a
        # os.popen2("vlc /tmp/file.wmv") I get the following error:
        #[00000259] main interface error: no suitable interface module
        #[00000001] main private error: interface "(null)" initialization failed
        #
        # The only thing that appears to work is
        # os.system("vlc /tmp/file.wmv")
        # but that halts Tribler, as it waits for the created shell to
        # finish. Hmmmm....
        #
        try:
            if sys.platform == 'win32':
                #os.system(cmd)
                (self.player_out,self.player_in) = os.popen2( cmd, 'b' )
            else:
                (self.player_out,self.player_in) = os.popen2( cmd, 'b' )
        except Exception, e:
            print_exc()
            self.onError(self.utility.lang.get('videoplayerstartfailure'),cmd,str(e.__class__)+':'+str(e))



    def escape_path(self,path):
        if path[0] != '"' and path[0] != "'" and path.find(' ') != -1:
           if sys.platform == 'win32':
               # Add double quotes
               path = "\""+path+"\""
           else:
               path = "\'"+path+"\'"
        return path


    def onError(self,action,value,errmsg=u''):
        self.onMessage(wx.ICON_ERROR,action,value,errmsg)

    def onWarning(self,action,value,errmsg=u''):
        self.onMessage(wx.ICON_INFORMATION,action,value,errmsg)

    def onMessage(self,icon,action,value,errmsg=u''):
        # Don't use language independence stuff, self.utility may not be
        # valid.
        msg = action
        msg += '\n'
        msg += value
        msg += '\n'
        msg += errmsg
        msg += '\n'
        dlg = wx.MessageDialog(None, msg, self.utility.lang.get('videoplayererrortitle'), wx.OK|icon)
        result = dlg.ShowModal()
        dlg.Destroy()

    def set_vod_postponed_downloads(self,dlist):
        self.vod_postponed_downloads = dlist
        
    def get_vod_postponed_downloads(self):
        return self.vod_postponed_downloads

    def set_vod_download(self,d):
        self.vod_download = d
        
    def get_vod_download(self):
        return self.vod_download


    def set_content_name(self,name):
        if self.playbackmode == PLAYBACKMODE_INTERNAL:
            self.videoframe.get_videopanel().SetContentName(name)

    def set_content_image(self,wximg):
        if self.playbackmode == PLAYBACKMODE_INTERNAL:
            self.videoframe.get_videopanel().SetContentImage(wximg)

    def determine_playbackmode(self):
        if self.alwaysinternalplayback:
            playbackmode = PLAYBACKMODE_INTERNAL
        else:
            # WARNING READS TRIBLER CONFIG, DON'T USE in SWARMPLAYER
            playbackmode = self.utility.config.Read('videoplaybackmode', "int")
        feasible = return_feasible_playback_modes(self.utility.getPath())
        if playbackmode in feasible:
            self.playbackmode = playbackmode
        else:
            self.playbackmode = feasible[0]

    def videohttpserver_error_callback(self,e,url):
        """ Called by HTTP serving thread """
        wx.CallAfter(self.videohttpserver_error_guicallback,e,url)
        
    def videohttpserver_error_guicallback(self,e,url):
        print >>sys.stderr,"main: Video server reported error",str(e)
        pass

    def videohttpserver_set_status_callback(self,status):
        """ Called by HTTP serving thread """
        wx.CallAfter(self.videohttpserver_set_status_guicallback,status)

    def videohttpserver_set_status_guicallback(self,status):
        self.videoframe.get_videopanel().SetPlayerStatus(status)
 



class VideoChooser(wx.Dialog):
    
    def __init__(self,parent,utility,filelist,title=None,expl=None):
        
        self.utility = utility
        self.filelist = []
        
        # Convert to Unicode for display
        for file in filelist:
            u = bin2unicode(file)
            self.filelist.append(u)

        if DEBUG:
            print >>sys.stderr,"VideoChooser: filelist",self.filelist
        
        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        if title is None:
            title = self.utility.lang.get('selectvideofiletitle')
        wx.Dialog.__init__(self,parent,-1,title,style=style)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        filebox = wx.BoxSizer(wx.VERTICAL)
        self.file_chooser=wx.Choice(self, -1, wx.Point(-1, -1), wx.Size(300, -1), self.filelist)
        self.file_chooser.SetSelection(0)
        
        if expl is None:
            self.utility.lang.get('selectvideofile')
        filebox.Add(wx.StaticText(self, -1, expl), 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        filebox.Add(self.file_chooser)
        sizer.Add(filebox, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        
        buttonbox = wx.BoxSizer(wx.HORIZONTAL)
        okbtn = wx.Button(self, wx.ID_OK, label=self.utility.lang.get('ok'), style = wx.BU_EXACTFIT)
        buttonbox.Add(okbtn, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5)
        cancelbtn = wx.Button(self, wx.ID_CANCEL, label=self.utility.lang.get('cancel'), style = wx.BU_EXACTFIT)
        buttonbox.Add(cancelbtn, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5)
        sizer.Add(buttonbox, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizerAndFit(sizer)

    def getChosenIndex(self):        
        return self.file_chooser.GetSelection()



class VODWarningDialog(wx.Dialog):
    
    def __init__(self, parent, utility, ds, infilename):
        self.parent = parent
        self.utility = utility

        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        title = self.utility.lang.get('vodwarntitle')
        wx.Dialog.__init__(self,parent,-1,title,style=style)

        msg = self.utility.lang.get('vodwarngeneral')
        """
        if bitrate is None:
            msg += self.utility.lang.get('vodwarnbitrateunknown')
            msg += self.is_mov_file(videoinfo)
            msg += self.utility.lang.get('vodwarnconclusionno')
        elif bitrate > maxuploadrate and maxuploadrate != 0:
            s = self.utility.lang.get('vodwarnbitrateinsufficient') % (str(bitrate/1024),str(maxuploadrate)+" KB/s")
            msg += s
            msg += self.is_mov_file(videoinfo)
            msg += self.utility.lang.get('vodwarnconclusionno')
        elif bitrate > maxmeasureduploadrate and maxuploadrate == 0:
            s = self.utility.lang.get('vodwarnbitrateinsufficientmeasured') % (str(bitrate/1024),str(maxuploadrate)+" KB/s")
            msg += s
            msg += self.is_mov_file(videoinfo)
            msg += self.utility.lang.get('vodwarnconclusionno')
            
        else:
            if maxuploadrate == 0:
                rate = self.utility.lang.get('unlimited')
            else:
                rate = str(maxuploadrate)+" KB/s"
            s = self.utility.lang.get('vodwarnbitratesufficient') % (str(bitrate/1024),rate)
            msg += s
            extra = self.is_mov_file(videoinfo)
            if extra  == '':
                msg += self.utility.lang.get('vodwarnconclusionyes')
            else:
                msg += extra
                msg += self.utility.lang.get('vodwarnconclusionno')
        
        """
        sizer = wx.BoxSizer(wx.VERTICAL)
        text = wx.StaticText(self, -1, msg)
        text.Wrap(500)
        sizer.Add(text, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 5)

        self.otherslist = [self.utility.lang.get('vodrestartothertorrents'),
                           self.utility.lang.get('vodstopothertorrents'),
                           self.utility.lang.get('vodleaveothertorrents')]

        othersbox = wx.BoxSizer(wx.VERTICAL)
        self.others_chooser=wx.Choice(self, -1, wx.Point(-1, -1), wx.Size(-1, -1), self.otherslist)
        
        self.others_chooser.SetSelection(OTHERTORRENTS_STOP_RESTART)
            
        othersbox.Add(wx.StaticText(self, -1, self.utility.lang.get('vodwhataboutothertorrents')), 1, wx.ALIGN_CENTER_VERTICAL)
        othersbox.Add(self.others_chooser)
        sizer.Add(othersbox, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        sizer.Add(wx.StaticText(self, -1, self.utility.lang.get('vodwarnprompt')), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        

        buttonbox = wx.BoxSizer(wx.HORIZONTAL)
        okbtn = wx.Button(self, wx.ID_OK, label=self.utility.lang.get('yes'), style = wx.BU_EXACTFIT)
        buttonbox.Add(okbtn, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5)
        cancelbtn = wx.Button(self, wx.ID_CANCEL, label=self.utility.lang.get('no'), style = wx.BU_EXACTFIT)
        buttonbox.Add(cancelbtn, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5)
        sizer.Add(buttonbox, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizerAndFit(sizer)

    def get_othertorrents(self):
        idx = self.others_chooser.GetSelection()
        if DEBUG:
            print >>sys.stderr,"videoplay: Other-torrents-policy is",idx
        return idx

    def is_mov_file(self,videoinfo):
        orig = videoinfo['inpath']
        (prefix,ext) = os.path.splitext(orig)
        low = ext.lower()
        if low == '.mov':
            return self.utility.lang.get('vodwarnmov')
        else:
            return ''
            

def parse_playtime_to_secs(hhmmss):
    if DEBUG:
        print >>sys.stderr,"videoplay: Playtime is",hhmmss
    r = re.compile("([0-9]+):*")
    occ = r.findall(hhmmss)
    t = None
    if len(occ) > 0:
        if len(occ) == 3:
            # hours as well
            t = int(occ[0])*3600 + int(occ[1])*60 + int(occ[2])
        elif len(occ) == 2:
            # minutes and seconds
            t = int(occ[0])*60 + int(occ[1])
        elif len(occ) == 1:
            # seconds
            t = int(occ[0])
    return t

def return_feasible_playback_modes(syspath):
    l = []
    try:
        import vlc
        vlcpath = os.path.join(syspath,"vlc")
        if sys.platform == 'win32':
            if os.path.isdir(vlcpath):
                l.append(PLAYBACKMODE_INTERNAL)
        else:
            l.append(PLAYBACKMODE_INTERNAL)
    except Exception:
        #print_exc(file=sys.stderr)
        pass
    
    if sys.platform == 'win32':
        l.append(PLAYBACKMODE_EXTERNAL_MIME)
        l.append(PLAYBACKMODE_EXTERNAL_DEFAULT)
    else:
        l.append(PLAYBACKMODE_EXTERNAL_DEFAULT)
    return l

