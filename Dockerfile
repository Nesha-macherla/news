# Use Python base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Set environment variables for NLTK, Matplotlib, and FontConfig
ENV NLTK_DATA=/app/nltk_data
ENV MPLCONFIGDIR=/tmp/matplotlib
ENV FONTCONFIG_PATH=/etc/fonts

# Create necessary directories with proper permissions
RUN mkdir -p /app/nltk_data /tmp/matplotlib /tmp/.cache/fontconfig && \
    chmod -R 777 /tmp/.cache/fontconfig /tmp/matplotlib

# Copy requirements first to leverage Docker caching
COPY requirements.txt /app/

# Install dependencies and download NLTK data
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m nltk.downloader -d /app/nltk_data vader_lexicon punkt stopwords

# Copy application code
COPY . /app/

# Create a startup script
RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'echo "Starting API using Gunicorn..."' >> /app/start.sh && \
    echo 'gunicorn --workers=2 --timeout 600 --bind 0.0.0.0:5000 app:app &' >> /app/start.sh && \
    echo 'API_PID=$!' >> /app/start.sh && \
    echo 'echo "Waiting for API to start..."' >> /app/start.sh && \
    echo 'retries=0' >> /app/start.sh && \
    echo 'while ! curl -s http://localhost:5000/api/health > /dev/null; do' >> /app/start.sh && \
    echo '  retries=$((retries+1))' >> /app/start.sh && \
    echo '  if [ $retries -gt 10 ]; then' >> /app/start.sh && \
    echo '    echo "API failed to start"; exit 1;' >> /app/start.sh && \
    echo '  fi' >> /app/start.sh && \
    echo '  sleep 2' >> /app/start.sh && \
    echo 'done' >> /app/start.sh && \
    echo 'echo "API started successfully, starting Streamlit..."' >> /app/start.sh && \
    echo 'exec streamlit run app_frontend.py --server.port 8501 --server.address 0.0.0.0 --server.headless true' >> /app/start.sh && \
    chmod +x /app/start.sh

# Expose Flask and Streamlit ports
EXPOSE 5000 8501

# Change CMD to use the startup script
CMD ["/app/start.sh"]
