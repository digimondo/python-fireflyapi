from fireflyapi import api

if __name__ == "__main__":
    f_api = api.API(token='<your supersecret token>')

    dev = f_api.get_device(eui='<device_eui>')
    count, packets = dev.get_up_packets(limit_to_last=5)

    print("start_index: %s, total: %s" % count)
    for p in packets:
        print(p)
