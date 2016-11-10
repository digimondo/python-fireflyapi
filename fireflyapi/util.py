from . import string_types
import types


def _enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    normal = dict((str(key), value) for key, value in enums.items())
    reverse = dict((value, str(key)) for key, value in enums.items())
    keys = [str(key[0]) for key in enums.items()]
    enums['mapping'] = normal
    enums['keys'] = keys
    enums['reverse_mapping'] = reverse
    enums['values'] = reverse.keys()
    #enums['has'] = lambda k: k in normal
    ret = type('Enum', (), enums)
    f_has = lambda self, k: k in self.keys
    ret.has = types.MethodType(f_has, ret)
    return ret

def is_string(s):
    return isinstance(s, string_types)

"""
HTTP 'verbs' enum
"""
HTTP_VERBS = _enum(GET=0, POST=1, PUT=2, DELETE=3, PATCH=4)

"""
PAYLOAD_ENCODING
"""
PAYLOAD_ENCODING = _enum(BASE16='Base16', BASE64='Base64', UTF_8='UTF-8')
