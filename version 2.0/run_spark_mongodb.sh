#!/bin/bash
spark-submit --master local[2] \
  --packages org.mongodb.spark:mongo-spark-connector_2.12:10.2.0 \
  --conf spark.mongodb.input.uri=mongodb+srv://shobi:1234@cluster0.9f9ln.mongodb.net/stock_data?retryWrites=true&w=majority \
  --conf spark.mongodb.output.uri=mongodb+srv://shobi:1234@cluster0.9f9ln.mongodb.net/stock_data?retryWrites=true&w=majority \
  data_stream.py