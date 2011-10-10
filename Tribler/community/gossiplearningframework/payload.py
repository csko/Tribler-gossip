from Tribler.Core.dispersy.payload import Payload

class MessagePayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, message):
            # TODO: assertions on message
            assert isinstance(message, GossipMessage)
            super(MessagePayload.Implementation, self).__init__(meta)
            self._message = message

        @property
        def message(self):
            return self._message

class GossipMessage:
    pass

class LinearMessage(GossipMessage):

  def __init__(self):
    self.w = []

class TreeMessage(GossipMessage):

  def __init__(self):
    self.mu0 = 0
    self.q = LinearMessage()
    self.q.w = [15]
