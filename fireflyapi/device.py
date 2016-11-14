from . import HTTP_VERBS, PAYLOAD_ENCODING, logger
import time
from datetime import datetime
from .api_entity import APIEntity, exists, not_exists
from .observable import Observable
from .api_exception import APIException, EntityAlreadyCreatedError, EntityNotFoundError
from .util import is_string
import base64
import numbers
import struct
import binascii
from . import PY3

try:
    import ujson as json
except ImportError:
    import json

from .packet import UpPacket, DownPacket


class Device(Observable, APIEntity):
    """
    A Device. Usually fetched from API but might also be created using the constructor.

    :param api : API reference

    :param eui : device EUI
    :param otaa : device is OTAA capable (True|False), defaults to False

    :param name : device friendly name (optional)
    :param description : device textual description (optional)
    :param tags : list of tags associated with this device (optional)

    :param application_key : if device is otaa capable, an application key MUST be set

    :param application_session_key : if device activates using ABP, this needs to be set
    :param network_session_key : if device activates using ABP, this needs to be set

    :param device_class: device class reference (optional)


    """
    #__slots__ = [
    #    'eui', 'name', 'description', 'created', 'updated',
    #    'otaa', 'network_session_key', 'application_session_key',
    #    'application_key', 'tags'
    #]

    #TODO: device class support
    _export = {
        'eui', 'name', 'address', 'description',
        'otaa', 'network_session_key', 'application_session_key',
        'application_key', 'tags', 'class_c'
    }

    api = None
    device_class = None

    eui = None
    name = None
    address = None
    description = None
    created = 0
    updated = 0
    otaa = False
    network_session_key = None
    application_session_key = None
    application_key = None
    tags = []
    application = 1  # application (internal) id, might be needet for creation
    class_c = False

    def __init__(self, api=None, **args):
        self.api = api
        # TODO: check for required fields !

        if('created_at' in args):
            self.created = int(time.mktime(datetime.strptime(args.pop('created_at'), '%Y-%m-%dT%H:%M:%S').timetuple()))

        if('updated_at' in args):
            self.updated = int(time.mktime(datetime.strptime(args.pop('updated_at'), '%Y-%m-%dT%H:%M:%S').timetuple()))

        if('tags' in args):
            if(not isinstance(args['tags'],list) and isinstance(args['tags'],basestring)):
                self.tags = args.pop('tags').split(',')

        _argcheck(args)

        #this can be dangerous ;)
        self.__dict__.update(args)
        self._not_dirty()

    def to_json(self, target=None):
        if(target=='update'):
            return self.to_json(target, exclude=['created', 'updated'])

        else:
            ret = {
                    'eui': self.eui,
                    'name': self.name,
                    'address': self.address,
                    'description': self.description,
                    'created_at': None,
                    'updated_at': None,
                    'otaa': self.otaa,
                    'network_session_key':self.network_session_key,
                    'application_session_key': self.application_session_key,
                    'application_key': self.application_key,
                    'class_c': self.class_c
            }

        return json.dumps(ret)

    @exists
    def get_up_packets(self, limit_to_last=1, offset=0, received_after=0):
        """
        Get device's down packets
        :param limit_to_last:   1 to 100
        :param offset:          offset value, ignore packets #<offset
        :param received_after:  only packets received after a specific date
        :return: a tuple containing a tuple with the packets start index (regarding offset/limit) and device's total
                 packet count as well as a generator providing fetched packets
        """
        query = {
            'limit_to_last': limit_to_last
        }

        if(offset>0):
            query['offset'] = offset

        if(received_after):
            #TODO: support datetime inst
            query['received_after'] = received_after

        res = self.api.call(HTTP_VERBS.GET, 'devices/eui/%s/packets' % self.eui, query=query)

        if (res.status_code == 404):
            raise EntityNotFoundError(res.json())

        resdata = res.json()
        return (resdata['count']-offset-limit_to_last, resdata['count']), _pkg_gen(self, resdata['packets'])

    @exists
    def get_down_packets(self, limit_to_last=1, offset=0, received_after=0):
        """
        Get device's down packets
        :param limit_to_last:   1 to 100
        :param offset:          offset value, ignore packets #<offset
        :param received_after:  only packets received after a specific date
        :return: a tuple containing a tuple with the packets start index (regarding offset/limit) and device's total
                 packet count as well as a generator providing fetched packets
        """
        query = {
            'limit_to_last': limit_to_last
        }

        if (offset > 0):
            query['offset'] = offset

        if (received_after):
            # TODO: support datetime inst
            query['received_after'] = received_after

        res = self.api.call(HTTP_VERBS.GET, 'devices/eui/%s/down_packets' % self.eui, query=query)

        if(res.status_code==404):
            raise EntityNotFoundError(res.json())

        resdata = res.json()
        return (resdata['count']-offset-limit_to_last, resdata['count']), _pkg_gen(self, resdata['packets'])

    @exists
    def get_all_up_packets(self, chunksize=100):
        """
        contineous stream all device up-packets, will lead to a lot of requests (depending on the total packet count and
        chunksize)
        :param chunksize : how many packets to fetch at a time
        :return: a generator for all packets of this device
        """
        count, last = self.get_up_packets()
        ucnt = 0
        dcnt = count[1]
        while(dcnt-chunksize>0):
            pc, pkts = self.get_up_packets(limit_to_last=chunksize, offset=ucnt)
            for p in pkts:
                yield p
            ucnt += chunksize
            dcnt -= chunksize

    @exists
    def delete(self):
        """
        Delete this device using the API
        """
        logger.info('deleting device %s' % self.eui)
        self.api.call(HTTP_VERBS.DELETE, 'devices/eui/%s' % self.eui)

        self._exists = False
        self._not_dirty()

    @exists
    def update(self):
        """
        Update this device using the API
        """
        logger.info('updating device %s' % self.eui)
        self.api.call(HTTP_VERBS.PUT, 'devices/eui/%s' % self.eui, data=self.to_json('update'))
        self._not_dirty()

    @exists
    def pull(self):
        """
        update local device instance
        """
        response = self.api.call(HTTP_VERBS.GET, 'devices/eui/%s' % self.eui)

        respdata = response.json()

        if (not 'device' in respdata):
            raise APIException('no such device eui="%s"' % self.eui)

        self.__dict__.update(respdata['device'])

    @exists
    def send_packet(self, payload, encoding=None, port=1, force_encode=False):
        """
        Sends a packet to the device
        :param payload:         Payload string. If encoding is forced, payload might be anything native(s) to objects
        :param encoding:        Payload encoding Base16, Base64, UTF-8
        :param port:            Package port number
        :param force_encode:    Encode payload to match encoding
        """
        if(not payload):
            raise APIException('empty payload')

        if (not encoding and force_encode):
            logger.warn('no encoding given but force encoding requested, defaulting to Base64')
            encoding = PAYLOAD_ENCODING.BASE64

        if(force_encode and not PAYLOAD_ENCODING.f_has(encoding)):
            raise APIException('unknown payload encoding')

        if(not force_encode and not is_string(payload)):
            raise APIException('payload must be a string if not forcing encode')

        data = {
            'encoding': encoding,
            'payload': _encode_payload(payload) if force_encode else payload,
            'port': port
        }

        self.api.call(HTTP_VERBS.POST, 'devices/eui/%s/packet' % self.eui, data=data)

    def export(self):
        return self._export

    @not_exists
    def create(self):
        """
        Create this device by Posting to the API
        """
        if(not self.api.orga_id):
            raise APIException('No organization id specified in API')


        reqdata = {
            'organization': self.api.orga_id,
            'device': {
                'eui': self.eui,
                'name': self.name,
                'description': self.description,
                'otaa': self.otaa,
                'class_c': self.class_c
            }
        }

        if(self.otaa):
            reqdata['device']['application_key'] = self.application_key
        else:
            reqdata['device']['network_session_key'] = self.network_session_key
            reqdata['device']['application_session_key'] = self.application_session_key
            reqdata['device']['address'] = self.address

        if(self.tags):
            reqdata['tags'] = ','.join(self.tags)
            if (self.application):
                reqdata['application'] = self.application

        res = self.api.call(HTTP_VERBS.POST, 'devices', data=reqdata)

        self._exists = True
        self.__dict__.update(res.json()['device'])
        self._not_dirty()


def _argcheck(*kwargs):
    # TODO: check **args when creating or leave this to the API ?
    pass

# TODO: there are dozens of more variants to encode a varible type of data, investigate and implement some more ;)
def _encode_payload(payload, encoding):
    if(encoding == PAYLOAD_ENCODING.UTF_8):
        if(is_string(payload)):
            if(not PY3):
                return unicode(payload)
            else:
                return payload
        elif(isinstance(payload, numbers.Number)):
            return str(payload)
        else:
            raise APIException('given payload is not encodeable using %s' % encoding)
    elif(encoding == PAYLOAD_ENCODING.BASE64):
        if (is_string(payload)):
            return base64.b64encode(payload)
        elif(isinstance(payload, int)):
            return base64.b64encode(struct.pack('i', payload))
        elif(isinstance(payload, float)):
            return base64.b64encode(struct.pack('f', payload))
        elif(isinstance(payload, numbers.Number)):
            return base64.b64encode(struct.pack('q', payload))
        else:
            raise APIException('given payload is not encodeable using %s' % encoding)
    elif(encoding == PAYLOAD_ENCODING.BASE16):
        if (is_string(payload)):
            return binascii.hexlify(payload)
        elif(isinstance(payload, (int, long))):
            return format(payload, 'x')
        elif (isinstance(payload, float)):
            return binascii.hexlify(struct.pack('f', payload))
        elif (isinstance(payload, numbers.Number)):
            return binascii.hexlify(struct.pack('q', payload))

def _pkg_gen(device, pkgs, _up=True):
    if(not pkgs):
        yield None
    for p in (pkgs):
        if(_up):
            up = UpPacket(device, **p)
            up._exists = True
            yield up
        else:
            dn = DownPacket(device, **p)
            dn._exists = True
            yield dn
