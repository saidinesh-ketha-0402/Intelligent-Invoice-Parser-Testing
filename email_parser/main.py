from utils.email_monitor import Monitor
from utils.extractor import Extractor
from utils.classifier import Classifier
from utils.blob_storage import Blob_Storage
from typing import List, Dict
import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel

class Message(BaseModel):
    id: str

app = FastAPI()
# email_monitor = Monitor()
# service = email_monitor.authenticate_gmail()

@app.get("/")
def read_root():
    email_monitor = Monitor()
    service = email_monitor.authenticate_gmail()
    messages = get_emails(email_monitor, service)
    download_attachments(messages, email_monitor, service)
    extract_and_classify_blob(email_monitor)
    return "This is a FAST API application for enabling the email parser to use other services."


# def read_root():
#     messages = requests.post("http://127.0.0.1:8000/fetch_emails").json()
#     download_response = requests.post("http://127.0.0.1:8000/download_attachments", json=messages)
#     return {
#         "message": "This is a FAST API application for enabling my email parser to use other services.",
#         "emails": messages,
#         "download_status": download_response.json()
#     }

# @app.post("/fetch_emails")
def get_emails(email_monitor, service):
    messages = email_monitor.search_emails_with_attachments(service)
    return messages

# @app.post("/download_attachments")
# def download_attachments_endpoint(messages: List[Message]):
#     result = download_attachments(messages)
#     return {"status": result}

def download_attachments(messages, email_monitor, service):
    if messages:
        for msg in messages:
            email_monitor.download_attachments(service, 'me', msg['id'])
    return "Attachments downloaded successfully."

def extract_and_classify_blob(email_monitor):
    email_monitor.storage.extract_and_classify_blob()
    return "Blob extracted and classified successfully."

# if messages:
#     for msg in messages:
#         email_monitor.download_attachments(service, 'me', msg['id'])

# blob_storage = Blob_Storage()
# blob_storage.extract_and_classify_blob()