from abc import ABCMeta
from .api_entity import APIEntity


class UpPacket(APIEntity):
    """
    Up Packet received by firefly
    """
    __metaclass__ = ABCMeta

    _export = [
        'ack', 'bandwidth', 'codr', 'datr', 'fopts', 'fcnt', 'freq', 'gwrx',
        'modu', 'mtype', 'parsed', 'payload', 'port', 'received_at', 'size',
        'spreading_factor'
    ]

    device = None
    ack = False
    bandwidth = None
    codr = None
    datr = None
    fopts = 0
    fcnt = 0
    freq = 0
    gwrx = {
        'gweui': None,
        'lsnr': 0,
        'rssi': 0,
        'time': 0,
        'tmst': 0
    }
    modu = None
    mtype = None
    parsed = None
    payload = None
    payload_encrypted = None
    port = 0
    received_at = 0
    size = 0
    spreading_factor = 0

    def __init__(self, device, **args):
        if('device_eui' in args):
            args.pop('device_eui')
        self.device = device

        # TODO: iso -> utc for ts

        self._exists = True
        self.__dict__.update(args)


class DownPacket(APIEntity):
    """
    down-packet sent to device
    """

    __metaclass__ = ABCMeta

    _export = [
        'ack', 'bandwidth', 'frame_counter', 'payload', 'received_at', 'rx_data', 'sent',
        'spreading_factor'
    ]

    ack = False
    bandwidth = 0
    frame_counter = 0
    parsed_packet = 0
    payload = None
    received_at = None
    rx_data = None
    sent = False
    spreading_factor = 0

    def __init__(self, device, args):
        if ('device_eui' in args):
            args.pop('device_eui')
        self.device = device

        # TODO: iso -> utc for ts

        self.__dict__.update(args)
