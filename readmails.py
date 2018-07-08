#!/usr/bin/env python3
# coding=utf-8
# vim: set ai et ts=4 sw=4:

# email-archive.py
# (c) Aleksander Alekseev 2017
# http://eax.me/

import imaplib
import hashlib
import getpass
import email
import email.message
import time
import os.path
import subprocess
import re
import sys

import os
import hvac


client = hvac.Client(url='http://80.211.91.158:8200', token=os.environ['VAULT_TOKEN'])

smtp = client.read('secret/ekaterina-gadanie.com')['data']
smsgate = client.read('secret/automate-cloud')['data']


server = smtp['smtp-server']
login = smtp['email']
password = smtp['password']

pause_time = 300
import hashlib

import quopri
import base64

import requests
import json

def SendSMS(phone, message):
    url = smsgate['url']
    headers = {'Content-type': 'application/json'}
    payload =json.dumps({
        "secret": smsgate['secret'],
        "to": smsgate['worker'],
        "device":None,
        "payload": phone+";"+message.replace(';',':')
    })
    r = requests.post(url, data=payload, headers=headers)
    return r.reason

import string
def main_loop_proc():
    print("Connecting to {}...".format(server))
    imap = imaplib.IMAP4_SSL(server)
    print("Connected! Logging in as {}...".format(login))
    imap.login(login, password)
    print("Logged in! Listing messages...")
    status, select_data = imap.select('INBOX')
    nmessages = select_data[0].decode('utf-8')
    status, search_data = imap.search(None, 'ALL')
    for msg_id in search_data[0].split():
        msg_id_str = msg_id.decode('utf-8')
        print("Fetching message {} of {}".format(msg_id_str,
                                                 nmessages))
        status, msg_data = imap.fetch(msg_id, '(RFC822)')
        msg_raw = msg_data[0][1]
        msg = email.message_from_string(msg_raw.decode())
        payload = msg.get_payload()[ 0 ]
        text = quopri.decodestring(payload.get_payload())
        #print(text)
        printable = text.decode('utf-8')
        print(printable)
        SendSMS('+79243132456',printable)
        SendSMS('+79183432881',text)
        imap.store(msg_id, '+FLAGS', '\\Deleted')
    imap.expunge()
    imap.logout()
from datetime import datetime
#while True:
main_loop_proc()
try:
    
    SendSMS('+79243132456',str(datetime.now())+" Служба отправки СМС: Ошибок нет.")
except Exception as e:
    print("ERROR:" + str(e))
    SendSMS('+79243132456',"ERROR:" + str(e))
#print("Sleeping {} seconds...".format(pause_time))
#time.sleep(pause_time)
