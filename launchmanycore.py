#!/usr/bin/env python

# Written by John Hoffman and Arno Bakker
# see LICENSE.txt for license information

from BitTornado import PSYCO
if PSYCO.psyco:
    try:
        import psyco
        assert psyco.__version__ >= 0x010100f0
        psyco.full()
    except:
        pass

import sys
import gc
import os

from random import seed
from socket import error as socketerror
from threading import Event, Thread, currentThread
from cStringIO import StringIO
from traceback import print_exc, print_stack
from tempfile import gettempdir

from BitTornado.launchmanycore import LaunchMany
from BitTornado.bencode import bencode
from BitTornado.__init__ import createPeerID, mapbase64
from Utility.constants import * #IGNORE:W0611
from safeguiupdate import DelayedEventHandler

from abcengine import ABCEngine

try:
    True
except:
    True = 1
    False = 0

DEBUG = False

def fmttime(n):
    try:
        n = int(n)  # n may be None or too large
        assert n < 5184000  # 60 days
    except:
        return 'downloading'
    m, s = divmod(n, 60)
    h, m = divmod(m, 60)
    return '%d:%02d:%02d' % (h, m, s)

#
# Try to do everything in BitTornado.LaunchMany such that the command-line
# tools also work.
#
class ABCLaunchMany(Thread,LaunchMany,DelayedEventHandler):
    def __init__(self, utility):
        self.utility = utility        
        self.output = Outputter()

        btconfig = utility.getBTParams()
        # Create dir for helper to put torrents and files in.
        #
        # CAREFUL: Sometimes there are problems when attempting to save 
        # downloads to a NFS filesystem, so make sure torrent_dir is on
        # a local disk.
        destdir = None
        if self.utility.config.Read('setdefaultfolder') == 1:
            destdir = self.utility.config.Read('defaultfolder')
        if destdir is None:
            destdir = gettempdir()

        torrent_dir = os.path.join( destdir, 'torrenthelping' )
        btconfig['torrent_dir'] = torrent_dir
        if not os.access(torrent_dir,os.F_OK):
            os.mkdir(torrent_dir)

        btconfig['parse_dir_interval'] = None # No parsing done at the moment
        btconfig['saveas_style'] = 1 # must be 1 for security during download helping
	btconfig['2fastbtlog'] = os.path.join(self.utility.getConfigPath(), "2fastbt.log")

        # Enable/disable features
        btconfig['buddycast'] = int(self.utility.config.Read('enablerecommender'))
        btconfig['download_help'] = int(self.utility.config.Read('enabledlhelp'))
        btconfig['torrent_collecting'] = int(self.utility.config.Read('enabledlcollecting'))

        # btconfig must be set before calling LaunchMany constructor
        Thread.__init__(self)
        LaunchMany.__init__(self,btconfig,self.output)
        DelayedEventHandler.__init__(self)
        
        # set by BitTornado.LaunchMany constructor
        self.utility.listen_port = self.listen_port

        self.setName( "ABCLaunchMany"+self.getName() )
    
    # override
    def go(self):
        pass

    def run(self):
        try:
            self.handler.listen_forever()
        except AssertionError:
            print >> sys.stderr,"launchmany: Exception in main loop"
            print_exc()
        except Exception,e:
            print >> sys.stderr,"launchmany: Exception in main loop",str(e)
            print_exc()
            data = StringIO()
            print_exc(file=data)
            self.output.exception(data.getvalue())
        

        for ABCTorrentTemp in self.utility.torrents["active"].keys():
            ABCTorrentTemp.shutdown()

        self.rawserver.shutdown()

    def stop(self):
        self.doneflag.set()

    # override
    def stats(self):
        for ABCTorrentTemp in self.utility.torrents["active"].keys():
            engine = ABCTorrentTemp.connection.engine
            
            if engine is None:
                continue
            
            progress = 0.0
            t = 0
            uprate = 0.0
            dnrate = 0.0
            spew = None
            s = None
            
            if engine.is_dead():
                status = self.utility.lang.get('stop')
            elif engine.waiting:
                status = self.utility.lang.get('waiting')
            elif engine.checking:
                status = engine.btstatus
                progress = engine.status_done
            else:
                stats = engine.statsfunc()    # call DownloaderFeedback.gather() actually
                
                s = stats['stats']
                spew = stats['spew']
                if engine.seed:
                    status = self.utility.lang.get('completedseeding')
                    progress = 1.0
                else:
                    if s.numSeeds + s.numPeers:
                        t = stats['time']
                        if t == 0:  # unlikely
                            t = 0.01
                        status = self.utility.lang.get('working')
                    else:
                        t = -1
                        status = self.utility.lang.get('connectingtopeers')
                    dnrate = stats['down']
                    progress = stats['frac']
                uprate = stats['up']
                #self.all_peers_cache.updateSpew(ABCTorrentTemp.torrent_hash, spew)

            engine.onUpdateStatus(progress, t, dnrate, uprate, status, s, spew)
        self.rawserver.add_task(self.stats, self.stats_period)


    def remove(self,torrent_hash):
        # Arno: at the moment I just stop the torrent, as removal from GUI list 
        # is rather complex (need to update the list shown to the user, who may 
        # just be editing it)

        # St*pid ABC code uses string with hex representation as infohash
        hexhash = "".join([hex(ord(x))[2:].zfill(2)for x in tuple(torrent_hash)])
        ABCTorrentTemp = self.utility.queue.getABCTorrent(-1,hexhash)

        if ABCTorrentTemp is None:
            if DEBUG:
                print >> sys.stderr,"launchmany: STOP_DOWNLOAD_HELP could not find torrent!"

        if ABCTorrentTemp is not None:
            if DEBUG:
                print >> sys.stderr,"launchmany: STOP_DOWNLOAD_HELP stopping torrent (postponed)"
            self.invokeLater(self.remove_callback,[ABCTorrentTemp])            

    def remove_callback(self,ABCTorrentTemp):
        if DEBUG:
            print >> sys.stderr,"launchmany: STOP_DOWNLOAD_HELP actually stopping torrent"
        #msg = self.utility.lang.get('helping_stopped')
        #ABCTorrentTemp.changeMessage( msg, "status")
        self.utility.actionhandler.procREMOVE([ABCTorrentTemp], removefiles = True)

    def add(self, hash, data):
        """ called by Tribler/toofastbt/HelperMessageHandler """
        if DEBUG:
            print >> sys.stderr,"launchmany: Adding torrent (postponed)"
        self.invokeLater(self.add_callback,[hash,data])

    # Make sure this is called by the MainThread, as it does GUI updates
    def add_callback(self, hash, data):
        if DEBUG:
            print >> sys.stderr,"launchmany: actually Adding torrent"
        self.utility.queue.addtorrents.AddTorrentFromFile(data['path'], caller = "helper", dest = data['dest'], caller_data = data)

        
    # polymorph/override
    def addDownload(self, ABCTorrentTemp):
        if DEBUG:
            print >> sys.stderr,"launchmany: addDownload",currentThread().getName()

        c = self.counter
        self.counter += 1
        x = ''
        for i in xrange(3):
            x = mapbase64[c & 0x3F]+x
            c >>= 6
        peer_id = createPeerID(x)
        engine = ABCEngine(ABCTorrentTemp, peer_id)
        ABCTorrentTemp.connection.engine = engine
        self.utility.torrents["active"][ABCTorrentTemp] = 1

        # To get coordinators and helpers
        self.downloads[ABCTorrentTemp.torrent_hash] = engine.dow

        engine.start()

    # override
    def hashchecksched(self, ABCTorrentTemp = None):
        if ABCTorrentTemp:
            self.hashcheck_queue.append(ABCTorrentTemp)

        # Sort by filesize (smallest should start first)
        
        self.hashcheck_queue.sort(lambda x, y: cmp(x.connection.engine.dow.datalength, y.connection.engine.dow.datalength))
#        self.hashcheck_queue.sort(key = lambda x: x.getColumnValue(COL_SIZE, -1.0))
        
        if not self.hashcheck_current:
            self._hashcheck_start()

    # override
    def _hashcheck_start(self):
        self.hashcheck_current = self.hashcheck_queue.pop(0)
        engine = self.hashcheck_current.connection.engine
        engine.hashcheck_start(self.hashcheck_callback)

    # override
    def hashcheck_callback(self):
        try:
            current = self.hashcheck_current.connection.engine
        except:
            current = None
            
        if current is not None:
            current.hashcheck_callback()
        if self.hashcheck_queue:
            self._hashcheck_start()
        else:
            self.hashcheck_current = None
        
    # polymorph/override
    def was_stopped(self, ABCTorrentTemp):
        try:
            self.hashcheck_queue.remove(ABCTorrentTemp)
        except:
            pass
        if self.hashcheck_current == ABCTorrentTemp:
            self.hashcheck_current = None
            if self.hashcheck_queue:
                self._hashcheck_start()

        ABCTorrentTemp.connection.engine = None

        self.invokeLater(self.make_inactive_callback,[ABCTorrentTemp])

    def make_inactive_callback(self,ABCTorrentTemp):
        # This touches the GUI, so delegate it.
        ABCTorrentTemp.makeInactive()
        
        # Run the garbage collector to
        # clean up cyclical references
        # (may be left behind when active torrents end)
        gc.collect()

    def dying_engines_errormsg(self,ABCTorrentTemp,msg,label):
        self.invokeLater(self.dying_engines_errormsg_callback,[ABCTorrentTemp,msg,label])

    def dying_engines_errormsg_callback(self,ABCTorrentTemp,msg,label):
        ABCTorrentTemp.changeMessage(msg, label)

class Outputter:
    def __init__(self):
        pass
        
    def exception(self, message):
        sys.stderr.write(message)
    
    def message(self, message):
        message = "-----------------------\n" + message + "\n-----------------------\n"
        sys.stderr.write(message)
