#!/usr/bin/python3
import logging
logging.basicConfig(filename='Events.log',level=logging.DEBUG)
logging.debug('Init global exeptions hook...')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.StreamHandler().setFormatter(formatter)
import sys
def Global_Except_hook(exctype, value, traceback):
    logging.exception('Global Except: '+str([exctype, value, traceback]))
    sys.__excepthook__(exctype, value, traceback)
    
sys.excepthook = Global_Except_hook

import requests
import json
import os
from flask import Flask, render_template, request
import raven
import string
import hvac
logging.debug('Get current version...')

from version import GetVersion
curver = GetVersion()

logging.debug(curver)

logging.debug('Connecting to vault...')

vault = hvac.Client(url='http://80.211.91.158:8200', token=os.environ['VAULT_TOKEN'])
import time

retry_count = 0
vault_state = 'connecting'
while vault_state!='ready':
    try:
        res = vault.read('secret/support')['data']['check']
        if res=='OK':
            logging.debug('Vault ready!')
            break
        else:
            logging.exception('Key Error: '+str(res))
    except Exception as e:
        logging.exception(e) 
    retry_count=retry_count+1
    if retry_count>5:
        break
    else:
        logging.exception('Retry...'+str(retry_count))
        time.sleep(3)

logging.debug('Get secrets...')
sentry_data = vault.read('secret/sentry')['data']
gate_data = vault.read('secret/automate-cloud')['data']
support_data = vault.read('secret/support')['data']
contact_data = vault.read('secret/contact')['data']

logging.debug('Connect sentry...')
sentry = raven.Client(sentry_data['url'])
sentry.captureMessage('Restart application!',level='info')

logging.debug('ReInit global exeptions hook with sentry...')
def Global_Except_hook_with_sentry(exctype, value, traceback):
    print(exctype, value, traceback)
    logging.exception('Global Except: '+str([ exctype, traceback]))
    try:
        raise value
    except Exception:
        sentry.captureException(
        extra={'value':value,'traceback':traceback})
    sys.__excepthook__(exctype, value, traceback)
sys.excepthook = Global_Except_hook_with_sentry

logging.debug('Init Flask...')
app = Flask(__name__)

class Del:
  def __init__(self, keep=string.digits):
    self.comp = dict((ord(c),c) for c in keep)
  def __getitem__(self, k):
    return self.comp.get(k)

DD = Del()

def SendSMS(phone_raw, message):
    try:
        phone = '+'+phone_raw.translate(DD)
        url = gate_data['url']

        headers = {'Content-type': 'application/json'}
        payload =json.dumps({
            "secret": gate_data['secret'],
            "to": gate_data['worker'],
            "device":None,
            "payload": phone+";"+message.replace(';',':')
        })
        r = requests.post(url, data=payload, headers=headers)
        sentry.captureMessage('SMS Sended!',extra=
        {'phone':phone,
        'raw_phone':phone_raw,
        'message':message} ,level='info')
        return r.reason
    except Exception as e:
        logging.exception(e) 
        sentry.captureException()
        
    

@app.route('/gate')
def gate():
    return render_template('index.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gate/callback_form')
def callback_form():
    sentry.captureMessage('Render Callback form simple!',level='info')
    return render_template('callback_form.html')    

@app.route('/gate/callback_form/<contact_id>')
def callback_form_contact(contact_id):
    sentry.captureMessage('Render Callback form!',level='info')
    return render_template('callback_form_contact.html',contact_id=contact_id)    


@app.route('/gate/callback', methods=['POST'])
def callback():
    try:
        logging.debug(str(request.form))
        message = request.form.get('name')+' ('+request.form.get('phone')+')'
        contact_id = request.form.get('contact')
        to = 'none'
        if  contact_id:
            if contact_id in contact_data.keys():
                to = contact_data[contact_id]
            else:
                raise Exception(contact_id+' not found in contact_data')
        else:
            to = contact_data['support']
        if not to:
            raise Exception('Target phone is None!')

        SendSMS(to,'Заказ звонка: '+message)
    except Exception as e:
        logging.exception(e) 
        sentry.captureException(
            extra={'Form data':request.form})
        return 'An error occurred: {}'.format(e), 500
    return render_template('callback_ok.html')


# [START example]
@app.route('/gate/send/sms', methods=['POST'])
def send_sms():
    to = request.form.get('phone')
    message = request.form.get('message')
    if not to:
        return ('Please enter phone number '), 400
    if not message:
        return ('Please enter message'), 400
    try:
        sentry.captureMessage('Send SMS via API',level='info', extra={'to':to,'message':message})
        SendSMS(to,message)
    except Exception as e:
        logging.exception(e) 
        sentry.captureException(e,level='fatal')
        return 'An error occurred: {}'.format(e), 500

    return 'OK',200
# [END example]

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    sentry.captureException(e,level='fatal')
    return """    An internal error occurred: <pre>{}</pre>    See logs for full stacktrace.    """.format(e), 500

if __name__ == '__main__':
    logging.debug('Check platform...')
    from sys import platform
    if platform == "linux" or platform == "linux2":
        # linux
        logging.debug('Platform: linux')
        #logging.debug('Init daemon tools...')
        #import daemon
        try:
            #with daemon.DaemonContext():
            logging.debug('Run main loop thread...')
            app.run(host='0.0.0.0', port=8080, debug=True)
        except Exception as e:
            logging.exception(e) 
            sentry.captureException(e,level='fatal')
            
    elif platform == "win32":  
        try:
            logging.debug('Platform: windows')
            logging.debug('Run main loop thread...')
            app.run(host='0.0.0.0', port=8080, debug=True)
        except Exception as e:
            logging.exception(e) 
            sentry.captureException(e,level='fatal')     
            