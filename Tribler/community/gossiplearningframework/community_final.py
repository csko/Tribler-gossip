from Tribler.Core.dispersy.authentication import MemberAuthentication
from Tribler.Core.dispersy.community import Community
from Tribler.Core.dispersy.conversion import DefaultConversion
from Tribler.Core.dispersy.message import DropMessage
from Tribler.Core.dispersy.distribution import DirectDistribution
from Tribler.Core.dispersy.member import Member
from Tribler.Core.dispersy.resolution import PublicResolution

from Tribler.Core.dispersy.destination import SubjectiveDestination
from Tribler.Core.dispersy.dispersy import Dispersy
from Tribler.Core.dispersy.dispersydatabase import DispersyDatabase
from Tribler.Core.dispersy.distribution import FullSyncDistribution, LastSyncDistribution
from Tribler.Core.dispersy.message import Message, DelayMessageByProof
from Tribler.Core.dispersy.resolution import LinearResolution
from Tribler.Core.dispersy.destination import CommunityDestination

from conversion import JSONConversion

from collections import deque

from payload import MessagePayload, GossipMessage
from models.logisticregression import LogisticRegressionModel
from models.adalineperceptron import AdalinePerceptronModel
from models.p2pegasos import P2PegasosModel

# Send messages every 1 seconds.
DELAY=1.0

# Start after 15 seconds.
INITIALDELAY=15.0

# Model queue size.
MODEL_QUEUE_SIZE=10

if __debug__:
    from Tribler.Core.dispersy.dprint import dprint

class GossipLearningCommunity(Community):
    @classmethod
    def get_master_members(cls):
        master_key = "3081a7301006072a8648ce3d020106052b810400270381920004039a2b5690996f961998e72174a9cf3c28032de6e50c810cde0c87cdc49f1079130f7bcb756ee83ebf31d6d118877c2e0080c0eccfc7ea572225460834298e68d2d7a09824f2f0150718972591d6a6fcda45e9ac854d35af1e882891d690b2b2aa335203a69f09d5ee6884e0e85a1f0f0ae1e08f0cf7fbffd07394a0dac7b51e097cfebf9a463f64eeadbaa0c26c0660".decode("HEX")
        master = Member.get_instance(master_key)
        return [master]

    @classmethod
    def load_community(cls, master, my_member):
        dispersy_database = DispersyDatabase.get_instance()
        try:
            dispersy_database.execute(u"SELECT 1 FROM community WHERE master = ?", (master.database_id,)).next()
        except StopIteration:
            return cls.join_community(master, my_member, my_member)
        else:
            return super(GossipLearningCommunity, cls).load_community(master)

    def __init__(self, master):
        super(GossipLearningCommunity, self).__init__(master)
        if __debug__: dprint('gossiplearningcommunity ' + self._cid.encode("HEX"))

        # Periodically we will send our data to other node(s).
        self._dispersy.callback.register(self.active_thread, delay=INITIALDELAY)

        # Stats
        self._msg_count = 0

        # These should be loaded from a database.

        # x and y are stored only locally in the list called _local_database
	self._local_database = None

        self._model_queue = deque(maxlen=MODEL_QUEUE_SIZE)

        # Initial model
        # initmodel = AdalinePerceptronModel()
        # initmodel = LogisticRegressionModel()
        initmodel = P2PegasosModel()

        self._model_queue.append(initmodel)

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
          # if __debug__: dprint("GOSSIP: calling self._dispersy.store_update_forward(%s, store = False, update = False, forward = True)." % send_messages)
          self._dispersy.store_update_forward(send_messages, store = False, update = False, forward = True)
#          self._dispersy.store_update_forward(send_messages, store = True, update = True, forward = True) # For testing

    def active_thread(self):
        """
        Active thread, send a message and wait delta time.
        """
        while True:
            # Send the last model in the queue.
            self.send_messages([self._model_queue[-1]])
            yield DELAY

    def check_model(self, messages):
        """
        One or more models have been received, we check them for validity.
        This is a generator function and we can either forward a message or drop it.
        """
        for message in messages:
            if isinstance(message.payload.message, GossipMessage):
                age = message.payload.message.age
                if not type(age) == int or age < 0:
                    yield DropMessage(message, "Age must be a nonnegative integer in this protocol.")
                else:
                    yield message # Accept message.
            else:
                yield DropMessage(message, "Message must be a Gossip Message.")

    def on_receive_model(self, messages):
        """
        One or more models have been received from other peers so we update and store.
        """
        for message in messages:
            # Stats.
            self._msg_count += 1
            if __debug__: dprint(("Received message:", message.payload.message))

            msg = message.payload.message

            assert isinstance(msg, GossipMessage)

            # Database was not initialized by the script
	    if self._local_database == None:
                if __debug__: dprint("Database was not initialized by the script.")
		continue

            # Create and store new model using one strategy.
            self._model_queue.append(self.create_model_mu(msg, self._model_queue[-1]))

    def update(self, model):
        """Update a model using all local training examples."""
        for (x, y) in self._local_database:
            model.update(x, y)

    def create_model_rw(self, m1, m2):
        self.update(m1)
        return m1

    def create_model_mu(self, m1, m2):
        m1.merge(m2)
        self.update(m1)
        return m1

    def create_model_um(self, m1, m2):
        self.update(m1)
        self.update(m2)
        m1.merge(m2)
        return m1

    def predict(self, x):
        """Predict with the last model in the queue."""
        return self._model_queue[-1].predict(x)

