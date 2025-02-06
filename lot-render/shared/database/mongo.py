import os
import pymongo


class MongoClient:
    def __init__(self, database_name: str):
        self.client = pymongo.MongoClient(os.getenv("MONGO_CONNECTION_STRING"))
        self.database = self.client[database_name]

    def disconnect(self):
        self.client.close()

    def get_collection(self, collection_name: str):
        return self.database[collection_name]

    def insert_one(self, collection_name: str, data: dict):
        collection = self.get_collection(collection_name)
        collection.insert_one(data)
