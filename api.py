# api.py
# Standard Library Imports
import logging
import os
import re
import time
import urllib.parse
from io import BytesIO

# Third-Party Imports
import pandas as pd
import requests
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from bs4 import BeautifulSoup

os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
import matplotlib.pyplot as plt
import seaborn as sns

# Flask Imports
from flask import Flask, request, jsonify


# Import existing classes
from classes import NewsArticle, NewsScraper, SentimentAnalyzer, ArticleQueryEngine, DataVisualizer, TextToSpeechGenerator

# Download NLTK data

import tempfile

# Set NLTK data path to a writable location
nltk_data_dir = os.environ.get('NLTK_DATA', '/tmp/nltk_data')
os.makedirs(nltk_data_dir, exist_ok=True)

# Update download calls
try:
    nltk.download('vader_lexicon', download_dir=nltk_data_dir, quiet=True)
    nltk.download('punkt', download_dir=nltk_data_dir, quiet=True)
    nltk.download('stopwords', download_dir=nltk_data_dir, quiet=True)
except Exception as e:
    print(f"Error downloading NLTK resources: {e}")


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize objects
scraper = NewsScraper()
analyzer = SentimentAnalyzer()
visualizer = DataVisualizer()
tts_generator = TextToSpeechGenerator()

@app.route('/api/search', methods=['POST'])
def search_company():
    """Endpoint to search for news about a company"""
    data = request.json
    company_name = data.get('company_name', '')
    num_articles = data.get('num_articles', 10)
    
    if not company_name:
        return jsonify({'error': 'Company name is required'}), 400
    
    try:
        # Get news articles
        articles = scraper.search_google_news(company_name, num_articles)
        
        # Analyze sentiment
        if articles:
            analyzed_articles = analyzer.analyze_articles(articles)
            
            # Generate comparative analysis
            analysis_result = analyzer.generate_comparative_analysis(analyzed_articles)
            
            # Create summary
            summary = analyzer.create_summary(company_name, analysis_result, analyzed_articles)
            
            # Convert articles to dictionaries
            article_dicts = [article.to_dict() for article in analyzed_articles]
            
            return jsonify({
                'articles': article_dicts,
                'analysis_result': analysis_result,
                'summary': summary
            })
        else:
            return jsonify({'error': 'No articles found'}), 404
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_visualization', methods=['POST'])
def generate_visualization():
    """Endpoint to generate visualizations"""
    data = request.json
    visualization_type = data.get('type', '')
    visualization_data = data.get('data', {})
    
    try:
        if visualization_type == 'pie_chart':
            chart = visualizer.create_sentiment_pie_chart(visualization_data)
            # Convert BytesIO to base64 for sending in JSON
            import base64
            if chart:
                chart.seek(0)
                encoded = base64.b64encode(chart.getvalue()).decode('utf-8')
                return jsonify({'image': encoded})
        
        elif visualization_type == 'topic_chart':
            chart = visualizer.create_topic_sentiment_chart(visualization_data)
            # Convert BytesIO to base64 for sending in JSON
            import base64
            if chart:
                chart.seek(0)
                encoded = base64.b64encode(chart.getvalue()).decode('utf-8')
                return jsonify({'image': encoded})
        
        return jsonify({'error': 'Visualization could not be generated'}), 400
    except Exception as e:
        logger.error(f"Error generating visualization: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_audio', methods=['POST'])
def generate_audio():
    """Endpoint to generate audio summary"""
    data = request.json
    company_name = data.get('company_name', '')
    analysis_result = data.get('analysis_result', {})
    articles = data.get('articles', [])
    
    try:
        # Convert articles from dictionaries back to objects
        article_objects = []
        for article_dict in articles:
            article = NewsArticle(
                article_dict['title'],
                article_dict['summary'],
                article_dict['url'],
                article_dict['source'],
                article_dict.get('date')
            )
            article.sentiment_label = article_dict['sentiment_label']
            article.sentiment_score = article_dict['sentiment_score']
            article.topics = article_dict['topics']
            article_objects.append(article)
        
        # Generate Hindi summary
        hindi_summary = analyzer.create_hindi_summary(company_name, analysis_result, article_objects)
        audio_buf = tts_generator.generate_audio(hindi_summary)
        
        # Convert BytesIO to base64 for sending in JSON
        import base64
        if audio_buf:
            audio_buf.seek(0)
            encoded = base64.b64encode(audio_buf.getvalue()).decode('utf-8')
            return jsonify({'audio': encoded, 'summary': hindi_summary})
        else:
            return jsonify({'error': 'Audio could not be generated'}), 400
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter_articles', methods=['POST'])
def filter_articles():
    """Endpoint to filter articles"""
    data = request.json
    articles = data.get('articles', [])
    query_text = data.get('query_text', '')
    sentiment_filter = data.get('sentiment_filter', 'all')
    topic_filter = data.get('topic_filter', 'all')
    
    try:
        # Convert articles from dictionaries back to objects
        article_objects = []
        for article_dict in articles:
            article = NewsArticle(
                article_dict['title'],
                article_dict['summary'],
                article_dict['url'],
                article_dict['source'],
                article_dict.get('date')
            )
            article.sentiment_label = article_dict['sentiment_label']
            article.sentiment_score = article_dict['sentiment_score']
            article.topics = article_dict['topics']
            article_objects.append(article)
        
        # Initialize query engine
        query_engine = ArticleQueryEngine()
        
        # Apply filters
        filtered_articles = article_objects
        
        if query_text:
            filtered_articles = query_engine.query_articles(filtered_articles, query_text)
        
        if sentiment_filter != "all":
            filtered_articles = query_engine.filter_by_sentiment(filtered_articles, sentiment_filter)
        
        if topic_filter != "all":
            filtered_articles = query_engine.filter_by_topic(filtered_articles, topic_filter)
        
        # Convert filtered articles back to dictionaries
        filtered_article_dicts = [article.to_dict() for article in filtered_articles]
        
        return jsonify({'filtered_articles': filtered_article_dicts})
    except Exception as e:
        logger.error(f"Error filtering articles: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
