from . import logger
from . import HTTP_VERBS
import sys
import logging
try:
    import ujson as json
except ImportError:
    import json
import requests
from .api_exception import APIException, EntityNotFoundError, EntityAlreadyCreatedError
from .device import Device
from .device_class import DeviceClass
from .application import Application


DEFAULT_HEADERS = {'Accept': 'application/json'}


class API(object):
    """
    firefly API wrapper defaults to https://fireflyiot.com:443/api/v1/, however server and baseurl might be
    set.

    :param token   : authtoken to access firefly API (must be set)
    :param server  : server dns or uri to connect to
    :param port    : server port (defaults to 443)
    :param version : api version (integer) v<version> (i.e. v1, v2, ...)
    :param base    : base uri (defaults to /api)
    :param loglevel: logging verbosity
    :param orga_id : organization id, not retrievable over REST-API
    """
    token = None

    version = 1
    base = 'api'
    server = 'fireflyiot.com'
    port = 443
    orga_id = 0

    def __init__(self, token=None, server=None, port=None, version=None, base=None, loglevel=logging.DEBUG, orga_id=0):
        self.loglevel = loglevel
        logger.setLevel(loglevel)

        if(not token or len(token) == 0):
            raise APIException('invalid token')

        if(server):
            self.server = server

        if(version):
            self.version = version

        if(base):
            self.base = base

        if(port):
            self.port = port

        self.token = token
        self.orga_id = orga_id
        self.init_logger()

    def init_logger(self):
        """
        Init api logging, override to use other handlers/formatters
        """
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(self.loglevel)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    def call(self, method, endpoint, query=None, data=None):
        """
        Basic call to REST API
        :param method  : HTTP Method to use (HTTP enum)
        :param endpoint: Endpoint to request
        :param query   : URL params as dict
        :param data    : data to be sent using POST/PUT/PATCH/...
        :return: the response object returned by the request
        """
        if(not query):
            query = {}

        # provide api key
        query.update({'auth': self.token})

        url = 'https://%s' % ('/'.join([
                '%s:%s' % (self.server, self.port),
                self.base, 'v%s' % self.version, endpoint
        ]))

        logger.debug('requesting [%s] : %s%s' % (HTTP_VERBS.reverse_mapping[method], url,
            '' if not query else '?%s' % '&'.join(['%s=%s' % (k, v) for k, v in query.items() if not k == 'auth'])))

        if(method == HTTP_VERBS.GET):
            response = requests.get(url=url, params=query, headers=DEFAULT_HEADERS)
        elif(method == HTTP_VERBS.POST):
            response = requests.post(url=url, params=query, json=data, headers=DEFAULT_HEADERS)
        elif (method == HTTP_VERBS.PUT):
            response = requests.put(url=url, params=query, json=data, headers=DEFAULT_HEADERS)
        elif (method == HTTP_VERBS.DELETE):
            response = requests.delete(url=url, params=query, headers=DEFAULT_HEADERS)

        logger.debug('successfully requested  %s' % url)
        if(data and not method in [HTTP_VERBS.GET,HTTP_VERBS.DELETE]):
            logger.debug('sent data: %s' % data)

        if(response.status_code >= 400):
            if('application/json' in response.headers.get('content-type', '')):
                logger.warn('HTTP Error [%s] : %s' % (response.status_code, response.content))
                if (response.status_code == 404):
                    raise EntityNotFoundError(response.json())
                elif (response.status_code == 422):
                    raise EntityAlreadyCreatedError(response.json())
                else:
                    raise APIException('HTTP Error [%s] : %s' %
                                        (response.status_code, response.content), response.json()
                                      )
            # dumb magic to get error message from html error page ;)
            elif ('html' in response.headers.get('content-type', '')):
                msgi = response.content.find('lead">')+6
                if(msgi>=0):
                    errmsg = response.content[msgi:response.content.find('</', msgi)]
                else:
                    errmsg = '--- unparseable error body type ---'

                if (response.status_code == 404):
                    raise EntityNotFoundError(errmsg)
                elif (response.status_code == 422):
                    raise EntityAlreadyCreatedError(errmsg)
                else:
                    raise APIException('HTTP Error [%s] : %s' % (response.status_code, errmsg))
            else:
                if (response.status_code == 404):
                    raise EntityNotFoundError(None)
                elif (response.status_code == 422):
                    raise EntityAlreadyCreatedError(None)
                else:
                    raise APIException('HTTP Error [%s] : %s' %
                                   (
                                        response.status_code,
                                        '--- unkown error body type %s---' %
                                        response.headers.get('content-type', None))
                                   )

        return response

    def get_devices(self, tags=None):
        """
        Get the list of devices accessible by the given API-Token
        :param tags: filter devices by given tags (list)
        :return: generator providing devices
        """
        query = {}

        if(tags and not isinstance(tags, list)):
            logger.warn('tags should be supplied as list')
            tags = [tags]

        if(tags):
            query = {'tags': ','.join(tags)}

        response = self.call(HTTP_VERBS.GET, 'devices', query=query)
        responsedata = response.json()

        if not responsedata['devices']:
            yield None

        for dev in responsedata['devices']:
            dev['_exists'] = True
            yield Device(self, **dev)

    def get_device(self, eui=None, address=None):
        """
        Get a single device either by it's eui or address (if both are set eui will be used to request device)
        :param eui      : the device's eui
        :param address  : the device's address
        :return: The fetched Device
        """
        if(not eui and not address):
            raise APIException('No identifier given')

        if(eui):
            response = self.call(HTTP_VERBS.GET, 'devices/eui/%s' % eui)
        elif(address):
            response = self.call(HTTP_VERBS.GET, 'devices/address/%s' % address)

        respdata = response.json()

        if(not 'device' in respdata):
            raise APIException('no such device %s="%s"' % ('eui' if eui else 'address', eui if eui else address))

        ret =Device(self, **respdata['device'])
        ret._exists = True
        return ret

    def get_device_classes(self):
        """
        Get the list of devices_classes accessible by the given API-Token
        :return: generator providing device classes
        """
        response = self.call(HTTP_VERBS.GET, 'device_classes/')

        respdata = response.json()

        for devc in respdata['device_classes']:
            yield DeviceClass(self, **devc)

    def get_applications(self):
        """
        Get the list of applications accessible by the given API-Token
        :return: generator providing applicatios
        """
        response = self.call(HTTP_VERBS.GET, 'applications/')

        respdata = response.json()

        for app in respdata['applications']:
            yield Application(self, **app)
