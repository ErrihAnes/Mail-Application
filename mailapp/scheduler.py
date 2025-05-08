from apscheduler.schedulers.background import BackgroundScheduler
from mailapp.brain.agent import chat, match_email_with_prompt
from mailapp.brain.brainFunction import GetMail, file_exist, moveFile, createfile
from mailapp.brain.models import Domain
from mailapp.mail.models import MailAccount
from flask_login import current_user
from mailapp.extentions import db


def auto_process_emails():
    mail_content = GetMail()
    prompt = "..."  # À personnaliser selon ton use case
    targetfile = "..."  # Idem, récupérer dynamiquement ou configurer

    res = match_email_with_prompt(mail_content, prompt)
    file = file_exist(targetfile)

    try:
        newdomain = Domain(user=current_user, domain=targetfile)
        db.session.add(newdomain)
        db.session.commit()
    except Exception as e:
        print(f"Erreur lors de l'ajout à la base de données : {e}")

    if file:
        moveFile(targetfile)
        print("Moved to existing file.")
    else:
        createfile(targetfile)
        moveFile(targetfile)
        print("Created and moved.")

    print("Résultat:", "Match" if res else "No match")


def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=auto_process_emails, trigger="interval", seconds=60)  # vérifie chaque 60 sec
    scheduler.start()
