
import requests
import json



import logging
import os

from flask import Flask, render_template, request


# [START config]
#SENDGRID_API_KEY = os.environ['SENDGRID_API_KEY']
#SENDGRID_SENDER = os.environ['SENDGRID_SENDER']
# [END config]

app = Flask(__name__)

def SendSMS(phone, message):
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
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END app]
