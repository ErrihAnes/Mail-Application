import imaplib
import email
from email.header import decode_header

from flask import jsonify


def get_imap_server(email:str):
    domain = email.split('@')[-1].lower()
    match domain:
        case 'gmail.com':
            return 'imap.gmail.com'
        case 'outlook.com' | 'hotmail.com' | 'live.com':
            return 'outlook.office365.com'
        case 'yahoo.com':
            return 'imap.mail.yahoo.com'
        case 'icloud.com' | 'me.com':
            return 'imap.mail.me.com'
        case _:
            return None



def get_email_count(username,password,imaphost):
    imap = imaplib.IMAP4_SSL(imaphost)
    imap.login(username, password)
    imap.select("inbox")
    status, messages = imap.search(None, 'ALL')
    email_ids = messages[0].split()
    count = len(email_ids)
    imap.close()
    imap.logout()
    return count