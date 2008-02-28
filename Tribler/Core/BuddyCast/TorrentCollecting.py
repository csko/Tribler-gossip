import sys
from Tribler.Core.CacheDB.CacheDBHandler import TorrentDBHandler,MyPreferenceDBHandler
from Tribler.Core.Utilities.utilities import show_permid
from random import randint
from time import time

DEBUG = False
    
class SimpleTorrentCollecting:
    """
        Simplest torrent collecting policy: randomly collect a torrent when received
        a buddycast message
    """
    
    def __init__(self, metadata_handler):
        self.torrent_db = TorrentDBHandler.getInstance()
        self.mypref_db = MyPreferenceDBHandler.getInstance()
        self.metadata_handler = metadata_handler
#        self.cooccurrence = {}
        
#    def updateAllCooccurrence(self):
#        self.cooccurrence = self.mypref_db.getAllTorrentCoccurrence()
        
    def getInfohashRelevance(self, infohash):
        return self.mypref_db.getInfohashRelevance(infohash)
        
    def updatePreferences(self, permid, preferences, selversion=-1):
        # called by overlay thread
        torrent = self.selecteTorrentToCollect(preferences)
        #print >> sys.stderr, '================= updatePreferences', `torrent`
        if torrent and self.metadata_handler:
            self.metadata_handler.send_metadata_request(permid, torrent, selversion)
        return torrent
    
    def closeConnection(self, permid):
        pass
    
    def selecteTorrentToCollect(self, preferences, random=False):
        preferences = list(preferences)
        candidates = []
        for torrent in preferences:
            if not self.torrent_db.hasMetaData(torrent):    # check if the torrent has been downloaded
                candidates.append(torrent)
                
        if not candidates:
            return None
        
        if not random:
            relevances = []
            for infohash in candidates:
                rel = self.getInfohashRelevance(infohash)
                relevances.append(rel)
            idx = relevances.index(max(relevances))
            return candidates[idx]
        else:
            idx = randint(0, len(candidates)-1)
            selected = candidates[idx]
            return selected
    

