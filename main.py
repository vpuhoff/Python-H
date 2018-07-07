
import requests
import json

import logging
import os
import hvac

vault = hvac.Client(url='http://80.211.91.158:8200', token=os.environ['VAULT_TOKEN'])


from flask import Flask, render_template, request
import raven

sentry_data = vault.read('secret/sentry')['data']
gate_data = vault.read('secret/automate-cloud')['data']

sentry = raven.Client(sentry_data['url'])
sentry.captureMessage('Restart application!',level='info')

app = Flask(__name__)
import string

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
        to = '+79243132456'
        message = request.form.get('name')+': '+request.form.get('phone')
        if not to:
            return ('Please enter phone number '), 400
        SendSMS(to,'Заказ звонка: '+message)
    except Exception as e:
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
