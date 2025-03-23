# Use Python base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy all files
COPY . /app

# Set environment variable for NLTK
ENV NLTK_DATA=/app/nltk_data

# Set a writable cache directory for Matplotlib
ENV MPLCONFIGDIR=/tmp/matplotlib

# Set a writable cache directory for Fontconfig
ENV FONTCONFIG_PATH=/etc/fonts
RUN mkdir -p /tmp/.cache/fontconfig && \
    chmod -R 777 /tmp/.cache/fontconfig


# Ensure directory exists
RUN mkdir -p /app/nltk_data

# Install dependencies and download NLTK data **during build** (not at runtime)
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m nltk.downloader -d /app/nltk_data vader_lexicon punkt stopwords

# Expose Flask (5000) and Streamlit (8501) ports
EXPOSE 5000 8501

# Start Flask API & Streamlit frontend
CMD gunicorn --workers=1 --timeout 600 --bind 0.0.0.0:5000 api:app & streamlit run app_frontend.py --server.port 8501 --server.address 0.0.0.0

