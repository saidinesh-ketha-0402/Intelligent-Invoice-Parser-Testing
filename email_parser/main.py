from utils.email_monitor import Monitor
from utils.extractor import Extractor
from utils.classifier import Classifier
from utils.blob_storage import Blob_Storage
import os

email_monitor = Monitor()
content_extractor = Extractor()
content_classifier = Classifier()

service = email_monitor.authenticate_gmail()
messages = email_monitor.search_emails_with_attachments(service)

if messages:
    for msg in messages:
        email_monitor.download_attachments(service, 'me', msg['id'])

# blob_storage = Blob_Storage()
# blob_storage.extract_and_classify_blob()