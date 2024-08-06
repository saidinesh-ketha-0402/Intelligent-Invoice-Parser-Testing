import os.path
import base64
import re
import datetime, time
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from utils.blob_storage import Blob_Storage
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, StandardBlobTier

class Monitor:

    def __init__(self):
        load_dotenv()
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
        self.storage = Blob_Storage()
        

    def authenticate_gmail(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return build('gmail', 'v1', credentials=creds)


    def is_valid_extension(self, file_path):
        _, file_extension = os.path.splitext(file_path)
        
        if file_extension.lower() in ['.txt', '.pdf', '.jpg', '.jpeg', '.png', '.eml']:
            return True
        
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")


    def search_emails_with_attachments(self, service, user_id='me'):
        
        # Query if the polling interval is 1 hour.
        # now = int(time.time())
        # five_minutes_ago = now - 60*60
        # query = f'in:inbox has:attachment after:{five_minutes_ago} before:{now}'
        
        # Query if the polling interval is 1 day.
        query = 'in:inbox has:attachment newer_than:4d'
        results = service.users().messages().list(userId=user_id, q=query).execute()
        messages = results.get('messages', [])
        if not messages:
            print("No messages found.")
        else:
            print(f"Found {len(messages)} messages with attachments.")
            return messages


    def mark_email_as_read(self, service, user_id, msg_id):
        body = {'removeLabelIds': ['UNREAD']}
        service.users().messages().modify(userId=user_id, id=msg_id, body=body).execute()
        print(f"Email with ID {msg_id} has been marked as read.")


    def download_attachments(self, service, user_id, msg_id):
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        parts = message.get('payload').get('parts')
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
        # mark_email_as_read(service, user_id, msg_id)

