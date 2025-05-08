import email
import imaplib

from apscheduler.schedulers.background import BackgroundScheduler

from mailapp.brain.models import Domain
from mailapp.extentions import db
from mailapp.user.models import User

userDomains = []
from flask import Blueprint,request
from flask_login import current_user
print(userDomains)
from mailapp.brain.agent import chat, match_email_with_prompt, response
from mailapp.brain.brainFunction import GetMail, file_exist, moveFile, createfile
from mailapp.mail.models import MailAccount

brain = Blueprint('brain',__name__)


def emailcontaint():

    mail_content = GetMail()
    result = chat(mail_content, userDomains)
    return result
@brain.route('/api/brain/traitement')
def traiter():

    mail_content = GetMail()
    result = chat(mail_content,userDomains)
    return result

@brain.route('/api/brain/adddomain',methods=['POST'])
def adddomain():
    targetfile = request.form.get('targetfile')
    prompt = request.form.get('prompt')

    try:
        newdomain = Domain(user=current_user, domain=targetfile,prompt=prompt,themeautoreply="non concerné",replyautoreply="non concerné")
        db.session.add(newdomain)
        db.session.commit()
    except Exception as e:
        print(f"Erreur lors de l'ajout a la base de donnée : {e}")

    return "we"


def automove_task(app_instance):  # app_instance est l'objet app Flask
    with app_instance.app_context():  # Nécessaire pour les opérations DB (User.query, Domain.query)
        all_users = User.query.all()

        if not all_users:
            print(" Aucun utilisateur trouvé.")
            return

        for user in all_users:
            user_domains = Domain.query.filter_by(user_id=user.uid).all()
            if not user_domains:
                print(f" Aucun domaine configuré pour l'utilisateur UID {user.uid}")
                continue
            print(f" {len(user_domains)} domaine(s) trouvé(s) pour l'utilisateur UID {user.uid}")

            emails_information = GetMail(user_id=user.uid)

            if not emails_information:
                print(f" Aucun email récupéré par GetMail pour l'utilisateur UID {user.uid}.")
                continue

            print(f" {len(emails_information)} email(s) récupéré(s) pour UID {user.uid}")
            for email_info in emails_information:
                mail_content_single = email_info['content']
                email_imap_uid = email_info['imap_id']  # C'est l'UID en BYTES
                email_subject = email_info['subject']

                print(
                    f"  Traitement de l'email UID (IMAP): {email_imap_uid.decode()} (Sujet: {email_subject}) pour user {user.uid}")

                for domain_obj in user_domains:
                    target_folder_name_on_server = domain_obj.domain  # Nom du dossier IMAP cible
                    print(
                        f"   Vérification domaine '{target_folder_name_on_server}' pour email UID {email_imap_uid.decode()}")

                    res = match_email_with_prompt(mail_content_single, domain_obj.prompt)

                    if res:
                        print(
                            f"   MATCH pour user {user.uid}, domaine '{target_folder_name_on_server}', email UID {email_imap_uid.decode()}.")

                        dossier_pret = False
                        # APPELS CORRIGÉS ICI :
                        if file_exist(target_folder_name_on_server, user_id=user.uid):
                            print(f"   Dossier IMAP '{target_folder_name_on_server}' existe déjà.")
                            dossier_pret = True
                        else:
                            print(
                                f"   Dossier IMAP '{target_folder_name_on_server}' non trouvé, tentative de création...")
                            # APPEL CORRIGÉ ICI :
                            if createfile(target_folder_name_on_server, user_id=user.uid):
                                print(f"   Dossier IMAP '{target_folder_name_on_server}' créé.")
                                dossier_pret = True
                            else:
                                print(
                                    f"   ÉCHEC de la création du dossier IMAP '{target_folder_name_on_server}'.")

                        if dossier_pret:
                            print(
                                f"  DEBUG Scheduler: Tentative de déplacement de l'email UID {email_imap_uid.decode()} vers '{target_folder_name_on_server}'...")
                            # APPEL CORRIGÉ ICI :
                            if moveFile(target_folder_name_on_server, email_imap_uid, user_id=user.uid):
                                print(
                                    f"  DEBUG Scheduler: SUCCÈS du déplacement de l'email UID {email_imap_uid.decode()} vers '{target_folder_name_on_server}'.")
                            else:
                                print(
                                    f"   ÉCHEC du déplacement de l'email UID {email_imap_uid.decode()} vers '{target_folder_name_on_server}'.")
                        else:
                            print(
                                f"   Dossier '{target_folder_name_on_server}' non prêt. abandon du déplacement.")

                        break  # Email traité (ou tentative), sortir de la boucle des domaines pour CET email
                    else:
                        print(
                            f"   NON-MATCH pour domaine '{target_folder_name_on_server}' et email UID {email_imap_uid.decode()}.")
        print(" automove_task terminé.")
@brain.route('/api/brain/response',methods=['POST'])
def res():
    mailco = current_user.email
    mail_account = MailAccount.query.filter_by(user_id =current_user.uid).first()
    theme = request.form.get('theme')
    prompt = request.form.get('prompt')
    newdomain = Domain(user=current_user, domain="non concerné", prompt="non concerné", themeautoreply=theme,
                       replyautoreply=prompt)
    db.session.add(newdomain)
    db.session.commit()


    return res
def autorespond_task(app_instance):
    with app_instance.app_context():
        all_users = User.query.all()

        for user in all_users:
            mail_account = MailAccount.query.filter_by(user_id=user.uid).first()
            if not mail_account:
                continue

            user_domains = Domain.query.filter_by(user_id=user.uid).all()
            if not user_domains:
                continue

            emails_information = GetMail(user_id=user.uid)
            if not emails_information:
                continue

            for email_info in emails_information:
                mail_content = email_info['content']

                for domain_obj in user_domains:
                    theme = domain_obj.domain  # Supposons que le nom du domaine est utilisé comme thème
                    user_prompt = domain_obj.prompt

                    reply = str(response(mail_content, user_prompt, theme))

                    if reply != "Hors sujet":
                        # À ce point, on a une réponse générée par IA à envoyer
                        # → Tu peux ici ajouter l'envoi du mail, ou la sauvegarde dans la BDD
                        print(f"Réponse générée pour user {user.uid}, sujet : {theme} :\n{reply}")
                        break  # Un seul domaine traité par mail

def start_scheduler(app):
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(func=automove_task, args=[app], trigger="interval", seconds=60)
    scheduler.add_job(func=autorespond_task, args=[app], trigger="interval", seconds=90)
    scheduler.start()
    print("APScheduler démarré.")
