import os
import subprocess
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Start Flask API
def start_api():
    logger.info("Starting Flask API...")
    return subprocess.Popen(["gunicorn", "--workers=1", "--timeout", "600", "--bind", "0.0.0.0:5000", "api:app"])

# Start Streamlit
def start_streamlit():
    logger.info("Starting Streamlit frontend...")
    return subprocess.Popen([
        "streamlit", "run", "app_frontend.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])

if __name__ == "__main__":
    api_process = start_api()

    # Wait for Flask API to be ready
    time.sleep(5)  # Allow API some time to start

    streamlit_process = start_streamlit()

    # Wait for both processes
    try:
        api_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        logger.info("Shutting down processes...")
        api_process.terminate()
        streamlit_process.terminate()
