This script downloads and archives emails from specified email folders using IMAP. It saves the emails, attachments, and body text to the local filesystem.

# Usage

1. Create a .env file in the project directory with the following content:
```sh
EMAIL_USER=your_email@example.com
EMAIL_PASSWORD=your_password
IMAP_URL=your_imap_server_url
```
2. Adjust date range and folder names in the main function in script as needed.
3. Run the script with `python3 script.py`.