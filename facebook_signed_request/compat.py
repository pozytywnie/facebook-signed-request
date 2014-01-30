import hashlib as _hashlib
import sys

IS_PYTHON2 = sys.version_info.major == 2

if IS_PYTHON2:
    str_class = basestring
else:
    str_class = str


class LibWrapper(object):
    __lib = None

    def getattr(self, attr):
        return getattr(self.lib, attr)

if IS_PYTHON2:
    class HashLibWrapper(LibWrapper):
        __lib = _hashlib
        algorithms_available = _hashlib.algorithms
    hashlib = HashLibWrapper()
else:
    hashlib = _hashlib
