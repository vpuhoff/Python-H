#!/usr/bin/python3
import logging
logging.basicConfig(filename='Events.log',level=logging.DEBUG)
import requests
import json
import os
from flask import Flask, render_template, request
import raven
import string
import hvac

logging.debug('Connect vault...')

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

logging.debug('Connect sentry...')
sentry = raven.Client(sentry_data['url'])
sentry.captureMessage('Restart application!',level='info')

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
    except Exception:
        sentry.captureException()
        logging.exception(e) 
    

@app.route('/gate')
def gate():
    return render_template('index.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gate/callback_form')
def callback_form():
    sentry.captureMessage('Render Callback form!',level='info')
    return render_template('callback_form.html')    

@app.route('/gate/callback', methods=['POST'])
def callback():
    try:
        to = support_data['phone']
        message = request.form.get('name')+': '+request.form.get('phone')
        if not to:
            return ('Please enter phone number '), 400
        SendSMS(to,'Заказ звонка: '+message)
    except Exception as e:
        sentry.captureException(
            extra={'Form data':request.form})
        return 'An error occurred: {}'.format(e), 500
        logging.exception(e) 
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
    sentry.captureException(e,level='fatal')
    logging.exception('An error occurred during a request.')
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
            sentry.captureException(e,level='fatal')
            logging.exception(e) 
    elif platform == "win32":  
        try:
            logging.debug('Platform: windows')
            logging.debug('Run main loop thread...')
            app.run(host='0.0.0.0', port=8080, debug=True)
        except Exception as e:
            sentry.captureException(e,level='fatal')     
            logging.exception(e) 