# Use Python base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy all files
COPY . /app

# Ensure NLTK data is stored in a writable directory
ENV NLTK_DATA=/app/nltk_data

# Install dependencies (including NLTK data)
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m nltk.downloader -d /app/nltk_data vader_lexicon punkt stopwords

# Expose Flask (5000) and Streamlit (8501) ports
EXPOSE 5000 8501

# Start Flask API & Streamlit frontend
CMD gunicorn --workers=2 --bind 0.0.0.0:5000 api:app & streamlit run app_frontend.py --server.port 8501 --server.address 0.0.0.0
