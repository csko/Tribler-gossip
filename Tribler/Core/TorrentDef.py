# Written by Arno Bakker 
# see LICENSE.txt for license information
""" Definition of a torrent, that is, a collection of files or a live stream. """
import sys
import os
#import time
import copy
import sha
import math
from traceback import print_exc,print_stack
from types import StringType,ListType,IntType,LongType

from Tribler.Core.BitTornado.bencode import bencode,bdecode

from Tribler.Core.simpledefs import *
from Tribler.Core.defaults import *
from Tribler.Core.exceptions import *
from Tribler.Core.Base import *

import Tribler.Core.APIImplementation.maketorrent as maketorrent
from Tribler.Core.APIImplementation.miscutils import *

from Tribler.Core.Utilities.utilities import find_prog_in_PATH,validTorrentFile,isValidURL
from Tribler.Core.Utilities.unicode import metainfoname2unicode
from Tribler.Core.Utilities.timeouturlopen import urlOpenTimeout
from Tribler.Core.osutils import *

class TorrentDef(Serializable,Copyable):
    """
    Definition of a torrent, that is, all params required for a torrent file,
    plus optional params such as thumbnail, playtime, etc.
    
    Note: to add fields to the torrent definition which are not supported
    by its API, first create the torrent def, finalize it, then add the
    fields to the metainfo, and create a new torrent def from that
    upgraded metainfo using TorrentDef.load_from_dict()

    cf. libtorrent torrent_info
    """
    def __init__(self,input=None,metainfo=None,infohash=None):
        """ Normal constructor for TorrentDef (The input, metainfo and infohash
        parameters are used internally to make this a copy constructor) """
        
        self.readonly = False
        if input is not None: # copy constructor
            self.input = input
            # self.metainfo_valid set in copy() 
            self.metainfo = metainfo
            self.infohash = infohash
            return
        
        self.input = {} # fields added by user, waiting to be turned into torrent file
        # Define the built-in default here
        self.input.update(tdefdefaults)
        try:
            self.input['encoding'] = sys.getfilesystemencoding()
        except:
            self.input['encoding'] = sys.getdefaultencoding()

        self.input['files'] = []

        
        self.metainfo_valid = False
        self.metainfo = None # copy of loaded or last saved torrent dict
        self.infohash = None # only valid if metainfo_valid
        
        
        # We cannot set a built-in default for a tracker here, as it depends on
        # a Session. Alternatively, the tracker will be set to the internal
        # tracker by default when Session::start_download() is called, if the
        # 'announce' field is the empty string.

    #
    # Class methods for creating a TorrentDef from a .torrent file
    #
    def load(filename):
        """
        Load a BT .torrent or Tribler .tribe file from disk and convert
        it into a finalized TorrentDef.
        
        @param filename  An absolute Unicode filename
        @return TorrentDef
        """
        # Class method, no locking required
        f = open(filename,"rb")
        return TorrentDef._read(f)
    load = staticmethod(load)
        
    def _read(stream):
        """ Internal class method that reads a torrent file from stream,
        checks it for correctness and sets self.input and self.metainfo
        accordingly. """
        bdata = stream.read()
        stream.close()
        data = bdecode(bdata)
        return TorrentDef._create(data)
    _read = staticmethod(_read)
        
    def _create(metainfo): # TODO: replace with constructor
        # raises ValueErrors if not good
        validTorrentFile(metainfo) 
        
        t = TorrentDef()
        t.metainfo = metainfo
        t.metainfo_valid = True
        t.infohash = sha.sha(bencode(metainfo['info'])).digest()
        
        # copy stuff into self.input
        maketorrent.copy_metainfo_to_input(t.metainfo,t.input)

        return t
    _create = staticmethod(_create)

    def load_from_url(url):
        """
        Load a BT .torrent or Tribler .tribe file from the URL and convert
        it into a TorrentDef.
        
        @param url URL
        @return TorrentDef.
        """
        # Class method, no locking required
        f = urlOpenTimeout(url)
        return TorrentDef._read(f)
    load_from_url = staticmethod(load_from_url)


    def load_from_dict(metainfo):
        """
        Load a BT .torrent or Tribler .tribe file from the metainfo dictionary
        it into a TorrentDef
        
        @param metainfo A dictionary following the BT torrent file spec.
        @return TorrentDef.
        """
        # Class method, no locking required
        return TorrentDef._create(metainfo)
    load_from_dict = staticmethod(load_from_dict)

    
    #
    # Convenience instance methods for publishing new content
    #
    def add_content(self,inpath,outpath=None,playtime=None):
        """
        Add a file or directory to this torrent definition. When adding a
        directory, all files in that directory will be added to the torrent.
        
        One can add multiple files and directories to a torrent definition.
        In that case the "outpath" parameter must be used to indicate how
        the files/dirs should be named in the torrent. The outpaths used must
        start with a common prefix which will become the "name" field of the
        torrent. 

        To seed the torrent via the core (as opposed to e.g. HTTP) you will
        need to start the download with the dest_dir set to the top-level
        directory containing the files and directories to seed. For example,
        a file "c:\Videos\file.avi" is seeded as follows:
        <pre>
            tdef = TorrentDef()
            tdef.add_content("c:\Videos\file.avi",playtime="1:59:20")
            tdef.set_tracker(s.get_internal_tracker_url())
            tdef.finalize()
            dscfg = DownloadStartupConfig()
            dscfg.set_dest_dir("c:\Video")
            s.start_download(tdef,dscfg)
        </pre>
        @param inpath Absolute name of file or directory on local filesystem, 
        as Unicode string.
        @param outpath (optional) Name of the content to use in the torrent def
        as Unicode string.
        @param playtime (optional) String representing the duration of the 
        multimedia file when played, in [hh:]mm:ss format. 
        """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()
        
        s = os.stat(inpath)
        d = {'inpath':inpath,'outpath':outpath,'playtime':playtime,'length':s.st_size}
        self.input['files'].append(d)
        
        self.metainfo_valid = False


    def remove_content(self,inpath):
        """ Remove a file or directory from this torrent definition 

        @param inpath Absolute name of file or directory on local filesystem, 
        as Unicode string.
        """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()
        
        for d in self.input['files']:
            if d['inpath'] == inpath:
                self.input['files'].remove(d)
                break

    def create_live(self,name,bitrate,playtime="1:00:00",authconfig=None):
        """ Create a live streaming multimedia torrent with a specific bitrate.
        
        The authconfig is a subclass LiveSourceAuthConfig with the key 
        information required to allow authentication of packets from the source,
        or None. In the latter case there is no source authentication. The other
        current legal value is an instance of ECDSALiveSourceAuthConfig. When
        using this method, a sequence number, real-time timestamp and an ECDSA
        signature of 64 bytesis put in each piece. As a result, the content in
        each packet is get_piece_length()-81, so that this into account when
        selecting the bitrate.
        
        The info from the authconfig is stored in the 'info' part of the 
        torrent file when finalized, so changing the authentication info changes
        the identity (infohash) of the torrent.
         
        @param name The name of the stream.
        @param bitrate The desired bitrate in bytes per second.
        @param playtime The virtual playtime of the stream as a string in 
        [hh:]mm:ss format.
        @param authconfig Parameters for the authentication of the source
        """
        self.input['bps'] = bitrate
        self.input['playtime'] = playtime # size of virtual content 

        # For source auth
        authparams = {}
        if authconfig is None:
            authparams['authmethod'] = LIVE_AUTHMETHOD_NONE
        else: 
            authparams['authmethod'] = authconfig.get_method()
            authparams['pubkey'] = str(authconfig.get_pubkey())

        self.input['live'] = authparams 

        d = {'inpath':name,'outpath':None,'playtime':None,'length':None}
        self.input['files'].append(d)

    #
    # Torrent attributes
    #
    def set_encoding(self,enc):
        """ Set the character encoding for e.g. the 'name' field """
        self.input['encoding'] = enc
        self.metainfo_valid = False
        
    def get_encoding(self):
        return self.input['encoding']

    def set_thumbnail(self,thumbfilename):
        """
        Reads image from file and turns it into a torrent thumbnail
        The file should contain an image in JPEG format, preferably 171x96.
        
        @param thumbfilename Absolute name of image file, as Unicode string.
        """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()
        
        f = open(thumbfilename,"rb")
        data = f.read()
        f.close()
        self.input['thumb'] = data 
        self.metainfo_valid = False


    def get_thumbnail(self):
        """ Returns (MIME type,thumbnail data) if present or (None,None)
        @return A tuple. """
        if 'thumb' not in self.input or self.input['thumb'] is None:
            return (None,None)
        else:
            thumb = self.input['thumb'] # buffer/string immutable
            return ('image/jpeg',thumb)
        

    def set_tracker(self,url):
        """ Sets the tracker (i.e. the torrent file's 'announce' field). 
        @param url The announce URL.
        """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()

        if not isValidURL(url):
            raise ValueError("Invalid URL")
        
        if url.endswith('/'):
            # Some tracker code can't deal with / at end
            url = url[:-1]
        self.input['announce'] = url 
        self.metainfo_valid = False

    def get_tracker(self):
        """ Returns the announce URL.
        @return URL """
        return self.input['announce']

    def set_tracker_hierarchy(self,hier):
        """ Set hierarchy of trackers (announce-list) following the spec
        at http://www.bittornado.com/docs/multitracker-spec.txt
        @param hier A hierarchy of trackers as a list of lists.
        """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()

        # TODO: check input, in particular remove / at end
        newhier = []
        if type(hier) != ListType:
            raise ValueError("hierarchy is not a list")
        for tier in hier:
            if type(tier) != ListType:
                raise ValueError("tier is not a list")
            newtier = []
            for url in tier:
                if not isValidURL(url):
                    raise ValueError("Invalid URL: "+`url`)
                
                if url.endswith('/'):
                    # Some tracker code can't deal with / at end
                    url = url[:-1]
                newtier.append(url)
            newhier.append(newtier)

        self.input['announce-list'] = newhier
        self.metainfo_valid = False

    def get_tracker_hierarchy(self):
        """ Returns the hierarchy of trackers.
        @return A list of lists. """
        return self.input['announce-list']

    def set_dht_nodes(self,nodes):
        """ Sets the DHT nodes required by the mainline DHT support,
        See http://www.bittorrent.org/DHT_protocol.html
        @param nodes A list of [hostname,port] lists.
        """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()

        # Check input
        if type(nodes) != ListType:
            raise ValueError("nodes not a list")
        else:
            for node in nodes:
                if type(node) != ListType and len(node) != 2:
                    raise ValueError("node in nodes not a 2-item list: "+`node`)
                if type(node[0]) != StringType:
                    raise ValueError("host in node is not string:"+`node`)
                if type(node[1]) != IntType:
                    raise ValueError("port in node is not int:"+`node`)
                
        self.input['nodes'] = nodes
        self.metainfo_valid = False 

    def get_dht_nodes(self):
        """ Returns the DHT nodes set. 
        @return A list of [hostname,port] lists. """
        return self.input['nodes']
        
    def set_comment(self,value):
        """ Set comment field.
        @param value A Unicode string.
         """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()

        self.input['comment'] = value
        self.metainfo_valid = False

    def get_comment(self):
        """ Returns the comment field of the def.
        @return A Unicode string. """
        return self.input['comment']

    def set_created_by(self,value):
        """ Set 'created by' field.
        @param value A Unicode string.
        """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()

        self.input['created by'] = value
        self.metainfo_valid = False

    def get_created_by(self):
        """ Returns the 'created by' field.
        @return Unicode string. """
        return self.input['created by']

    def set_httpseeds(self,value):
        """ Set list of HTTP seeds following the spec at
        http://www.bittornado.com/docs/webseed-spec.txt
        @param value A list of URLs.
        """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()

        for url in value:
            if not isValidURL(url):
                raise ValueError("Invalid URL: "+`url`)

        self.input['httpseeds'] = value
        self.metainfo_valid = False

    def get_httpseeds(self):
        """ Returns the list of HTTP seeds.
        @return A list of URLs. """
        return self.input['httpseeds']

    def set_piece_length(self,value):
        """ Set the size of the pieces in which the content is traded. 
        The piece size must be a multiple of the chunk size, the unit in which
        it is transmitted, which is 16K by default (see 
        DownloadConfig.set_download_slice_size()). The default is automatic 
        (value 0).
        @param value A number of bytes as per the text.
        """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()

        if not (type(value) == IntType or type(value) == LongType):
            raise ValueError("Piece length not an int/long")

        self.input['piece length'] = value
        self.metainfo_valid = False

    def get_piece_length(self):
        """ Returns the piece size.
        @return A number of bytes. """
        return self.input['piece length']

    def set_add_md5hash(self,value):
        """ Whether to add an end-to-end MD5 checksum to the def.
        @param value Boolean.
        """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()

        self.input['makehash_md5'] = value
        self.metainfo_valid = False

    def get_add_md5hash(self):
        """ Returns whether to add an MD5 checksum. """
        return self.input['makehash_md5']

    def set_add_crc32(self,value):
        """ Whether to add an end-to-end CRC32 checksum to the def.
        @param value Boolean.
        """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()

        self.input['makehash_crc32'] = value
        self.metainfo_valid = False

    def get_add_crc32(self):
        """ Returns whether to add an end-to-end CRC32 checksum to the def.
        @return Boolean. """
        return self.input['makehash_crc32']

    def set_add_sha1hash(self,value):
        """ Whether to add end-to-end SHA1 checksum to the def.
        @param value Boolean.
        """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()

        self.input['makehash_sha1'] = value
        self.metainfo_valid = False

    def get_add_sha1hash(self):
        """ Returns whether to add an end-to-end SHA1 checksum to the def. 
        @return Boolean."""
        return self.input['makehash_sha1']

    def set_create_merkle_torrent(self,value):
        """ Create a Merkle torrent instead of a regular BT torrent. A Merkle
        torrent uses a hash tree for checking the integrity of the content
        received. As such it creates much smaller torrent files than the
        regular method. Tribler-specific feature."""
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()

        self.input['createmerkletorrent'] = value
        self.metainfo_valid = False

    def get_create_merkle_torrent(self):
        """ Returns whether to create a Merkle torrent.
        @return Boolean. """
        return self.input['createmerkletorrent']

    def set_signature_keypair_filename(self,value):
        """ Set absolute filename of keypair to be used for signature.
        When set, a signature will be added.
        @param value A filename containing an Elliptic Curve keypair.
        """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()

        self.input['torrentsigkeypairfilename'] = value
        self.metainfo_valid = False

    def get_signature_keypair_filename(self):
        """ Returns the filename containing the signing keypair or None.
        @return Unicode String or None. """
        return self.input['torrentsigkeypairfilename']

    def get_live(self):
        """ Returns whether this definition is for a live torrent.
        @return Boolean. """
        return 'live' in self.input and self.input['live']

    def get_live_authmethod(self):
        """ Returns the method for authenticating the source.
        <pre>
        LIVE_AUTHMETHOD_ECDSA
        </pre>
        @return String
        """
        return 'live' in self.input and self.input['live']['authmethod']

    def get_live_pubkey(self):
        """ Returns the public key used for authenticating packets from
        the source.
        @return A public key in DER.
        """
        if 'live' in self.input and 'pubkey' in self.input['live']:
            return self.input['live']['pubkey']
        else:
            return None
        

    def finalize(self,userabortflag=None,userprogresscallback=None):
        """ Create BT torrent file by reading the files added with
        add_content() and calculate the torrent file's infohash. 
        
        Creating the torrent file can take a long time and will be carried out
        by the calling thread. The process can be made interruptable by passing 
        a threading.Event() object via the userabortflag and setting it when 
        the process should be aborted. The also optional userprogresscallback 
        will be called by the calling thread periodically, with a progress 
        percentage as argument.
        
        The userprogresscallback function will be called by the calling thread. 
        
        @param userabortflag threading.Event() object
        @param userprogresscallback Function accepting a fraction as first
        argument. 
        """
        if self.readonly:
            raise OperationNotPossibleAtRuntimeException()
        
        if self.metainfo_valid:
            return

        if 'live' in self.input:
            # Make sure the duration is an integral number of pieces, for
            # security (live source auth).
            secs = parse_playtime_to_secs(self.input['playtime'])
            pl = float(self.get_piece_length())
            length = float(self.input['bps']*secs)
            
            diff = length % pl
            add = (pl - diff) % pl
            newlen = int(length + add)

                
            print >>sys.stderr,"CHECK INFO LENGTH",secs,newlen

            d = self.input['files'][0]
            d['length'] = newlen


        # Note: reading of all files and calc of hashes is done by calling 
        # thread.
        (infohash,metainfo) = maketorrent.make_torrent_file(self.input,userabortflag=userabortflag,userprogresscallback=userprogresscallback)
        if infohash is not None:
            self.infohash = infohash
            self.metainfo = metainfo
            self.input['name'] = metainfo['info']['name']
            self.metainfo_valid = True

    def is_finalized(self):
        """ Returns whether the TorrentDef is finalized or not.
        @return Boolean. """
        return self.metainfo_valid

    #
    # Operations on finalized TorrentDefs
    #
    def get_infohash(self):
        """ Returns the infohash of the torrent.
        @return A string of length 20. """
        if self.metainfo_valid:
            return self.infohash
        else:
            raise TorrentDefNotFinalizedException()

    def get_metainfo(self):
        """ Returns the torrent definition as a dictionary that follows the BT
        spec for torrent files. 
        @return dict
        """
        if self.metainfo_valid:
            return self.metainfo
        else:
            raise TorrentDefNotFinalizedException()

    def get_name(self):
        """ Returns the info['name'] field as raw string of bytes.
        @return String """
        if self.metainfo_valid:
            return self.input['name'] # string immutable
        else:
            raise TorrentDefNotFinalizedException()

    def get_name_as_unicode(self):
        """ Returns the info['name'] field as Unicode string.
        @return Unicode string. """
        if self.metainfo_valid:
            (namekey,uniname) = metainfoname2unicode(self.metainfo)
            return uniname
        else:
            raise TorrentDefNotFinalizedException()

    def verify_torrent_signature(self):
        """ Verify the signature on the finalized torrent definition. Returns
        whether the signature was valid.
        @return Boolean.
        """
        if self.metainfo_valid:
            return Tribler.Core.Overlay.permid.verify_torrent_signature(self.metainfo)
        else:
            raise TorrentDefNotFinalizedException()


    def save(self,filename):
        """
        Finalizes the torrent def and writes a torrent file i.e., bencoded dict 
        following BT spec) to the specified filename. Note this make take a
        long time when the torrent def is not yet finalized.
        
        @param filename An absolute Unicode path name.
        """
        if not self.readonly:
            self.finalize()

        bdata = bencode(self.metainfo)
        f = open(filename,"wb")
        f.write(bdata)
        f.close()


    def get_bitrate(self,file=None):
        """ Returns the bitrate of the specified file. If no file is specified, 
        we assume this is a single-file torrent.
        
        @param file (Optional) the file in the torrent to retrieve the bitrate of.
        @return The bitrate in bytes per second.
        """ 
        if not self.metainfo_valid:
            raise NotYetImplementedException() # must save first

        return maketorrent.get_bitrate_from_metainfo(file,self.metainfo)

    def get_files(self,exts=None):
        """ The list of files in the finalized torrent def.
        @param exts (Optional) list of filename extensions (without leading .)
        to search for.
        @return A list of filenames.
        """
        if not self.metainfo_valid:
            raise NotYetImplementedException() # must save first
        
        return maketorrent.get_files(self.metainfo,exts)

    def get_length(self,selectedfiles=None):
        """ Returns the total size of the content in the torrent. If the
        optional selectedfiles argument is specified, the method returns
        the total size of only those files.
        @return A length (long)
        """
        if not self.metainfo_valid:
            raise NotYetImplementedException() # must save first
        
        (length,filepieceranges) = maketorrent.get_length_filepieceranges_from_metainfo(self.metainfo,selectedfiles)
        return length

    def is_multifile_torrent(self):
        """ Returns whether this TorrentDef is a multi-file torrent.
        @return Boolean
        """
        if not self.metainfo_valid:
            raise NotYetImplementedException() # must save first
        
        return 'files' in self.metainfo['info']

    
    #
    # Internal methods
    #
    def get_index_of_file_in_files(self,file):
        if not self.metainfo_valid:
            raise NotYetImplementedException() # must save first

        info = self.metainfo['info']

        if file is not None and 'files' in info:
            for i in range(len(info['files'])):
                x = info['files'][i]
                    
                intorrentpath = maketorrent.pathlist2filename(x['path'])
                if intorrentpath == file:
                    return i
            return ValueError("File not found in torrent")
        else:
            raise ValueError("File not found in single-file torrent")

    #
    # Copyable interface
    # 
    def copy(self):
        input = copy.copy(self.input)
        metainfo = copy.copy(self.metainfo)
        infohash = self.infohash
        t = TorrentDef(input,metainfo,infohash)
        t.metainfo_valid = self.metainfo_valid
        return t
