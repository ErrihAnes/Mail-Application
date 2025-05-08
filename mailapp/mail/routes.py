from venv import logger
from flask_login import current_user, login_required
from mailapp.mail.mailFunc import get_imap_server,get_email_count
from mailapp.extentions import db
from flask import request, redirect, Blueprint
import imaplib
from mailapp.mail.models import MailAccount
import logging
mail = Blueprint('mail',__name__)

@mail.route('/api/config/param',methods=['POST'])
def config():
    apppassword = request.form.get('apppassword')
    imaphost = request.form.get('imaphost')
    imapport = request.form.get('imapport')
    smtphost = request.form.get('smtphost')
    smtpport = request.form.get('smtpport')
    newmail = MailAccount(user= current_user,apppassword=apppassword,imaphost=imaphost,imapport=imapport,smtphost=smtphost,smtpport=smtpport)
    db.session.add(newmail)
    db.session.commit()


    return " gg config terminer "
##    stats
@mail.route('api/config/stat_count',methods=['GET'])
@login_required
def get_total_mail():
    if (not  current_user or not current_user.is_authenticated):
        logger.warning("User not authenticated.")
        return None, "User not authenticated."
    email_utilisateur_connecte = current_user.email
    mail_account = MailAccount.query.filter_by(user_id =current_user.uid).first()
    print(email_utilisateur_connecte)
    print(mail_account.apppassword)
    print(mail_account.imaphost)
    ##count = get_email_count(email_utilisateur_connecte, mail_account.apppassword, mail_account.imaphost)
    imap = imaplib.IMAP4_SSL(mail_account.imaphost)
    imap.login(email_utilisateur_connecte, mail_account.apppassword)
    imap.select("inbox")
    status, messages = imap.search(None, 'ALL')
    email_ids = messages[0].split()
    count = len(email_ids)
    imap.close()
    imap.logout()
    return str(count)




