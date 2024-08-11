import os.path
import base64
import json
import dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from utils.blob_storage import Blob_Storage

class Monitor:

    def __init__(self):
        dotenv.load_dotenv()
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
        self.storage = Blob_Storage()
        

    def authenticate_gmail(self):
        creds = None
        token_json = os.environ['TOKEN']

        if token_json:
            creds = Credentials.from_authorized_user_info(json.loads(token_json), self.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                config = json.loads(os.environ['CRED'])
                flow = InstalledAppFlow.from_client_config(
                    config, self.SCOPES)
                creds = flow.run_local_server(port=0)
            dotenv.set_key('.env', "TOKEN", creds.to_json())
        return build('gmail', 'v1', credentials=creds)


    def is_valid_extension(self, file_path):
        _, file_extension = os.path.splitext(file_path)
        
        if file_extension.lower() in ['.txt', '.pdf', '.jpg', '.jpeg', '.png', '.eml']:
            return True
        
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def get_label_ids(self, service):
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        user_labels = [label for label in labels if label['type'] == 'user']
        return user_labels


    def search_emails_with_attachments(self, service, user_id='me'):
        
        # Query if the polling interval is 1 hour.
        # now = int(time.time())
        # five_minutes_ago = now - 60*60
        # query = f'in:inbox has:attachment after:{five_minutes_ago} before:{now}'
        
        # Query if the polling interval is 1 day.
        query = 'in:inbox has:attachment newer_than:1d -label:processed'
        results = service.users().messages().list(userId=user_id, q=query).execute()
        messages = results.get('messages', [])
        if not messages:
            print("No messages found.")
        else:
            print(f"Found {len(messages)} messages with attachments.")
            return messages


    def mark_email_as_processed(self, service, user_id, msg_id, user_labels):
        body = {'removeLabelIds': ['UNREAD'], 'addLabelIds': [user_labels[0]['id']]}
        service.users().messages().modify(userId=user_id, id=msg_id, body=body).execute()
        print(f"Email with ID {msg_id} has been processed and marked as read.\n")


    def download_attachments(self, service, user_id, msg_id):
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        parts = message.get('payload').get('parts')
        user_labels = self.get_label_ids(service)

        if parts:
            for part in parts:
                if part.get('filename') and self.is_valid_extension(part.get('filename')):
                    if 'data' in part['body']:
                        data = part['body']['data']
                    else:
                        att_id = part['body'].get('attachmentId')
                        att = service.users().messages().attachments().get(userId=user_id, messageId=msg_id, id=att_id).execute()
                        data = att['data']
                    file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                    self.storage.upload_to_blob(part['filename'], file_data)
        
        # Enable it before pushing it into production.
        self.mark_email_as_processed(service, user_id, msg_id, user_labels)

