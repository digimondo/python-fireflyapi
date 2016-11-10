from fireflyapi import api

if __name__ == "__main__":
    f_api = api.API(token='<your supersecret token>')

    for d in f_api.get_devices():
        print(d)
