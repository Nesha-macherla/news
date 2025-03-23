import os
import threading
import time
import subprocess
import signal

# Function to start the Flask API server
def start_api_server():
    from api import app
    app.run(host='0.0.0.0', port=5000,debug=False, threaded=True)

# Function to start the Streamlit frontend
def start_streamlit():
    subprocess.run(["streamlit", "run", "app_frontend.py", "--server.port", "8501", "--server.address", "0.0.0.0","--server.headless", "true",
        "--browser.serverAddress", "0.0.0.0",
        "--browser.gatherUsageStats", "false"])

if __name__ == "__main__":
    # Start Flask API in a separate thread
    api_thread = threading.Thread(target=start_api_server)
    api_thread.daemon = True
    api_thread.start()
    
    # Give the API a moment to start
    time.sleep(5)
    
    # Start Streamlit in the main thread
    start_streamlit()
