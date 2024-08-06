import os
from openai import AzureOpenAI
from dotenv import load_dotenv

class Classifier:

    def __init__(self):
        load_dotenv()
        self.GPT_KEY = os.getenv('GPT_KEY')
        self.GPT_ENDPOINT = os.getenv('GPT_ENDPOINT')
        self.GPT_VERSION = os.getenv('GPT_VERSION')
        self.GPT_DEPLOYMENT_NAME = os.getenv('GPT_DEPLOYMENT_NAME')

        self.client = AzureOpenAI(
            api_key = self.GPT_KEY,
            api_version = self.GPT_VERSION,
            azure_endpoint = self.GPT_ENDPOINT
        )

    def invoice_classifier(self, content):
        query = f'''Does the below content indicate an Invoice statement ?
                {content}
                // Yes or No.'''

        response = self.client.chat.completions.create(
                            model = self.GPT_DEPLOYMENT_NAME,
                            messages = [
                                {
                                    "role": "system",
                                    "content": [
                                        {
                                        "type": "text",
                                        "text": ''' You are an helpful AI assistant. You help users to decide whether the content provided by them represents an invoice or not. You can judge the content based on certain invoice-related keywords. A few of them include:
                                        - Invoice Number
                                        - Invoice Date
                                        - Statement
                                        - Total Due
                                        - Due Date
                                        - Bill To
                                        - Sold to
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

        return(response.choices[0].message.content)