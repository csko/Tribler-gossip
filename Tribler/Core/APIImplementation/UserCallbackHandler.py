# Written by Arno Bakker 
# see LICENSE.txt for license information

import sys
import os
import shutil
import binascii
from threading import Thread,currentThread
from traceback import print_exc,print_stack

from Tribler.Core.simpledefs import *
from Tribler.Core.APIImplementation.ThreadPool import ThreadPool
from Tribler.Core.CacheDB.Notifier import Notifier

DEBUG = False

class UserCallbackHandler:
    
    def __init__(self,session):
        self.session = session
        self.sesslock = session.sesslock
        self.sessconfig = session.sessconfig

        # Notifier for callbacks to API user
        self.threadpool = ThreadPool(2)
        self.notifier = Notifier.getInstance(self.threadpool)

    def shutdown(self):
        # stop threadpool
        self.threadpool.joinAll()

    def perform_vod_usercallback(self,d,usercallback,event,params):
        """ Called by network thread """
        if DEBUG:
            print >>sys.stderr,"Session: perform_vod_usercallback()",`d.get_def().get_name_as_unicode()`
        def session_vod_usercallback_target():
            try:
                usercallback(d,event,params)
            except:
                print_exc()
        self.perform_usercallback(session_vod_usercallback_target)

    def perform_getstate_usercallback(self,usercallback,data,returncallback):
        """ Called by network thread """
        if DEBUG:
            print >>sys.stderr,"Session: perform_getstate_usercallback()"
        def session_getstate_usercallback_target():
            try:
                (when,getpeerlist) = usercallback(data)
                returncallback(usercallback,when,getpeerlist)
            except:
                print_exc()
        self.perform_usercallback(session_getstate_usercallback_target)


    def perform_removestate_callback(self,infohash,contentdest,removecontent):
        """ Called by network thread """
        if DEBUG:
            print >>sys.stderr,"Session: perform_removestate_callback()"
        def session_removestate_callback_target():
            if DEBUG:
                print >>sys.stderr,"Session: session_removestate_callback_target called",currentThread().getName()
            try:
                self.sesscb_removestate(infohash,contentdest,removecontent)
            except:
                print_exc()
        self.perform_usercallback(session_removestate_callback_target)
        
    def perform_usercallback(self,target):
        self.sesslock.acquire()
        try:
            # TODO: thread pool, etc.
            self.threadpool.queueTask(target)
            
        finally:
            self.sesslock.release()

    def sesscb_removestate(self,infohash,contentdest,removecontent):
        """  See DownloadImpl.setup().
        Called by SessionCallbackThread """
        if DEBUG:
            print >>sys.stderr,"Session: sesscb_removestate called",`infohash`,`contentdest`,removecontent
        self.sesslock.acquire()
        try:
            dlpstatedir = os.path.join(self.sessconfig['state_dir'],STATEDIR_DLPSTATE_DIR)
            trackerdir = os.path.join(self.sessconfig['state_dir'],STATEDIR_ITRACKER_DIR)
        finally:
            self.sesslock.release()

        # See if torrent uses internal tracker
        try:
            self.session.remove_from_internal_tracker_by_infohash(infohash)
        except:
            # Show must go on
            print_exc()

        # Remove checkpoint
        hexinfohash = binascii.hexlify(infohash)
        try:
            basename = hexinfohash+'.pickle'
            filename = os.path.join(dlpstatedir,basename)
            if DEBUG:
                print >>sys.stderr,"Session: sesscb_removestate: removing dlcheckpoint entry",filename
            if os.access(filename,os.F_OK):
                os.remove(filename)
        except:
            # Show must go on
            print_exc()

        # Remove downloaded content from disk
        if removecontent:
            if DEBUG:
                print >>sys.stderr,"Session: sesscb_removestate: removing saved content",contentdest
            if not os.path.isdir(contentdest):
                # single-file torrent
                os.remove(contentdest)
            else:
                # multi-file torrent
                shutil.rmtree(contentdest,True) # ignore errors


    def notify(self, subject, changeType, obj_id, *args):
        """
        Notify all interested observers about an event with threads from the pool
        """
        if DEBUG:
            print >>sys.stderr,"ucb: notify called:",subject,changeType,`obj_id`, args
        self.notifier.notify(subject,changeType,obj_id,*args)
        
        
