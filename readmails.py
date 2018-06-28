import smtplib
import time
import imaplib
import email

SMTP_SERVER='smtp.gmail.com'
FROM_EMAIL='site.06.2018@gmail.com'
FROM_PWD='!Ntoaa123'
# -------------------------------------------------
#
# Utility to read email from Gmail Using Python
#
# ------------------------------------------------
import nltk   
from urllib.parse import urlencode
from bs4 import BeautifulSoup
import quopri
import base64

def read_email_from_gmail():
    print('Connecting...')
    mail = imaplib.IMAP4_SSL(SMTP_SERVER)
    mail.login(FROM_EMAIL,FROM_PWD)
    mail.select('inbox')

    type, data = mail.search(None, 'ALL')
    mail_ids = data[0]

    id_list = mail_ids.split()   
    first_email_id = int(id_list[0])
    latest_email_id = int(id_list[-1])

    print('Latest mail...', first_email_id,latest_email_id)
    for i in range(latest_email_id,first_email_id, -1):
        typ, data = mail.fetch(str(i), '(UID BODY[TEXT])' )
        soup = BeautifulSoup(data[0][1].decode())
        print(soup.get_text())
        #print(typ, data)
        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_string(response_part[1].decode())
                email_subject = msg['subject']
                email_subject = email_subject.replace('=?UTF-8?B?','')
                email_subject = base64.urlsafe_b64decode(email_subject).decode()
                email_from = msg['from']
                print(msg['text'])
                print ('From : ' + email_from + '\n')
                print ('Subject : ' + email_subject + '\n')
    try:
        pass

    except Exception as e:
        print (str(e))

read_email_from_gmail()