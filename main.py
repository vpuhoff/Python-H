
import requests
import json

import logging
import os
import hvac

client = hvac.Client(url='http://80.211.91.158:8200', token=os.environ['VAULT_TOKEN'])

#smtp = client.read('secret/ekaterina-gadanie.com')['data']

from flask import Flask, render_template, request


# [START config]
#SENDGRID_API_KEY = os.environ['SENDGRID_API_KEY']
#SENDGRID_SENDER = os.environ['SENDGRID_SENDER']
# [END config]

app = Flask(__name__)
import string

class Del:
  def __init__(self, keep=string.digits):
    self.comp = dict((ord(c),c) for c in keep)
  def __getitem__(self, k):
    return self.comp.get(k)

DD = Del()

def SendSMS(phone_raw, message):
    phone = '+'+phone_raw.translate(DD)
    url = 'https://llamalab.com/automate/cloud/message'

    headers = {'Content-type': 'application/json'}
    payload =json.dumps({
        "secret": "1.IsCmZnfHe-m-gF2DB6lsSvtkaM6R0uNsLyVLs1RSvWA=",
        "to": "vpuhoff92@gmail.com",
        "device":None,
        "payload": phone+";"+message.replace(';',':')
    })
    r = requests.post(url, data=payload, headers=headers)
    return r.reason

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/callback_form')
def callback_form():
    return render_template('callback_form.html')    

@app.route('/callback', methods=['POST'])
def callback():
    to = '+79243132456'
    message = request.form.get('name')+': '+request.form.get('phone')
    if not to:
        return ('Please enter phone number '), 400
    try:
        SendSMS(to,'Заказ звонка: '+message)
    except Exception as e:
        SendSMS(to,'Error: {}'.format(e))
        return 'An error occurred: {}'.format(e), 500

    return render_template('callback_ok.html')


# [START example]
@app.route('/send/sms', methods=['POST'])
def send_sms():
    to = request.form.get('phone')
    message = request.form.get('message')
    if not to:
        return ('Please enter phone number '), 400
    if not message:
        return ('Please enter message'), 400
    try:
        SendSMS(to,message)
    except Exception as e:
        return 'An error occurred: {}'.format(e), 500

    return 'Message sent.'
# [END example]

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """    An internal error occurred: <pre>{}</pre>    See logs for full stacktrace.    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='0.0.0.0', port=8080, debug=False)
# [END app]
