from conversion import JSONConversion
from payload import MessagePayload, GossipMessage

from Tribler.Core.dispersy.authentication import MemberAuthentication
from Tribler.Core.dispersy.community import Community
from Tribler.Core.dispersy.conversion import DefaultConversion
from Tribler.Core.dispersy.message import DropMessage
from Tribler.Core.dispersy.distribution import DirectDistribution
from Tribler.Core.dispersy.resolution import PublicResolution

from Tribler.Core.dispersy.destination import SubjectiveDestination
from Tribler.Core.dispersy.dispersy import Dispersy
from Tribler.Core.dispersy.distribution import FullSyncDistribution, LastSyncDistribution
from Tribler.Core.dispersy.message import Message, DelayMessageByProof
from Tribler.Core.dispersy.resolution import LinearResolution
from Tribler.Core.dispersy.destination import CommunityDestination

# Delay for each message.
MSGDELAY=1.0

if __debug__:
    from Tribler.Core.dispersy.dprint import dprint

class AbstractGossipCommunity(Community):
    hardcoded_cid = "0792e0a3741c52fbb25bcfd172b695ad3c67b8f8".decode("HEX")
    hardcoded_master_public_key = "3081a7301006072a8648ce3d020106052b810400270381920004039a2b5690996f961998e72174a9cf3c28032de6e50c810cde0c87cdc49f1079130f7bcb756ee83ebf31d6d118877c2e0080c0eccfc7ea572225460834298e68d2d7a09824f2f0150718972591d6a6fcda45e9ac854d35af1e882891d690b2b2aa335203a69f09d5ee6884e0e85a1f0f0ae1e08f0cf7fbffd07394a0dac7b51e097cfebf9a463f64eeadbaa0c26c0660".decode("HEX")

#    @classmethod
#    def load_community(cls, master, my_member=None):
#        dispersy_database = DispersyDatabase.get_instance()
#        try:
#            dispersy_database.execute(u"SELECT 1 FROM community WHERE master = ?", (master.database_id,)).next()
#        except StopIteration:
#            return cls.join_community(master, my_member, my_member)
#        else:
#            return super(AbstractGossipCommunity, cls).load_community(master)

    def __init__(self, master):
        super(AbstractGossipCommunity, self).__init__(master)
        if __debug__: dprint('abstractgossipcommunity ' + self._cid.encode("HEX"))

        # Periodically we will send our data to other node(s).
        initialdelay = 15.0 # TODO
        self._dispersy.callback.register(self.active_thread, delay=initialdelay)

    def initiate_meta_messages(self):
        """Define the messages we will be using."""
        return [Message(self, u"modeldata",
                MemberAuthentication(encoding="sha1"), # Only signed with the owner's SHA1 digest
                PublicResolution(),
                DirectDistribution(),
#                FullSyncDistribution(), # Full gossip
                CommunityDestination(node_count=1), # Reach only one node each time.
                MessagePayload(),
                self.check_model,
                self.on_receive_model)]

    def initiate_conversions(self):
        return [DefaultConversion(self),
                JSONConversion(self)]

    def send_messages(self, messages):
        meta = self.get_meta_message(u"modeldata")

        send_messages = []

        for message in messages:
          assert isinstance(message, GossipMessage)

          # Create and implement message with 3 parameters
          send_messages.append(meta.impl(authentication=(self._my_member,),
                                   distribution=(self.global_time,),
                                   payload=(message,)))
          self._dispersy.store_update_forward(send_messages, store = False, update = False, forward = True)
#          self._dispersy.store_update_forward(send_messages, store = True, update = True, forward = True) # For testing

    def active_thread(self):
      raise NotImplementedError('active_thread')

    def check_model(self, messages):
      raise NotImplementedError('check_model')

    def on_receive_model(self, messages):
      raise NotImplementedError('on_receive_model')
