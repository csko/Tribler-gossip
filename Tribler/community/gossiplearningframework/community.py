from payload import MessagePayload, GossipMessage
from abstractcommunity import AbstractGossipCommunity

from models.logisticregression import LogisticRegressionModel
from models.adalineperceptron import AdalinePerceptronModel

# Send messages every 2 seconds.
DELAY=2.0

# Start after 15 seconds.
#INITIALDELAY=15.0

if __debug__:
    from Tribler.Core.dispersy.dprint import dprint

# TODO: refactor so that we can use many models
# TODO: queue support
class GossipLearningCommunity(AbstractGossipCommunity):

    def __init__(self, master):
        super(GossipLearningCommunity, self).__init__(master)
        if __debug__: dprint('gossiplearningcommunity' + self._cid.encode("HEX"))

        # Stats
        self._msg_count = 0

        # They should be loaded from a database.

        # x and y are stored only locally
        self._x = None
        self._y = None

        # Initial model
        self._model = AdalinePerceptronModel()
        self._model2 = LogisticRegressionModel()

    def active_thread(self):
        # "Active thread", send a message and wait delta time.
        while True:
            # TODO: queue
            self.send_messages([self._model])
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
              yield DropMessage(message, "Message must be a Gossip Message")

    def on_receive_model(self, messages):
        """
        One or more models have been received from other peers so we update and store.
        """
        # TODO: Use queue.
        for message in messages:
            # Stats.
            self._msg_count += 1
            dprint(("Received message:", message.payload.message))

            msg = message.payload.message

            assert isinstance(msg, GossipMessage)

            # Database not yet loaded.
            if self._x == None or self._y == None:
              dprint("Database not yet loaded.")
              continue

            # Update model.
            msg.update(self._x, self._y)

            # Store model.
            self._model = msg
