from typing import List
from utils.email_monitor import Monitor
from fastapi import FastAPI
from pydantic import BaseModel
import requests

class MessageIds(BaseModel):
    ids: List[str]

app = FastAPI()
email_monitor = Monitor()
service = email_monitor.authenticate_gmail()


@app.get("/")
def read_root():
    messages = requests.post(f"http://127.0.0.1:8000/fetch_emails").json()
    msg_ids = [msg['id'] for msg in messages]
    requests.post(f"http://127.0.0.1:8000/download_attachments", json={"ids": msg_ids})
    requests.post(f"http://127.0.0.1:8000/extract_and_classify_blob")
    return "This is a FAST API application for enabling the email parser to use other services."


@app.post("/fetch_emails")
def get_emails():
    messages = email_monitor.search_emails_with_attachments(service)
    return messages


@app.post("/download_attachments")
def download_attachments(msg_ids: MessageIds):
    if msg_ids:
        for msg in msg_ids.ids:
            email_monitor.download_attachments(service, 'me', msg)
    return "Attachments downloaded successfully."


@app.post("/extract_and_classify_blob")
def extract_and_classify_blob():
    email_monitor.storage.extract_and_classify_blob()
    return "Blob extracted and classified successfully."