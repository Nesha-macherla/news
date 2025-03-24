import os
import time
import subprocess
import logging
import requests
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Middleware to log request time
@app.before_request
def start_timer():
    request.start_time = time.time()

@app.after_request
def log_response(response):
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        app.logger.info(f"Processed {request.path} in {duration:.2f}s")
    return response

# Global variables for lazy initialization
scraper = None
analyzer = None
visualizer = None
tts_generator = None

def initialize_resources():
    """Lazily initialize resources only when needed"""
    global scraper, analyzer, visualizer, tts_generator
    
    if scraper is None:
        logger.info("Initializing resources...")

        # Set a writable directory for NLTK
        os.makedirs("/app/nltk_data", exist_ok=True)

        # Import resources only when needed
        from classes import NewsScraper, SentimentAnalyzer, DataVisualizer, TextToSpeechGenerator

        # Initialize objects
        scraper = NewsScraper()
        analyzer = SentimentAnalyzer()
        visualizer = DataVisualizer()
        tts_generator = TextToSpeechGenerator()

        logger.info("Resources initialized successfully")

@app.route('/api/search', methods=['POST'])
def search_company():
    """Search for news & analyze sentiment"""
    initialize_resources()
    
    data = request.json
    company_name = data.get('company_name', '').strip()
    num_articles = data.get('num_articles', 10)

    if not company_name:
        return jsonify({'error': 'Company name is required'}), 400

    try:
        articles = scraper.search_google_news(company_name, num_articles)
        if articles:
            analyzed_articles = analyzer.analyze_articles(articles)
            analysis_result = analyzer.generate_comparative_analysis(analyzed_articles)
            summary = analyzer.create_summary(company_name, analysis_result, analyzed_articles)
            
            return jsonify({
                'articles': [article.to_dict() for article in analyzed_articles],
                'analysis_result': analysis_result,
                'summary': summary
            })
        else:
            return jsonify({'error': 'No articles found'}), 404
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check for API"""
    return jsonify({'status': 'healthy', 'message': 'API is running'}), 200

# Function to check if API is ready
def wait_for_api(url, retries=10, delay=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                logger.info("Flask API is up and running!")
                return True
        except requests.ConnectionError:
            logger.info(f"API not ready yet... retrying ({attempt+1}/{retries})")
            time.sleep(delay)
    logger.error("API failed to start within the expected time!")
    return False

# Function to start Streamlit
def start_streamlit():
    logger.info("Starting Streamlit frontend...")
    return subprocess.Popen([
        "streamlit", "run", "app_frontend.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ])

if __name__ == '__main__':
    from waitress import serve
    logger.info("Starting API using Waitress...")
    
    # Start API in a separate process
    api_process = subprocess.Popen([
        "gunicorn", "--workers=2", "--timeout=300", "--bind", "0.0.0.0:5000", "app:app"
    ])

    # Wait for API to be ready before launching Streamlit
    if wait_for_api("http://127.0.0.1:5000/api/health"):
        streamlit_process = start_streamlit()
    else:
        logger.error("Exiting: API did not start correctly!")
        api_process.terminate()
        exit(1)

    # Handle process shutdown gracefully
    try:
        api_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        logger.info("Shutting down processes gracefully...")
        api_process.terminate()
        streamlit_process.terminate()
