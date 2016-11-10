import time
from datetime import datetime
from abc import ABCMeta
from .api_entity import APIEntity


class Application(APIEntity):
    """
    Firefly application entity.
    """
    __metaclass__ = ABCMeta

    _export = [
        'id', 'eui', 'name', 'description', 'sink', 'created', 'updated'
    ]

    api = None
    id = -1
    eui = None
    name = None
    description = None
    created = 0
    updated = 0
    sink = None

    def __init__(self, api, **args):
        self.api = api
        if ('created_at' in args):
            self.created = int(
                time.mktime(datetime.strptime(args.pop('created_at'), '%Y-%m-%dT%H:%M:%S').timetuple()))

        if ('updated_at' in args):
            self.updated = int(
                time.mktime(datetime.strptime(args.pop('updated_at'), '%Y-%m-%dT%H:%M:%S').timetuple()))

        self._exists = True
        self.__dict__.update(args)

    def export(self):
        return self._export

    def to_json(self, target, transcript={'created': 'inserted_at', 'updated': 'updated_at'}, exclude=['api']):
        return super(Application, self).to_json(target, transcript)
