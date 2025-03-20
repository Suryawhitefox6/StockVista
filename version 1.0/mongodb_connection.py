from pymongo import MongoClient
from config import MONGO_URI, DATABASE_NAME

def get_mongo_client():
    client = MongoClient(MONGO_URI)
    return client[DATABASE_NAME]

if __name__ == "__main__":
    db = get_mongo_client()
    print("Connected to MongoDB Atlas:", db.list_collection_names())