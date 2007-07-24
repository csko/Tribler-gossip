# written by Yuan Yuan
# see LICENSE.txt for license information

from threading import Thread, Lock
from traceback import print_exc
from time import sleep, time

from Tribler.TrackerChecking.TrackerChecking import trackerChecking
from Tribler.CacheDB.SynDBHandler import SynTorrentDBHandler
from Tribler.DecentralizedTracking.mainlineDHTChecker import mainlineDHTChecker


class ManualChecking(Thread):
    
    def __init__(self, check_list):
        self.check_list = check_list
        Thread.__init__(self)
        self.setName('ManualChecking-'+self.getName())
        self.setDaemon(True)
        
    def run(self):
        for torrent in self.check_list:
            t = SingleManualChecking(torrent)
            t.setDaemon(True)
            t.start()
            sleep(1)
            
class SingleManualChecking(Thread):
    
    def __init__(self,torrent):
        Thread.__init__(self)
        self.setDaemon(True)
        self.setName('SingleManualChecking-'+self.getName())
        
        self.torrent = torrent
        self.torrent_db = SynTorrentDBHandler()
        self.mldhtchecker = mainlineDHTChecker.getInstance()
        

    def run(self):        
        try:
            trackerChecking(self.torrent)
            # Must come after tracker check, such that if tracker dead and DHT still alive, the
            # status is still set to good
            self.mldhtchecker.lookup(self.torrent['infohash'])
        except:
            print_exc()
        kw = {
            'last_check_time': int(time()),
            'seeder': self.torrent['seeder'],
            'leecher': self.torrent['leecher'],
            'status': self.torrent['status'],
            'info': self.torrent['info']
            }
        self.torrent_db.updateTorrent(self.torrent['infohash'], updateFlag=True, **kw)
