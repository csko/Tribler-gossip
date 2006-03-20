#########################################################################
# Author : Choopan RATTANAPOKA
# Description : To change local upload options for each torrent
#########################################################################
import wx
from os import path


################################################################
#
# Class: LocalSettingDialog
#
# Allows for setting local limits on rates or changing the
# upload options for torrents on an individual basis.
#
################################################################
class LocalSettingDialog(wx.Dialog):
    def __init__(self, parent, torrentlist):
        
        self.utility = parent.utility
        
        title = self.utility.lang.get('localsetting')
        
        pre = wx.PreDialog()
        pre.Create(parent, -1, title)
        self.this = pre.this
        self.torrentlist = torrentlist

        outerbox = wx.BoxSizer( wx.VERTICAL )
        
        leftrightbox = wx.BoxSizer(wx.HORIZONTAL)
        leftbox = wx.BoxSizer(wx.VERTICAL)
        rightbox = wx.BoxSizer(wx.VERTICAL)
        
        # GUI for local upload setting
        ################################

        # Upload setting
        ########################################
               
        uploadsection_title = wx.StaticBox(self,  -1,  self.utility.lang.get('uploadsetting'))
        uploadsection = wx.StaticBoxSizer(uploadsection_title, wx.VERTICAL)

        self.maxupload = wx.SpinCtrl(self, size = wx.Size(60, -1))
        self.maxupload.SetRange(2, 100)

        maxuploadsbox = wx.BoxSizer(wx.HORIZONTAL)
        maxuploadsbox.Add(wx.StaticText(self, -1,  self.utility.lang.get('maxuploads')), 0, wx.ALIGN_CENTER_VERTICAL)
        maxuploadsbox.Add(self.maxupload, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)

        uploadsection.Add(maxuploadsbox, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        maxuploadratebox = wx.BoxSizer(wx.HORIZONTAL)
        maxuploadratebox.Add(wx.StaticText(self, -1,  self.utility.lang.get('maxuploadrate')), 0, wx.ALIGN_CENTER_VERTICAL)

        self.uploadrate = self.utility.makeNumCtrl(self, 0, integerWidth = 4)
        maxuploadratebox.Add(self.uploadrate, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        maxuploadratebox.Add(wx.StaticText(self, -1,  self.utility.lang.get('KB') + "/" + self.utility.lang.get('l_second')), 0, wx.ALIGN_CENTER_VERTICAL)
        
        uploadsection.Add(maxuploadratebox, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        uploadsection.Add(wx.StaticText(self, -1,  self.utility.lang.get('zeroisauto')), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)

        leftbox.Add( uploadsection, 0, wx.EXPAND|wx.ALL, 5)

        # Download setting
        ########################################
        
        downloadsection_title = wx.StaticBox(self,  -1,  self.utility.lang.get('downloadsetting'))
        downloadsection = wx.StaticBoxSizer(downloadsection_title, wx.VERTICAL)

        maxdownloadratebox = wx.BoxSizer(wx.HORIZONTAL)
        maxdownloadratebox.Add(wx.StaticText(self, -1,  self.utility.lang.get('maxdownloadrate')), 0, wx.ALIGN_CENTER_VERTICAL)

        self.downloadrate = self.utility.makeNumCtrl(self, 0, integerWidth = 4)
        maxdownloadratebox.Add(self.downloadrate, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        maxdownloadratebox.Add(wx.StaticText(self, -1,  self.utility.lang.get('KB') + "/" + self.utility.lang.get('l_second')), 0, wx.ALIGN_CENTER_VERTICAL)
        
        downloadsection.Add(maxdownloadratebox, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        downloadsection.Add(wx.StaticText(self, -1,  self.utility.lang.get('zeroisauto')), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)

        leftbox.Add( downloadsection, 0, wx.EXPAND|wx.ALL, 5)

        # Upload setting for completed file
        ########################################

        continuesection_title = wx.StaticBox(self, -1,  self.utility.lang.get('uploadoptforcompletedfile'))
        continuesection = wx.StaticBoxSizer(continuesection_title, wx.VERTICAL)

        uploadlist = [self.utility.lang.get('unlimitedupload'), self.utility.lang.get('continueuploadfor'), self.utility.lang.get('untilratio')]

        rb1 = wx.RadioButton(self, -1, uploadlist[0], wx.Point(-1,-1), wx.Size(-1, -1), wx.RB_GROUP)
        rb2 = wx.RadioButton(self, -1, uploadlist[1], wx.Point(-1,-1), wx.Size(-1, -1))
        rb3 = wx.RadioButton(self, -1, uploadlist[2], wx.Point(-1,-1), wx.Size(-1, -1))
        self.rb = [rb1, rb2, rb3]
              
        mtimeval = ['30', '45', '60', '75']
        htimeval = []
        for i in range(24):
            htimeval.append(str(i))
            
        self.cbhtime = wx.ComboBox(self, -1, "", wx.Point(-1, -1),                                  
                                  wx.Size(37, -1), htimeval, wx.CB_DROPDOWN|wx.CB_READONLY)
        self.cbmtime = wx.ComboBox(self, -1, "", wx.Point(-1, -1),
                                  wx.Size(37, -1), mtimeval, wx.CB_DROPDOWN|wx.CB_READONLY)

        continuesection.Add(rb1, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        time_sizer = wx.BoxSizer(wx.HORIZONTAL)
        time_sizer.Add(rb2, 0, wx.ALIGN_CENTER_VERTICAL)
        time_sizer.Add(self.cbhtime, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        time_sizer.Add(wx.StaticText(self, -1, self.utility.lang.get('hour')), 0, wx.ALIGN_CENTER_VERTICAL)
        time_sizer.Add(self.cbmtime, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        time_sizer.Add(wx.StaticText(self, -1, self.utility.lang.get('minute')), 0, wx.ALIGN_CENTER_VERTICAL)
        
        continuesection.Add(time_sizer, -1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        ratioval = ['50', '75', '100', '125', '150','175','200', '300', '400', '500']
        self.cbratio = wx.ComboBox(self, -1, "",
                                  wx.Point(-1, -1), wx.Size(45, -1), ratioval, wx.CB_DROPDOWN|wx.CB_READONLY)
       
        percent_sizer = wx.BoxSizer(wx.HORIZONTAL)
        percent_sizer.Add(rb3, 0, wx.ALIGN_CENTER_VERTICAL)
        percent_sizer.Add(self.cbratio, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        percent_sizer.Add(wx.StaticText(self, -1, "%"), 0, wx.ALIGN_CENTER_VERTICAL)
        
        continuesection.Add(percent_sizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        rightbox.Add( continuesection, 0, wx.EXPAND|wx.ALL, 5)
        
        self.timeoutbox = wx.CheckBox(self, -1, self.utility.lang.get('disabletimeout'))
        
        rightbox.Add( self.timeoutbox, 0, wx.EXPAND|wx.ALL, 10)
        
        leftrightbox.Add(leftbox)
        leftrightbox.Add(rightbox)
        outerbox.Add(leftrightbox)

        applybtn  = wx.Button(self, -1, self.utility.lang.get('apply'))
        self.Bind(wx.EVT_BUTTON, self.onApply, applybtn)
        okbtn  = wx.Button(self, -1, self.utility.lang.get('ok'))
        self.Bind(wx.EVT_BUTTON, self.onOK, okbtn)

        cancelbtn = wx.Button(self, wx.ID_CANCEL, self.utility.lang.get('cancel'))

        setDefaultsbtn = wx.Button(self, -1, self.utility.lang.get('reverttodefault'))
        self.Bind(wx.EVT_BUTTON, self.RevertToDefault, setDefaultsbtn)

        buttonbox = wx.BoxSizer( wx.HORIZONTAL )
        buttonbox.Add(applybtn, 0, wx.ALL, 5)
        buttonbox.Add(okbtn, 0, wx.ALL, 5)
        buttonbox.Add(cancelbtn, 0, wx.ALL, 5)
        buttonbox.Add(setDefaultsbtn, 0, wx.ALL, 5)

        outerbox.Add( buttonbox, 0, wx.ALIGN_CENTER)
        
        self.setDefaults()

        self.SetAutoLayout( True )
        self.SetSizer( outerbox )
        self.Fit()

    def RevertToDefault(self, event = None):
        maxupt = int(self.utility.config.Read('maxupload'))
        loc_maxupload       = maxupt
        
        loc_uploadopt       = self.utility.config.Read('uploadoption')
        loc_uploadtimeh     = self.utility.config.Read('uploadtimeh')
        loc_uploadtimem     = self.utility.config.Read('uploadtimem')
        loc_uploadratio     = self.utility.config.Read('uploadratio')

        self.maxupload.SetValue(loc_maxupload)

        self.rb[int(loc_uploadopt)].SetValue(True)

        self.cbratio.SetValue(loc_uploadratio)

        self.cbhtime.SetValue(loc_uploadtimeh)
        self.cbmtime.SetValue(loc_uploadtimem)
        
        loc_maxuploadrate = 0
        self.uploadrate.SetValue(int(loc_maxuploadrate))

        loc_maxdownloadrate = 0
        self.downloadrate.SetValue(int(loc_maxdownloadrate))

        self.timeoutbox.SetValue(0)      
        
    def setDefaults(self, event = None):
        ABCTorrentTemp      = self.torrentlist[0]
        
        loc_uploadopt       = ABCTorrentTemp.connection.getSeedOption('uploadoption')
        self.rb[int(loc_uploadopt)].SetValue(True)

        self.maxupload.SetValue(ABCTorrentTemp.connection.getMaxUpload())

        self.cbratio.SetValue(ABCTorrentTemp.connection.getSeedOption('uploadratio'))

        self.cbhtime.SetValue(ABCTorrentTemp.connection.getSeedOption('uploadtimeh'))
        self.cbmtime.SetValue(ABCTorrentTemp.connection.getSeedOption('uploadtimem'))
        
        self.uploadrate.SetValue(ABCTorrentTemp.connection.getLocalRate('up'))
        self.downloadrate.SetValue(ABCTorrentTemp.connection.getLocalRate('down'))

        self.timeoutbox.SetValue(not ABCTorrentTemp.connection.timeout)
        
    def onApply(self, event = None):
        upload_rate = int(self.uploadrate.GetValue())

        if upload_rate < 3 and upload_rate != 0:
            #display warning
            dlg = wx.MessageDialog(self, self.utility.lang.get('uploadrateminwarningauto')  , self.utility.lang.get('error'), wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        loc_info = {}
        loc_info['maxupload'] = self.maxupload.GetValue()      #maxupload
        loc_info['uploadrate'] = self.uploadrate.GetValue()     #maxuploadrate

        loc_info['downloadrate'] = self.downloadrate.GetValue()     #maxdownloadrate

        for i in range (0, 3):                          #uploadopt
            if self.rb[i].GetValue():
                loc_info['uploadoption'] = str(i)
                break

        loc_info['uploadtimeh'] = self.cbhtime.GetValue()        #uploadtimeh   
        loc_info['uploadtimem'] = self.cbmtime.GetValue()        #uploadtimem   
        loc_info['uploadratio'] = self.cbratio.GetValue()        #uploadratio

        loc_info['timeout'] = not self.timeoutbox.IsChecked()

        for ABCTorrentTemp in self.torrentlist:
            ABCTorrentTemp.connection.changeLocalInfo(loc_info)
        self.utility.queue.updateAndInvoke()

        # Sent new parameter to process
        #################################
        # must change now
        # - maxupload, maxuploadrate, numsimdownload
        # - uploadoption, uploadtimeh, uploadtimem,
        # - uploadratio
        #########################################
        
        return True

    def onOK(self, event = None):
        if self.onApply():
            self.EndModal(wx.ID_OK)
