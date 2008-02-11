# Written by Arno Bakker, Jan David Mol
# see LICENSE.txt for license information

import wx,time
import sys,os


class BufferInfo:
    """ Arno: WARNING: the self.tricolore member is read by the MainThread and 
        written by the network thread. As it is a fixed array with simple values, this
        concurrency problem is ignored.
    """
    NOFILL = " "
    SOMEFILL = ".-+="
    ALLFILL = "#"

    def __init__(self,numbuckets=100,full=False):
        self.numbuckets = numbuckets
        self.playable = False
        self.movieselector = None
        if full == True:
            self.tricolore = [2] * self.numbuckets
    
    def set_numpieces(self,numpieces):
        self.numpieces = numpieces
        self.buckets = [0] * self.numbuckets
        self.tricolore = [0] * self.numbuckets
        #self.bucketsize = int(ceil(float(self.numpieces) / self.numbuckets))
        self.bucketsize = float(self.numpieces) / float(self.numbuckets)
        self.lastbucketsize = self.numpieces - int(float(self.numbuckets-1) * self.bucketsize)

    def complete( self, piece ):
        bucket = int(float(piece) / self.bucketsize)
        
        #print >>sys.stderr,"BUCKET",bucket,"piece",piece,"bucksize",self.bucketsize
        # If there is a multi-file torrent that has been partially downloaded before we go
        # to VOD, it can happen that pieces outside the range of the file selected are
        # reported as complete here.
        if bucket < 0 or bucket >= self.numbuckets:
            return
        
        self.buckets[bucket] += 1

        fill = self.buckets[bucket]
        if bucket == self.numbuckets-1:
            total = self.lastbucketsize
        else:
            total = int(self.bucketsize)
            
        if fill == 0:
            colour = 0
        elif fill >= total:
            colour = 2
        else:
            colour = 1

        self.tricolore[bucket] = colour

    def str( self ):
        def chr( fill, total ):
            if fill == 0:
                return self.NOFILL
            if fill >= int(total):
                return self.ALLFILL

            index = int(float(fill*len(self.SOMEFILL))/total)
            if index >= len(self.SOMEFILL):
                index = len(self.SOMEFILL)-1
            return self.SOMEFILL[index]

        chars = [chr( self.buckets[i], self.bucketsize ) for i in xrange(0,self.numbuckets-1)]
        chars.append( chr( self.buckets[-1], self.lastbucketsize ) )
        return "".join(chars)


    def set_playable(self):
        self.playable = True
        
    def get_playable(self):
        return self.playable

    def set_movieselector(self,movieselector):
        self.movieselector = movieselector
    
    def get_bitrate(self):
        if self.movieselector is not None:
            return self.movieselector.get_bitrate()
        else:
            return 0.0

    def get_blocks(self):
        return self.tricolore


class ProgressInf:
    def __init__(self):
        self.bufferinfo = BufferInfo()
        self.callback = None
        
    def get_bufferinfo(self):
        return self.bufferinfo

    def set_callback(self,callback):
        self.callback = callback
        
    def bufferinfo_updated_callback(self):
        if self.callback is not None:
            self.callback()
        


class ProgressBar(wx.Control):
    #def __init__(self, parent, colours = ["#cfcfcf","#d7ffd7","#00ff00"], *args, **kwargs ):
    #def __init__(self, parent, colours = ["#cfcfcf","#fde72d","#00ff00"], *args, **kwargs ):
    #def __init__(self, parent, colours = ["#ffffff","#fde72d","#00ff00"], *args, **kwargs ):
    def __init__(self, parent, colours = ["#ffffff","#CBCBCB","#ff3300"], *args, **kwargs ):
        self.colours = colours
        self.pens    = [wx.Pen(c,0) for c in self.colours]
        self.brushes = [wx.Brush(c) for c in self.colours]
        self.reset()

        style = wx.SIMPLE_BORDER
        wx.Control.__init__(self, parent, -1, style=style)
        self.SetMaxSize((-1,6))
        self.SetMinSize((1,6))
        self.SetBackgroundColour(wx.WHITE)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.SetSize((100,6))

        self.progressinf = None

    def AcceptsFocus(self):
        return False

    def OnEraseBackground(self, event):
        pass # Or None
    
    def OnPaint(self, evt):
        
        # define condition
        x,y,maxw,maxh = self.GetClientRect()
        #dc.DrawRectangle(x,y,)
        
        arrowsize = 6
        arrowspace = 1
        numrect = len(self.blocks)

        # create blocks
        w = max(1,maxw/numrect)
        h = maxh
        
        width, height = self.GetClientSizeTuple()
        buffer = wx.EmptyBitmap(width, height)
        #dc = wx.PaintDC(self)
        dc = wx.BufferedPaintDC(self, buffer)
        dc.BeginDrawing()
        dc.Clear()
        
        rectangles = [(x+i*w,y,w,h) for i in xrange(0,numrect)]

        # draw the blocks
        pens = [self.pens[c] for c in self.blocks]
        brushes = [self.brushes[c] for c in self.blocks]
                
        dc.DrawRectangleList(rectangles,pens,brushes)

        dc.EndDrawing()

    def set_blocks(self,blocks):
        """ Called by MainThread """
        self.blocks = blocks
        
    def setNormalPercentage(self, perc):
        perc = int(perc)
        self.blocks = ([2]*perc)+([0]* (100-perc))

    def reset(self,colour=0):
        self.blocks = [colour] * 100
        
class ProgressSlider(wx.Panel):
    
    def __init__(self, parent, utility, colours = ["#ffffff","#CBCBCB","#ff3300"], *args, **kwargs ):
        self.colours = colours
        #self.backgroundImage = wx.Image('')
        self.progress      = 0.0
        self.videobuffer  = 0.0
        self.videoPosition = 0
        self.timeposition = None
        self.videoLength   = None
        #wx.Control.__init__(self, parent, -1)
        wx.Panel.__init__(self, parent, -1)
        self.SetMaxSize((-1,25))
        self.SetMinSize((1,25))
        self.SetBackgroundColour(wx.WHITE)
        self.utility = utility
        self.bgImage = wx.Bitmap(os.path.join(self.utility.getPath(), 'Tribler','Images','background.png'))
        self.dotImage = wx.Bitmap(os.path.join(self.utility.getPath(), 'Tribler','Images','sliderDot.png'))
        self.sliderPosition = None
        self.rectHeight = 5
        self.rectBorderColour = wx.LIGHT_GREY
        self.textWidth = 70
        self.margin = 10
        self.doneColor = wx.RED
        self.bufferColor = wx.GREEN
        self.sliderWidth = 0
        self.range = (0,1)
        self.dragging = False
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)
        #self.SetSize((-1,self.bgImage.GetSize()[1]))
        
    def AcceptsFocus(self):
        return False

    def OnEraseBackground(self, event):
        pass # Or None
    
    def OnSize(self, event):
        self.Refresh()
    
    def OnMouse(self, event):
        pos = event.GetPosition()
        if event.ButtonDown():
            if self.onSliderButton(pos):
                print >> sys.stderr, 'Start drag'
                self.dragging = True
            elif self.onSlider(pos): # click somewhere on the slider
                self.setSliderPosition(pos,True)
        elif event.ButtonUp():
            if self.dragging:
                self.setSliderPosition(pos, True)
                print >> sys.stderr, 'End drag'
            self.dragging = False
        elif event.Dragging():
            if self.dragging:
                self.setSliderPosition(pos, False)
        elif event.Leaving():
            if self.dragging:
                self.setSliderPosition(pos,True)
                
    def onSliderButton(self, pos):
        if not self.sliderPosition:
            return False
        x,y = pos
        bx, by = self.sliderPosition
        dotSize = self.dotImage.GetSize()
        return abs(x-bx) < dotSize[0]/2 and abs(y-by)<dotSize[1]/2
        
    def onSlider(self, pos):
        x,y = pos
        width, height = self.GetClientSizeTuple()
        return (x > self.margin and x<= self.margin+self.sliderWidth and \
                abs(y - height/2) < self.rectHeight/2+4)
        
    def setSliderPosition(self, pos, ready):
        x, y = pos
        tmp_progress = (x-self.margin)/float(self.sliderWidth)
        self.progress = min(1.0, max(0.0, tmp_progress))
        self.videoPosition = self
        self.Refresh()
        if ready:
            #theEvent = wx.ScrollEvent(pos=self.progress)
            #self.GetEventHandler().ProcessEvent(theEvent)
            #print >> sys.stderr, 'Posted event'
            print >> sys.stderr, 'Set progress to : %f' % self.progress
            self.sliderChangedAction()
            
    def sliderChangedAction(self):
        self.GetParent().Seek(None)
            
        
                
        
    def setBufferFromPieces(self, pieces_complete):
        if not pieces_complete:
            self.videobuffer = 0.0
            return
        current_piece = int(len(pieces_complete)*self.progress)
        last_buffered_piece = current_piece
        while last_buffered_piece<len(pieces_complete) and pieces_complete[last_buffered_piece]:
            last_buffered_piece+=1
        bufferlen = (last_buffered_piece - current_piece+1)
        print >> sys.stderr, '%d/%d pieces continuous buffer (frac %f)' % \
            (bufferlen, len(pieces_complete), bufferlen / float(len(pieces_complete)))
        self.videobuffer = bufferlen/float(len(pieces_complete))+self.progress
                    
            
    def SetValue(self, b):
        if self.range[0] == self.range[1]:
            return
        
        if not self.dragging:
            self.progress = max(0.0, min((b - self.range[0]) / float(self.range[1] - self.range[0]), 1.0))
            self.Refresh()
        
    def GetValue(self):
        print >>sys.stderr, 'Progress: %f, Range (%f, %f)' % (self.progress, self.range[0], self.range[1])
        return self.progress * (self.range[1] - self.range[0])+ self.range[0]

    def SetRange(self, a,b):
        self.range = (a,b)
    
    def setVideoBuffer(self, buf):
        self.videobuffer = buf
    
    def SetTimePosition(self, timepos, duration):
        self.timeposition = timepos
        self.videoLength = duration
        
    def formatTime(self, s):
        longformat = time.strftime('%d:%H:%M:%S', time.gmtime(s))
        if longformat.startswith('01:'):
            longformat = longformat[3:]
        while longformat.startswith('00:') and len(longformat) > len('00:00'):
            longformat = longformat[3:]
        return longformat
    
    def OnPaint(self, evt):
        width, height = self.GetClientSizeTuple()
        buffer = wx.EmptyBitmap(width, height)
        #dc = wx.PaintDC(self)
        dc = wx.BufferedPaintDC(self, buffer)
        dc.BeginDrawing()
        dc.Clear()
        
        # Draw background
        bgSize = self.bgImage.GetSize()
        for i in xrange(width/bgSize[0]+1):
            dc.DrawBitmap(self.bgImage, i*(bgSize[0]-1),0)
        
        
        self.sliderWidth = width-(3*self.margin+self.textWidth)
        position = self.sliderWidth * self.progress
        self.sliderPosition = position+self.margin, height/2
        self.bufferlength = (self.videobuffer-self.progress) * self.sliderWidth
        self.bufferlength = min(self.bufferlength, self.sliderWidth-position)
        
        # Time strings
        if self.videoLength is not None:
            durationString = self.formatTime(self.videoLength)
        else:
            durationString = '--:--'
        if self.timeposition is not None:
            timePositionString = self.formatTime(self.timeposition)
        else:
            timePositionString = '--:--'
        
        if width > 3*self.margin+self.textWidth:
            # Draw slider rect
            dc.SetPen(wx.Pen(self.rectBorderColour, 2))
            dc.DrawRectangle(self.margin,height/2-self.rectHeight/2, self.sliderWidth, self.rectHeight)
            # Draw slider rect inside
            dc.SetPen(wx.Pen(self.doneColor, 0))
            dc.SetBrush(wx.Brush(self.doneColor))
            smallRectHeight = self.rectHeight - 2
            dc.DrawRectangle(self.margin,height/2-smallRectHeight/2, position, smallRectHeight)
            dc.SetBrush(wx.Brush(self.bufferColor))
            dc.SetPen(wx.Pen(self.bufferColor, 0))
            dc.DrawRectangle(position+self.margin,height/2-smallRectHeight/2, self.bufferlength, smallRectHeight)
            # draw circle
            dotSize = self.dotImage.GetSize()
            dc.DrawBitmap(self.dotImage, position+self.margin-dotSize[0]/2, height/2-dotSize[1]/2)
        if width > 2*self.margin+self.textWidth:
            # Draw times
            font = self.GetFont()
            font.SetPointSize(8)
            dc.SetFont(font)
            dc.DrawText('%s / %s' % (timePositionString, durationString), width-self.margin-self.textWidth, height/2-dc.GetCharHeight()/2)

        dc.EndDrawing()

  
class VolumeSlider(wx.Panel):
    
    def __init__(self, parent, utility):
        self.progress      = 0.0
        self.position = 0
        
        #wx.Control.__init__(self, parent, -1)
        wx.Panel.__init__(self, parent, -1)
        self.SetMaxSize((-1,25))
        self.SetMinSize((1,25))
        self.SetBackgroundColour(wx.WHITE)
        self.utility = utility
        self.bgImage = wx.Bitmap(os.path.join(self.utility.getPath(), 'Tribler','Images','background.png'))
        self.sliderPosition = None
        self.rectHeight = 5
        self.rectBorderColour = wx.LIGHT_GREY
        self.margin = 10
        self.cursorsize = [4,19]
        self.doneColor = wx.RED
        self.sliderWidth = 0
        self.range = (0,1)
        self.dragging = False
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)
        #self.SetSize((-1,self.bgImage.GetSize()[1]))
        
    def AcceptsFocus(self):
        return False

    def OnEraseBackground(self, event):
        pass # Or None
    
    def OnSize(self, event):
        self.Refresh()
    
    def OnMouse(self, event):
        pos = event.GetPosition()
        if event.ButtonDown():
            if self.onSliderButton(pos):
                print >> sys.stderr, 'Start drag'
                self.dragging = True
            elif self.onSlider(pos): # click somewhere on the slider
                self.setSliderPosition(pos,True)
        elif event.ButtonUp():
            if self.dragging:
                self.setSliderPosition(pos, True)
                print >> sys.stderr, 'End drag'
            self.dragging = False
        elif event.Dragging():
            if self.dragging:
                self.setSliderPosition(pos, False)
        elif event.Leaving():
            if self.dragging:
                self.setSliderPosition(pos,True)
                
    def onSliderButton(self, pos):
        if not self.sliderPosition:
            return False
        x,y = pos
        bx, by = self.sliderPosition
        extraGrip = 3 # 3px extra grip on sliderButton
        return abs(x-bx) < self.cursorsize[0]/2+extraGrip and abs(y-by)<self.cursorsize[1]/2
        
    def onSlider(self, pos):
        x,y = pos
        width, height = self.GetClientSizeTuple()
        return (x > self.margin and x<= self.margin+self.sliderWidth and \
                abs(y - height/2) < self.rectHeight/2+4)
        
    def setSliderPosition(self, pos, ready):
        x, y = pos
        tmp_progress = (x-self.margin)/float(self.sliderWidth)
        self.progress = min(1.0, max(0.0, tmp_progress))
        self.videoPosition = self
        self.Refresh()
        if ready:
            #theEvent = wx.ScrollEvent(pos=self.progress)
            #self.GetEventHandler().ProcessEvent(theEvent)
            #print >> sys.stderr, 'Posted event'
            print >> sys.stderr, 'Set progress to : %f' % self.progress
            self.sliderChangedAction()
            
    def sliderChangedAction(self):
        self.GetParent().SetVolume()
            
            
    def SetValue(self, b):
        if not self.dragging:
            self.progress = min((b - self.range[0]) / float(self.range[1] - self.range[0]), 1.0)
            self.Refresh()
        
    def GetValue(self):
        print >>sys.stderr, 'Progress: %f, Range (%f, %f)' % (self.progress, self.range[0], self.range[1])
        return self.progress * (self.range[1] - self.range[0])+ self.range[0]

    def SetRange(self, a,b):
        self.range = (a,b)
    
    def OnPaint(self, evt):
        width, height = self.GetClientSizeTuple()
        buffer = wx.EmptyBitmap(width, height)
        #dc = wx.PaintDC(self)
        dc = wx.BufferedPaintDC(self, buffer)
        dc.BeginDrawing()
        dc.Clear()
        
        # Draw background
        bgSize = self.bgImage.GetSize()
        for i in xrange(width/bgSize[0]+1):
            dc.DrawBitmap(self.bgImage, i*(bgSize[0]-1),0)
        
        
        self.sliderWidth = width-(2*self.margin)
        position = self.sliderWidth * self.progress
        self.sliderPosition = position+self.margin, height/2
        
        
        if width > 2*self.margin:
            # Draw slider rect
            dc.SetPen(wx.Pen(self.rectBorderColour, 2))
            dc.DrawRectangle(self.margin,height/2-self.rectHeight/2, self.sliderWidth, self.rectHeight)
            # Draw slider rect inside
            dc.SetPen(wx.Pen(self.doneColor, 0))
            dc.SetBrush(wx.Brush(self.doneColor))
            smallRectHeight = self.rectHeight - 2
            dc.DrawRectangle(self.margin,height/2-smallRectHeight/2, position, smallRectHeight)
            # draw circle
            dc.SetPen(wx.NullPen)
            dc.SetBrush(wx.Brush(self.rectBorderColour))
            dc.DrawRectangle(position+self.margin-self.cursorsize[0]/2, height/2-self.cursorsize[1]/2, self.cursorsize[0], self.cursorsize[1])
        
        dc.EndDrawing()

        
