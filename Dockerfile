FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt'); nltk.download('stopwords')"

# Copy all application files
COPY . .

# Expose ports for Flask and Streamlit
EXPOSE 5000
EXPOSE 8501

# Create a startup script
RUN echo '#!/bin/bash \n\
python app.py' > /app/start.sh && \
chmod +x /app/start.sh

# Command to run our startup script
CMD ["/app/start.sh"]
CMD gunicorn --bind 0.0.0.0:5000 api:app & streamlit run app_frontend.py --server.port 8501 --server.address 0.0.0.0

