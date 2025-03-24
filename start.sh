#!/bin/bash

# Print some information
echo "Starting Company Sentiment Analyzer application..."

# Set environment variables for NLTK, Matplotlib, and FontConfig
export NLTK_DATA=/tmp/nltk_data
mkdir -p $NLTK_DATA

export MPLCONFIGDIR=/tmp/matplotlib
mkdir -p $MPLCONFIGDIR

export FONTCONFIG_PATH=/etc/fonts
mkdir -p /tmp/.cache/fontconfig
chmod -R 777 /tmp/.cache/fontconfig

# Start Flask API with Gunicorn (better performance)
echo "Starting Flask API server..."
gunicorn -w 2 -b 0.0.0.0:5000 api:app &
API_PID=$!

# Give Flask a moment to start
echo "Waiting for API to initialize..."
sleep 5

# Start Streamlit frontend
echo "Starting Streamlit frontend..."
exec streamlit run app_frontend.py --server.port 8501 --server.address 0.0.0.0

# If Streamlit exits, clean up Flask process
echo "Streamlit exited, cleaning up..."
kill $API_PID
