from abc import ABCMeta, abstractmethod
try:
    import ujson as json
except ImportError:
    import json


class JSONDump(object):
    """
    Object type that provides basic json dump mechanisms and supports transcription
    """
    __metaclass__ = ABCMeta

    def to_json(self, target=None, exclude=None, transcript=None):
        """
        Get a json representation of all members returned from export()
        :param target:      target
        :param exclude:
        :param transcript:
        :return:
        """
        members = {k: v for k, v in self.__dict__.items() if k in dir(self)}
        export = self.export()
        if(not export):
            dt = members
        else:
            dt = {k: members.get(k, None) for k in export}

        # transcript
        if(transcript):
            ret = {}

            for k, v in dt.items():
                if(k in transcript):
                    ret[transcript[k]] = v
                else:
                    ret[k] = v

            return json.dumps(ret)
        else:
            return json.dumps(dt)

    @abstractmethod
    def export(self):
        return None

    def __str__(self):
        return self.to_json('debug')
