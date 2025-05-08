import email
import imaplib
from flask import abort, current_app
from flask_login import current_user
from mailapp.mail.models import MailAccount
from mailapp.user.models import User
import re



def _get_imap_credentials_and_usermail(user_id=None):
    target_user = None
    user_uid_db = None

    if user_id:
        target_user = User.query.get(user_id)
        if not target_user:
            print(f"IMAP Helper: Aucun utilisateur trouvé pour user_id: {user_id}")
            return None, None, None, None
        user_uid_db = target_user.uid
        usermail = target_user.email
    elif current_user and current_user.is_authenticated:
        target_user = current_user
        user_uid_db = target_user.uid  # ou current_user.id
        usermail = target_user.email
    else:
        print("IMAP Helper: Ni user_id fourni, ni utilisateur authentifié.")
        if hasattr(current_app, 'request_context_class') and current_app.request_context_class:
            abort(401)
        return None, None, None, None

    if not target_user:
        return None, None, None, None

    mail_account = MailAccount.query.filter_by(user_id=user_uid_db).first()
    if not mail_account:
        print(f"IMAP Helper: Aucun MailAccount trouvé pour l'utilisateur: {usermail} (ID DB: {user_uid_db})")
        return None, None, None, None

    password = mail_account.apppassword
    imaphost = mail_account.imaphost

    if not password or not imaphost:
        print(f"IMAP Helper: Informations IMAP (apppassword ou imaphost) manquantes pour {usermail}")
        return None, None, None, None

    return usermail, password, imaphost, user_uid_db



def GetMail(user_id=None):
    usermail, password, imaphost, user_uid_db = _get_imap_credentials_and_usermail(user_id)
    if not usermail:
        return []

    print(f"GetMail (UID): Connexion à {imaphost} pour {usermail}...")
    emails_info = []
    try:
        mail = imaplib.IMAP4_SSL(imaphost)
        mail.login(usermail, password)

        status, _ = mail.select("inbox")
        if status != 'OK':
            print(f"GetMail (UID): Impossible de sélectionner INBOX pour {usermail}.")
            mail.logout()
            return []

        # Utiliser UID SEARCH
        result, data_uid = mail.uid('search', None, "UNSEEN")
        if result != 'OK':
            print(f"GetMail (UID): Erreur lors de la recherche UID pour {usermail}.")
            mail.logout()
            return []

        target_uids_bytes = []
        if data_uid and data_uid[0]:
            for block in data_uid:
                target_uids_bytes.extend(block.split())

        if not target_uids_bytes:
            print(f"GetMail (UID): Aucun email non lu (UNSEEN) trouvé par UID pour {usermail}.")
            mail.logout()
            return []

        print(f"GetMail (UID): {len(target_uids_bytes)} email(s) non lu(s) trouvé(s) par UID pour {usermail}.")

        for email_uid_bytes in target_uids_bytes[-5:]:
            # Utiliser UID FETCH
            result_fetch, msg_data = mail.uid('fetch', email_uid_bytes, "(RFC822)")
            if result_fetch != 'OK' or not msg_data or not msg_data[0]:
                print(
                    f"GetMail (UID): Erreur lors du fetch UID de l'email ID {email_uid_bytes.decode()} pour {usermail}.")
                continue

            raw_email = msg_data[0][1]
            message = email.message_from_bytes(raw_email)

            mail_from = message.get("From", "N/A")
            mail_subject = message.get("Subject", "N/A")
            email_uid_str = email_uid_bytes.decode()
            print(f"  GetMail (UID): Traitement de l'email UID {email_uid_str} de: {mail_from}, Sujet: {mail_subject}")

            current_email_content = ""
            if message.is_multipart():
                for part in message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if "attachment" not in content_disposition and "text/plain" in content_type:
                        try:
                            payload = part.get_payload(decode=True)
                            encodings_to_try = [part.get_content_charset(), 'utf-8', 'iso-8859-1', 'windows-1252']
                            for enc in encodings_to_try:
                                if enc:
                                    try:
                                        current_email_content = payload.decode(enc)
                                        break
                                    except UnicodeDecodeError:
                                        continue
                            if not current_email_content and payload:
                                print(
                                    f"    GetMail (UID): Impossible de décoder une partie text/plain de l'email UID {email_uid_str}.")
                            break
                        except Exception as e_decode:
                            print(
                                f"    GetMail (UID): Erreur lors du décodage de la partie de l'email UID {email_uid_str}: {e_decode}")
            else:
                if "text/plain" in message.get_content_type():
                    try:
                        payload = message.get_payload(decode=True)
                        encodings_to_try = [message.get_content_charset(), 'utf-8', 'iso-8859-1', 'windows-1252']
                        for enc in encodings_to_try:
                            if enc:
                                try:
                                    current_email_content = payload.decode(enc)
                                    break
                                except UnicodeDecodeError:
                                    continue
                        if not current_email_content and payload:
                            print(
                                f"    GetMail (UID): Impossible de décoder le corps non-multipart de l'email UID {email_uid_str}.")
                    except Exception as e_decode:
                        print(
                            f"    GetMail (UID): Erreur lors du décodage du corps de l'email UID {email_uid_str}: {e_decode}")

            if current_email_content:
                print(
                    f"  GetMail (UID): Contenu extrait pour l'email UID {email_uid_str} (longueur: {len(current_email_content)}).")
                emails_info.append({
                    'imap_id': email_uid_bytes,
                    'subject': mail_subject,
                    'content': current_email_content
                })
            else:
                print(f"  GetMail (UID): Aucun contenu text/plain extrait pour l'email UID {email_uid_str}.")

        mail.logout()
        return emails_info

    except imaplib.IMAP4.error as e_imap:
        print(f"GetMail (UID): Erreur IMAP pour {usermail}: {e_imap}")
        return []
    except Exception as e_general:
        print(f"GetMail (UID): Erreur générale pour {usermail}: {e_general}")
        import traceback
        traceback.print_exc()
        return []

def file_exist(target_folder_name, user_id=None):
    usermail, password, imaphost, _ = _get_imap_credentials_and_usermail(user_id)
    if not usermail:
        return False

    print(f"file_exist (IMAP): Vérification du dossier '{target_folder_name}' pour {usermail} sur {imaphost}")
    try:
        mail = imaplib.IMAP4_SSL(imaphost)
        mail.login(usermail, password)
        status, folders_data = mail.list()
        mail.logout()

        if status != "OK":
            print(f"file_exist (IMAP): Erreur lors de la récupération des dossiers pour {usermail}.")
            return False

        for folder_entry in folders_data:
            try:
                decoded_entry = folder_entry.decode('utf-8', 'ignore')
                match = re.search(r'"([^"]+)"$', decoded_entry)
                if match:
                    folder_name_on_server = match.group(1)
                    if folder_name_on_server.lower() == target_folder_name.lower():
                        print(f"file_exist (IMAP): Dossier '{target_folder_name}' trouvé pour {usermail}.")
                        return True
            except Exception as e_parse:
                print(
                    f"file_exist (IMAP): Erreur de parsing d'une entrée de dossier: {folder_entry}, erreur: {e_parse}")
                continue

        print(f"file_exist (IMAP): Dossier '{target_folder_name}' non trouvé pour {usermail}.")
        return False
    except Exception as e:
        print(
            f"file_exist (IMAP): Erreur IMAP lors de la vérification du dossier '{target_folder_name}' pour {usermail}: {e}")
        return False


def createfile(target_folder_name, user_id=None):
    usermail, password, imaphost, _ = _get_imap_credentials_and_usermail(user_id)
    if not usermail:
        return False

    print(f"createfile (IMAP): Tentative de création du dossier '{target_folder_name}' pour {usermail} sur {imaphost}")
    try:
        mail = imaplib.IMAP4_SSL(imaphost)
        mail.login(usermail, password)
        status, response = mail.create(
            target_folder_name)
        mail.logout()

        if status == "OK":
            print(f"createfile (IMAP): Dossier '{target_folder_name}' créé avec succès pour {usermail}.")
            return True
        else:
            print(
                f"createfile (IMAP): Échec de la création du dossier '{target_folder_name}' pour {usermail}. Réponse: {response}")
            return False
    except Exception as e:
        print(
            f"createfile (IMAP): Erreur IMAP lors de la création du dossier '{target_folder_name}' pour {usermail}: {e}")
        return False



def moveFile(target_folder_name, email_imap_uid_bytes, user_id=None):
    usermail, password, imaphost, _ = _get_imap_credentials_and_usermail(user_id)
    if not usermail:
        return False

    if not email_imap_uid_bytes:
        print("moveFile (IMAP UID): UID de l'email non fourni ou invalide.")
        return False

    if isinstance(email_imap_uid_bytes, str):
        email_imap_uid_bytes = email_imap_uid_bytes.encode()

    print(
        f"moveFile (IMAP UID): Tentative de déplacement de l'email UID '{email_imap_uid_bytes.decode()}' vers '{target_folder_name}' pour {usermail}")
    try:
        mail = imaplib.IMAP4_SSL(imaphost)
        mail.login(usermail, password)

        status_select, _ = mail.select("inbox")
        if status_select != 'OK':
            print(f"moveFile (IMAP UID): Impossible de sélectionner INBOX pour {usermail}.")
            mail.logout()
            return False



        resp_fetch_uid, data_fetch_uid = mail.uid('fetch', email_imap_uid_bytes, '(UID)')
        if resp_fetch_uid != 'OK' or not data_fetch_uid or not data_fetch_uid[0]:
            print(
                f"moveFile (IMAP UID): Email UID '{email_imap_uid_bytes.decode()}' non trouvé dans INBOX pour {usermail} (ou erreur fetch).")
            mail.logout()
            return False


        print(
            f"moveFile (IMAP UID): Tentative de copie de UID '{email_imap_uid_bytes.decode()}' vers '{target_folder_name}'...")
        status_copy, response_copy = mail.uid('copy', email_imap_uid_bytes, target_folder_name)

        if status_copy != 'OK':
            print(
                f"moveFile (IMAP UID): Échec de la copie de l'email UID '{email_imap_uid_bytes.decode()}' vers '{target_folder_name}'. Réponse: {response_copy}")

            if response_copy and response_copy[0] and b'NONEXISTENT' in response_copy[0].upper():
                print(f"moveFile (IMAP UID): Le dossier cible '{target_folder_name}' n'existe probablement pas.")
            mail.logout()
            return False

        print(
            f"moveFile (IMAP UID): Email UID '{email_imap_uid_bytes.decode()}' copié avec succès vers '{target_folder_name}'.")


        print(f"moveFile (IMAP UID): Marquage \\Deleted pour UID '{email_imap_uid_bytes.decode()}'...")
        status_store, response_store = mail.uid('store', email_imap_uid_bytes, '+FLAGS', '\\Deleted')
        if status_store != 'OK':
            print(
                f"moveFile (IMAP UID): Échec du marquage \\Deleted pour l'email UID '{email_imap_uid_bytes.decode()}'. Réponse: {response_store}")



        print(f"moveFile (IMAP UID): Exécution de expunge...")
        status_expunge, response_expunge = mail.expunge()
        if status_expunge != 'OK':
            print(f"moveFile (IMAP UID): Problème potentiel avec expunge. Réponse: {response_expunge}")
        else:
            if response_expunge and response_expunge != [None] and response_expunge != [b'']:
                print(f"moveFile (IMAP UID): Expunge a traité les messages: {response_expunge}")
            else:
                print(f"moveFile (IMAP UID): Expunge exécuté (aucun message à expurger ou réponse non verbeuse).")
            print(
                f"moveFile (IMAP UID): Email UID '{email_imap_uid_bytes.decode()}' marqué \\Deleted et expunge tenté.")

        mail.logout()
        return True

    except imaplib.IMAP4.error as e_imap:
        print(
            f"moveFile (IMAP UID): Erreur IMAP lors du déplacement de l'email UID '{email_imap_uid_bytes.decode()}' pour {usermail}: {e_imap}")
        if hasattr(e_imap, 'args') and e_imap.args and e_imap.args[0] and isinstance(e_imap.args[0],
                                                                                     bytes) and b'NONEXISTENT' in \
                e_imap.args[0].upper():
            print(
                f"moveFile (IMAP UID): Le dossier cible '{target_folder_name}' n'existe probablement pas pour {usermail}.")
        return False
    except Exception as e:
        print(
            f"moveFile (IMAP UID): Erreur générale lors du déplacement de l'email UID '{email_imap_uid_bytes.decode()}' pour {usermail}: {e}")
        import traceback
        traceback.print_exc()
        return False