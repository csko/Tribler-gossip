# written by Arno Bakker
# see LICENSE.txt for license information

import sys
from traceback import print_exc,print_stack
from cStringIO import StringIO
import struct
import time

from sha import sha


from M2Crypto import EC
from Tribler.Core.Overlay.permid import sign_data,verify_data_pubkeyobj


DEBUG = False

class Authenticator:
    
    def __init__(self,piecelen,npieces):
        self.piecelen = piecelen
        self.npieces = npieces
    
    def get_piece_length(self):
        return self.piecelen
    
    def get_npieces(self):
        return self.npieces
    
    def get_content_blocksize(self):
        pass
    
    def sign(self,content):
        pass
    
    def verify(self,piece):
        pass
    
    def get_content(self,piece):
        pass


class NullAuthenticator(Authenticator):
    
    def __init__(self,piecelen,npieces):
        Authenticator.__init__(self,piecelen,npieces)
        self.contentblocksize = piecelen
    
    def get_content_blocksize(self):
        return self.contentblocksize
    
    def sign(self,content):
        return [content]
    
    def verify(self,piece):
        return True
    
    def get_content(self,piece):
        return piece


class ECDSAAuthenticator(Authenticator):
    """ Authenticator who places a ECDSA signature in the last part of a
    piece. In particular, the sig consists of:
    - an 8 byte sequence number
    - an 8 byte real-time timestamp
    - a 1 byte length field followed by
    - a variable-length ECDSA signature in ASN.1, (max 64 bytes)  
    - optionally 0x00 padding bytes, if the ECDSA sig is less than 64 bytes,
    to give a total of 81 bytes.
    """
    
    SEQNUM_SIZE = 8
    RTSTAMP_SIZE = 8
    LENGTH_SIZE = 1
    MAX_ECDSA_ASN1_SIGSIZE = 64
    EXTRA_SIZE = SEQNUM_SIZE + RTSTAMP_SIZE
    # = seqnum + rtstamp + 1 byte length + MAX_ECDSA, padded
    # put seqnum + rtstamp directly after content, so we calc the sig directly 
    # from the received buffer.
    OUR_SIGSIZE = EXTRA_SIZE+LENGTH_SIZE+MAX_ECDSA_ASN1_SIGSIZE 
    
    def __init__(self,piecelen,npieces,keypair=None,pubkeypem=None):
        
        print >>sys.stderr,"ECDSAAuth: npieces",npieces
        
        Authenticator.__init__(self,piecelen,npieces)
        self.contentblocksize = piecelen-self.OUR_SIGSIZE
        self.keypair = keypair
        if pubkeypem is not None:
            #print >>sys.stderr,"ECDSAAuth: pubkeypem",`pubkeypem`
            self.pubkey = EC.pub_key_from_der(pubkeypem)
        else:
            self.pubkey = None
        self.seqnum = 0L

    def get_content_blocksize(self):
        return self.contentblocksize
    
    def sign(self,content):
        rtstamp = time.time()
        #print >>sys.stderr,"ECDSAAuth: sign: ts %.5f s" % rtstamp
        
        extra = struct.pack('>Qd', self.seqnum,rtstamp)
        self.seqnum += 1L

        sig = sign_data(content,extra,self.keypair)
        # The sig returned is either 64 or 63 bytes long (62 also possible I 
        # guess). Therefore we transmit size as 1 bytes and fill to 64 bytes.
        lensig = chr(len(sig))
        if len(sig) != self.MAX_ECDSA_ASN1_SIGSIZE:
            # Note: this is not official ASN.1 padding. Also need to modify
            # the header length for that I assume.
            diff = self.MAX_ECDSA_ASN1_SIGSIZE-len(sig)
            padding = '\x00' * diff 
            return [content,extra,lensig,sig,padding]
        else:
            return [content,extra,lensig,sig]
        
    def verify(self,piece,index):
        """ A piece is valid if:
        - the signature is correct,
        - the seqnum % npieces == piecenr.
        - the seqnum is no older than self.seqnum - npieces
        @param piece The piece data as received from peer
        @param index The piece number as received from peer
        @return Boolean
        """
        try:
            # Can we do this without memcpy?
            #print >>sys.stderr,"ECDSAAuth: verify",len(piece)
            extra = piece[-self.OUR_SIGSIZE:-self.OUR_SIGSIZE+self.EXTRA_SIZE]
            lensig = ord(piece[-self.OUR_SIGSIZE+self.EXTRA_SIZE])
            if lensig > self.MAX_ECDSA_ASN1_SIGSIZE:
                print >>sys.stderr,"ECDSAAuth: @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ failed piece",index,"lensig wrong",lensig
                return False
            #print >>sys.stderr,"ECDSAAuth: verify lensig",lensig
            diff = lensig-self.MAX_ECDSA_ASN1_SIGSIZE
            if diff == 0:
                sig = piece[-self.OUR_SIGSIZE+self.EXTRA_SIZE+self.LENGTH_SIZE:]
            else:
                sig = piece[-self.OUR_SIGSIZE+self.EXTRA_SIZE+self.LENGTH_SIZE:diff]
            content = piece[:-self.OUR_SIGSIZE]
            if DEBUG:
                print >>sys.stderr,"ECDSAAuth: verify piece",index,"sig",`sig`
                print >>sys.stderr,"ECDSAAuth: verify dig",sha(content).hexdigest()
        
            ret = verify_data_pubkeyobj(content,extra,self.pubkey,sig)
            if ret:
                (seqnum, rtstamp) = struct.unpack('>Qd',extra)
                
                if DEBUG:
                    print >>sys.stderr,"ECDSAAuth: verify piece",index,"seq",seqnum,"ts %.5f s" % rtstamp,"ls",lensig
                
                mod = seqnum % self.get_npieces()
                thres = self.seqnum - self.get_npieces()/2
                if seqnum <= thres:
                    print >>sys.stderr,"ECDSAAuth: @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ failed piece",index,"old seqnum",seqnum,"<<",self.seqnum
                    return False
                elif mod != index:
                    print >>sys.stderr,"ECDSAAuth: @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ failed piece",index,"expected",mod
                    return False 
                else:
                    self.seqnum = max(self.seqnum,seqnum)
            else:
                print >>sys.stderr,"ECDSAAuth: @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ piece",index,"failed sig"
            
            return ret
        except:
            print_exc()
            return False 

    def get_content(self,piece):
        return piece[:-self.OUR_SIGSIZE]

    # Extra fields
    def get_seqnum(self,piece):
        (seqnum, rtstamp) = self._decode_extra(piece)
        return seqnum

    def get_rtstamp(self,piece):
        (seqnum, rtstamp) = self._decode_extra(piece)
        return rtstamp
        
    def _decode_extra(self,piece):
        extra = piece[-self.OUR_SIGSIZE:-self.OUR_SIGSIZE+self.EXTRA_SIZE]
        return struct.unpack('>Qd',extra)

    
def sign_data(plaintext,extra,ec_keypair):
    digester = sha(plaintext)
    digester.update(extra)
    digest = digester.digest()
    return ec_keypair.sign_dsa_asn1(digest)
    
def verify_data_pubkeyobj(plaintext,extra,pubkey,blob):
    digester = sha(plaintext)
    digester.update(extra)
    digest = digester.digest()
    return pubkey.verify_dsa_asn1(digest,blob)
    
    
class AuthStreamWrapper:
    """ Wrapper around the stream returned by VideoOnDemand/MovieOnDemandTransporter
    that strips of the signature info
    """
    
    def __init__(self,inputstream,authenticator):
        self.inputstream = inputstream
        self.buffer = StringIO()
        self.authenticator = authenticator
        self.piecelen = authenticator.get_piece_length()
        self.last_rtstamp = None

    def read(self,numbytes=None):
        rawdata = self._readn(self.piecelen)
        content = self.authenticator.get_content(rawdata)
        self.last_rtstamp = self.authenticator.get_rtstamp(rawdata)
        if numbytes is None:
            return content
        elif numbytes < len(content):
            # TODO: buffer unread data for next read
            raise ValueError('reading less than piecesize not supported yet')
        else:
            return content

    def get_generation_time(self):
        """ Returns the time at which the last read piece was generated at the source. """
        return self.last_rtstamp
    
    def seek(self,pos,whence=None):
        if pos != 0:
            raise ValueError("authstream does not support seek")
        
    def close(self):
        self.inputstream.close()

    # Internal method
    def _readn(self,n):
        """ read exactly n bytes from inputstream, block if unavail """
        nwant = n
        while True:
            data = self.inputstream.read(nwant)
            if len(data) == 0:
                return data
            nwant -= len(data)
            self.buffer.write(data)
            if nwant == 0:
                break
        self.buffer.seek(0)
        data = self.buffer.read(n)
        self.buffer.seek(0)
        return data
        
