# Use Python base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy all files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask (5000) and Streamlit (8501) ports
EXPOSE 5000 8501

# Start Flask API & Streamlit frontend (with delay)
CMD gunicorn --bind 0.0.0.0:5000 api:app & sleep 5 && streamlit run app_frontend.py --server.port 8501 --server.address 0.0.0.0
