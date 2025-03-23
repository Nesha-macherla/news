FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt'); nltk.download('stopwords')"

COPY . .

# Expose ports for Flask and Streamlit
EXPOSE 5000
EXPOSE 8501

# Command to run both servers
CMD ["python", "app.py"]