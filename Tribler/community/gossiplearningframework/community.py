from conversion import Conversion
from payload import MessagePayload, LinearMessage, GossipMessage

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

# Send every 5 seconds.
DELAY=5.0

if __debug__:
    from Tribler.Core.dispersy.dprint import dprint

class VotingTestCommunity(Community):
    # Identifier used for 5.4.0 debugging
    hardcoded_cid = "61d3ec235ebefc4b5ae1959619f33afb46b9729d".decode("HEX")
    hardcoded_master_public_key = "3081a7301006072a8648ce3d020106052b810400270381920004054a2ad3d209398195ef97d34743a61a26cc2ba995827d4d06a58818f3ef64a8995ad308e68c54abb79fba03cfb55a4d37b902bc8fb4a5f5743a32df87dd1e2367ddf2f627fb2800036b9392afc9d05d72cd3e14f5b5348344293ffaadf37750bb4c4ee3c0c0bc46dc31aad4945c73aa5ca339b223ab0d84d5bcfff3f9a3d6c762ca4e1dc762a183d93454043d8fd3ea".decode("HEX")

    @classmethod
    def join_hardcoded_community(cls, my_member):
        # ensure that the community has not already been loaded (as a HardKilledCommunity)
        if not Dispersy.get_instance().has_community(cls.hardcoded_cid):
            return cls.join_community(cls.hardcoded_cid, cls.hardcoded_master_public_key, my_member)

    @classmethod
    def load_hardcoded_community(cls):
        # ensure that the community has not already been loaded (as a HardKilledCommunity)
        if not Dispersy.get_instance().has_community(cls.hardcoded_cid):
            return cls.load_community(cls.hardcoded_cid, cls.hardcoded_master_public_key)

    def __init__(self, cid, master_public_key):
        super(VotingTestCommunity, self).__init__(cid, master_public_key)
        if __debug__: dprint(self._cid.encode("HEX"))

        # The (now static) message we will be sending. These parameters will be used to create the payload.
        self._message = LinearMessage()
        self._message.w = [1,2]

        # Periodically we will send our data to ther node(s).
        self._dispersy.callback.register(self._periodically_send_model, delay=DELAY)

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
                self.on_receive_model,
                delay=DELAY)]

    def initiate_conversions(self):
        return [DefaultConversion(self),
                Conversion(self)]

    def _periodically_send_model(self):
        meta = self.get_meta_message(u"modeldata")
        if __debug__:
            dprint(meta)

        # TODO: Reuse code?
        assert isinstance(self._message, GossipMessage)

        # "Active thread", send a message and wait delta time.
        while True:
            # Create and implement message with 3 parameters
            message = meta.implement(meta.authentication.implement(self._my_member),
                                     meta.distribution.implement(self.global_time),
#                                     meta.distribution.implement(self.claim_global_time()),
                                     meta.destination.implement(),
#                                     meta.destination.implement(True),
                                     meta.payload.implement(self._message))
            self._dispersy.store_update_forward([message], False, False, True)
#            self._dispersy.store_update_forward([message], True, True, True) # For testing

            # wait some time and make a new message
            yield DELAY

    def check_model(self, messages):
        """
        One or more models have been received, we check them for validity.
        This is a generator function and We can either forward a message or drop it.
        """
        for message in messages:
            # Example.
            if message.number == 1234.0:
                yield DropMessage("1234.0 is an invalid number in this protocol.")
            else:
                yield message # Accept message.

    def on_receive_model(self, messages):
        """
        One or more models have been received from other peers so we update.
        """
        for message in messages:
            dprint("Message")
            dprint(message)
            dprint(message.payload)
            dprint(("Received message:", message.payload.message))
            dprint(message.payload.message.w)
        # TODO: update.
