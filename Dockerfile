# Use Python base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Set environment variables
ENV NLTK_DATA=/app/nltk_data
ENV MPLCONFIGDIR=/tmp/matplotlib
ENV FONTCONFIG_PATH=/etc/fonts

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK resources
RUN python -m nltk.downloader -d /app/nltk_data vader_lexicon punkt stopwords

# Copy application files
COPY . /app/

# Expose Flask and Streamlit ports
EXPOSE 5000 8501

# Run API and Streamlit together
CMD ["python", "app.py"]
