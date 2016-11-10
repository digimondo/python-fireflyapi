from .api_exception import APIException
from .json_dump import JSONDump
from abc import ABCMeta


class APIEntity(JSONDump):
    """
    APIEntity Baseclass
    """
    __metaclass__ = ABCMeta

    _exists = False
    _export = []

    def export(self):
        return self._export


# existance decorator, will fail if ent does not yet exist
def exists(func):
    def wrap(self, *args, **kwargs):
        if(isinstance(self, APIEntity.__class__) and not self._exists):
            raise APIException('%s is no API entity instance' % self.__class__.__name__)

        if(not self._exists):
            raise APIException('%s is not yet created remotely' % self.__class__.__name__)

        return func(self, *args, **kwargs)
    return wrap


# (not)existance decorator, will fail if ent does exist
def not_exists(func):
    def wrap(self, *args, **kwargs):
        if(isinstance(self, APIEntity.__class__) and not self._exists):
            raise APIException('%s is no API entity instance' % self.__class__.__name__)

        if(self._exists):
            raise APIException('%s is already created remotely' % self.__class__.__name__)

        return func(self, *args, **kwargs)
    return wrap
