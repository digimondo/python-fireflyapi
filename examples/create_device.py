from fireflyapi import api
from fireflyapi.api_exception import APIException
from fireflyapi.device import Device

if __name__ == "__main__":
    f_api = api.API(token='<your supersecret token>', orga_id='<your orga id>')  # orga id is *not* retrievable ...

    device = Device(
        f_api, otaa=True,
        name='Dummy Test device',
        eui='abcdefabcdefabcd',
        application_key='abcdefabcdefabcdefabcdefabcdabcd',
        application=1
    )  # ... *nor* is the app id

    try:
        # this won't work, as the device is not yet created remotely !
        device.get_up_packets()
    except APIException as apie:
        print('ERROR: %s' % apie)

    device.create()
    print("up packets %s" % device.get_up_packets()[0][0])
