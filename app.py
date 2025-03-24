import os
import threading
import time
import subprocess
import signal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to start the Flask API server
def start_api_server():
    try:
        logger.info("Starting Flask API server...")
        from api import app
        
        # Add a health check endpoint
        @app.route('/health')
        def health():
            return {"status": "healthy"}
            
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"Error in Flask API: {e}")
        raise

# Function to start the Streamlit frontend
def start_streamlit():
    try:
        logger.info("Starting Streamlit frontend...")
        subprocess.run([
            "streamlit", "run", "app_frontend.py", 
            "--server.port", "8501", 
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--browser.serverAddress", "0.0.0.0",
            "--browser.gatherUsageStats", "false"
        ])
    except Exception as e:
        logger.error(f"Error in Streamlit: {e}")
        raise

if __name__ == "__main__":
    # Start Flask API in a separate thread
    api_thread = threading.Thread(target=start_api_server)
    api_thread.daemon = True  # Keep as daemon to ensure it exits with main program
    api_thread.start()
    
    # Check if Flask API is ready before continuing
    logger.info("Waiting for API to be ready...")
    from urllib.request import urlopen
    from urllib.error import URLError
    
    api_ready = False
    max_retries = 10
    retry_count = 0
    
    while not api_ready and retry_count < max_retries:
        try:
            urlopen("http://localhost:5000/health")
            api_ready = True
            logger.info("API is ready!")
        except URLError:
            retry_count += 1
            logger.info(f"API not ready yet. Retry {retry_count}/{max_retries}")
            time.sleep(2)
    
    if not api_ready:
        logger.warning("Could not confirm API is ready, but continuing anyway...")
    
    # Start Streamlit in the main thread
    start_streamlit()
