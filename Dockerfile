FROM python:3.9-slim

WORKDIR /app

# Set up writable directories
ENV NLTK_DATA=/tmp/nltk_data
ENV MPLCONFIGDIR=/tmp/matplotlib
RUN mkdir -p /tmp/matplotlib && chmod 777 /tmp/matplotlib


# Install dependencies
COPY requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

# Download necessary NLTK data
RUN python -c "import nltk; nltk.download('vader_lexicon', download_dir='/tmp/nltk_data'); nltk.download('punkt', download_dir='/tmp/nltk_data'); nltk.download('stopwords', download_dir='/tmp/nltk_data')"

# Copy all project files
COPY . .

# Start script for Flask + Streamlit
RUN echo '#!/bin/bash\n\
gunicorn -w 2 -b 0.0.0.0:5000 api:app & \n\
sleep 5  # Wait for API to start \n\
exec streamlit run app_frontend.py --server.port 8501 --server.address 0.0.0.0' > start.sh

RUN chmod +x start.sh
CMD ["./start.sh"]
