#!/usr/bin/python

from string import digits, letters, punctuation
from time import strftime

def _encode_str(l, value):
    assert isinstance(l, list)
    assert isinstance(value, str)
    for char in value:
        if not char in _printable:
            value = value.encode("HEX")
            l.extend(("h", str(len(value)), ":", value))
            break
    else:
        l.extend(("s", str(len(value)), ":", value))

def _encode_unicode(l, value):
    value = value.encode("UTF-8")
    for char in value:
        if not char in _printable:
            value = value.encode("HEX")
            l.extend(("H", str(len(value)), ":", value))
            break
    else:
        l.extend(("u", str(len(value)), ":", value))

def _encode_int(l, value):
    l.extend(("i", str(value)))

def _encode_float(l, value):
    l.extend(("f", str(value)))

def _encode_boolean(l, value):
    l.extend(("b", value and "True" or "False"))

def _encode_none(l, value):
    l.append("nNone")

def _encode_tuple(l, values):
    if values:
        l.extend(("t", str(len(values)), ":", "("))
        for value in values:
            _encode(l, value)
            l.append(", ")
        l[-1] = ")"
    else:
        l.append("t0:()")

def _encode_list(l, values):
    if values:
        l.extend(("l", str(len(values)), ":", "["))
        for value in values:
            _encode(l, value)
            l.append(", ")
        l[-1] = "]"
    else:
        l.append("l0:[]")

def _encode_dict(l, values):
    if values:
        l.extend(("m", str(len(values)), ":", "{"))
        for key, value in values.iteritems():
            _encode(l, key)
            l.append(":")
            _encode(l, value)
            l.append(", ")
        l[-1] = "}"
    else:
        l.append("m0:{}")

def _encode(l, value):
    if type(value) in _encode_mapping:
        _encode_mapping[type(value)](l, value)
    else:
        raise ValueError("Can not encode {0}".format(type(value)))

def log(filename, _message, **kargs):
    assert isinstance(_message, str)
    assert ";" not in _message

    global _encode_initiated
    if _encode_initiated:
        l = [strftime("%Y%m%d%H%M%S"), _seperator]
    else:
        _encode_initiated = True
        l = ["################################################################################", "\n",
             strftime("%Y%m%d%H%M%S"), _seperator, "s6:logger", _seperator, "event:s5:start", "\n",
             strftime("%Y%m%d%H%M%S"), _seperator]

    _encode_str(l, _message)
    for key in sorted(kargs.keys()):
        l.append(_seperator)
        l.extend((key, ":"))
        _encode(l, kargs[key])
    l.append("\n")
    s = "".join(l)

    # save to file
    open(filename, "a+").write(s)

def to_string(datetime, _message, **kargs):
    assert isinstance(_message, str)
    assert ";" not in _message
    l = [datetime.strftime("%Y%m%d%H%M%S"), _seperator]
    _encode_str(l, _message)
    for key in sorted(kargs.keys()):
        l.append(_seperator)
        l.extend((key, ":"))
        _encode(l, kargs[key])
    return "".join(l)

_printable = "".join((digits, letters, punctuation, " "))
_seperator = "   "
_valid_key_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_"
_encode_initiated = False
_encode_mapping = {str:_encode_str,
                   unicode:_encode_unicode,
                   int:_encode_int,
                   float:_encode_float,
                   bool:_encode_boolean,
                   type(None):_encode_none,
                   tuple:_encode_tuple,
                   list:_encode_list,
                   dict:_encode_dict}

