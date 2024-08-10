import os
from dotenv import load_dotenv
from pymongo import MongoClient

class Invoice_Status_DB:

    def __init__(self):
        load_dotenv()
        self.CONNECTION_STRING = os.environ["AZURE_MONGODB_CONNECTION_STRING"]
        self.client = MongoClient(self.CONNECTION_STRING)
        self.DB_NAME = os.environ["AZURE_MONGODB_NAME"]
        self.COLLECTION_NAME = os.environ["MONGODB_COLLECTION_NAME"]
        self.db = self.client[self.DB_NAME]
        self.collection = self.db[self.COLLECTION_NAME]
    
    def create_document(self, blob_name, status, container_name):
        document = {
            "blob_name": blob_name,
            "status": status,
            "container_name": container_name
        }
        self.collection.insert_one(document)
        print("Document inserted")


    def read_document(self, blob_name):
        document = self.collection.find_one({"blob_name": blob_name})
        if document:
            print("Document found:", document)
        else:
            print("Document not found")

    
    def update_document(self, blob_name, new_status):
        result = self.collection.update_one(
            {"blob_name": blob_name},
            {"$set": {"status": new_status}}
        )
        if result.modified_count > 0:
            print("Document updated")
        else:
            print("No document found to update")

    
    def delete_document(self, blob_name):
        result = self.collection.delete_one({"blob_name": blob_name})
        if result.deleted_count > 0:
            print("Document deleted")
        else:
            print("No document found to delete")

