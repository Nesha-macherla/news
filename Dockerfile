# Use Python base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Set environment variables for NLTK and matplotlib
ENV NLTK_DATA=/app/nltk_data
ENV MPLCONFIGDIR=/tmp/matplotlib
ENV FONTCONFIG_PATH=/etc/fonts

# Create necessary directories with proper permissions
RUN mkdir -p /app/nltk_data && \
    mkdir -p /tmp/matplotlib && \
    mkdir -p /tmp/.cache/fontconfig && \
    chmod -R 777 /tmp/.cache/fontconfig

# Copy requirements first to leverage Docker caching
COPY requirements.txt /app/

# Install dependencies and download NLTK data during build
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m nltk.downloader -d /app/nltk_data vader_lexicon punkt stopwords

# Copy application code
COPY . /app/

# Apply a patch to remove NLTK downloads from runtime code
RUN sed -i 's/nltk.download(/# nltk.download(/g' api.py

# Add a proper health check endpoint to Flask app (if not already present)
RUN grep -q "@app.route('/health'" api.py || \
    echo 'import os' > /tmp/health_endpoint.py && \
    echo '@app.route("/health")' >> /tmp/health_endpoint.py && \
    echo 'def health_check():' >> /tmp/health_endpoint.py && \
    echo '    return jsonify({"status": "healthy"})' >> /tmp/health_endpoint.py && \
    sed -i "/app = Flask/r /tmp/health_endpoint.py" api.py

# Create startup script
RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'python api.py &' >> /app/start.sh && \
    echo 'API_PID=$!' >> /app/start.sh && \
    echo 'echo "Waiting for API to start..."' >> /app/start.sh && \
    echo 'sleep 5' >> /app/start.sh && \
    echo 'curl -s http://localhost:5000/health || { echo "API failed to start"; exit 1; }' >> /app/start.sh && \
    echo 'echo "API started successfully, starting Streamlit..."' >> /app/start.sh && \
    echo 'streamlit run app_frontend.py --server.port 8501 --server.address 0.0.0.0 --server.headless true' >> /app/start.sh && \
    chmod +x /app/start.sh

# Expose Flask and Streamlit ports
EXPOSE 5000 8501

# Change the CMD to use the startup script
CMD ["/app/start.sh"]
