from Tribler.TrackerChecking.TorrentChecking import TorrentChecking
from time import sleep
from Tribler.CacheDB.CacheDBHandler import TorrentDBHandler
from Tribler.TrackerChecking.TrackerChecking import trackerChecking




def run():
    print "start run"
#    torrent_db = TorrentDBHandler()
#    key = ['infohash', 'torrent_name', 'torrent_dir', 'relevance', 'info', 
#                'num_owners', 'leecher', 'seeder', 'category']
#    data = torrent_db.getRecommendedTorrents(key)
#
#    for idata in data[54:100]:
#        trackerChecking(idata)
    for x in range(1000):        
        t = TorrentChecking()
        t.start()
        sleep(2)

