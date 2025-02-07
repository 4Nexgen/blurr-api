from pymongo.mongo_client import MongoClient

import os
from dotenv import load_dotenv
load_dotenv()

class MongoDBDatabase:
    def __init__(self):
        self.MONGODB_URI = os.getenv("MONGODB_URI")
        self.MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")

    def load_db(self):
        try:
            client = MongoClient(self.MONGODB_URI)
            
            admindb = client.admin
            admindb.command('ping')
            
            print("The MongoDB connection has been successfully established.")
        except Exception as e:
            print(e)
            
    def get_db(self):
        try:
            client = MongoClient(self.MONGODB_URI)
            db = client[self.MONGODB_DATABASE]
            
            return db
        except Exception as e:
            print(e)