# Written by Jan David Mol, Arno Bakker
# see LICENSE.txt for license information

import sys
import time
from math import ceil
import random
from traceback import print_exc,print_stack

from Tribler.Core.BitTornado.BT1.PiecePicker import PiecePicker 

DEBUG = False
DEBUGPP = False

class PiecePickerStreaming(PiecePicker):
    """ Implements piece picking for streaming video. Keeps track of playback
        point and avoids requesting obsolete pieces. """

    # order of initialisation and important function calls
    #   PiecePicker.__init__              (by BitTornado.BT1Download.__init__)
    #   PiecePicker.complete              (by hash checker, for pieces on disk)
    #   MovieSelector.__init__
    #   PiecePicker.set_download_range    (indirectly by MovieSelector.__init__)
    #   MovieOnDemandTransporter.__init__ (by BitTornado.BT1Download.startEngine)
    #   PiecePicker.set_bitrate           (by MovieOnDemandTransporter)
    #   PiecePicker.set_transporter       (by MovieOnDemandTransporter)
    #
    #   PiecePicker._next                 (once connections are set up)
    #
    #   PiecePicker.complete              (by hash checker, for pieces received)

    # size of high probability set, in seconds
    HIGH_PROB_SETSIZE = 10

    # relative size of mid-priority set
    MU = 4

    def __init__(self, numpieces,
                 rarest_first_cutoff = 1, rarest_first_priority_cutoff = 3,
                 priority_step = 20, helper = None, rate_predictor = None, piecesize = 0):
        PiecePicker.__init__( self, numpieces, rarest_first_cutoff, rarest_first_priority_cutoff,
                              priority_step, helper, rate_predictor )

        self.videostatus = None

        # maximum existing piece number, to avoid scanning beyond it in next()
        self.maxhave = 0

        # some statistics
        self.stats = {}
        self.stats["high"] = 0
        self.stats["mid"] = 0
        self.stats["low"] = 0

        # playback module
        self.transporter = None

        # video speed in bytes/s
        self.outstanding = {}
        
        # Piece timeout policy parameters
        """
        minprebufspeed = 10.0 # KB/s
        self.PIECETIME = piecesize/(minprebufspeed*1024.0)
        self.MAXDLTIME=2.0*self.PIECETIME 
        self.MAXDLTIME_NONPREBUF=4.0*self.PIECETIME
        """
        # Works for 32KB pieces, like vuze.com
        self.PIECETIME = 10.0
        self.MAXDLTIME = 20.0
        self.MAXDLTIME_NONPREBUF=30.0

        """
        # Dynamic
        prebufsize = 1000000.0 # 1 MB
        prebuftime = 60.0 # secs, prebuffering should finish in this time
        prebufspeed = prebufsize/prebuftime
        PIECETIME = float(piecesize)/prebufspeed # the amount of time a peer has to dl a piece
        """
        
        
    def set_transporter(self, transporter):
        self.transporter = transporter

        # update its information -- pieces read from disk
        if not self.videostatus.live_streaming:
            for i in xrange(self.videostatus.first_piece,self.videostatus.last_piece+1):
                if self.has[i]:
                    self.transporter.complete( i, downloaded=False )

    def set_videostatus(self,videostatus):
        """ Download in a wrap-around fashion between pieces [0,numpieces).
            Look at most delta pieces ahead from download_range[0].
        """
        self.videostatus = videostatus

    def got_have(self, piece, connection=None):
        if DEBUG:
            print >>sys.stderr,"PiecePickerStreaming: got_have:",piece
        self.maxhave = max(self.maxhave,piece)
        PiecePicker.got_have( self, piece, connection )

    def got_seed(self):
        self.maxhave = self.numpieces
        PiecePicker.got_seed( self )

    def lost_have(self, piece):
        PiecePicker.lost_have( self, piece )

    def got_peer(self, connection):
        PiecePicker.got_peer( self, connection )

    def lost_peer(self, connection):
        PiecePicker.lost_peer( self, connection )

    def complete(self, piece):
        if DEBUG:
            print >>sys.stderr,"PiecePickerStreaming: complete:",piece
        PiecePicker.complete( self, piece )
        if self.transporter:
            self.transporter.complete( piece )
        try:
            del self.outstanding[piece]
        except:
            pass

    # next: selects next piece to download. adjusts wantfunc with filter for streaming; calls
    #   _next: selects next piece to download. completes partial downloads first, if needed, otherwise calls
    #     next_new: selects next piece to download. override this with the piece picking policy

    def next(self, haves, wantfunc, sdownload, complete_first = False, helper_con = False, slowpieces=[], willrequest=True,connection=None):
        def newwantfunc( piece ):
            #print >>sys.stderr,"S",self.streaming_piece_filter( piece ),"!sP",not (piece in slowpieces),"w",wantfunc( piece )
            return not (piece in slowpieces) and wantfunc( piece )

        # fallback: original piece picker
        p = PiecePicker.next(self, haves, newwantfunc, sdownload, complete_first, helper_con, slowpieces=slowpieces, willrequest=willrequest,connection=connection)
        if DEBUGPP and self.videostatus.prebuffering:
            print >>sys.stderr,"PiecePickerStreaming: next returns",p
        if p is None and not self.videostatus.live_streaming:
            # When the file we selected from a multi-file torrent is complete,
            # we won't request anymore pieces, so the normal way of detecting 
            # we're done is not working and we won't tell the video player 
            # we're playable. Do it here instead.
            self.transporter.notify_playable()
        return p

    def _next(self, haves, wantfunc, complete_first, helper_con, willrequest=True, connection=None):
        """ First, complete any partials if needed. Otherwise, select a new piece. """

        #print >>sys.stderr,"PiecePickerStreaming: complete_first is",complete_first,"started",self.started

        # cutoff = True:  random mode
        #          False: rarest-first mode
        cutoff = self.numgot < self.rarest_first_cutoff

        # whether to complete existing partials first -- do so before the
        # cutoff, or if forced by complete_first, but not for seeds.
        #complete_first = (complete_first or cutoff) and not haves.complete()
        complete_first = (complete_first or cutoff)

        # most interesting piece
        best = None

        # interest level of best piece
        bestnum = 2 ** 30

        # select piece we started to download with best interest index.
        for i in self.started:
# 2fastbt_
            if haves[i] and wantfunc(i) and (self.helper is None or helper_con or not self.helper.is_ignored(i)):
# _2fastbt
                if self.level_in_interests[i] < bestnum:
                    best = i
                    bestnum = self.level_in_interests[i]

        if best is not None:
            # found a piece -- return it if we are completing partials first
            # or if there is a cutoff
            if complete_first or (cutoff and len(self.interests) > self.cutoff):
                self.register_piece(best)
                return best

        # Arno: Keep track of how long pieces are outstanding. If too slow,
        # cancel the request and rerequest it from another peer.
        now = time.time()
        newoutstanding = {}
        
        cancelpieces = []
        for (p,t) in self.outstanding.iteritems():
            diff = t-now
            if diff < self.PIECETIME:
                # Peer failed to deliver intime
                print >>sys.stderr,"PiecePickerStreaming: request too slow, due in",diff,p,"#"
                cancelpieces.append(p)
            else:
                newoutstanding[p] = t
        self.outstanding = newoutstanding

        # Cancel all pieces that are too late
        if len(cancelpieces) > 0:
            self.downloader.cancel_piece_download(cancelpieces,allowrerequest=False)

        p = self.next_new(haves, wantfunc, complete_first, helper_con,willrequest=willrequest,connection=connection)
        if p is not None:
            self.register_piece(p)
        return p

    def register_piece(self,p):
        vs = self.videostatus
        now = time.time()
        rawdue = self.transporter.piece_due(p)
        diff = rawdue - now
        f,t = vs.playback_pos, vs.normalize( vs.playback_pos + self.transporter.max_prebuf_packets )
        if vs.prebuffering and vs.in_range( f, t, p ):
            # not playing, prioritize prebuf
            self.outstanding[p] = now+self.MAXDLTIME
            #print >>sys.stderr,"PiecePickerStreaming: prebuf due soonest",p,"#"
        elif diff > 1000000.0:
            #print >>sys.stderr,"PiecePickerStreaming: prebuf due soon",p,"#"
            self.outstanding[p] = now+self.MAXDLTIME_NONPREBUF
        elif diff < self.PIECETIME: # need it fast
            #print >>sys.stderr,"PiecePickerStreaming: due asap in",(rawdue-now),p,"#"
            self.outstanding[p] = now+self.MAXDLTIME # otherwise we cancel it again right away
        else:
            #print >>sys.stderr,"PiecePickerStreaming: due later in",(rawdue-now),p,"#"
            self.outstanding[p] = rawdue


    def next_new(self, haves, wantfunc, complete_first, helper_con, willrequest=True, connection=None):
        """ Determine which piece to download next from a peer.

        haves:          set of pieces owned by that peer
        wantfunc:       custom piece filter
        complete_first: whether to complete partial pieces first
        helper_con:
        willrequest:    whether the returned piece will actually be requested

        """

        vs = self.videostatus

        def pick_first( f, t ): # no shuffle
            for i in vs.generate_range((f,t)):
                # Is there a piece in the range the peer has?
                # Is there a piece in the range we don't have?
                if not haves[i] or self.has[i]: 
                    continue

                if not wantfunc(i): # Is there a piece in the range we want? 
                    continue

                if self.helper is None or helper_con or not self.helper.is_ignored(i):
                    return i

            return None

        def pick_rarest_loop_over_small_range(f,t,shuffle=True):
            # Arno: pick_rarest is way expensive for the midrange thing,
            # therefore loop over the list of pieces we want and see
            # if it's avail, rather than looping over the list of all
            # pieces to see if one falls in the (f,t) range.
            #
            xr = vs.generate_range((f,t))
            r = None
            if shuffle:
                # xr is an xrange generator, need real values to shuffle
                r = []
                r.extend(xr)
                random.shuffle(r)
            else:
                r = xr
            for i in r:
                #print >>sys.stderr,"H",
                if not haves[i] or self.has[i]:
                    continue

                #print >>sys.stderr,"W",
                if not wantfunc(i):
                    continue

                if self.helper is None or helper_con or not self.helper.is_ignored(i):
                    return i

            return None


        def pick_rarest_small_range(f,t):
            #print >>sys.stderr,"choice small",f,t
            d = vs.dist_range(f,t)
            
            for level in xrange(len(self.interests)):
                piecelist  = self.interests[level]
                
                if len(piecelist) > d:
                #if level+1 == len(self.interests):
                    # Arno: Lowest level priorities / long piecelist.
                    # This avoids doing a scan that goes over the entire list 
                    # of pieces when we already have the hi and/or mid ranges.
                    
                    # Arno, 2008-05-21: Apparently, the big list is not always
                    # at the lowest level, hacked distance metric to determine
                    # whether to use slow or fast method.
                    
                    #print >>sys.stderr,"choice QUICK"
                    return pick_rarest_loop_over_small_range(f,t)
                    #print >>sys.stderr,"choice Q",diffstr,"l",level,"s",len(piecelist) 
                else:
                    # Higher priorities / short lists
                    for i in piecelist:
                        if not vs.in_range( f, t, i ):
                            continue
    
                        #print >>sys.stderr,"H",
                        if not haves[i] or self.has[i]:
                            continue
    
                        #print >>sys.stderr,"W",
                        if not wantfunc(i):
                            continue
    
                        if self.helper is None or helper_con or not self.helper.is_ignored(i):
                            return i

            return None


        def pick_rarest(f,t): #BitTorrent already shuffles the self.interests for us
            for piecelist in self.interests:
                for i in piecelist:
                    if not vs.in_range( f, t, i ):
                        continue

                    #print >>sys.stderr,"H",
                    if not haves[i] or self.has[i]:
                        continue

                    #print >>sys.stderr,"W",
                    if not wantfunc(i):
                        continue

                    if self.helper is None or helper_con or not self.helper.is_ignored(i):
                        return i

            return None

        h = vs.time_to_pieces( self.HIGH_PROB_SETSIZE )

        first,last = vs.download_range()
        if vs.wraparound:
            max_lookahead = vs.wraparound_delta
        else:
            max_lookahead = vs.last_piece - vs.playback_pos

        highprob_cutoff = vs.normalize( first + min( h, max_lookahead ) )
        midprob_cutoff  = vs.normalize( first + min( h + self.MU * h, max_lookahead ) )

        if vs.live_streaming and vs.live_startpos is None:
            self.transporter.calc_live_startpos( self.transporter.max_prebuf_packets, False )
            print >>sys.stderr,"vod: pp determined startpos of",vs.live_startpos

        if vs.prebuffering:
            f = first
            t = vs.normalize( first + self.transporter.max_prebuf_packets )
            choice = pick_rarest_small_range(f,t)
            type = "high"
        else:
            choice = None

        if choice is None:
            if vs.live_streaming:
               choice = pick_rarest_small_range( first, highprob_cutoff )
            else:
               choice = pick_first( first, highprob_cutoff )
            type = "high"

        if choice is None:
            choice = pick_rarest_small_range( highprob_cutoff, midprob_cutoff )
            type = "mid"

        if choice is None:
            if vs.live_streaming:
                # Want: loop over what peer has avail, respecting piece priorities
                # (could ignore those for live).
                #
                # Attempt 1: loop over range (which is 25% of window (see 
                # VideoStatus), ignoring priorities, no shuffle.
                #print >>sys.stderr,"vod: choice low RANGE",midprob_cutoff,last
                #choice = pick_rarest_loop_over_small_range(midprob_cutoff,last,shuffle=False)
                pass
            else:
                choice = pick_rarest( midprob_cutoff, last )
            type = "low"
            
        if choice and willrequest:
            self.stats[type] += 1

        if DEBUG:
            print >>sys.stderr,"vod: picked piece %s [type=%s] [%d,%d,%d,%d]" % (`choice`,type,first,highprob_cutoff,midprob_cutoff,last)

        return choice

    def is_valid_piece(self,piece):
       return self.videostatus.in_valid_range(piece)
   
   
PiecePickerVOD = PiecePickerStreaming

