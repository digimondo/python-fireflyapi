import sys

PY3 = sys.version_info[0] == 3

if(PY3):
    string_types = str
else:
    string_types = basestring

from .util import HTTP_VERBS, PAYLOAD_ENCODING
from .api import API