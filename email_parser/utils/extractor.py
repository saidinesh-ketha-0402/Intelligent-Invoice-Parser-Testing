import os
import io
import email
import base64
from mimetypes import guess_type
from email.parser import BytesParser
import pdfplumber
from dotenv import load_dotenv
from openai import AzureOpenAI

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials


class Extractor:
    
    def __init__(self):
        load_dotenv()
        self.AZURE_OCR_KEY =  os.environ["VISION_KEY"]
        self.AZURE_OCR_ENDPOINT =  os.environ["VISION_ENDPOINT"]
        self.GPT_KEY = os.getenv('GPT_KEY')
        self.GPT_ENDPOINT = os.getenv('GPT_ENDPOINT')
        self.GPT_VERSION = os.getenv('GPT_VERSION')
        self.GPT_DEPLOYMENT_NAME = os.getenv('GPT_DEPLOYMENT_NAME')

        self.client = AzureOpenAI(
            api_key = self.GPT_KEY,
            api_version = self.GPT_VERSION,
            azure_endpoint = self.GPT_ENDPOINT
        )


    def get_file_extension(self, file_path):
        _, file_extension = os.path.splitext(file_path)
        return file_extension
    

    def image_to_data_url(self, image_path, img_byte_arr):
        mime_type, _ = guess_type(image_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'

        base64_encoded_data = base64.b64encode(img_byte_arr).decode('utf-8')

        return f"data:{mime_type};base64,{base64_encoded_data}"
    

    def read_document(self, file_path, file_data):
        file_extension = self.get_file_extension(file_path)
        
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
    

    def read_img_gpt_4o(self, image_url):
        query = "Extract the text from the image."
        response = self.client.chat.completions.create(
                            model = os.getenv('GPT_DEPLOYMENT_NAME'),
                            messages = [
                                {
                                    "role": "system",
                                    "content": [
                                        {
                                        "type": "text",
                                        "text": ''' You are an helpful AI assistant and your job is to extract the text in the image and provide it to the user. You can use the image to text conversion techniques to extract the text. Once you have extracted the text, you can provide it to the user. Just output the extracted text and nothing else.'''
                                        }
                                    ]
                                },
                                {
                                    "role" : "user",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": f"{query}"
                                        },
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url" : f"{image_url}"
                                            }
                                        }
                                        
                                    ]
                                },
                            ],
                            max_tokens = 2000,
                            temperature = 0,
                            top_p = 1
                        )

        return response.choices[0].message.content


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
                    attachments_content[file_name] = (content, attachment_data)

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
    

    def read_pdf_as_image_gpt(self, img_path, file_data):
        print("Reading PDF as image using GPT...")
        try:
            content = ''
            with pdfplumber.open(io.BytesIO(file_data)) as pdf:
                for page in pdf.pages:
                    image = page.to_image()
                    img_byte_arr = io.BytesIO()
                    image.original.save(img_byte_arr, format='PNG')
                    img_byte_arr = img_byte_arr.getvalue()
                    image_url = self.image_to_data_url(img_path, img_byte_arr)
                    content += self.read_img_gpt_4o(image_url)
            return content                    
                
        except Exception as e:
            print(f"Failed to extract text from PDF: {e}")
            return ""
