from typing import List, Optional, Union
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
import instructor

load_dotenv()

GPT_KEY = os.getenv('OPENAI_API_KEY')
GPT_ENDPOINT = os.getenv('OPENAI_API_BASE')
GPT_VERSION = os.getenv('OPENAI_API_VERSION')
MODEL = os.getenv('OPENAI_API_DEPLOYMENT')

client = AzureOpenAI(
    api_key=GPT_KEY,
    api_version=GPT_VERSION,
    azure_endpoint=GPT_ENDPOINT
)

class Address(BaseModel):
    name: Optional[str] = Field("", title="Name",description="Name of the company")
    street: Optional[str] = Field("", title="Street")
    city: Optional[str] = Field("", title="City")
    state: Optional[str] = Field("", title="State")
    zip_code: Optional[str] = Field("", title="Zip Code")
    country: Optional[str] = Field("", title="Country",description="Country of the address. It is optional, and if could not find, default value is empty string.")

    class Config:
        schema_extra = {
            "example": {
                "name": "ABC Company",
                "street": "123 Main St",
                "city": "City",
                "state": "State",
                "zip_code": "12345",
                "country": "USA"
            }
        }

class Product(BaseModel):
    part_number: Optional[str] = Field(None, title="Customer Part Number", description="Unique identifier assigned to the product for the customer (Customer part number).")
    product_description: Optional[str] = Field(None, title="Product Description", description="Description of the product")
    quantity: Optional[int] = Field(None, title="Quantity", description="Number of units")
    unit_price: Optional[float] = Field(None, title="Unit Price", description="Price per unit")
    total_price: Optional[float] = Field(None, title="Total Price", description="Total price (quantity * unit price)")
    class Config:
        schema_extra = {
            "example": {
                "part_number": "P12345",
                "product_description": "Receiver, Somero SSR2",
                "quantity": 10,
                "unit_price": 2.99,
                "total_price": 100
            }
        }

class Invoice(BaseModel):
    invoice_number: Optional[str] = Field(None, title="Invoice Number", description="Unique identifier for the invoice")
    issue_date: Optional[str] = Field(None, title="Invoice Date", description="Date when the invoice was issued")
    due_date: Optional[str] = Field(None, title="Due Date", description="Date when the payment is due")
    po_number: Optional[str] = Field(None, title="Purchase Order Number", description="Unique identifier for the purchase order. ")
    customer_id: Optional[str] = Field(None, title="Customer ID", description="Unique identifier for the customer")
    sales_person: Optional[str] = Field(None, title="Sales Person", description="Name of the sales person handling the invoice")
    payment_terms: Optional[str] = Field(None, title="Payment Terms", description="Terms of payment")
    packaging_slip_number: Optional[Union[str, List[str]]] = Field(None, title="Packaging Slip Number", description="Unique identifier for the packaging slip")
    tracking_number: Optional[Union[str, List[str]]] = Field(None, title="Tracking Number", description="Unique identifier for the tracking number")
    vendor_name: Optional[str] = Field(..., title="Vendor Name", description="Name of the vendor")
    remit_address: Optional[Address] = Field(None, title="Remit Address of the vendor.", description="A destination for receiving payment via  cheques(or checks) .")
    bill_to_address: Optional[Union[Address, List[Address]]] = Field(None, title="Bill To", description="Address where the recipient of goods or services would like the invoice or bill to be sent.")
    ship_to_address: Optional[Union[Address, List[Address]]] = Field(None, title="Ship To", description="Address to which the goods are sent.")
    products: Optional[Union[Product, List[Product]]] = Field(None, title="Products", description="List of products included in the invoice")
    total_amount: Optional[float] = Field(None, title="Total Amount", description="Total amount of the invoice")
    currency: Optional[str] = Field(None, title="Currency", description="Currency of the total amount or currency of invoice")

    class Config:
        schema_extra = {
            "examples": {
                "example1": {
                    "invoice_number": "Invoice 291870.4-1",
                    "issue_date": "2022-01-01",
                    "due_date": "2022-01-31",
                    "po_number": "PO123456",
                    "customer_id": "C12345",
                    "sales_person": "John Doe",
                    "payment_terms": "Net 30",
                    "packaging_slip_number": "PS12345",
                    "tracking_number": "T12345",
                    "vendor_name": "ABC Company",
                    "total_amount": "₹ 31.98"
                },
                "example2": {
                    "invoice_number": "Invoice 291870.4-2",
                    "issue_date": "Jul 12, 2024",
                    "due_date": "Aug 12, 2024",
                    "po_number": "PO654321",
                    "customer_id": "C54321",
                    "sales_person": "Jane Doe",
                    "payment_terms": "NET 45",
                    "packaging_slip_number": "PS54321",
                    "tracking_number": "T54321",
                    "vendor_name": "DEF Company",
                    "total_amount": "$ 200"
                }
            }
        }

def parse_text(text: str) -> dict:
    response = instructor.from_openai(client).chat.completions.create(
        model=MODEL,
        response_model=Invoice,
        messages=[
            {"role": "system", "content": "You are a helpful assistant helping me with extracting information from an invoice text."},
            {"role": "user", "content": f"Consider the following text below:\n {text} and Extract information based on response_model specified in the function. If you cannot extract then specify the field as None."},
        ],
        temperature=0.2,
    )
    data = {
        'invoice_number': [response.invoice_number],
        'issue_date': [response.issue_date],
        'po_number': [response.po_number],
        'due_date': [response.due_date],
        'customer_id': [response.customer_id],
        'sales_person': [response.sales_person],
        'payment_terms': [response.payment_terms],
        'packaging_slip_number': [response.packaging_slip_number],
        'tracking_number': [response.tracking_number],
        'vendor_name': [response.vendor_name],
        'remit_address': [
            {
                'name': address.name,
                'street': address.street,
                'city': address.city,
                'state': address.state,
                'zip_code': address.zip_code,
                'country': address.country
            } for address in (response.remit_address if isinstance(response.remit_address, list) else [response.remit_address] if response.remit_address else [])
        ],
        'bill_to_address': [
            {
                'name': address.name,
                'street': address.street,
                'city': address.city,
                'state': address.state,
                'zip_code': address.zip_code,
                'country': address.country
            } for address in (response.bill_to_address if isinstance(response.bill_to_address, list) else [response.bill_to_address] if response.bill_to_address else [])
        ],
        'ship_to_address': [
            {
                'name': address.name,
                'street': address.street,
                'city': address.city,
                'state': address.state,
                'zip_code': address.zip_code,
                'country': address.country
            } for address in (response.ship_to_address if isinstance(response.ship_to_address, list) else [response.ship_to_address] if response.ship_to_address else [])
        ],
        'products': [
            {
                'part_number': product.part_number,
                'product_description': product.product_description,
                'quantity': product.quantity,
                'unit_price': product.unit_price,
                'total_price': product.total_price
            } for product in (response.products if isinstance(response.products, list) else [response.products] if response.products else [])
        ],
        'total_amount': [response.total_amount],
        'currency': [response.currency]
    }
    return data

def parse_image(base64_img: str) -> dict:
    response = instructor.from_openai(client).chat.completions.create(
    model=MODEL,
    response_model = Invoice,
    messages=[
        {"role": "system", "content": "You are a helpful assistant helping me with extracting information from an invoice image."},
        {"role": "user", "content": [
            {"type": "text", "text": "Extract information based on response_model specified in the function . If you cannot extract then specify the field as None."},
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{base64_img}"}
            }
        ]}
    ],
    temperature=0.2,
    )
    data = {
        'invoice_number': [response.invoice_number],
        'issue_date': [response.issue_date],
        'po_number': [response.po_number],
        'due_date': [response.due_date],
        'customer_id': [response.customer_id],
        'sales_person': [response.sales_person],
        'payment_terms': [response.payment_terms],
        'packaging_slip_number': [response.packaging_slip_number],
        'tracking_number': [response.tracking_number],
        'vendor_name': [response.vendor_name],
        'remit_address': [
            {
                'name': address.name,
                'street': address.street,
                'city': address.city,
                'state': address.state,
                'zip_code': address.zip_code,
                'country': address.country
            } for address in (response.remit_address if isinstance(response.remit_address, list) else [response.remit_address] if response.remit_address else [])
        ],
        'bill_to_address': [
            {
                'name': address.name,
                'street': address.street,
                'city': address.city,
                'state': address.state,
                'zip_code': address.zip_code,
                'country': address.country
            } for address in (response.bill_to_address if isinstance(response.bill_to_address, list) else [response.bill_to_address] if response.bill_to_address else [])
        ],
        'ship_to_address': [
            {
                'name': address.name,
                'street': address.street,
                'city': address.city,
                'state': address.state,
                'zip_code': address.zip_code,
                'country': address.country
            } for address in (response.ship_to_address if isinstance(response.ship_to_address, list) else [response.ship_to_address] if response.ship_to_address else [])
        ],
        'products': [
            {
                'part_number': product.part_number,
                'product_description': product.product_description,
                'quantity': product.quantity,
                'unit_price': product.unit_price,
                'total_price': product.total_price
            } for product in (response.products if isinstance(response.products, list) else [response.products] if response.products else [])
        ],
        'total_amount': [response.total_amount],
        'currency': [response.currency]
    }

    return data