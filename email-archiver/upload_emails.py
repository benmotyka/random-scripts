import os
import imaplib
import email
import time
import logging
from email.utils import parsedate_to_datetime
from imaplib import Time2Internaldate

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_env():
    """Load environment variables from a .env file."""
    try:
        if os.path.exists('.env'):
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
        logging.info(f"Logged in to {imap_url} as {email_user}.")
        return mail
    except imaplib.IMAP4.error as error:
        logging.critical(f"Failed to connect to the email server: {error}")
        raise

def get_destination_folder(source_folder_name):
    """Map source folder names to destination folder names."""
    # Mapping based on your request and folder structure
    # Source (from filesystem) -> Destination (IMAP folder)
    mapping = {
        'Elementy wys&AUI-ane': 'INBOX.INBOX.Sent',
        'INBOX': 'INBOX',
        # Add other mappings if necessary
    }
    return mapping.get(source_folder_name, source_folder_name)

def upload_emails():
    base_download_path = 'downloaded-emails'
    
    if not os.path.exists(base_download_path):
        logging.error(f"Directory {base_download_path} does not exist.")
        return

    # Load credentials for destination
    dest_user = os.getenv('EMAIL_USER_2')
    dest_password = os.getenv('EMAIL_PASSWORD_2')
    dest_imap_url = os.getenv('IMAP_URL_2')

    if not dest_user or not dest_password or not dest_imap_url:
        raise ValueError("Missing required environment variables for destination (EMAIL_USER_2, EMAIL_PASSWORD_2, IMAP_URL_2).")

    mail = connect_to_email_server(dest_imap_url, dest_user, dest_password)

    # Walk through the downloaded-emails directory
    # Structure: downloaded-emails / <Folder Name> / <Date_Subject> / email.eml
    
    # List top level folders (Inbox, Sent, etc.)
    try:
        folders = [f for f in os.listdir(base_download_path) if os.path.isdir(os.path.join(base_download_path, f))]
        
        for folder_name in folders:
            dest_folder = get_destination_folder(folder_name)
            source_folder_path = os.path.join(base_download_path, folder_name)
            
            logging.info(f"Processing folder: {folder_name} -> Uploading to: {dest_folder}")
            
            # Ensure destination folder exists (optional, but good practice. SELECT will fail if not)
            typ, data = mail.select(dest_folder)
            if typ != 'OK':
                logging.warning(f"Destination folder {dest_folder} might not exist or select failed. Attempting to create or skip.")
                # You might want to try mail.create(dest_folder) here if appropriate
            
            # Iterate through email directories
            email_dirs = [d for d in os.listdir(source_folder_path) if os.path.isdir(os.path.join(source_folder_path, d))]
            email_dirs.sort() # upload in order, roughly
            
            for email_dir in email_dirs:
                email_path = os.path.join(source_folder_path, email_dir, 'email.eml')
                if os.path.exists(email_path):
                    upload_single_email(mail, dest_folder, email_path)
                else:
                    logging.warning(f"No email.eml found in {email_dir}")

    finally:
        mail.logout()
        logging.info("Logged out from destination server.")

def upload_single_email(mail, dest_folder, file_path):
    try:
        with open(file_path, 'rb') as f:
            raw_email = f.read()
        
        msg = email.message_from_bytes(raw_email)
        
        # Parse date for InternalDate
        date_header = msg['Date']
        internal_date = None
        if date_header:
            try:
                dt = parsedate_to_datetime(date_header)
                # Convert to time.struct_time usually expected, or let imaplib format it
                # imaplib.Time2Internaldate takes time.time() float or struct_time
                internal_date = Time2Internaldate(time.mktime(dt.timetuple()))
            except Exception as e:
                logging.warning(f"Could not parse date '{date_header}': {e}. Using current time.")
                internal_date = Time2Internaldate(time.time())
        else:
             internal_date = Time2Internaldate(time.time())

        # Append to folder
        # Arguments: folder, flags, date_time, message
        typ, data = mail.append(dest_folder, '(\\Seen)', internal_date, raw_email)
        
        if typ == 'OK':
            logging.info(f"Successfully uploaded: {os.path.basename(os.path.dirname(file_path))}")
        else:
            logging.error(f"Failed to upload {file_path}: {data}")

    except Exception as e:
        logging.error(f"Error uploading {file_path}: {e}")

def main():
    try:
        load_env()
        upload_emails()
    except Exception as e:
        logging.critical(f"Critical error: {e}")

if __name__ == '__main__':
    main()

