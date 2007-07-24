import wx, math, time, os, sys, threading
import random
from traceback import print_exc
from Tribler.utilities import *
from wx.lib.stattext import GenStaticText as StaticText
from Tribler.vwxGUI.GuiUtility import GUIUtility
from safeguiupdate import FlaglessDelayedInvocation
from Tribler.unicode import *
from font import *
import cStringIO
import TasteHeart

DEBUG = False

# font sizes
if sys.platform == 'darwin':
    FS_PERSONSTITLE = 10
    FS_HEARTRANK = 10
    FS_ONLINE = 10
else:
    FS_PERSONSTITLE = 10
    FS_HEARTRANK = 7
    FS_ONLINE = 8

class PersonsItemPanel(wx.Panel):
    """
    PersonsItemPanel shows one persons item inside the PersonsGridPanel
    """
    def __init__(self, parent, keyTypedFun=None):
        global TORRENTPANEL_BACKGROUND
        
        wx.Panel.__init__(self, parent, -1)
        self.guiUtility = GUIUtility.getInstance()
        self.utility = self.guiUtility.utility
        self.parent = parent
        self.data = None
        self.datacopy = None
        self.titleLength = 37 # num characters
        self.selected = False
        self.warningMode = False
        self.oldCategoryLabel = None
        self.guiserver = parent.guiserver
        self.mm = parent.mm
        self.selected = False
        self.superpeer_db = parent.superpeer_db
        self.keyTypedFun = keyTypedFun
        self.addComponents()
        self.Show()
        self.Refresh()
        self.Layout()
        

    def addComponents(self):
        self.Show(False)
        self.SetMinSize((80,110))
        self.selectedColour = wx.Colour(255,200,187)       
        self.unselectedColour = wx.WHITE
        
        self.SetBackgroundColour(self.unselectedColour)
        self.vSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.Bind(wx.EVT_LEFT_UP, self.mouseAction)
        self.Bind(wx.EVT_KEY_UP, self.keyTyped)
        
        # Add title
        self.thumb = ThumbnailViewer(self)
        self.thumb.setBackground(wx.BLACK)
        self.thumb.SetSize((80,80))
        self.vSizer.Add(self.thumb, 0, wx.ALL, 0)        
        self.title =wx.StaticText(self,-1,"",wx.Point(0,0),wx.Size(80,15))        
        self.title.SetBackgroundColour(wx.WHITE)
        self.title.SetFont(wx.Font(FS_PERSONSTITLE,FONTFAMILY,FONTWEIGHT,wx.NORMAL,False,FONTFACE))
        self.title.SetMinSize((80,30))
        self.vSizer.Add(self.title, 0, wx.BOTTOM, 3)     

        self.SetSizer(self.vSizer);
        self.SetAutoLayout(1);
        self.Layout();
        self.Refresh()
        
        for window in self.GetChildren():
            window.Bind(wx.EVT_LEFT_UP, self.mouseAction)
            window.Bind(wx.EVT_KEY_UP, self.keyTyped)
                             
    def setData(self, peer_data):
        # set bitmap, rating, title
        
        #print >>sys.stderr,"pip: setData:",peer_data
            
        if peer_data is None:
            self.datacopy = None
        
        if self.datacopy is not None and peer_data is not None and self.datacopy['permid'] == peer_data['permid']:
            if (self.datacopy['last_seen'] == peer_data['last_seen'] and
                self.datacopy['similarity'] == peer_data['similarity'] and
                self.datacopy['name'] == peer_data['name'] and
                self.datacopy['content_name'] == peer_data['content_name'] and
                self.datacopy.get('friend') == peer_data.get('friend')):
                return
        
        self.data = peer_data

        if peer_data is not None:
            # deepcopy no longer works with 'ThumnailBitmap' on board
            self.datacopy = {}
            self.datacopy['permid'] = peer_data['permid']
            self.datacopy['last_seen'] = peer_data['last_seen']
            self.datacopy['similarity'] = peer_data['similarity']
            self.datacopy['name'] = peer_data['name']
            self.datacopy['content_name'] = peer_data['content_name']
            self.datacopy['friend'] = peer_data.get('friend')
        else:
            peer_data = {}
        
        if peer_data.get('content_name'):
            title = peer_data['content_name'][:self.titleLength]
            self.title.Enable(True)
            self.title.SetLabel(title)
            self.title.Wrap(self.title.GetSize()[0])
            self.title.SetToolTipString(peer_data['content_name'])
        else:
            self.title.SetLabel('')
            self.title.SetToolTipString('')
            self.title.Enable(False)

        self.thumb.setData(peer_data)
               
        self.Layout()
        self.Refresh()
        #self.parent.Refresh()
        
    def select(self, rowIndex, colIndex):
        if DEBUG:
            print 'pip: person selected'
        self.selected = True
        self.thumb.setSelected(True)
        self.title.SetBackgroundColour(self.selectedColour)
        self.title.Refresh()
                
    def deselect(self, rowIndex, colIndex):
        self.selected = False
        self.thumb.setSelected(False)
        self.title.SetBackgroundColour(self.unselectedColour)
        self.title.Refresh()
    
    def keyTyped(self, event):
        if self.selected:
            key = event.GetKeyCode()
            if (key == wx.WXK_DELETE):
                if self.data:
                    if DEBUG:
                        print >>sys.stderr,'pip: deleting'
#                    self.guiUtility.deleteTorrent(self.data)
        event.Skip()
        
    def mouseAction(self, event):
        if DEBUG:
            print "pip: set focus"
        self.SetFocus()
        if self.data:
            self.guiUtility.selectPeer(self.data)
            
    def getIdentifier(self):
        if self.data:
            return self.data['permid']

class ThumbnailViewer(wx.Panel, FlaglessDelayedInvocation):
    """
    Show thumbnail and mast with info on mouseOver
    """

    def __init__(self, *args, **kw):
        self.triblerGrey = wx.Colour(128,128,128)   
        self.triblerLightGrey = wx.Colour(203,203,203)   
        if len(args) == 0:
            pre = wx.PrePanel()
            # the Create step is done by XRC.
            self.PostCreate(pre)
            self.Bind(wx.EVT_WINDOW_CREATE, self.OnCreate)
        else:
            wx.Panel.__init__(self, *args, **kw)
            self._PostInit()
        
    def OnCreate(self, event):
        self.Unbind(wx.EVT_WINDOW_CREATE)
        wx.CallAfter(self._PostInit)
        event.Skip()
        return True
    
    def _PostInit(self):
        # Do all init here
        FlaglessDelayedInvocation.__init__(self)
        self.backgroundColor = wx.WHITE
        self.dataBitmap = self.maskBitmap = None
        self.data = None
        self.mouseOver = False
        self.guiUtility = GUIUtility.getInstance()
        self.utility = self.guiUtility.utility
        self.Bind(wx.EVT_MOUSE_EVENTS, self.mouseAction)
        self.Bind(wx.EVT_LEFT_UP, self.guiUtility.buttonClicked)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnErase)
        self.selected = False
        self.border = None
        #create the heart
        #I will use TasteHeart.BITMAPS to paint the right one

        self.mm = self.GetParent().parent.mm
        self.superpeer_db = self.GetParent().parent.superpeer_db
    
    def setData(self, data):
        
        if not data:
            self.Hide()
            self.Refresh()
            return
        
        if not self.IsShown():
                self.Show()
        if data != self.data:
            self.data = data
            self.setThumbnail(data)

    def setThumbnail(self, data):
        # Get the file(s)data for this torrent
        try:
            bmp = self.mm.get_default('personsMode','DEFAULT_THUMB')
            # Check if we have already read the thumbnail and metadata information from this torrent file
            if data.get('metadata'):
                bmp = data['metadata'].get('ThumbnailBitmap')
                tt = data['metadata'].get('triend_time')
                if not bmp:
                    now = time()
                    #print "BMP IS NONE",data['name']
                    bmp = self.mm.get_default('personsMode','DEFAULT_THUMB')
                    if now > tt+(15*60.0):
                        #print "REFRESH OF PEER IMAGE SCHEDULED"
                        self.GetParent().guiserver.add_task(lambda:self.loadMetadata(data),0)
            else:
                self.GetParent().guiserver.add_task(lambda:self.loadMetadata(data),0)
            
            self.setBitmap(bmp)
            width, height = self.GetSize()
            d = 1
            self.border = [wx.Point(0,d), wx.Point(width-d, d), wx.Point(width-d, height-d), wx.Point(d,height-d), wx.Point(d,0)]
            self.Refresh()
            
        except:
            print_exc(file=sys.stderr)
            return {}           
        
         
    def setBitmap(self, bmp):
        # Recalculate image placement
        w, h = self.GetSize()
        iw, ih = bmp.GetSize()
                
        self.dataBitmap = bmp
        self.xpos, self.ypos = (w-iw)/2, (h-ih)/2
        

    def loadMetadata(self,data,type=None):
        """ Called by non-GUI thread """
        
        if DEBUG:
            print "pip: ThumbnailViewer: loadMetadata: Peer",show_permid_short(data['permid']),data['name']
            
        # We can't do any wx stuff here apparently, so the only thing we can do is to
        # read the data from the file and create the wxBitmap in the GUI callback.
        [mimetype,bmpdata] = self.mm.load_data(data['permid'],data['name'])
        #print "PersonsItemPanel: ThumbnailViewer: loadMetadata: Got",show_permid_short(permid),mimetype

        self.invokeLater(self.metadata_thread_gui_callback,[data,mimetype,bmpdata,type])
             
    def metadata_thread_gui_callback(self,data,mimetype,bmpdata,type=None):
        """ Called by GUI thread """

        metadata = {}
        metadata['triend_time'] = time()+(random.random()*100)
        if mimetype is not None:
            metadata['ThumbnailBitmap'] = self.mm.data2wxBitmap(mimetype,bmpdata)
        else:
            superpeers = self.superpeer_db.getSuperPeerList()
            
            """
            if data['name'].lower().startswith("superpeer"):
                print >>sys.stderr,"pip: Name is superpeer",data['name'],"permid",show_permid_short(data['permid'])
                for speer in superpeers:
                    print >>sys.stderr,"pip: Comparing to superpeer",show_permid_short(speer)
            """
            if data['permid'] in superpeers:
                bm = self.mm.get_default('personsMode','SUPERPEER_BITMAP')
                metadata['ThumbnailBitmap'] = bm
            else:
                metadata['ThumbnailBitmap'] = None

        if type and metadata['ThumbnailBitmap'] is not None:
            iw, ih = metadata['ThumbnailBitmap'].GetSize()
            w, h = self.GetSize()
            if (iw/float(ih)) > (w/float(h)):
                nw = w
                nh = int(ih * w/float(iw))
            else:
                nh = h
                nw = int(iw * h/float(ih))
            if nw != iw or nh != ih:
                #print 'Rescale from (%d, %d) to (%d, %d)' % (iw, ih, nw, nh)
                img = wx.ImageFromBitmap(metadata['ThumbnailBitmap'])
                img.Rescale(nw, nh)
                metadata['ThumbnailBitmap'+type] = wx.BitmapFromImage(img)
            #print >>sys.stderr,"pip: Netresult is",metadata['ThumbnailBitmap']

        if DEBUG:
            print "pip: ThumbnailViewer: GUI callback"
        data['metadata'] = metadata
        
        # This item may be displaying another person right now, only show the icon
        # when it's still the same person
        if data['permid'] == self.data['permid']:
            thumb_type = 'ThumbnailBitmap'
            if type:
                thumb_type = thumb_type+type
            if thumb_type in metadata and metadata[thumb_type] is not None:
                self.setBitmap(metadata[thumb_type])
            self.Refresh()
    
    
    def OnErase(self, event):
        pass
        #event.Skip()
        
    def setSelected(self, sel):
        self.selected = sel
        self.Refresh()
        
    def isSelected(self):
        return self.selected
        
    def mouseAction(self, event):
        if event.Entering():
            if DEBUG:
                print 'pip: enter' 
            self.mouseOver = True
            self.Refresh()
        elif event.Leaving():
            self.mouseOver = False
            if DEBUG:
                print 'pip: leave'
            self.Refresh()
#        elif event.ButtonUp():
#            self.ClickedButton()
        #event.Skip()
        """
    def ClickedButton(self):
        print 'Click'
        """
                
    def setBackground(self, wxColor):
        self.backgroundColor = wxColor
        
    def OnPaint(self, evt):
        dc = wx.BufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self.backgroundColor))
        dc.Clear()
        
        if self.dataBitmap:
            dc.DrawBitmap(self.dataBitmap, self.xpos,self.ypos, True)
#        if self.mouseOver:
        if self.data is not None and type(self.data)==type({}) and self.data.get('permid'):
            rank = self.guiUtility.peer_manager.getRank(peer_data = self.data)#['permid'])
            #because of the fact that hearts are coded so that lower index means higher ranking, then:
            heartBitmap = TasteHeart.getHeartBitmap(rank)
            if self.mouseOver:
                mask = self.mm.get_default('personsMode','MASK_BITMAP_CLEAN')
                y_pos = 0
                m_height = mask.GetSize()[1]
                y_height = self.GetSize()[1]
                while y_pos<y_height:
                    dc.DrawBitmap(mask,0 ,y_pos, True)
                    y_pos = y_pos + m_height
            if heartBitmap or self.data.get('friend') or self.data.get('online'):
                mask = self.mm.get_default('personsMode','MASK_BITMAP')
                dc.DrawBitmap(mask,0 ,62, True)
            if heartBitmap:
                dc.DrawBitmap(heartBitmap,5 ,64, True)
                dc.SetFont(wx.Font(FS_HEARTRANK,FONTFAMILY,FONTWEIGHT, wx.BOLD, False, FONTFACE))
                text = repr(rank)                
                dc.DrawText(text, 22, 66)
            if self.data.get('friend'):
                if self.data.get('online'):
                    friend = self.mm.get_default('personsMode','FRIEND_ONLINE_BITMAP')
                else:
                    friend = self.mm.get_default('personsMode','FRIEND_OFFLINE_BITMAP')
                dc.DrawBitmap(friend,60 ,65, True)   
            elif self.data.get('online'):         
                dc.SetFont(wx.Font(FS_ONLINE,FONTFAMILY,FONTWEIGHT, wx.BOLD, False,FONTFACE))
                dc.SetTextForeground('#007303')
                dc.DrawText('online', 38, 64)
        
#        dc.SetTextForeground(wx.WHITE)
        #dc.DrawText('rating', 5, 60)

        if self.border:
            if self.selected:
                dc.SetPen(wx.Pen(wx.Colour(255,51,0), 2))
            else:
                dc.SetPen(wx.Pen(self.triblerLightGrey, 2))
            dc.DrawLines(self.border)
        

