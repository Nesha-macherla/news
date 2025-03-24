FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Add this to your Dockerfile
ENV NLTK_DATA=/tmp/nltk_data
RUN mkdir -p /tmp/nltk_data && chmod 777 /tmp/nltk_data
# Download NLTK data
RUN python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt'); nltk.download('stopwords')"

# Expose ports for Flask and Streamlit
EXPOSE 5000 8501

# Create a script to run both services
RUN echo '#!/bin/bash\npython api.py &\nstreamlit run app_frontend.py' > start.sh
RUN chmod +x start.sh

CMD ["./start.sh"]
