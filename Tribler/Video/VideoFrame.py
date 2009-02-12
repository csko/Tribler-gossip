# Written by Fabian van der Werf and Arno Bakker
# see LICENSE.txt for license information

import wx
import sys

from Tribler.Video.EmbeddedPlayer import EmbeddedPlayerPanel

class VideoBaseFrame:

    def show_videoframe(self):
        pass
    
    def hide_videoframe(self):
        pass

    def get_videopanel(self):
        pass
    
    def delete_videopanel(self):
        pass

    def OnCloseWindow(self, event = None):
        pass

    def get_window(self):
        pass



class VideoFrame(wx.Frame,VideoBaseFrame):
    """ Provides a wx.Frame around an EmbeddedPlayerPanel so the embedded player
    is shown as a separate window. The Embedded Player consists of a VLCLogoWindow
    and the media controls such as Play/Pause buttons and Volume Control.
    """
    
    def __init__(self,parent,title,iconpath,vlcwrap,logopath):
        self.utility = parent.utility
        if title is None:
            title = self.utility.lang.get('tb_video_short')
        
        if vlcwrap is None:
            size = (800,150)
        else:
            size = (800,520) # Use 16:9 aspect ratio: 500 = (800/16) * 9 + 50 for controls
        wx.Frame.__init__(self, None, -1, title, size=size) 
        
        self.create_videopanel(vlcwrap,logopath)

        # Set icons for Frame
        self.icons = wx.IconBundle()
        self.icons.AddIconFromFile(iconpath,wx.BITMAP_TYPE_ICO)
        self.SetIcons(self.icons)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def create_videopanel(self,vlcwrap, logopath):
        self.showingframe = False
        self.videopanel = EmbeddedPlayerPanel(self, self.utility, vlcwrap, logopath)
        self.Hide()

    def show_videoframe(self):
        if DEBUG:
            print >>sys.stderr,"videoframe: Swap IN videopanel"
            
        if self.videopanel is not None:
            if not self.showingframe:
                self.showingframe = True
                self.Show()
                
            self.Raise()
            self.SetFocus()
                       
            # H4x0r: We need to tell the VLC wrapper a XID of a
            # window to paint in. Apparently on win32 the XID is only
            # known when the window is shown. We give it the command
            # to show here, so shortly after it should be shown.
            #
            wx.CallAfter(self.videopanel.TellLVCWrapWindow4Playback)

    
    def hide_videoframe(self):
        if DEBUG:
            print >>sys.stderr,"videoframe: Swap OUT videopanel"

        if self.videopanel is not None:
            self.videopanel.Reset()
            if self.showingframe:
                self.showingframe = False
                self.Hide()

    def get_videopanel(self):
        return self.videopanel

    def delete_videopanel(self):
        self.videopanel = None

    def get_window(self):
        return self


    def OnCloseWindow(self, event = None):
        self.hide_videoframe()        

                 

class VideoDummyFrame(VideoBaseFrame):
    """ Provides a fake Frame around an EmbeddedPlayerPanel so the embedded player
    can be shown inside another window. 
    """
    
    def __init__(self,parent,utility,vlcwrap,logopath):
        self.parent = parent
        self.utility = utility
        self.create_videopanel(vlcwrap,logopath)

    def create_videopanel(self,vlcwrap, logopath):
        # ARNO50: Uses 5.0 colours
        self.showingframe = False
        self.videopanel = EmbeddedPlayerPanel(self.parent,self.utility,vlcwrap,logopath,fg=wx.WHITE,bg=(216,233,240))
        self.videopanel.Hide()

    def show_videoframe(self):
        if not self.showingframe:
            self.showingframe = True
            self.videopanel.Show()
                
        # H4x0r: We need to tell the VLC wrapper a XID of a
        # window to paint in. Apparently on win32 the XID is only
        # known when the window is shown. We give it the command
        # to show here, so shortly after it should be shown.
        #
        wx.CallAfter(self.videopanel.TellLVCWrapWindow4Playback)
    
    def hide_videoframe(self):
        if self.showingframe:
            self.showingframe = False
            self.videopanel.Hide()

    def show_videoframe(self):
        self.videopanel.Show()

        # H4x0r: We need to tell the VLC wrapper a XID of a
        # window to paint in. Apparently on win32 the XID is only
        # known when the window is shown. We give it the command
        # to show here, so shortly after it should be shown.
        #
        wx.CallAfter(self.videopanel.TellLVCWrapWindow4Playback)


    def hide_videoframe(self):
        self.videopanel.Hide()

    def get_videopanel(self):
        return self.videopanel

    def delete_videopanel(self):
        self.videopanel = None

    def get_window(self):
        return self.parent

