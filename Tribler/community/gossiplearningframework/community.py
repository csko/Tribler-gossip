from random import choice

from conversion import Conversion
from payload import TextPayload

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

from Tribler.Core.Statistics.Status.NullReporter import NullReporter
from Tribler.Core.Statistics.Status.Status import get_status_holder
from Tribler.Core.Statistics.Status.TUDelftReporter import TUDelftReporter

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

        # A container for the votes
        self._queue = []

        # initially we either choose yes or no at random
        self._choice = choice(["yes", "no"])

        # periodically we will tell other nodes out choice
        self._dispersy.callback.register(self._periodically_tell_choice, delay=DELAY)

    def initiate_meta_messages(self):
        return [Message(self, u"choice",
                MemberAuthentication(encoding="sha1"), # Only signed with the owner's SHA1 digest
                PublicResolution(),
                DirectDistribution(),
#                FullSyncDistribution(), # Full gossip
                CommunityDestination(node_count=1),
                TextPayload(),
                self.check_choice,
                self.on_choice,
                delay=DELAY)]

    def initiate_conversions(self):
        return [DefaultConversion(self),
                Conversion(self)]

    def _periodically_tell_choice(self):
        meta = self.get_meta_message(u"choice")
        dprint(meta)
        dprint(self._choice)
        choice = unicode(self._choice)
        assert isinstance(choice, unicode)
        while True:
            # create message with my choice
            message = meta.implement(meta.authentication.implement(self._my_member),
                                     meta.distribution.implement(self.global_time),
#                                     meta.distribution.implement(self.claim_global_time()),
                                     meta.destination.implement(),
#                                     meta.destination.implement(True),
                                     meta.payload.implement(choice))
#                                     meta.payload.implement(text))
            self._dispersy.store_update_forward([message], False, False, True)
#            self._dispersy.store_update_forward([message], True, True, True)

            # wait some time and make a new message
            yield DELAY

    def check_choice(self, messages):
        """
        Check one or more 'choice' messages that have been received.
        """
        # since we allow any text to be put in our messages, we much ensure that it is either "yes"
        # or "no"
        dprint("check_choice")
        for message in messages:
            if message.payload.text in ("yes", "no"):
                yield message
            else:
                yield DropMessage("The choice should be either 'yes' or 'no'")

    def on_choice(self, messages):
        """
        One or more 'choice' messages have been received.
        """
        # add choices to the queue
        for message in messages:
            self._queue.append(message.payload.text)
        dprint("Received message!")
        dprint(self._queue)

        # when we have two or more choices we will make a new choice
        if len(self._queue) > 1:
            yes_votes = 1 if self._choice == "yes" else 0
            no_votes = 1 if self._choice == "no" else 0
            for vote in self._queue:
                if vote == "yes":
                    yes_votes += 1
                else:
                    assert vote == "no"
                    no_votes += 1

            # our new choice is...
            if yes_votes != no_votes:
                self._choice = "yes" if yes_votes > no_votes else "no"
            dprint("New vote: %s" % self._choice)

