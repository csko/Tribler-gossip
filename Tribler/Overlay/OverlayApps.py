# Written by Arno Bakker
# see LICENSE.txt for license information
#
# All applications on top of the SecureOverlay should be started here.
#
import sys
from traceback import print_exc

from BitTornado.BT1.MessageID import HelpCoordinatorMessages, HelpHelperMessages, \
        MetadataMessages, BuddyCastMessages, DIALBACK_REQUEST, getMessageName
from Tribler.toofastbt.CoordinatorMessageHandler import CoordinatorMessageHandler
from Tribler.toofastbt.HelperMessageHandler import HelperMessageHandler
from MetadataHandler import MetadataHandler
from Tribler.BuddyCast.buddycast import BuddyCastFactory
from Tribler.NATFirewall.DialbackMsgHandler import DialbackMsgHandler
from Tribler.Overlay.SecureOverlay import OLPROTO_VER_SECOND
from Tribler.utilities import show_permid_short

DEBUG = 0

class OverlayApps:
    # Code to make this a singleton
    __single = None

    def __init__(self):
        if OverlayApps.__single:
            raise RuntimeError, "OverlayApps is Singleton"
        OverlayApps.__single = self 
        self.coord_handler = None
        self.help_handler = None
        self.metadata_handler = None
        self.buddycast = None
        self.collect = None
        self.dialback_handler = None
        self.msg_handlers = {}
        
        self.torrent_collecting_solution = 1    # TODO: read from config
        # 1: simplest solution: per torrent/buddycasted peer/4hours
        # 2: simple and efficent solution: random collecting on group base
        # 3: advanced solution: personlized collecting on group base

    def getInstance(*args, **kw):
        if OverlayApps.__single is None:
            OverlayApps(*args, **kw)
        return OverlayApps.__single
    getInstance = staticmethod(getInstance)

    def register(self, secure_overlay, launchmany, rawserver, config):
        
        self.secure_overlay = secure_overlay
        
        # OverlayApps gets all messages, and demultiplexes 
        secure_overlay.register_recv_callback(self.handleMessage)
        secure_overlay.register_conns_callback(self.handleConnection)

        # Create handler for metadata messages
        self.metadata_handler = MetadataHandler.getInstance()
        self.metadata_handler.register(secure_overlay, self.help_handler, launchmany, 
                                       config['config_path'], config['max_torrents'])            
        self.register_msg_handler(MetadataMessages, self.metadata_handler.handleMessage)
        
        if config['download_help']:
            # Create handler for messages to dlhelp coordinator
            self.coord_handler = CoordinatorMessageHandler(launchmany)
            self.register_msg_handler(HelpHelperMessages, self.coord_handler.handleMessage)

            # Create handler for messages to dlhelp helper
            self.help_handler = HelperMessageHandler(launchmany)
            self.help_handler.register(self.metadata_handler)
            self.register_msg_handler(HelpCoordinatorMessages, self.help_handler.handleMessage)
        
        if not config['torrent_collecting']:
            self.torrent_collecting_solution = 0
        
        if config['buddycast']:
            
            # Create handler for Buddycast messages
            self.buddycast = BuddyCastFactory.getInstance(superpeer=config['superpeer'])
            # Using buddycast to handle torrent collecting since they are dependent
            self.buddycast.register(secure_overlay, launchmany.rawserver, launchmany, 
                                    launchmany.listen_port, launchmany.exchandler, True,
                                    self.metadata_handler, self.torrent_collecting_solution)
            self.register_msg_handler(BuddyCastMessages, self.buddycast.handleMessage)

        if config['dialback']:
            self.dialback_handler = DialbackMsgHandler.getInstance()
            self.dialback_handler.register(secure_overlay, launchmany.rawserver, launchmany,
                                           launchmany.handler, launchmany.listen_port,
                                           config['max_message_length'], 
                                           config['dialback_active'],
                                           config['dialback_trust_superpeers'],
                                           config['dialback_interval'])
            self.register_msg_handler([DIALBACK_REQUEST],
                                      self.dialback_handler.handleSecOverlayMessage)

    def register_msg_handler(self, ids, handler):
        """ 
        ids is the [ID1, ID2, ..] where IDn is a sort of message ID in overlay
        swarm. Each ID can only be handled by one handler, but a handler can 
        handle multiple IDs
        """
        for id in ids:
            if DEBUG:
                print >> sys.stderr,"olapps: Handler registered for",getMessageName(id)
            self.msg_handlers[id] = handler
        

    def handleMessage(self,permid,selversion,message):
        """ demultiplex message stream to handlers """
        id = message[0]
        if DEBUG:
            print >> sys.stderr,"olapps: got_message",getMessageName(id),"v"+str(selversion)
        if not self.msg_handlers.has_key(id):
            if DEBUG:
                print >> sys.stderr,"olapps: No handler found for",getMessageName(id)
            return False
        else:
            if DEBUG:
                print >> sys.stderr,"secover: Giving message to handler for",getMessageName(id)
            try:
                return self.msg_handlers[id](permid,selversion,message)
            except:
                # Catch all
                print_exc(file=sys.stderr)
                return False


    def handleConnection(self,exc,permid,selversion,locally_initiated):
        """ An overlay-connection was established. Notify interested parties. """

        if DEBUG:
            print >> sys.stderr,"olapps: handleConnection",exc

        if self.dialback_handler is not None:
            # overlay-protocol version check done inside
            self.dialback_handler.handleSecOverlayConnection(exc,permid,selversion,locally_initiated)
        
        if self.buddycast:
            self.buddycast.handleConnection(exc,permid,selversion,locally_initiated)
            
            if DEBUG:
                nconn = 0
                conns = self.buddycast.buddycast_core.connections
                print >> sys.stdout, "\n****** conn in buddycast"
                for peer_permid in conns:
                    _permid = show_permid_short(peer_permid)
                    nconn += 1
                    print >> sys.stdout, "***", nconn, _permid, conns[peer_permid]

