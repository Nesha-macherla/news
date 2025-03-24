#!/bin/bash

# Print some information
echo "Starting Company Sentiment Analyzer application..."

# Set NLTK data path to a writable location
export NLTK_DATA=/tmp/nltk_data
mkdir -p $NLTK_DATA

# Set Matplotlib config directory to a writable location
export MPLCONFIGDIR=/tmp/matplotlib
mkdir -p $MPLCONFIGDIR

# Start Flask API in the background
echo "Starting Flask API server..."
python api.py &
API_PID=$!

# Give Flask a moment to start
echo "Waiting for API to initialize..."
sleep 3

# Start Streamlit
echo "Starting Streamlit frontend..."
streamlit run app_frontend.py

# If Streamlit exits, kill the Flask process
echo "Streamlit exited, cleaning up..."
kill $API_PID
