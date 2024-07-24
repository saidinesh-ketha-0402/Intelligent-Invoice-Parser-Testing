import os
import PyPDF2
import docx
import mammoth
import easyocr
import email
from openai import AzureOpenAI
from dotenv import load_dotenv

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials

def read_document(file_path):
    _, file_extension = os.path.splitext(file_path)
    
    if file_extension.lower() == '.txt':
        return read_txt(file_path)
    elif file_extension.lower() == '.pdf':
        return read_pdf(file_path)
    elif file_extension.lower() == '.docx':
        return read_docx(file_path)
    elif file_extension.lower() == '.doc':
        return read_doc(file_path)
    elif file_extension.lower() in ['.jpg', '.jpeg', '.png']:
        return read_img_azure_ocr(file_path)
    elif file_extension.lower() == '.eml':
        return read_eml(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

def read_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    
    except Exception as e:
        print(f"Error reading TXT: {e}")
        return ""

def read_pdf(file_path):
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            content = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
            content += page.extract_text()
        return content
    
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def read_docx(file_path):
    try:
        doc = docx.Document(file_path)
        content = '\n'.join([para.text for para in doc.paragraphs])
        return content
    
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""

def read_doc(file_path):
    try:
        with open(file_path, "rb") as file:
            result = mammoth.extract_raw_text(file)
            content = result.value
        return content
    
    except Exception as e:
        print(f"Error reading DOC: {e}")
        return ""

def read_img(file_path):
    try:
        reader = easyocr.Reader(['en'], verbose=False)
        result = reader.readtext(file_path)
        content = ' '.join([text[1] for text in result])
        return content
    
    except Exception as e:
        print(f"Error reading Image: {e}")
        return ""

def read_img_azure_ocr(file_path):
    try:
        content = ''
        load_dotenv()
        subscription_key = os.environ["VISION_KEY"]
        endpoint = os.environ["VISION_ENDPOINT"]
        computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))
        
        with open(file_path, "rb") as image_stream:
            ocr_result = computervision_client.recognize_printed_text_in_stream(image_stream)

        for region in ocr_result.regions:
            for line in region.lines:
                line_text = " ".join([word.text for word in line.words])
                content += line_text + ' '
        
        return content

    except Exception as e:
        print(f"Error reading Image: {e}")
        return ""

def read_eml(file_path, output_dir='attachments/'):  
    try:
        attachments_content = []
        with open(file_path, 'r') as file:
            msg = email.message_from_file(file)
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue

                file_name = part.get_filename()
                if file_name:
                    filepath = os.path.join(output_dir, file_name)
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    print(f"Attachment {file_name} downloaded.")
                    content = read_document(output_dir + file_name)
                    attachments_content.append(content)

        return content
    
    except Exception as e:
        print(f"Error reading EML: {e}")
        return ""

# Example usage
file_path = 'attachments/Positive Examples/images/Statement_1759_from_Green_Circuits_Inc.pdf.png'
content = read_document(file_path)
print('Extracted Content:\n' , content)


load_dotenv()

GPT_KEY = os.getenv('GPT_KEY')
GPT_ENDPOINT = os.getenv('GPT_ENDPOINT')
GPT_VERSION = os.getenv('GPT_VERSION')
GPT_DEPLOYMENT_NAME = os.getenv('GPT_DEPLOYMENT_NAME')

client = AzureOpenAI(
    api_key = GPT_KEY,
    api_version = GPT_VERSION,
    azure_endpoint = GPT_ENDPOINT
)

query = f'''Does the below content indicate an Invoice statement ?
        {content}
        // Yes or No.'''

response = client.chat.completions.create(
                    model = GPT_DEPLOYMENT_NAME,
                    messages = [
                        {
                            "role": "system",
                            "content": [
                                {
                                "type": "text",
                                "text": ''' You are an helpful AI assistant. You help users to decide whether the content provided by them represents an invoice or not. You can judge the content based on certain invoice-related keywords. A few of them include:
                                - Invoice Number
                                - Invoice Date
                                - Due Date
                                - Bill To
                                - Ship To
                                - Customer
                                - Order Number
                                - Purchase Order (PO) Number
                                - Terms
                                - Line Item
                                - Quantity
                                - Unit Price
                                - Total
                                - Subtotal
                                - Tax
                                - Discount
                                - Shipping Cost
                                - Balance Due
                                - Amount Paid
                                - Remit To
                                - Description
                                - Net Price
                                - Contact Information
                                If you find a **good amount of keywords in the given content**, you can **return your verdict as Yes, else No**. Give your verdict in a simple Yes/No format.
                                '''
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
                            ]
                        },
                    ],
                    max_tokens = 100,
                    temperature = 0,
                    top_p = 0.95,
                    seed=101
                )

print(response.choices[0].message.content)