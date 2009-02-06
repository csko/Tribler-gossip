# generated by wx.Glade 0.6.3 on Thu Feb 05 15:42:50 2009
# 
# Arno: please edit TopSearchPanel.xrc in some XRC editor, then generate
# code for it using wxGlade (single python file mode), and copy the
# relevant parts from it into this file, see "MAINLY GENERATED" line below.
#

import sys
import wx
import os

# begin wx.Glade: extracode
# end wx.Glade

from bgPanel import bgPanel
from GuiUtility import GUIUtility
from Tribler.__init__ import LIBRARYNAME

class TopSearchPanel(bgPanel):
    def __init__(self, *args, **kwds):
        bgPanel.__init__(self,*args,**kwds)
        self.guiUtility = GUIUtility.getInstance()
        self.installdir = self.guiUtility.utility.getPath()
      
    def Bitmap(self,path,type):
        namelist = path.split("/")
        path = os.path.join(self.installdir,LIBRARYNAME,"Main","vwxGUI",*namelist)
        return wx.Bitmap(path,type)
        
    def OnCreate(self,event):
        bgPanel.OnCreate(self,event)
   
# MAINLY GENERATED BELOW, replace wxStaticBitmap, etc. with wx.StaticBitmap 
# and replace wx.BitMap with self.Bitmap
#
# What makes this code (either as Python or as XRC fail is the last statement:
#       self.SetSizer(object_1)
# should be
#       self.SetSizerAndFit(object_1)
# ----------------------------------------------------------------------------------------          
        
        self.black_spacer = wx.StaticBitmap(self, -1, self.Bitmap("images/5.0/black_spacer.png", wx.BITMAP_TYPE_ANY))
        self.files_friends = wx.StaticBitmap(self, -1, self.Bitmap("images/5.0/search_files.png", wx.BITMAP_TYPE_ANY))
        self.searchField = wx.TextCtrl(self, -1, "", style=wx.TE_PROCESS_ENTER)
        self.go = wx.Panel(self, -1)
        self.familyfilter = wx.StaticText(self, -1, "Family Filter:ON")
        self.search_results = wx.StaticText(self, -1, "")
        self.sharing_reputation = wx.StaticBitmap(self, -1, self.Bitmap("images/5.0/sharing_reputation.png", wx.BITMAP_TYPE_ANY))
        self.srgradient = wx.StaticBitmap(self, -1, self.Bitmap("images/5.0/SRgradient.png", wx.BITMAP_TYPE_ANY))
        self.help = wx.StaticBitmap(self, -1, self.Bitmap("images/5.0/help.png", wx.BITMAP_TYPE_ANY))
        self.sr_indicator = wx.StaticBitmap(self, -1, self.Bitmap("images/5.0/SRindicator.png", wx.BITMAP_TYPE_ANY))
        self.settings = wx.StaticText(self, -1, "Settings")
        self.newFile = wx.StaticText(self, -1, "")
        self.seperator = wx.StaticBitmap(self, -1, self.Bitmap("images/5.0/seperator.png", wx.BITMAP_TYPE_ANY))
        self.my_files = wx.StaticText(self, -1, "My Files")
        self.tribler_logo2 = wx.StaticBitmap(self, -1, self.Bitmap("images/logo4video2.png", wx.BITMAP_TYPE_ANY))

        self.__set_properties()
        self.__do_layout()
        # end wx.Glade

    def __set_properties(self):
        # begin wx.Glade: MyPanel.__set_properties
        self.SetSize((1000,90))
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.searchField.SetMinSize((320,23))
        self.searchField.SetForegroundColour(wx.Colour(0, 0, 0))
        self.searchField.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, 0, "Verdana"))
        self.searchField.SetFocus()
        self.go.SetMinSize((24,24))
        self.go.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.familyfilter.SetMinSize((100,15))
        self.familyfilter.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, "UTF-8"))
        self.search_results.SetMinSize((100,10))
        self.search_results.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.settings.SetMinSize((50,15))
        self.settings.SetForegroundColour(wx.Colour(255, 51, 0))
        self.settings.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, "UTF-8"))
        self.newFile.SetForegroundColour(wx.Colour(255, 0, 0))
        self.my_files.SetMinSize((50,15))
        self.my_files.SetForegroundColour(wx.Colour(255, 51, 0))
        self.my_files.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, "UTF-8"))
        # end wx.Glade

    def __do_layout(self):
        # begin wx.Glade: MyPanel.__do_layout
        object_1 = wx.BoxSizer(wx.HORIZONTAL)
        object_12 = wx.BoxSizer(wx.VERTICAL)
        object_11 = wx.BoxSizer(wx.VERTICAL)
        object_10 = wx.BoxSizer(wx.VERTICAL)
        object_2 = wx.BoxSizer(wx.HORIZONTAL)
        object_7 = wx.BoxSizer(wx.VERTICAL)
        object_9 = wx.BoxSizer(wx.HORIZONTAL)
        object_8 = wx.BoxSizer(wx.HORIZONTAL)
        object_3 = wx.BoxSizer(wx.VERTICAL)
        object_5 = wx.BoxSizer(wx.HORIZONTAL)
        object_6 = wx.BoxSizer(wx.VERTICAL)
        object_4 = wx.BoxSizer(wx.HORIZONTAL)
        object_1.Add((10, 0), 0, 0, 0)
        object_1.Add(self.black_spacer, 0, 0, 0)
        object_3.Add((0, 20), 0, 0, 0)
        object_3.Add(self.files_friends, 0, 0, 0)
        object_3.Add((0, 5), 0, 0, 0)
        object_4.Add(self.searchField, 0, wx.LEFT, -2)
        object_4.Add((2, 0), 0, 0, 0)
        object_4.Add(self.go, 0, 0, 0)
        object_3.Add(object_4, 0, 0, 0)
        object_6.Add((0, 0), 0, 0, 0)
        object_6.Add(self.familyfilter, 0, 0, 0)
        object_5.Add(object_6, 0, 0, 0)
        object_5.Add((120, 0), 1, 0, 0)
        object_5.Add(self.search_results, 0, wx.ALIGN_RIGHT, 0)
        object_3.Add(object_5, 0, 0, 0)
        object_2.Add(object_3, 0, wx.EXPAND, 0)
        object_2.Add((100, 0), 0, 0, 0)
        object_7.Add((0, 20), 0, 0, 0)
        object_7.Add(self.sharing_reputation, 0, 0, 0)
        object_7.Add((0, 5), 0, 0, 0)
        object_8.Add(self.srgradient, 0, 0, 0)
        object_8.Add((5, 0), 0, 0, 0)
        object_8.Add(self.help, 0, 0, 0)
        object_7.Add(object_8, 0, 0, 0)
        object_7.Add((0, 5), 0, 0, 0)
        object_9.Add((50, 0), 0, 0, 0)
        object_9.Add(self.sr_indicator, 0, wx.TOP, -17)
        object_7.Add(object_9, 0, 0, 0)
        object_2.Add(object_7, 0, wx.EXPAND, 0)
        object_1.Add(object_2, 1, wx.EXPAND, 0)
        object_1.Add((7, 0), 0, 0, 0)
        object_10.Add((0, 20), 0, 0, 0)
        object_10.Add(self.settings, 0, 0, 0)
        object_10.Add((0, 0), 0, 0, 0)
        object_10.Add(self.newFile, 0, 0, 0)
        object_1.Add(object_10, 0, 0, 0)
        object_1.Add((7, 0), 0, 0, 0)
        object_11.Add((0, 20), 0, 0, 0)
        object_11.Add(self.seperator, 0, 0, 0)
        object_1.Add(object_11, 0, 0, 0)
        object_1.Add((7, 0), 0, 0, 0)
        object_12.Add((0, 20), 0, 0, 0)
        object_12.Add(self.my_files, 0, 0, 0)
        object_12.Add((0, 0), 0, 0, 0)
        object_1.Add(object_12, 0, 0, 0)
        object_1.Add((7, 0), 0, 0, 0)
        object_1.Add(self.tribler_logo2, 0, 0, 0)
        object_1.Add((10, 0), 0, 0, 0)
        self.SetSizerAndFit(object_1)
        # end wx.Glade

# end of class MyPanel


