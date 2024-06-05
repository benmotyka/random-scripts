import os
import imaplib
import email
from email.header import decode_header
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_env():
    """Load environment variables from a .env file."""
    try:
        with open('.env', 'r') as file:
            for line in file:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    except IOError as e:
        logging.error("Failed to load environment variables from .env file.")
        raise

def connect_to_email_server(imap_url, email_user, email_password):
    """Connect to the IMAP server and log in."""
    try:
        mail = imaplib.IMAP4_SSL(imap_url)
        mail.login(email_user, email_password)
        logging.info("Logged in to the email server.")
        return mail
    except imaplib.IMAP4.error as error:
        logging.critical(f"Failed to connect to the email server: {error}")
        raise

def decode_and_clean_filename(encoded_filename):
    """Decode MIME encoded strings and sanitize the filename."""
    decoded_filename = decode_header(encoded_filename)[0][0]
    if isinstance(decoded_filename, bytes):
        decoded_filename = decoded_filename.decode('utf-8', errors='ignore')
    return decoded_filename.lstrip('/').replace('/', '_')

def save_attachment(msg, download_folder):
    """Save attachments from email message to specified folder."""
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
            continue
        filename = part.get_filename()
        if filename:
            filename = decode_and_clean_filename(filename)
            filepath = os.path.join(download_folder, filename)
            with open(filepath, 'wb') as f:
                f.write(part.get_payload(decode=True))
                logging.info(f"Saved attachment to {filepath}")

def save_mail_body(msg, download_folder, filename):
    """Save the email body and images from the message."""
    body_saved = False
    for part in msg.walk():
        content_type = part.get_content_type()
        part_filename = part.get_filename()
        if content_type == 'text/plain' and not body_saved:
            save_content(part, download_folder, filename + '.txt')
            body_saved = True
        elif content_type.startswith('image/') and part_filename:
            image_filename = decode_and_clean_filename(part_filename)
            save_content(part, download_folder, image_filename)

def save_content(part, folder, filename):
    """Generalized saving function for text and binary content."""
    filepath = os.path.join(folder, filename)
    if part.get_content_maintype() == 'image':
        with open(filepath, 'wb') as f:
            f.write(part.get_payload(decode=True))
            logging.info(f"Saved binary file to {filepath}")
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(part.get_payload(decode=True).decode('utf-8', errors='ignore'))
            logging.info(f"Saved text file to {filepath}")

def process_emails(mail):
    mail_folder_names = ['INBOX.INBOX.Sent', 'Inbox']
    base_save_path = 'downloaded-emails'
    emails_timeframe = '(SINCE "01-Jan-2022" BEFORE "01-Jan-2023")'

    os.makedirs(base_save_path, exist_ok=True)
    for folder_name in mail_folder_names:
        process_folder(mail, folder_name, base_save_path, emails_timeframe)
    mail.logout()
    logging.info("Emails downloaded successfully.")

def process_folder(mail, folder_name, base_save_path, emails_timeframe):
    try:
        typ, data = mail.select(folder_name)
        if typ != 'OK':
            logging.error(f"Email folder \"{folder_name}\" was not found.")
            return

        save_path = os.path.join(base_save_path, folder_name.replace('.', '_'))
        os.makedirs(save_path, exist_ok=True)
        typ, data = mail.search(None, emails_timeframe)
        if typ != 'OK':
            logging.error(f"Failed to search emails in folder \"{folder_name}\".")
            return

        mail_ids = data[0].split()
        for num in mail_ids:
            fetch_and_save_email(mail, num, save_path)
    except Exception as e:
        logging.error(f"Error processing folder {folder_name}: {e}")

def fetch_and_save_email(mail, num, save_path):
    typ, data = mail.fetch(num, '(RFC822)')
    if typ != 'OK':
        logging.error(f"Failed to fetch email ID {num}.")
        return

    raw_email = data[0][1]
    email_message = email.message_from_bytes(raw_email)

    subject_header = email_message['subject']
    subject = 'no-subject' if subject_header is None else decode_header(subject_header)[0][0]
    subject = subject if isinstance(subject, str) else subject.decode('utf-8', errors='ignore')
    date_header = email.utils.parsedate_to_datetime(email_message['date'])
    date_str = date_header.strftime('%Y-%m-%d_%H-%M-%S') if date_header else time.strftime('%Y-%m-%d_%H-%M-%S')
    mail_folder = f"{date_str}_{subject[:50]}".replace('/', '_')
    individual_path = os.path.join(save_path, mail_folder)
    os.makedirs(individual_path, exist_ok=True)

    mail_filepath = os.path.join(individual_path, 'email.eml')
    with open(mail_filepath, 'wb') as f:
        f.write(raw_email)
    save_attachment(email_message, individual_path)
    save_mail_body(email_message, individual_path, 'email_body')

def main():
    try:
        load_env()
        user = os.getenv('EMAIL_USER')
        password = os.getenv('EMAIL_PASSWORD')
        imap_url = os.getenv('IMAP_URL')

        if not user or not password or not imap_url:
            raise ValueError("Missing required environment variables.")

        mail = connect_to_email_server(imap_url, user, password)
        process_emails(mail)
    except Exception as e:
        logging.critical(f"Critical error: {e}")

if __name__ == '__main__':
    main()
