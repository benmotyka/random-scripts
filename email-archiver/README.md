This project contains scripts to download and upload emails using IMAP.

## download_emails (script.py)

Downloads and archives emails from specified email folders. It saves the emails (`.eml`), attachments, and body text to the local filesystem in `downloaded-emails/`.

### Usage

1. Create a `.env` file in the project directory with your source email credentials:
```sh
EMAIL_USER=your_email@example.com
EMAIL_PASSWORD=your_password
IMAP_URL=your_imap_server_url
```
2. Run the script:
```sh
python3 script.py
```

## upload_emails (upload_emails.py)

Uploads the locally downloaded emails (from `downloaded-emails/`) to a destination email account.

### Usage

1. Add your destination email credentials to the `.env` file:
```sh
# Destination credentials
EMAIL_USER_2=dest_email@example.com
EMAIL_PASSWORD_2=dest_password
IMAP_URL_2=ssl0.ovh.net
```
2. Run the script:
```sh
python3 upload_emails.py
```

### Folder Mapping
The script maps local folders to destination IMAP folders.
- `Elementy wys&AUI-ane` -> `INBOX.INBOX.Sent`
- `INBOX` -> `INBOX`
You can modify the `get_destination_folder` function in `upload_emails.py` to adjust these mappings.
