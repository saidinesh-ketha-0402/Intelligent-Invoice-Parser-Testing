from data import process_image, process_pdf
from prettytable import PrettyTable
import os
import time
import threading

def stopwatch():
    start_time = time.time()
    while not stop_event.is_set():
        elapsed_time = time.time() - start_time
        print(f"Elapsed Time: {elapsed_time:.2f} seconds", end='\r')
        time.sleep(0.1)  # Update every 0.1 seconds
    elapsed_time = time.time() - start_time
    print(f"\nTotal Elapsed Time: {elapsed_time:.2f} seconds")

def print_data(data_dict: dict, output_text):
    for data in data_dict.values():
        # Function to print tables
        def print_table(title, fields, data, output_text):
            table = PrettyTable()
            table.field_names = fields
            max_len = max((len(data[field]) for field in fields),default=0)  # Find the maximum length among the fields
            for i in range(max_len):
                row = []
                for field in fields:
                    if i < len(data[field]):
                        row.append(data[field][i])
                    else:
                        row.append("")  # Append "" if the index is out of range
                table.add_row(row)
            print(f"\n{title}")
            print(table)

            with open(output_text, 'a') as file:
                file.write(f"\n{title}\n")
                file.write(str(table))

        # Address fields
        address_fields = ['remit_address', 'bill_to_address', 'ship_to_address']
        address_data = {
            field: (
                [f"{address.get('name')}\n{address.get('street')}\n{address.get('city')}, {address.get('state')} {address.get('zip_code')}\n{address.get('country')}"] 
                if (address := data.get(field)[0]) else None
            ) 
            for field in address_fields
        }

        # Product fields
        product_fields = ['part_number', 'product_description', 'quantity', 'unit_price', 'total_price']
        product_data = {field: [product.get(field) for product in data.get('products')] for field in product_fields}

        # Other fields
        invoice_fields = ['invoice_number','po_number','issue_date','due_date','customer_id','sales_person','payment_terms','packaging_slip_number','tracking_number','total_amount','currency']
        invoice_data = {field: data.get(field) for field in invoice_fields}

        # Print the vendor name
        border = '*' * (len(data.get("vendor_name")[0]) + 4)
        print("\n\n")
        print(border)
        print(f"* {data.get("vendor_name")[0]} *")
        print(border)

        with open(output_text, 'a') as file:
            file.write("\n\n")
            file.write(border + "\n")
            file.write(f"* {data.get('vendor_name')[0]} *\n")
            file.write(border + "\n")

        # Print the tables
        print_table("Invoice Fields", invoice_fields, invoice_data,output_text)
        print_table("Address Fields", address_fields, address_data,output_text)
        print_table("Product Fields", product_fields, product_data,output_text)

def determine_file_type(file_path):
    # Get the file extension
    _, file_extension = os.path.splitext(file_path)
    
    # Convert the extension to lowercase to handle case insensitivity
    file_extension = file_extension.lower()
    
    # Determine the file type based on the extension
    if file_extension == ".pdf":
        return "pdf"
    elif file_extension == ".jpeg" or file_extension == ".jpg":
        return "jpeg"
    elif file_extension == ".png":
        return "png"
    else:
        return "unknown"

def main():
    # Start the stopwatch thread
    stopwatch_thread = threading.Thread(target=stopwatch)
    stopwatch_thread.start()
    
    invoice_no = 3

    file_path = f"C:/Users/harikrs/Documents/fresh-start-genai/Invoices/Invoice{invoice_no}.pdf"
    output_text = f"C:/Users/harikrs/Documents/fresh-start-genai/Extraction 3/Outputs/{invoice_no}.txt"

    with open(output_text, 'w') as file:
        file.write(f"\n{invoice_no}\n")

    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return
    
    file_type = determine_file_type(file_path)

    if file_type == "pdf":
        extracted_data = process_pdf(file_path)
    elif file_type == "jpeg" or file_type == "png":
        extracted_data = process_image(file_path)
    print_data(extracted_data,output_text)

    # Signal the stopwatch to stop
    stop_event.set()
    stopwatch_thread.join()

if __name__ == "__main__":
    stop_event = threading.Event()  # Event to signal the stopwatch to stop    
    main()