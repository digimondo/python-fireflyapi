import time
from datetime import datetime
from abc import ABCMeta
from .api_entity import APIEntity


class DeviceClass(APIEntity):
    """
    Firefly device class entity.
    """

    __metaclass__ = ABCMeta

    _export = [
        'id', 'name', 'description', 'script', 'created', 'updated'
    ]

    api = None
    id = -1
    name = None
    script = None
    created = 0
    updated = 0

    def __init__(self, api=None, **args):
        self.api = api
        if ('inserted_at' in args):
            self.created = int(
                time.mktime(datetime.strptime(args.pop('inserted_at'), '%Y-%m-%dT%H:%M:%S').timetuple()))

        if ('updated_at' in args):
            self.updated = int(
                time.mktime(datetime.strptime(args.pop('updated_at'), '%Y-%m-%dT%H:%M:%S').timetuple()))

        self._exists = True
        self.__dict__.update(args)


    def export(self):
        return self._export

    def to_json(self, target, transcript={'created': 'inserted_at', 'updated': 'updated_at'}, exclude=['api']):
        return super(DeviceClass, self).to_json(target, transcript)
