import pdfplumber
import fitz
import base64
import os
from parsing import parse_text, parse_image

def merge_dicts(dict1, dict2):
    merged_dict = {}
    for key in set(dict1.keys()):
        value1 = dict1.get(key)
        value2 = dict2.get(key)
        
        if value1 == [None] and value2 == [None]:
            merged_dict[key] = [None]
        elif value1 == [None]:
            merged_dict[key] = value2
        elif value2 == [None]:
            merged_dict[key] = value1
        elif value1 == value2:
            merged_dict[key] = value1
        else:
            merged_dict[key] = [value1, value2] if not isinstance(value1, list) else value1 + value2

    return merged_dict

def club_data(invoice_dict: dict) -> dict:
    final_data = {}
    for index, (_, data_list) in enumerate(invoice_dict.items(), start=1):
        final_data[index] = data_list[0]
        for data in data_list:
            final_data[index] = merge_dicts(final_data[index], data)
    return final_data

def process_pdf(pdf_path):
    invoice_dict = {}
    most_recent_invoice_number = None

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            
            if page_text:
                # Process text-based page
                extracted_data = parse_text(page_text)
            else:
                # Process image-based page
                doc = fitz.open(pdf_path)
                page = doc.load_page(page_num)  # Load the current page

                # Calculate the zoom factor based on desired DPI
                dpi = 300
                zoom = dpi / 72  # PDF default resolution is 72 DPI
                mat = fitz.Matrix(zoom, zoom)
            
                pix = page.get_pixmap(matrix=mat)  # Render page to an image

                image_path = f"page_{page_num + 1}.png"
                pix.save(image_path)  # Save the image

                with open(image_path, "rb") as image_file:
                    base64_img = base64.b64encode(image_file.read()).decode('utf-8')
                
                extracted_data = parse_image(base64_img)
                os.remove(image_path)  # Remove the image file

                doc.close()  # Close the document
            
            invoice_number = extracted_data.get('invoice_number')[0]
                
            if invoice_number:
                most_recent_invoice_number = invoice_number
            if most_recent_invoice_number not in invoice_dict:
                invoice_dict[most_recent_invoice_number] = []
            invoice_dict[most_recent_invoice_number].append(extracted_data)
            if most_recent_invoice_number is None and invoice_number is None:
                raise ValueError("Invoice number not found on the first page.")

    final_data = club_data(invoice_dict)
    return final_data

def process_image(image_path):
    with open(image_path, "rb") as image_file:
        base64_img = base64.b64encode(image_file.read()).decode('utf-8')
        
    extracted_data = parse_image(base64_img)

    return extracted_data
