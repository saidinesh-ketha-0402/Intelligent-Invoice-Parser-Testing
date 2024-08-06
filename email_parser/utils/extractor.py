import os
import io
import PyPDF2
import docx
import mammoth
import easyocr
import email
from email.parser import BytesParser
import pymupdf
import pdfplumber
from openai import AzureOpenAI
from dotenv import load_dotenv

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials


class Extractor:
    
    def __init__(self):
        load_dotenv()
        self.AZURE_OCR_KEY =  os.environ["VISION_KEY"]
        self.AZURE_OCR_ENDPOINT =  os.environ["VISION_ENDPOINT"]
        self.container_name = os.environ["CONTAINER_NAME"]


    def read_document(self, file_path, file_data):
        _, file_extension = os.path.splitext(file_path)
        
        if file_extension.lower() == '.pdf' :
            return self.read_pdf_pdfPlumber(file_data)
        elif file_extension.lower() in ['.jpg', '.jpeg', '.png']:
            return self.read_img_azure_ocr(file_data)
        elif file_extension.lower() == '.eml':
            return self.read_eml(file_data)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")


    def read_pdf_pdfPlumber(self, file_data):
        try:
            with pdfplumber.open(io.BytesIO(file_data)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return text
            
        except Exception as e:
            print(f"Failed to extract text from PDF: {e}")
            return ""


    def read_img_azure_ocr(self, file_data):
        try:
            content = ''
            load_dotenv()
            subscription_key = self.AZURE_OCR_KEY
            endpoint = self.AZURE_OCR_ENDPOINT
            computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))
            
            ocr_result = computervision_client.recognize_printed_text_in_stream(io.BytesIO(file_data))

            for region in ocr_result.regions:
                for line in region.lines:
                    line_text = " ".join([word.text for word in line.words])
                    content += line_text + ' '
            
            return content

        except Exception as e:
            print(f"Error reading Image: {e}")
            return ""

    def read_eml(self, file_data):  
        try:
            attachments_content = dict()
            msg = BytesParser(policy=email.policy.default).parsebytes(file_data)
            
            # Process the email parts
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue

                file_name = part.get_filename()
                if file_name:
                    # Read the attachment content directly from memory
                    attachment_data = part.get_payload(decode=True)
                    # Process the attachment content
                    content = self.read_document(file_name, attachment_data)
                    attachments_content[file_name] = content

            return attachments_content
        
        except Exception as e:
            print(f"Error reading EML: {e}")
            return ""
    
    def read_pdf_as_image_azureocr(self, file_data, image_path='attachments/Positive Examples/images/sample.png'):
            print("Reading PDF as image using Azure OCR...")
            try:
                content = ''
                with pdfplumber.open(io.BytesIO(file_data)) as pdf:
                    for page in pdf.pages:
                        image = page.to_image()
                        img_byte_arr = io.BytesIO()
                        image.original.save(img_byte_arr, format='PNG')
                        img_byte_arr = img_byte_arr.getvalue()
                        content += self.read_img_azure_ocr(img_byte_arr)
                return content                    
                    
            except Exception as e:
                print(f"Failed to extract text from PDF: {e}")
                return ""
