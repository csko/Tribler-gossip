from struct import pack, unpack_from
from json import dumps, loads

from Tribler.Core.dispersy.message import DropPacket
from Tribler.Core.dispersy.conversion import BinaryConversion

if __debug__:
    from Tribler.Core.dispersy.dprint import dprint

class Conversion(BinaryConversion):
    def __init__(self, community):
        super(Conversion, self).__init__(community, "\x01") # Community version 1
        # Message type ID 1
        self.define_meta_message(chr(1), community.get_meta_message(u"modeldata"), self._encode_text, self._decode_text)

    def _encode_text(self, message):
        assert len(message.payload.text.encode("UTF-8")) < 256
        assert len(message.payload.array) < 100

        text = message.payload.text.encode("UTF-8")
        structure = {'text': text, 'number': message.payload.number, 'array': message.payload.array}

        wiredata = dumps(structure).encode("UTF-8")
        assert len(wiredata) < 2**16
        if __debug__: dprint(wiredata)

        # Encode the length on 2 bytes, network byte order. The wire data follows.
        return pack("!H", len(wiredata)), wiredata

    def _decode_text(self, meta_message, offset, data):
        if len(data) < offset + 1:
            raise DropPacket("Insufficient packet size")

        data_length, = unpack_from("!H", data, offset)
        offset += 2

        try:
            wiredata = loads(data[offset:offset + data_length].decode("UTF-8"))
            offset += data_length
        except UnicodeError:
            raise DropPacket("Unable to decode UTF-8")

        return offset, meta_message.payload.implement(wiredata['text'], wiredata['number'], wiredata['array'])

