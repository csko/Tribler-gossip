from Tribler.Core.dispersy.payload import Payload

class MixedPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, text, number, array):
            assert isinstance(text, unicode)
            assert isinstance(number, float)
            assert isinstance(array, list)
            assert len(text.encode("UTF-8")) < 256
            assert len(array) < 100
            super(MixedPayload.Implementation, self).__init__(meta)
            self._text = text
            self._number = number
            self._array = array

        @property
        def text(self):
            return self._text

        @property
        def number(self):
            return self._number

        @property
        def array(self):
            return self._array

