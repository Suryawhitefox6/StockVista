# StockVista: Real-Time & Historical Stock Analytics

**StockVista** is a comprehensive Big Data Analytics project designed to provide real-time and historical stock market analysis. It leverages Dash for interactive visualizations, PySpark for data processing, and MongoDB for data storage.

## Features

- **Real-Time Data Streaming**: Continuously fetch and store real-time stock data.
- **Historical Data Analysis**: Analyze historical stock data for insights.
- **Interactive Dashboard**: Visualize stock data using Dash and Plotly.
- **Technical Indicators**: Calculate and display various technical indicators like SMA, EMA, MACD, and RSI.
- **Top Gainers & Losers**: Identify top-performing and underperforming stocks.
- **Volume Analysis**: Analyze trading volumes over time.
- **Moving Averages**: Visualize moving averages for trend analysis.
- **Overall Analysis**: Comprehensive view combining multiple analyses.

## Project Structure

### BDA (Version 1.0)

- **dashboard.py**: Dash application for visualizing stock data.
- **data_streaming.py**: PySpark script for fetching and storing stock data.
- **mongodb_connections.py**: Utility script for MongoDB connections.
- **config.py**: Configuration file for MongoDB URI, database name, collection name, and stock list.

### BDA 2.0 (Version 2.0)

- **dashboard.py**: Enhanced Dash application with additional features.
- **data_stream.py**: Improved PySpark script for data processing and storage.
- **mongodb_connections.py**: Utility script for MongoDB and Spark connections.
- **config.py**: Configuration file for MongoDB URI, database name, collection name, and stock list.
- **run_spark_mongodb.bat**: Batch script for running Spark job on Windows.
- **run_spark_mongodb.sh**: Shell script for running Spark job on Unix-based systems.

## Setup Instructions

### Prerequisites

- Python 3.x
- MongoDB Atlas account
- Apache Spark
- Yahoo Finance API access

### Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/StockVista.git
    cd StockVista
    ```

2. **Install required Python packages**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure MongoDB**:
    - Update `config.py` with your MongoDB URI, database name, and collection name.

4. **Run the Dash Application**:
    ```bash
    python dashboard.py
    ```

5. **Run the Data Streaming Script**:
    - For Windows:
        ```bash
        run_spark_mongodb.bat
        ```
    - For Unix-based systems:
        ```bash
        ./run_spark_mongodb.sh
        ```

## Usage

1. **Access the Dashboard**:
    - Open your web browser and navigate to `http://127.0.0.1:8050/`.
    - Select a stock from the dropdown menu.
    - Choose a date range using the date picker.
    - Explore different tabs for various analyses.

2. **Data Streaming**:
    - The data streaming script will continuously fetch real-time stock data and store it in MongoDB.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Dash for interactive web applications.
- PySpark for distributed data processing.
- MongoDB for scalable data storage.
- Yahoo Finance API for stock data.
