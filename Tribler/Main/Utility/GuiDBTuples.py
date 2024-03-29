#Niels: getValidArgs based on http://stackoverflow.com/questions/196960/can-you-list-the-keyword-arguments-a-python-function-receives
import sys
import os.path
from datetime import date
from inspect import getargspec
from Tribler.Video.utils import videoextdefaults
from Tribler.Main.vwxGUI import VLC_SUPPORTED_SUBTITLES, PLAYLIST_REQ_COLUMNS,\
    CHANNEL_REQ_COLUMNS
from Tribler.Core.simpledefs import DLSTATUS_DOWNLOADING, DLSTATUS_STOPPED,\
    DLSTATUS_SEEDING, DLSTATUS_REPEXING, DLSTATUS_HASHCHECKING,\
    DLSTATUS_WAITING4HASHCHECK
from Tribler.Main.vwxGUI.IconsManager import data2wxBitmap, IconsManager, SMALL_ICON_MAX_DIM
from Tribler.community.channel.community import ChannelCommunity
from Tribler.Core.Search.SearchManager import split_into_keywords

def getValidArgs(func, argsDict):
    args, _, _, defaults = getargspec(func)
    try:
        args.remove('self')
    except:
        pass
    
    argsDict = dict((key, value) for key, value in argsDict.iteritems() if key in args)
    if defaults:
        args = args[:-len(defaults)]
        
    notOk = set(args).difference(argsDict)
    if notOk:
        print >> sys.stderr, "Missing",notOk,"arguments for",func 
    return argsDict

#Niels: from http://wiki.python.org/moin/PythonDecoratorLibrary#Memoize

def cache(func):
    def _get(self):
        key = func.__name__
        try:
            return self._cache[key]
        except AttributeError:
            self._cache = {}
            x = self._cache[key] = func(self)
            return x
        except KeyError:
            x = self._cache[key] = func(self)
            return x
    return _get

def cacheProperty(func):
    
    def _get(self):
        key = func.__name__
        try:
            return self._cache[key]
        
        except AttributeError:
            self._cache = {}
            x = self._cache[key] = func(self)
            return x
        
        except KeyError:
            x = self._cache[key] = func(self)
            return x
        return func(self)
    
    def _del(self):
        key = func.__name__
        try:
            del self._cache[key]
        except:
            pass
    return property(_get, None, _del)

class Helper(object):
    __slots__ = ('_cache')
    def get(self, key, default = None):
        return getattr(self, key, default)
    
    def __contains__(self, key):
        return key in self.__slots__
    
    def __eq__(self, other):
        if other:
            return self.id == other.id
        return False
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __getstate__(self):
        statedict = {}
        for key in self.__slots__:
            statedict[key] = getattr(self, key, None)
        return statedict
    
    def __setstate__(self, statedict):
        for key, value in statedict.iteritems():
            setattr(self, key, value)

class Torrent(Helper):
    __slots__ = ('_torrent_id', 'infohash', 'name', 'length', 'category_id', 'status_id', 'num_seeders', 'num_leechers' ,'_channel', 'channeltorrents_id', 'torrent_db', 'channelcast_db', 'ds', 'progress', 'relevance_score', 'query_permids')
    def __init__(self, torrent_id, infohash, name, length, category_id, status_id, num_seeders, num_leechers, channel):
        self._torrent_id = torrent_id
        self.infohash = infohash
        self.name = name
        self.length = length or 0
        self.category_id = category_id
        self.status_id = status_id
        
        self.num_seeders = num_seeders or 0
        self.num_leechers = num_leechers or 0
        
        self._channel = channel
        
        self.channeltorrents_id = None
        self.torrent_db = None
        self.channelcast_db = None
        self.ds = None
        self.relevance_score = None
        self.query_permids = None
   
    @cacheProperty
    def categories(self):
        if self.category_id:
            return [self.torrent_db.id2category[self.category_id]]
    
    @cacheProperty
    def status(self):
        if self.status_id:
            return self.torrent_db.id2status[self.status_id]
    
    @cacheProperty
    def torrent_id(self):
        if not self._torrent_id:
            self._torrent_id = self.torrent_db.getTorrentID(self.infohash)
        return self._torrent_id
    
    @cacheProperty
    def channel(self):
        if self._channel is not None:
            return self._channel
        
        channel = self.channelcast_db.getMostPopularChannelFromTorrent(self.infohash)
        if channel:
            self.channeltorrents_id = channel[-1]
            return Channel(*channel[:-1])
        return False
    
    def updateChannel(self, c):
        self._channel = c
        try:
            del self._cache['channel']
        except:
            pass
    
    def hasChannel(self):
        return self.channel
    
    @property
    def state(self):
        stateList = []
        if self.ds:
            status = self.ds.get_status()
            if status in [DLSTATUS_STOPPED, DLSTATUS_REPEXING]:
                stateList.append('stopped')
                
            if status in [DLSTATUS_DOWNLOADING, DLSTATUS_SEEDING]:
                stateList.append('active')
            
            if status in [DLSTATUS_HASHCHECKING, DLSTATUS_WAITING4HASHCHECK]:
                stateList.append('checking')
                
            if status == DLSTATUS_SEEDING:
                stateList.append('seeding')
            
            if status == DLSTATUS_DOWNLOADING:
                stateList.append('downloading')
            
            if self.ds.progress == 1.0:
                stateList.append('completed')
            
        return stateList
    
    def assignRelevance(self, matches):
        """
        Assigns a relevance score to this Torrent.
        @param matches A dict containing sets stored under the keys 'swarmname', 'filenames' and 'fileextensions'.
        """
        
        # Find the lowest term position of the matching keywords 
        pos_score = None
        if matches['swarmname']:
            swarmnameTerms = split_into_keywords(self.name)
            swarmnameMatches = matches['swarmname']
            
            for i, term in enumerate(swarmnameTerms):
                if term in swarmnameMatches:
                    pos_score = -i
                    break
        
        self.relevance_score = [len(matches['swarmname']), pos_score, len(matches['filenames']), len(matches['fileextensions']), 0]
            
    def __eq__(self, other):
        if other and isinstance(other, Torrent):
            return self.infohash == other.infohash
        return False
    
    def __str__(self):
        return self.name
    
    #Required for drag and drop
    def __getstate__(self):
        statedict = {}
        for key in Torrent.__slots__:
            if key not in ['ds', 'channelcast_db', 'torrent_db']:
                statedict[key] = getattr(self, key, None)
        return statedict
    
class RemoteTorrent(Torrent):
    __slots__ = ()
    def __init__(self, torrent_id, infohash, name, length = 0, category_id = None, status_id = None, num_seeders = 0, num_leechers = 0, query_permids = set(), channel = False):
        Torrent.__init__(self, torrent_id, infohash, name, length, category_id, status_id, num_seeders, num_leechers, channel)
        self.query_permids = query_permids

class CollectedTorrent(Helper):
    __slots__ = ('comment', 'trackers', 'creation_date', 'files', 'last_check', 'torrent')
    def __init__(self, torrent, torrentdef):
        assert isinstance(torrent, Torrent)
        
        self.torrent = torrent
        
        self.comment = torrentdef.get_comment_as_unicode()
        self.trackers = torrentdef.get_trackers_as_single_tuple()
        self.creation_date = torrentdef.get_creation_date()
        self.files = torrentdef.get_files_as_unicode_with_length()
        self.last_check = -1

    def __getattr__(self, name):
        return getattr(self.torrent, name)
    
    def __setattr__(self, name, value):
        try:
            Helper.__setattr__(self, name, value)
        except:
            setattr(self.torrent, name, value)
            
    def __delattr__(self, name):
        try:
            Helper.__delattr__(self, name)
        except:
            delattr(self.torrent,name)
    
    def __contains__(self, key):
        if key in self.__slots__:
            return True
        return key in self.torrent
    
    @cacheProperty
    def swarminfo(self):
        swarminfo = self.torrent_db.getSwarmInfo(self.torrent_id)
        
        if swarminfo:
            self.torrent.num_seeders = swarminfo[1] or 0
            self.torrent.num_leechers = swarminfo[2] or 0
            self.last_check = swarminfo[3] or -1
        return swarminfo
    
    @cacheProperty
    def videofiles(self):
        videofiles = []
        for filename, _ in self.files:
            _, ext = os.path.splitext(filename)
            if ext.startswith('.'):
                ext = ext[1:] 
            
            if ext in videoextdefaults:
                videofiles.append(filename)
        return videofiles
    
    @cacheProperty
    def largestvideofile(self):
        if len(self.videofiles) > 0:
            _, filename = max([(size, filename) for filename, size in self.files if filename in self.videofiles])
            return filename
    
    @cacheProperty
    def subtitlefiles(self):
        subtitles = []
        for filename, length in self.files:
            prefix, ext = os.path.splitext(filename)
            if not ext.startswith('.'):
                ext = '.'+ext
            if ext in VLC_SUPPORTED_SUBTITLES:
                subtitles.append(filename)
        return subtitles
    
    @cache
    def isPlayable(self):
        return len(self.videofiles) > 0
    
    def formatCreationDate(self, format = '%Y-%m-%d'):
        if self.creation_date > 0:
            return date.fromtimestamp(self.creation_date).strftime(format)
        return 'Unknown'
    
class NotCollectedTorrent(CollectedTorrent):
    __slots__ = ()
    def __init__(self, torrent, files, trackers):
        assert isinstance(torrent, Torrent)
        
        self.torrent = torrent
        self.comment = None
        self.trackers = trackers
        self.creation_date = -1
        self.files = files
        self.last_check = -1
        
class LibraryTorrent(Torrent):
    __slots__ = ()
    def __init__(self, torrent_id, infohash, name, length, category_id, status_id, num_seeders, num_leechers, progress):
        Torrent.__init__(self, torrent_id, infohash, name, length, category_id, status_id, num_seeders, num_leechers, None)
        if progress > 1:
            progress = progress / 100.0
            
        self.progress = progress
    
class ChannelTorrent(Torrent):
    __slots__ = ('channeltorrent_id', 'dispersy_id', 'colt_name', 'chant_name', 'description', 'time_stamp', 'inserted', 'playlist')
    def __init__(self, torrent_id, infohash, name, length, category_id, status_id, num_seeders, num_leechers, channeltorrent_id, dispersy_id, chant_name, colt_name, description, time_stamp, inserted, channel, playlist):
        Torrent.__init__(self, torrent_id, infohash, name, length, category_id, status_id, num_seeders, num_leechers, channel)
        
        self.channeltorrent_id = channeltorrent_id
        self.dispersy_id = dispersy_id
        self.colt_name = colt_name
        self.chant_name = chant_name
        self.description = description
        self.time_stamp = time_stamp
        self.inserted = inserted
        self.playlist = playlist
        
    # @property
    def __get_name(self):
        return self.chant_name or self.colt_name
    # @property
    def __set_name(self, name):
        pass
    # .setter was introduced in Python 2.6
    name = property(__get_name, __set_name)
    
    @cacheProperty
    def getPlaylist(self):
        playlist = self.channelcast_db.getPlaylistForTorrent(self.channeltorrent_id, PLAYLIST_REQ_COLUMNS)
        if playlist:
            return Playlist(*playlist+(self.channel,))
    
    #Required for drag and drop
    def __getstate__(self):
        statedict = Torrent.__getstate__(self)
        for key in self.__slots__:
            statedict[key] = getattr(self, key, None)
        return statedict
    
class RemoteChannelTorrent(ChannelTorrent):
    __slots__ = ()
    def __init__(self, torrent_id, infohash, name, length = 0, category_id = None, status_id = None, num_seeders = 0, num_leechers = 0, channel = False, query_permids = set()):
        ChannelTorrent.__init__(self, torrent_id, infohash, name, length, category_id, status_id, num_seeders, num_leechers, -1, '-1', '', name, '', None, None, channel, None)
        self.query_permids = query_permids

    
class Channel(Helper):
    __slots__ = ('id', 'dispersy_cid', 'name', 'description', 'nr_torrents', 'nr_favorites', 'nr_spam', 'my_vote', 'modified', 'my_channel', 'torrents')
    def __init__(self, id, dispersy_cid, name, description, nr_torrents, nr_favorites, nr_spam, my_vote, modified, my_channel):
        self.id = id
        self.dispersy_cid = str(dispersy_cid)
        
        self.name = name[:40]
        self.description = description[:1024]
        
        self.nr_torrents = nr_torrents
        self.nr_favorites = nr_favorites or 0
        self.nr_spam = nr_spam or 0
        self.my_vote = my_vote
        self.modified = modified
        self.my_channel = my_channel
        self.torrents = None
    
    def isDispersy(self):
        return len(self.dispersy_cid) == 20
    
    def isFavorite(self):
        return self.my_vote == 2
    
    def isSpam(self):
        return self.my_vote == -1
    
    def isMyChannel(self):
        return self.my_channel
    
    def isEmpty(self):
        return self.nr_torrents == 0
    
    def isOpen(self):
        state, myChannel = self.getState()
        return state >= ChannelCommunity.CHANNEL_OPEN
    
    def isSemiOpen(self):
        state, myChannel = self.getState()
        return state >= ChannelCommunity.CHANNEL_SEMI_OPEN
    
    @cache
    def getState(self):
        if self.isDispersy():
            from Tribler.Main.vwxGUI.SearchGridManager import ChannelManager
            
            searchManager = ChannelManager.getInstance()
            result = searchManager.getChannelStateByCID(self.dispersy_cid)
            if result:
                return result 
        
        return ChannelCommunity.CHANNEL_CLOSED, self.isMyChannel()
    
    def refreshState(self):
        try:
            del self._cache['getState']
        except:
            pass
        return self.getState()

    def addTorrent(self, torrent):
        if not self.torrents:
            self.torrents = set()
        self.torrents.add(torrent)
        
    def getTorrent(self, infohash):
        if self.torrents:
            for torrent in self.torrents:
                if torrent.infohash == infohash:
                    return torrent
                
    def __eq__(self, other):
        if other:
            if isinstance(other, Channel):
                return self.id == other.id
            if isinstance(other, int):
                return self.id == other
        return False
    
    def __str__(self):
        return 'Channel name=%s\nid=%d\ndispersy_cid=%s'%(self.name.encode('utf8'), self.id, self.dispersy_cid.encode("HEX"))

class RemoteChannel(Channel):
    __slots__ = ('permid')
    def __init__(self, permid, name):
        Channel.__init__(self, 0, '-1', name, '', 0, 0, 0, 0, 0, False)
        self.permid = permid
        
class Comment(Helper):
    __slots__ = ('id', 'dispersy_id', 'channeltorrent_id', '_name', 'peer_id', 'comment', 'reply_to_id', 'replies', 'inserted', 'time_stamp', 'playlist', '_torrent', 'channel', 'get_nickname', 'get_mugshot')
    def __init__(self, id, dispersy_id, channeltorrent_id, name, peer_id, comment, reply_to_id, inserted, time_stamp, channel, playlist, torrent):
        self.id = id
        self.dispersy_id = dispersy_id
        self.channeltorrent_id = channeltorrent_id
        
        self._name = name
        self.peer_id = peer_id
        self.comment = comment
        self.reply_to_id = reply_to_id
        self.replies = []
        self.inserted = inserted
        self.time_stamp = time_stamp
        
        self.playlist = playlist
        self._torrent = torrent
        self.channel = channel
        
    @cacheProperty
    def name(self):
        if self.peer_id == None:
            return self.get_nickname()
        if not self._name:
            return 'Peer %d'%self.peer_id
        return self._name
    
    def isMyComment(self):
        return self.peer_id == None
    
    @cacheProperty
    def avantar(self):
        im = IconsManager.getInstance()
        
        if self.peer_id == None:
            mime, data = self.get_mugshot()
            if data:
                data = data2wxBitmap(mime, data, SMALL_ICON_MAX_DIM)
        else:
            data = im.load_wxBitmapByPeerId(self.peer_id, SMALL_ICON_MAX_DIM)

        if data is None:
            data = im.get_default('PEER_THUMB',SMALL_ICON_MAX_DIM)
        return data
    
    @cacheProperty
    def torrent(self):
        if self._torrent is not None:
            return self._torrent
        
        if self.channeltorrent_id:
            from Tribler.Main.vwxGUI.SearchGridManager import ChannelManager
            
            searchManager = ChannelManager.getInstance()
            return searchManager.getTorrentFromChannelTorrentId(self.channel, self.channeltorrent_id)
    
class Playlist(Helper):
    __slots__ = ('id', 'dispersy_id', 'channel_id', 'name', 'description', 'nr_torrents', 'channel')
    def __init__(self, id, dispersy_id, channel_id, name, description, nr_torrents, channel):
        self.id = id
        self.dispersy_id = dispersy_id
        self.channel_id = channel_id
        self.name = name
        self.description = description
        self.nr_torrents = nr_torrents
        
        self.channel = channel
        
    @cacheProperty
    def extended_description(self):
        if self.description:
            return self.description
        
        from Tribler.Main.vwxGUI.SearchGridManager import ChannelManager
        
        #No description, get swarmnames
        searchManager = ChannelManager.getInstance()
        _,_, torrents =  searchManager.getTorrentsFromPlaylist(self, limit = 3)
        names = [torrent.name for torrent in torrents]
        if len(names) > 0:
            return "Contents: '"+"'    '".join(names)+"'"
        elif self.channel.isOpen():
            return 'This playlist is currently empty, drag and drop any .torrent to add it to this playlist.'
        elif self.channel.isMyChannel():
            return 'This playlist is currently empty, you are the only one who can add torrents to it.'            
        return 'This playlist is currently empty, the channel owner has restricted anyone but himself to add torrents to it.'
    
    def __eq__(self, other):
        if other:
            if isinstance(other, Playlist):
                return self.id == other.id
            
            if isinstance(other, int):
                return self.id == other
        return False
                
class Modification(Helper):
    __slots__ = ('id', 'dispersy_id', 'peer_id', 'type_id', 'value', 'time_stamp', 'inserted', 'moderation', 'channeltorrent_id', 'channelcast_db', 'get_nickname')
    def __init__(self, id, dispersy_id, peer_id, type_id, value, time_stamp, inserted, channeltorrent_id):
        self.id = id
        self.dispersy_id = dispersy_id
        self.peer_id = peer_id
        self.type_id = type_id
        self.value = value
        self.time_stamp = time_stamp
        self.inserted = inserted
        self.channeltorrent_id = channeltorrent_id
        
        self.moderation = None
        
    @cacheProperty
    def name(self):
        return self.channelcast_db.id2modification[self.type_id]
    
    @cacheProperty
    def peer_name(self):
        if self.peer_id == None:
            return self.get_nickname()
        return 'Peer %d'%self.peer_id
    
    @cacheProperty
    def torrent(self):
        if self.channeltorrent_id:
            from Tribler.Main.vwxGUI.SearchGridManager import ChannelManager
            
            searchManager = ChannelManager.getInstance()
            return searchManager.getTorrentFromChannelTorrentId(None, self.channeltorrent_id)

class Moderation(Helper):
    __slots__ = ('id', 'channel_id', 'peer_id', 'by_peer_id', 'severity', 'message', 'time_stamp', 'inserted', 'modification', 'channelcast_db', 'get_nickname')
    def __init__(self, id, channel_id, peer_id, by_peer_id, severity, message, time_stamp, inserted):
        self.id = id
        self.channel_id = channel_id
        self.peer_id = peer_id
        self.by_peer_id = by_peer_id
        self.severity = severity
        self.message = message
        self.time_stamp = time_stamp
        self.inserted = inserted
        self.modification = None
        
    @cacheProperty
    def peer_name(self):
        if self.peer_id == None:
            return self.get_nickname()
        return 'Peer %d'%self.peer_id
    
    @cacheProperty
    def by_peer_name(self):
        if self.by_peer_id == None:
            return self.get_nickname()
        return 'Peer %d'%self.by_peer_id
    
class Marking(Helper):
    __slots__ = ('dispersy_id', 'channeltorrent_id', 'peer_id', 'type', 'time_stamp', 'get_nickname')
    def __init__(self, dispersy_id, channeltorrent_id, peer_id, type, time_stamp):
        self.dispersy_id = dispersy_id
        self.channeltorrent_id = channeltorrent_id
        self.peer_id = peer_id
        self.type = type
        self.time_stamp = time_stamp
    
    @cacheProperty
    def peer_name(self):
        if self.peer_id == None:
            return self.get_nickname()
        return 'Peer %d'%self.peer_id
    
    @cacheProperty
    def torrent(self):
        if self.channeltorrent_id:
            from Tribler.Main.vwxGUI.SearchGridManager import ChannelManager
            
            searchManager = ChannelManager.getInstance()
            return searchManager.getTorrentFromChannelTorrentId(None, self.channeltorrent_id)
