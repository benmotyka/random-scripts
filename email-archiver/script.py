import os
import imaplib
import email
from email.header import decode_header
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_env():
    """Load environment variables from a .env file."""
    with open('.env', 'r') as file:
        for line in file:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

def save_attachment(msg, download_folder):
    """Save attachments from email message to specified folder."""
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
            continue
        filename = part.get_filename()
        if filename:
            decoded_filename = decode_header(filename)[0][0]
            if isinstance(decoded_filename, bytes):
                filename = decoded_filename.decode('utf-8', errors='ignore')
            else:
                filename = decoded_filename
            filename = filename.lstrip('/').replace('/', '_')
            filepath = os.path.join(download_folder, filename)
            with open(filepath, 'wb') as f:
                f.write(part.get_payload(decode=True))

def save_mail_body(msg, download_folder, filename):
    """Save the email body and images from the message."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/plain':
                body = part.get_payload(decode=True)
                if body:
                    text_filepath = os.path.join(download_folder, filename + '.txt')
                    with open(text_filepath, 'w', encoding='utf-8') as f:
                        f.write(body.decode('utf-8', errors='ignore'))
            elif content_type.startswith('image/'):
                image_filename = part.get_filename()
                if image_filename:
                    decoded_filename = decode_header(image_filename)[0][0]
                    if isinstance(decoded_filename, bytes):
                        image_filename = decoded_filename.decode('utf-8', errors='ignore')
                    image_filepath = os.path.join(download_folder, image_filename)
                    with open(image_filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
    else:
        body = msg.get_payload(decode=True)
        if body:
            text_filepath = os.path.join(download_folder, filename + '.txt')
            with open(text_filepath, 'w', encoding='utf-8') as f:
                f.write(body.decode('utf-8', errors='ignore'))

def main():
    try:
        load_env()

        # Check required environment variables
        user = os.getenv('EMAIL_USER')
        password = os.getenv('EMAIL_PASSWORD')
        imap_url = os.getenv('IMAP_URL')

        if not user or not password or not imap_url:
            raise ValueError("Missing required environment variables.")

        mail_folder_names = ['INBOX.INBOX.Sent', 'Inbox']
        base_save_path = 'downloaded-emails'
        emails_timeframe = '(SINCE "01-Jan-2023" BEFORE "01-Jan-2024")'

        os.makedirs(base_save_path, exist_ok=True)

        # Connect to the IMAP server
        mail = imaplib.IMAP4_SSL(imap_url)
        mail.login(user, password)
        logging.info("Logged in to the email server.")

        for folder_name in mail_folder_names:
            try:
                typ, data = mail.select(folder_name)
                if typ != 'OK':
                    logging.error(f"Email folder \"{folder_name}\" was not found.")
                    continue
                
                save_path = os.path.join(base_save_path, folder_name)
                os.makedirs(save_path, exist_ok=True)

                typ, data = mail.search(None, emails_timeframe)
                if typ != 'OK':
                    logging.error(f"Failed to search emails in folder \"{folder_name}\".")
                    continue

                mail_ids = data[0].split()

                for num in mail_ids:
                    try:
                        typ, data = mail.fetch(num, '(RFC822)')
                        if typ != 'OK':
                            logging.error(f"Failed to fetch email ID {num}.")
                            continue

                        raw_email = data[0][1]
                        email_message = email.message_from_bytes(raw_email)

                        subject_header = email_message['subject']
                        subject = 'no-subject' if subject_header is None else decode_header(subject_header)[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode('utf-8', errors='ignore')
                        if not subject:
                            subject = 'no-subject'

                        date_header = email.utils.parsedate_to_datetime(email_message['date'])
                        date_str = date_header.strftime('%Y-%m-%d_%H-%M-%S') if date_header else time.strftime('%Y-%m-%d_%H-%M-%S')
                        mail_folder = f"{date_str}_{subject[:50]}"
                        mail_folder = ''.join(e for e in mail_folder if e.isalnum() or e in "_-")
                        individual_path = os.path.join(save_path, mail_folder)
                        os.makedirs(individual_path, exist_ok=True)

                        mail_filepath = os.path.join(individual_path, 'email.eml')
                        with open(mail_filepath, 'wb') as f:
                            f.write(raw_email)
                        save_attachment(email_message, individual_path)
                        save_mail_body(email_message, individual_path, 'email_body')

                    except Exception as e:
                        logging.error(f"Error processing mail ID {num}: {e}")

            except Exception as e:
                logging.error(f"Error processing folder {folder_name}: {e}")

        mail.logout()
        logging.info("Emails downloaded successfully.")

    except Exception as e:
        logging.critical(f"Critical error: {e}")

if __name__ == '__main__':
    main()
