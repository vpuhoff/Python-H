
#python Transfer.py --out_folder \\Torpedo3\vol1\IK0295\OUT\  --redis_host capman.ca.sbrf.ru --cmd_db 2 --store_db 3 --vault_host capman.ca.sbrf.ru --channels "['Test']"
import redis
import time
import json
import signal
import time
import sys

import hvac
import os
vault_token = os.environ['VAULT_TOKEN']

def GetSecret(Secret,Key):
    return vault.read('secret/'+Secret)["data"][Key]

import argparse
parser = argparse.ArgumentParser(description='')
parser.add_argument('--out_folder', dest='out_folder', action='store',
                    help='out folder path')
parser.add_argument('--redis_host', dest='host', action='store',
                    help='host of redis server')
parser.add_argument('--cmd_db', dest='cmd_db', action='store',
                    help='db for cmd data on redis server')  
parser.add_argument('--store_db', dest='store_db', action='store',
                    help='db for store data on redis server')        
parser.add_argument('--vault_host', dest='vault', action='store',
                    help='host of vault server')      
parser.add_argument('--channels', dest='channels', action='store',
                    help='list of channels')                 

transfer_tag = 'Transfer.'
raw_tag = 'Raw.'
args = parser.parse_args()
print(args)

import os, time
outFolder=args.out_folder
host = args.host
cmd_db = int(args.cmd_db)
store_db = int(args.store_db)
vault = hvac.Client(url='http://'+args.vault+':8200', token=vault_token)
redis_pass = GetSecret('CapmanRedis','Password')

redis_cmd = redis.StrictRedis(host, db=cmd_db, password=redis_pass)
redis_storage = redis.StrictRedis(host, db=store_db, password=redis_pass)

Receiver = redis_cmd.pubsub(ignore_subscribe_messages=False)

import uuid
uuid.uuid4()
import datetime
def GetUID():
    now = datetime.datetime.now()
    return '.'.join([str(now.year),str(now.month),str(now.day),str(now.hour),str(now.minute),str(now.second),str(now.microsecond),str(uuid.uuid4())])

def my_handler(message):
    channel = message["channel"].decode()
    if channel=='pMrbUEpRup7E5Jr':
        data = message["data"]
        key = GetUID()
        with open(outFolder+raw_tag+channel+'.'+key+".zip",'wb') as f:
            f.write(data)
            f.flush()
            f.close()
        print ('Message sended: ', channel,key,len(data))
    else:
        key = message["data"].decode()
        data = redis_storage.get(key)
        with open(outFolder+transfer_tag+channel+'.'+GetUID()+".zip",'wb') as f:
            f.write(data)
            f.flush()
            f.close()
        redis_storage.delete(key)
        print ('Message sended: ', channel,key,len(data))


def exit_gracefully(signum, frame):
    signal.signal(signal.SIGINT, original_sigint)
    sys.exit(1)
    signal.signal(signal.SIGINT, exit_gracefully)

Channels = eval(args.channels)
print('Scan channels:',Channels)
for channel in Channels:
    print(channel,'...')
    for key in redis_storage.scan_iter(channel+'.*'):
        channel = key.decode().split('.')[0]
        message=dict()
        print(channel)
        message["channel"]=channel.encode()
        message["data"]=key
        my_handler(message)


def CheckRedis():
    try:
        if redis_cmd.get(GetUID()):
            raise Exception('BadAnswer')
        if redis_storage.get(GetUID()):
            raise Exception('BadAnswer')    
        return False
    except Exception as e:
        return True
    
if __name__ == '__main__':
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, exit_gracefully)
    for channel in Channels:
        Receiver.subscribe(**{channel: my_handler})
    thread = Receiver.run_in_thread(sleep_time=1.101,daemon=True)
    while True:
        time.sleep(10)
        if 'stopped' in str(thread) or CheckRedis() :
            print('Reconnect...')
            try:
                redis_cmd = None
                redis_cmd = redis.StrictRedis("localhost", db=1)
                Receiver= None
                Receiver = redis_cmd.pubsub(ignore_subscribe_messages=True)
                for channel in Channels:
                    Receiver.subscribe(**{channel: my_handler})
                thread._delete()
                thread = None
                print('Reconnect... OK')
                thread = Receiver.run_in_thread(sleep_time=1.101,daemon=True)
            except:
                print('Reconnect failed...')
        
        print(thread)
        