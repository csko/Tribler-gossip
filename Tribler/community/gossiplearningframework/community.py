from conversion import Conversion
from payload import MessagePayload, LinearMessage, GossipMessage
from abstractcommunity import AbstractGossipCommunity

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

# Send messages every 3 seconds.
DELAY=3.0

# Start after 1 second.
INITIALDELAY=1.0

if __debug__:
    from Tribler.Core.dispersy.dprint import dprint

class GossipLearningCommunity(AbstractGossipCommunity):

    def __init__(self, cid, master_public_key):
        super(GossipLearningCommunity, self).__init__(cid, master_public_key, INITIALDELAY)
        if __debug__: dprint('gossiplearningcommunity' + self._cid.encode("HEX"))

        # The (now static) message we will be sending. These parameters will be used to create the payload.

        # x and y are stored only locally
        # TODO: load from database
        self._x = [3, 4]
        self._y = 1.0

        # Initial model
        self._message = LinearMessage()
        self._message.w = [0, 0]
        self._message.age = 0

    def active_thread(self):
        # "Active thread", send a message and wait delta time.
        while True:
            self.send_messages([self._message])
            yield DELAY

    def check_model(self, messages):
        """
        One or more models have been received, we check them for validity.
        This is a generator function and we can either forward a message or drop it.
        """
        for message in messages:
            print message
            if isinstance(message.payload.message, GossipMessage):
              age = message.payload.message.age
              if not type(age) == int or age < 0:
                yield DropMessage(message, "Age must be a nonnegative integer in this protocol.")
              else:
                yield message # Accept message.
            else:
              yield DropMessage(message, "Message must be a Gossip Message")

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

            msg = message.payload.message

            assert isinstance(msg, GossipMessage)


            # Set up some variables.
            age = msg.age + 1
            rate = 1.0 / age
            x = self._x
            label = self._y

            # Perform the Adaline update: w_{i+1} = w_i + eta_i * (y - w' * x) * x.
            # Assume the same size (TODO).
            w = self._message.w
            wx = sum([wi * xi for (wi,xi) in zip(w, x)])
            dprint(wx)
            self._message.w = [w[i] + rate * (label - wx) * x[i] for i in range(len(w))]
            dprint(self._message.w)

    def predict(self, x):
      # Calculate w' * x.
      w = self._message.w
      wx = sum([wi * xi for (wi,xi) in zip(w, x)])

      # Return sign(w' * x).
      return 1.0 if wx >= 0 else 0.0
