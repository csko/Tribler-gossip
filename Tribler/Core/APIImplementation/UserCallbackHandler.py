# Written by Arno Bakker 
# see LICENSE.txt for license information

import sys
import os
import shutil
from threading import Thread,currentThread
from traceback import print_exc,print_stack
from Tribler.Core.APIImplementation.ThreadPool import ThreadPool
from Tribler.Core.CacheDB.Notifier import Notifier

DEBUG = False

class UserCallbackHandler:
    
    def __init__(self,sesslock,sessconfig):
        self.sesslock = sesslock
        self.sessconfig = sessconfig

        # Notifier for callbacks to API user
        self.threadpool = ThreadPool(4)
        self.notifier = Notifier.getInstance(self.threadpool)

    def shutdown(self):
        # stop threadpool
        self.threadpool.joinAll()

    def perform_vod_usercallback(self,d,usercallback,mimetype,stream,filename):
        """ Called by network thread """
        if DEBUG:
            print >>sys.stderr,"Session: perform_vod_usercallback()"
        def session_vod_usercallback_target():
            try:
                usercallback(d,mimetype,stream,filename)
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


    def perform_removestate_callback(self,infohash,correctedinfoname,removecontent,dldestdir):
        """ Called by network thread """
        if DEBUG:
            print >>sys.stderr,"Session: perform_removestate_callback()"
        def session_removestate_callback_target():
            if DEBUG:
                print >>sys.stderr,"Session: session_removestate_callback_target called",currentThread().getName()
            try:
                self.sesscb_removestate(infohash,correctedinfoname,removecontent,dldestdir)
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


    def sesscb_removestate(self,infohash,correctedinfoname,removecontent,dldestdir):
        """ Called by SessionCallbackThread """
        if DEBUG:
            print >>sys.stderr,"Session: sesscb_removestate called",`infohash`,`correctedinfoname`,removecontent,dldestdir
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
            filename = os.path.join(dldestdir,correctedinfoname)
            if DEBUG:
                print >>sys.stderr,"Session: sesscb_removestate: removing saved content",filename
            if not os.path.isdir(filename):
                # single-file torrent
                os.remove(filename)
            else:
                # multi-file torrent
                shutil.rmtree(filename,True) # ignore errors

    def notify(self, subject, changeType, obj_id, *args):
        """
        Notify all interested observers about an event with threads from the pool
        """
        self.notifier.notify(subject,changeType,obj_id,*args)
        