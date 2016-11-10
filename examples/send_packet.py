from fireflyapi import api, PAYLOAD_ENCODING

if __name__ == "__main__":
    f_api = api.API(token='<your supersecret token>')

    dev = f_api.get_device(eui='abcdefabcdefabcd')
    dev.send_packet(encoding=PAYLOAD_ENCODING.BASE16, payload='DEADBEEF')
