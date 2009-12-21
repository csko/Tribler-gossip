# Written by Boudewijn Schoon
# see LICENSE.txt for license information
"""
Alternate stdout and stderr with much more protection
"""

import sys 

class SafePrintStream:
    def __init__(self, stream):
        self._stream = stream

    def write(self, arg):
        self._stream.write(arg.encode("ASCII", "backslashreplace"))
        
    def flush(self):
        self._stream.flush()

class SafeLinePrintStream:
    def __init__(self, stream):
        self._stream = stream
        self._parts = []

    def write(self, arg):
        self._parts.append(arg.encode("ASCII", "backslashreplace"))
        if arg == "\n":
            self._stream.write("".join(self._parts))
            self._parts = []
        
    def flush(self):
        self._stream.write("".join(self._parts))
        self._parts = []
        self._stream.flush()
        
sys.stderr = SafeLinePrintStream(sys.stderr)
sys.stdout = sys.stderr
