import os
import time
import threading
import logging
import subprocess
from flask import Flask, request, jsonify
import requests
import socket

# Import custom classes
from classes import NewsScraper, SentimentAnalyzer, DataVisualizer, TextToSpeechGenerator, NewsArticle

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask App Setup
app = Flask(__name__)

# Initialize objects
scraper = NewsScraper()
analyzer = SentimentAnalyzer()
visualizer = DataVisualizer()
tts_generator = TextToSpeechGenerator()

# API Route for Searching News
@app.route('/api/search', methods=['POST'])
def search_news():
    data = request.json
    company_name = data.get('company_name', '')
    num_articles = data.get('num_articles', 10)

    if not company_name:
        return jsonify({'error': 'Company name is required'}), 400

    try:
        articles = scraper.search_google_news(company_name, num_articles)
        analyzed_articles = analyzer.analyze_articles(articles)
        analysis_result = analyzer.generate_comparative_analysis(analyzed_articles)
        summary = analyzer.create_summary(company_name, analysis_result, analyzed_articles)

        return jsonify({
            'articles': [article.to_dict() for article in analyzed_articles],
            'analysis_result': analysis_result,
            'summary': summary
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

# Health Check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

# Function to Find a Free Port
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 0))
        return s.getsockname()[1]

# Function to Start Streamlit
def start_streamlit():
    streamlit_port = find_free_port()
    os.environ["STREAMLIT_SERVER_PORT"] = str(streamlit_port)  # Set port as environment variable
    logger.info(f"Starting Streamlit on port {streamlit_port}...")
    subprocess.run(["streamlit", "run", "app_frontend.py", "--server.port", str(streamlit_port), "--server.address", "0.0.0.0"])

if __name__ == '__main__':
    # Start Streamlit in a separate thread
    threading.Thread(target=start_streamlit, daemon=True).start()

    # Start Flask API
    app.run(host="0.0.0.0", port=5000, debug=True)
