# Written by Vincent Heinink and Rameez Rahman
# see LICENSE.txt for license information
#
#Utilities for moderationcast (including databases)
#
import sys

from Tribler.Core.CacheDB.sqlitecachedb import bin2str, str2bin
#For validity-checks
from types import StringType, ListType, DictType
from time import time
from Tribler.Core.BitTornado.bencode import bencode
from Tribler.Core.Overlay.permid import verify_data
from os.path import exists, isfile
from Tribler.Core.Subtitles.RichMetadataInterceptor import validMetadataEntry


DEBUG = False

TIMESTAMP_IN_FUTURE = 5 * 60    # 5 minutes is okay

#*****************Validity-checks*****************
def validInfohash(infohash):
    """ Returns True iff infohash is a valid infohash """
    r = isinstance(infohash, str) and len(infohash) == 20
    if not r:
        if DEBUG:
            print >>sys.stderr, "Invalid infohash: type(infohash) ==", str(type(infohash))+\
            ", infohash ==", `infohash`
    return r

def validPermid(permid):
    """ Returns True iff permid is a valid Tribler Perm-ID """
    r = type(permid) == str and len(permid) <= 125
    if not r:
        if DEBUG:
            print >>sys.stderr, "Invalid permid: type(permid) ==", str(type(permid))+\
            ", permid ==", `permid`
    return r

def now():
    """ Returns current-system-time in UTC, seconds since the epoch (type==int) """
    return int(time())

def validTimestamp(timestamp):
    """ Returns True iff timestamp is a valid timestamp """
    r = timestamp is not None and type(timestamp) == int and timestamp > 0 and timestamp <= now() + TIMESTAMP_IN_FUTURE
    if not r:
        if DEBUG:
            print >>sys.stderr, "Invalid timestamp"
    return r

def validVoteCastMsg(data):
    """ Returns True if VoteCastMsg is valid, ie, be of type [(mod_id,vote)] """
    if data is None:
        print >> sys.stderr, "data is None"
        return False
     
    if not type(data) == DictType:
        print >> sys.stderr, "data is not Dictionary"
        return False
    
    for key,value in data.items():
        #if DEBUG: 
        #    print >>sys.stderr, "validvotecastmsg: ", repr(record)
        if not validPermid(key):
            if DEBUG:
                print >> sys.stderr, "not valid permid: ", repr(key) 
            return False
        if not ('vote' in value and 'time_stamp' in value):
            if DEBUG:
                print >> sys.stderr, "validVoteCastMsg: key missing, got", value.keys()
            return False
        if not type(value['vote']) == int:
            if DEBUG:
                print >> sys.stderr, "Vote is not int: ", repr(value['vote']) 
            return False
        if not(value['vote']==2 or value['vote']==-1):
            if DEBUG:
                print >> sys.stderr, "Vote is not -1 or 2: ", repr(value['vote']) 
            return False
        if not type(value['time_stamp']) == int:
            if DEBUG:
                print >> sys.stderr, "time_stamp is not int: ", repr(value['time_stamp']) 
            return False    
    return True


def validChannelCastMsg(channelcast_data):
    """ Returns true if ChannelCastMsg is valid,
    format: {'signature':{'publisher_id':, 'publisher_name':, 'infohash':, 'torrenthash':, 'torrent_name':, 'timestamp':, 'signature':}} 
     """
     
        
    if not isinstance(channelcast_data,dict):
        return False
    for signature, ch in channelcast_data.items():
        if not isinstance(ch,dict):
            if DEBUG:
                print >>sys.stderr,"validChannelCastMsg: value not dict"
            return False
        
        # 08-04-2010 We accept both 6 and 7 fields to allow
        # compatibility with messages from older versions 
        # the rich metadata field
        length = len(ch)
        if not 6 <= length <= 7:
            if DEBUG:
                print >>sys.stderr,"validChannelCastMsg: #keys!=7"
            return False
        if not ('publisher_id' in ch and 'publisher_name' in ch and 'infohash' in ch and 'torrenthash' in ch \
                and 'torrentname' in ch and 'time_stamp' in ch):
            if DEBUG:
                print >>sys.stderr,"validChannelCastMsg: key missing"
            return False
        
        if length == 7:
            if 'rich_metadata' not in ch: #enriched Channelcast
                if DEBUG:
                    print >>sys.stderr,"validChannelCastMsg: key missing"
                    return False
            else:
                if not validMetadataEntry(ch['rich_metadata']):
                    print >> sys.stderr, "validChannelCastMsg: invalid rich metadata"
                    return False
                
        
        
        if not (validPermid(ch['publisher_id']) and isinstance(ch['publisher_name'],str) \
                and validInfohash(ch['infohash']) and validInfohash(ch['torrenthash'])
                and isinstance(ch['torrentname'],str) and validTimestamp(ch['time_stamp'])):
            if DEBUG:
                print >>sys.stderr,"validChannelCastMsg: something not valid"
            return False
        # now, verify signature
        # Nitin on Feb 5, 2010: Signature is validated using binary forms of permid, infohash, torrenthash fields
        l = (ch['publisher_id'],ch['infohash'], ch['torrenthash'], ch['time_stamp'])
        if not verify_data(bencode(l),ch['publisher_id'],signature):
            if DEBUG:
                print >>sys.stderr, "validChannelCastMsg: verification failed!"
            return False
    return True
     
#*************************************************

def voteCastMsgToString(data):
    return repr(data)
