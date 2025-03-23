# utils.py
import re
import nltk
import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import logging
import requests
from bs4 import BeautifulSoup
import time
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure NLTK data is downloaded
def download_nltk_data():
    try:
        nltk.download('vader_lexicon', quiet=True)
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        logger.info("NLTK data downloaded successfully")
    except Exception as e:
        logger.error(f"Error downloading NLTK resources: {e}")

# Text cleaning utilities
def clean_text(text):
    """Clean and normalize text for analysis"""
    if not text:
        return ""
    
    # Remove special characters and digits
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    filtered_text = [word for word in word_tokens if word not in stop_words]
    
    return ' '.join(filtered_text)

# Web scraping utilities
def fetch_url_content(url, timeout=10, max_retries=3):
    """Fetch content from a URL with retries"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to fetch URL: {url}, Status: {response.status_code}")
                time.sleep(1)
        except Exception as e:
            logger.warning(f"Error fetching URL: {url}, Attempt {attempt+1}/{max_retries}, Error: {str(e)}")
            time.sleep(1)
    
    return None

def extract_article_content(html_content):
    """Extract main content from HTML using BeautifulSoup"""
    if not html_content:
        return None
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove scripts, styles, and other irrelevant tags
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
        
        # Extract paragraphs
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text() for p in paragraphs])
        
        # Clean the content
        content = re.sub(r'\s+', ' ', content).strip()
        return content
    except Exception as e:
        logger.error(f"Error extracting content from HTML: {e}")
        return None

# Sentiment analysis utilities
def analyze_sentiment(text):
    """Calculate sentiment scores for text"""
    if not text:
        return {'pos': 0, 'neg': 0, 'neu': 0, 'compound': 0}
    
    sia = SentimentIntensityAnalyzer()
    sentiment = sia.polarity_scores(text)
    return sentiment

def get_sentiment_label(score):
    """Convert sentiment score to label"""
    if score >= 0.05:
        return "positive"
    elif score <= -0.05:
        return "negative"
    else:
        return "neutral"

# Topic extraction utilities
def extract_topics(text, n=5):
    """Extract key topics/keywords from text"""
    if not text:
        return []
    
    # Clean and tokenize
    text = clean_text(text)
    words = word_tokenize(text)
    
    # Remove stopwords and short words
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words and len(word) > 3]
    
    # Count frequency
    freq = {}
    for word in words:
        if word in freq:
            freq[word] += 1
        else:
            freq[word] = 1
    
    # Sort by frequency
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    
    # Return top n topics
    return [word for word, count in sorted_freq[:n]]

# Visualization utilities
def create_pie_chart(data):
    """Create a pie chart visualization"""
    try:
        plt.figure(figsize=(8, 6))
        labels = data.keys()
        values = data.values()
        colors = ['#4CAF50', '#FFC107', '#F44336']
        
        plt.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.title('Sentiment Distribution')
        
        # Save figure to BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        return buf
    except Exception as e:
        logger.error(f"Error creating pie chart: {e}")
        return None

def create_bar_chart(data, title="Topic Sentiment Analysis"):
    """Create a bar chart for topic sentiment"""
    try:
        # Prepare data for bar chart
        topics = []
        scores = []
        for topic, info in data.items():
            topics.append(topic)
            scores.append(info['avg_score'])
        
        # Sort by score
        sorted_data = sorted(zip(topics, scores), key=lambda x: x[1])
        topics_sorted, scores_sorted = zip(*sorted_data)
        
        # Limit to top 10 topics
        if len(topics_sorted) > 10:
            topics_sorted = topics_sorted[-10:]
            scores_sorted = scores_sorted[-10:]
        
        # Create colors based on scores
        colors = ['#4CAF50' if s > 0 else '#F44336' for s in scores_sorted]
        
        # Create bar chart
        plt.figure(figsize=(10, 6))
        plt.barh(topics_sorted, scores_sorted, color=colors)
        plt.xlabel('Sentiment Score')
        plt.ylabel('Topics')
        plt.title(title)
        plt.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        plt.tight_layout()
        
        # Save figure to BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        return buf
    except Exception as e:
        logger.error(f"Error creating bar chart: {e}")
        return None

# Data handling utilities
def safe_dict_to_json(obj):
    """Safely convert Python objects to JSON serializable format"""
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, BytesIO):
        return base64.b64encode(obj.getvalue()).decode('utf-8')
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [safe_dict_to_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: safe_dict_to_json(v) for k, v in obj.items()}
    else:
        return str(obj)