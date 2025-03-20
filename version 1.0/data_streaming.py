from pyspark.sql import SparkSession
import yfinance as yf
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
from config import STOCKS, INTERVAL, MONGO_URI, DATABASE_NAME, COLLECTION_NAME

# Initialize Spark Session
spark = SparkSession.builder.appName("StockDataStreaming").getOrCreate()

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Calculate 1-week start date
END_DATE = datetime.now().strftime('%Y-%m-%d')
START_DATE = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

# Function to fetch and store 1-week historical data
def fetch_historical_data():
    for ticker in STOCKS:
        data = yf.download(ticker, start=START_DATE, end=END_DATE, interval=INTERVAL)
        if not data.empty:
            records = []
            for index, row in data.iterrows():
                records.append({
                    "Ticker": ticker,
                    "Timestamp": index.strftime('%Y-%m-%d %H:%M:%S'),
                    "Open": float(row["Open"]),
                    "High": float(row["High"]),
                    "Low": float(row["Low"]),
                    "Close": float(row["Close"]),
                    "Volume": float(row["Volume"])
                })
            collection.insert_many(records)
            print(f"Inserted historical data for {ticker}")

# Function to continuously fetch real-time data
def fetch_real_time_data():
    while True:
        for ticker in STOCKS:
            data = yf.Ticker(ticker).history(period="1d", interval=INTERVAL)
            if not data.empty:
                latest = data.iloc[-1]
                record = {
                    "Ticker": ticker,
                    "Timestamp": latest.name.strftime('%Y-%m-%d %H:%M:%S'),
                    "Open": float(latest["Open"]),
                    "High": float(latest["High"]),
                    "Low": float(latest["Low"]),
                    "Close": float(latest["Close"]),
                    "Volume": float(latest["Volume"])
                }
                collection.insert_one(record)
                print(f"Inserted real-time {ticker} data at {record['Timestamp']}")
        time.sleep(60)  # Fetch every minute

if __name__ == "__main__":
    fetch_historical_data()  # Fetch 1-week historical data once
    fetch_real_time_data()  # Start real-time streaming
