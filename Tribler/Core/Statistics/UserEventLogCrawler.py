# Written by Boudewijn Schoon
# Modified by Niels Zeilemaker
# see LICENSE.txt for license information

import sys
# import cPickle
from time import strftime

from Tribler.Core.Overlay.SecureOverlay import OLPROTO_VER_FIFTEENTH

from Tribler.Core.BitTornado.BT1.MessageID import CRAWLER_USEREVENTLOG_QUERY
from Tribler.Core.CacheDB.sqlitecachedb import SQLiteCacheDB
from Tribler.Core.Utilities.utilities import show_permid, show_permid_short
from Tribler.Core.Statistics.Crawler import Crawler
from Tribler.Core.dispersy.encoding import encode

DEBUG = False

class UserEventLogCrawler:
    __single = None

    @classmethod
    def get_instance(cls, *args, **kargs):
        if not cls.__single:
            cls.__single = cls(*args, **kargs)
        return cls.__single

    def __init__(self):
        self._sqlite_cache_db = SQLiteCacheDB.getInstance()

        crawler = Crawler.get_instance()
        if crawler.am_crawler():
            msg = "# Crawler started" 
            self.__log(msg)

    def query_initiator(self, permid, selversion, request_callback):
        """
        Established a new connection. Send a CRAWLER_USEREVENTLOG_QUERY request.
        @param permid The Tribler peer permid
        @param selversion The oberlay protocol version
        @param request_callback Call this function one or more times to send the requests: request_callback(message_id, payload)
        """
        if DEBUG: print >>sys.stderr, "usereventlogcrawler: query_initiator", show_permid_short(permid)

        if selversion >= OLPROTO_VER_FIFTEENTH:
            sql = "SELECT * FROM UserEventLog; DELETE FROM UserEventLog;"
            request_callback(CRAWLER_USEREVENTLOG_QUERY, sql, callback=self._after_request_callback)

    def _after_request_callback(self, exc, permid):
        """
        Called by the Crawler with the result of the request_callback
        call in the query_initiator method.
        """
        if not exc:
            if DEBUG: print >>sys.stderr, "usereventlogcrawler: request send to", show_permid_short(permid)
            
            msg = "; ".join(['REQUEST', show_permid(permid)])
            self.__log(msg)

    def handle_crawler_request(self, permid, selversion, channel_id, message, reply_callback):
        """
        Received a CRAWLER_USEREVENTLOG_QUERY request.
        @param permid The Crawler permid
        @param selversion The overlay protocol version
        @param channel_id Identifies a CRAWLER_REQUEST/CRAWLER_REPLY pair
        @param message The message payload
        @param reply_callback Call this function once to send the reply: reply_callback(payload [, error=123])
        """
        if DEBUG:
            print >> sys.stderr, "usereventlogcrawler: handle_crawler_request", show_permid_short(permid), message

        # execute the sql
        try:
            #has to be execute_read, delete statements are also allowed in this function
            cursor = self._sqlite_cache_db.execute_read(message)

        except Exception, e:
            reply_callback(str(e), error=1)
        else:
            if cursor:
                reply_callback(encode(list(cursor)))
                # reply_callback(cPickle.dumps(list(cursor), 2))
            else:
                reply_callback("error", error=2)

    def handle_crawler_reply(self, permid, selversion, channel_id, channel_data, error, message, request_callback):
        """
        Received a CRAWLER_USEREVENTLOG_QUERY reply.
        @param permid The Crawler permid
        @param selversion The overlay protocol version
        @param channel_id Identifies a CRAWLER_REQUEST/CRAWLER_REPLY pair
        @param error The error value. 0 indicates success.
        @param message The message payload
        @param request_callback Call this function one or more times to send the requests: request_callback(message_id, payload)
        """
        if error:
            if DEBUG:
                print >> sys.stderr, "usereventlogcrawler: handle_crawler_reply", error, message
                
            msg = "; ".join(['REPLY', show_permid(permid), str(error), str(message)])
            self.__log(msg)
        else:
            if DEBUG:
                print >> sys.stderr, "usereventlogcrawler: handle_crawler_reply", show_permid_short(permid), len(message), "bytes"
                
            # 24/06/11 boudewijn: we are storing the received message in HEX format.  unfortunately
            # this will make it unreadable in the text file, however, it will protect against pickle
            # security issues while still being compatible with both the secure (encode) and the
            # unsecure (pickle) crawlers on the client side.  when parsing the logs care needs to be
            # taken when parsing the pickled data!
            msg = "; ".join(['REPLY', show_permid(permid), str(error), message.encode("HEX")])
            self.__log(msg)
            
    def __log(self, message):
        file = open("usereventlogcrawler"+strftime("%Y-%m-%d")+".txt", "a")
        print >> file, strftime("%Y/%m/%d %H:%M:%S"), message 
        file.close()
