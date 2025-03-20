from pyspark.sql import SparkSession
from pymongo import MongoClient
from config import MONGO_URI, DATABASE_NAME

def get_mongo_client():
    client = MongoClient(MONGO_URI)
    return client[DATABASE_NAME]

def get_spark_session():
    return SparkSession.builder.appName("StockAnalytics")\
        .config("spark.mongodb.input.uri", MONGO_URI)\
        .config("spark.mongodb.output.uri", MONGO_URI)\
        .getOrCreate()

if __name__ == "__main__":
    db = get_mongo_client()
    spark = get_spark_session()
    print("Connected to MongoDB Atlas:", db.list_collection_names())
    print("Spark Session Initialized")
