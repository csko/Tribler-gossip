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

class GossipMessage(object):
    pass
