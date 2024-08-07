import os
from dotenv import load_dotenv
from utils.extractor import Extractor
from utils.classifier import Classifier
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, StandardBlobTier
from adlfs import AzureBlobFileSystem

class Blob_Storage:

    def __init__(self) -> None:
        load_dotenv()
        self.connection_string = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container_name = os.environ["CONTAINER_NAME"]
        self.extractor = Extractor()
        self.classifier = Classifier()
    
    def upload_to_blob(self, filename, file_data):
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=filename)
        blob_client.upload_blob(file_data, overwrite=True)
        print(f"Attachment {filename} uploaded to Azure Blob Storage.")


    def access_blob(self, filename):
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=filename)
        blob_data = blob_client.download_blob()
        return blob_data.readall()
    
    def extract_and_classify_blob(self):
        container_client = self.blob_service_client.get_container_client(self.container_name)
        blob_list = container_client.list_blobs()
        
        for blob in blob_list:
            blob_name = blob.name
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_name)
            blob_data = blob_client.download_blob()
            file_data = blob_data.readall()
            blob_extension = self.extractor.get_file_extension(blob_name)
            
            if blob_extension.lower() == '.eml':
                print(f"Attachment {blob_name}:")
                attachments_content = self.extractor.read_eml(file_data)
                for att_content in attachments_content:
                    content_extension = self.extractor.get_file_extension(att_content)
                    content, attachment_data = attachments_content[att_content]

                    isInvoice = self.classifier.invoice_classifier(content)
                    
                    if "No" in isInvoice and content_extension.lower() == '.pdf':
                        content = self.extractor.read_pdf_as_image_azureocr(attachment_data)
                        isInvoice = self.classifier.invoice_classifier(content)

                    print(f"{att_content} is Invoice: {isInvoice}") 
                
                print('\n')
            
            elif blob_extension.lower() == '.pdf':
                content = self.extractor.read_pdf_pdfPlumber(file_data)
                isInvoice = self.classifier.invoice_classifier(content)
                
                if "No" in isInvoice:
                    content = self.extractor.read_pdf_as_image_azureocr(file_data)
                    isInvoice = self.classifier.invoice_classifier(content)

                print(f"Attachment {blob_name} is Invoice ?: {isInvoice}")

            else:
                content = self.extractor.read_document(blob_name, file_data)
                isInvoice = self.classifier.invoice_classifier(content)
                print(f"Attachment {blob_name} is Invoice ?: {isInvoice}")
        
        return



    def set_blob_access_tier(self):
        container_client = self.blob_service_client.get_container_client(self.container_name)
        blob_list = container_client.list_blobs()
        print(f"Blobs in '{self.container_name}' container:")
        for blob in blob_list:
            blob_name = blob.name
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_name)

            blob_properties = blob_client.get_blob_properties()
            access_tier = blob_properties.blob_tier
            print(f"The access tier of blob '{blob_name}' is '{access_tier}'.")

            # Change the access tier
            new_tier = StandardBlobTier.HOT  # Options: Hot, Cool, Archive
            blob_client.set_standard_blob_tier(new_tier)

            print(f"The access tier of blob '{blob_name}' has been set to '{new_tier}'.\n")
