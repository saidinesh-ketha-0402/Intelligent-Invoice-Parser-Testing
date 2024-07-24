import os.path
import base64
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def is_valid_extension(file_path):
    _, file_extension = os.path.splitext(file_path)
    
    if file_extension.lower() in ['.txt', '.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png', '.eml']:
        return True
    
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")


def search_emails_with_attachments(service, user_id='me'):
    query = 'in:inbox is:unread has:attachment'
    results = service.users().messages().list(userId=user_id, q=query).execute()
    messages = results.get('messages', [])
    if not messages:
        print("No messages found.")
    else:
        print(f"Found {len(messages)} messages with attachments.")
        return messages

def mark_email_as_read(service, user_id, msg_id):
    body = {'removeLabelIds': ['UNREAD']}
    service.users().messages().modify(userId=user_id, id=msg_id, body=body).execute()
    print(f"Email with ID {msg_id} has been marked as read.")

def download_attachments(service, user_id, msg_id, store_dir):
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    parts = message.get('payload').get('parts')
    if parts:
        for part in parts:
            if part.get('filename') and is_valid_extension(part.get('filename')):
                if 'data' in part['body']:
                    data = part['body']['data']
                else:
                    att_id = part['body'].get('attachmentId')
                    att = service.users().messages().attachments().get(userId=user_id, messageId=msg_id, id=att_id).execute()
                    data = att['data']
                file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                path = os.path.join(store_dir, part['filename'])
                with open(path, 'wb') as f:
                    f.write(file_data)
                print(f"Attachment {part['filename']} downloaded.")
    
    # Enable it before pushing it into production.
    # mark_email_as_read(service, user_id, msg_id)

service = authenticate_gmail()
messages = search_emails_with_attachments(service)

store_dir = 'attachments'
if not os.path.exists(store_dir):
    os.makedirs(store_dir)

if messages:
    for msg in messages:
        download_attachments(service, 'me', msg['id'], store_dir)
