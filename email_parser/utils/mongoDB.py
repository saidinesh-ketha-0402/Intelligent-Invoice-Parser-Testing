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
    
    
    def get_documents_by_status(self, status):
        doc_ids = []
        documents = self.collection.find({"status": status})
        for document in documents:
            doc_ids.append(document["_id"])
        return doc_ids
    
    def get_document_by_id(self, id):
        document = self.collection.find_one({"_id": id})
        return document

    
    def update_document(self, id, new_status):
        result = self.collection.update_one(
            {"_id": id},
            {"$set": {"status": new_status}}
        )
        if result.modified_count > 0:
            print("Document updated")
        else:
            print("No document found to update")

    
    def delete_document(self, id):
        result = self.collection.delete_one({"_id": id})
        if result.deleted_count > 0:
            print("Document deleted")
        else:
            print("No document found to delete")

