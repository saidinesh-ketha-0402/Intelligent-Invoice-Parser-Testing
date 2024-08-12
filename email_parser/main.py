from typing import List
from utils.email_monitor import Monitor
from fastapi import FastAPI
from pydantic import BaseModel
import httpx

class MessageIds(BaseModel):
    ids: List[str]

app = FastAPI()
email_monitor = Monitor()
service = email_monitor.authenticate_gmail()


@app.get("/")
async def root():
    return await read_root()

async def read_root():
    async with httpx.AsyncClient() as client:
        # Fetch emails
        fetch_response = await client.post("http://127.0.0.1:8000/fetch_emails")
        if fetch_response.status_code != 200:
            return {"error": "Failed to fetch emails"}
        
        messages = fetch_response.json()
        
        if messages:
            msg_ids = [msg['id'] for msg in messages]
            
            # Download attachments
            download_response = await client.post("http://127.0.0.1:8000/download_attachments", json={"ids": msg_ids})
            if download_response.status_code != 200:
                return {"error": "Failed to download attachments"}
            
            # Extract and classify blob
            classify_response = await client.post("http://127.0.0.1:8000/extract_and_classify_blob")
            if classify_response.status_code != 200:
                return {"error": "Failed to extract and classify blob"}
        
    return "This is a FAST API application for enabling the email parser to use other services."



@app.post("/fetch_emails")
async def get_emails():
    messages = email_monitor.search_emails_with_attachments(service)
    return messages


@app.post("/download_attachments")
async def download_attachments(msg_ids: MessageIds):
    if msg_ids:
        for msg in msg_ids.ids:
            email_monitor.download_attachments(service, 'me', msg)
    return "Attachments downloaded successfully."


@app.post("/extract_and_classify_blob")
async def extract_and_classify_blob():
    email_monitor.storage.extract_and_classify_blob()
    return "Blob extracted and classified successfully."