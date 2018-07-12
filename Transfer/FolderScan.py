#python FolderScan.py --in_folder \\Torpedo3\vol1\IK0295\IN\  --redis_host capman.ca.sbrf.ru --cmd_db 2 --store_db 3 --vault_host  capman.ca.sbrf.ru
#
import hvac
import os
vault_token = os.environ['VAULT_TOKEN']

def GetSecret(Secret,Key):
    return vault.read('secret/'+Secret)["data"][Key]

import argparse
parser = argparse.ArgumentParser(description='In folder path',)
parser.add_argument('--in_folder', dest='in_folder', action='store',
                    help='in folder path')
parser.add_argument('--redis_host', dest='host', action='store',
                    help='host of redis server')
parser.add_argument('--cmd_db', dest='cmd_db', action='store',
                    help='db for cmd data on redis server')  
parser.add_argument('--store_db', dest='store_db', action='store',
                    help='db for store data on redis server')        
parser.add_argument('--vault_host', dest='vault', action='store',
                    help='host of vault server')                  

transfer_tag = 'Transfer.'
args = parser.parse_args()
print(args)

import os, time
in_folder = args.in_folder
host = args.host
cmd_db = int(args.cmd_db)
store_db = int(args.store_db)
vault = hvac.Client(url='http://'+args.vault+':8200', token=vault_token)
redis_pass = GetSecret('CapmanRedis','Password')

import redis
import time
import json
redis_cmd = redis.StrictRedis(host, db=cmd_db, password=redis_pass)
redis_storage = redis.StrictRedis(host, db=store_db, password=redis_pass)

import uuid
uuid.uuid4()
import datetime

def GetUID(channel):
    now = datetime.datetime.now()
    return '.'.join([channel,str(now.year),str(now.month),str(now.day),str(now.hour),str(now.minute),str(now.second),str(now.microsecond),str(uuid.uuid4()).replace('-','.')])

def SaveOnRedisWithExpire(key,data,expire=2419200):
    redis_storage.set(key,data,ex=expire)

def SendToRedis(channel,data):
    uid = GetUID(channel)
    print(channel,uid)
    SaveOnRedisWithExpire(uid,data)
    redis_cmd.rpush(channel,uid.encode())

def WorkOnFile(x):
    if not '.LOK' in x:
        if transfer_tag in x:
            tags = x.split('.')
            channel = tags[1]
            filepath=in_folder+"\\"+x
            with open(filepath,'rb') as rf:
                data = rf.read()
                SendToRedis(channel,data)
                print ("Added: ", x,len(data))
            os.remove(filepath)
        else:
            print('Skip new file:' ,x)
print('First scan...')
before = dict ([(f, None) for f in os.listdir (in_folder)])
for x in before:
    WorkOnFile(x)

import os 
debug = os.environ.get('DEBUG',False)=='True'

while 1:
    try:
        time.sleep (5)
        after = dict ([(f, None) for f in os.listdir (in_folder)])
        added = [f for f in after if not f in before]
        removed = [f for f in before if not f in after]
        if after: 
            for x in added:
                WorkOnFile(x)
        if removed: 
            print ("Removed: ", ", ".join (removed))
        before = after
    except Exception as e:
        if  debug:
            raise e
        else:
            print(e)
