from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
import yfinance as yf
import time
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from config import STOCKS, INTERVAL, MONGO_URI, DATABASE_NAME, COLLECTION_NAME

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("StockStreaming") \
    .master("local[2]") \
    .getOrCreate()

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

END_DATE = datetime.now().strftime('%Y-%m-%d')
START_DATE = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

# Define schema for the DataFrame
stock_schema = StructType([
    StructField("Ticker", StringType(), False),
    StructField("Timestamp", StringType(), False),
    StructField("Open", DoubleType(), False),
    StructField("High", DoubleType(), False),
    StructField("Low", DoubleType(), False),
    StructField("Close", DoubleType(), False),
    StructField("Volume", DoubleType(), False)
])


def convert_value_to_float(value):
    """Safely convert a value to float, handling both Series and regular values."""
    if isinstance(value, pd.Series):
        return float(value.iloc[0])
    return float(value)


def fetch_historical_data():
    """Fetch historical stock data and store in MongoDB"""
    for ticker in STOCKS:
        print(f"Downloading data for {ticker}...")
        try:
            data = yf.download(ticker, start=START_DATE, end=END_DATE, interval=INTERVAL)

            if not data.empty:
                # Convert pandas DataFrame to list of Python dictionaries with proper type conversion
                records = []
                for index, row in data.iterrows():
                    record = {
                        "Ticker": ticker,
                        "Timestamp": index.strftime('%Y-%m-%d %H:%M:%S'),
                        "Open": convert_value_to_float(row["Open"]),
                        "High": convert_value_to_float(row["High"]),
                        "Low": convert_value_to_float(row["Low"]),
                        "Close": convert_value_to_float(row["Close"]),
                        "Volume": convert_value_to_float(row["Volume"])
                    }
                    records.append(record)

                if records:
                    # Method 1: Using Spark and PyMongo together
                    # Create DataFrame with explicit schema
                    df = spark.createDataFrame(records, schema=stock_schema)

                    # Convert back to Python objects and insert directly with PyMongo
                    mongo_records = [row.asDict() for row in df.collect()]
                    if mongo_records:
                        collection.insert_many(mongo_records)
                        print(f"Inserted {len(mongo_records)} historical records for {ticker}")
                else:
                    print(f"No records to insert for {ticker}")

        except Exception as e:
            print(f"Error processing historical data for {ticker}: {str(e)}")


def fetch_real_time_data():
    """Continuously fetch real-time stock data and store in MongoDB"""
    try:
        while True:
            for ticker in STOCKS:
                try:
                    data = yf.Ticker(ticker).history(period="1d", interval=INTERVAL)
                    if not data.empty:
                        latest = data.iloc[-1]
                        # Create a record with explicit type conversion
                        record = {
                            "Ticker": ticker,
                            "Timestamp": latest.name.strftime('%Y-%m-%d %H:%M:%S'),
                            "Open": convert_value_to_float(latest["Open"]),
                            "High": convert_value_to_float(latest["High"]),
                            "Low": convert_value_to_float(latest["Low"]),
                            "Close": convert_value_to_float(latest["Close"]),
                            "Volume": convert_value_to_float(latest["Volume"])
                        }

                        # Insert directly to MongoDB using PyMongo
                        collection.insert_one(record)
                        print(f"Inserted real-time {ticker} data at {datetime.now()}")
                except Exception as e:
                    print(f"Error processing real-time data for {ticker}: {str(e)}")

            print(f"Sleeping for 60 seconds before next update...")
            time.sleep(60)
    except KeyboardInterrupt:
        print("Real-time data collection stopped by user")


if __name__ == "__main__":
    print("Starting stock data processing pipeline...")
    fetch_historical_data()
    fetch_real_time_data()