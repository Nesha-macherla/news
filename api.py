# api.py
import logging
import os
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Global variables to hold lazily loaded resources
scraper = None
analyzer = None
visualizer = None
tts_generator = None

def initialize_resources():
    """Lazily initialize resources only when needed"""
    global scraper, analyzer, visualizer, tts_generator
    
    if scraper is None:
        logger.info("Initializing resources...")
        
        # Set a writable directory for NLTK downloads
        NLTK_DIR = "/app/nltk_data"
        os.makedirs(NLTK_DIR, exist_ok=True)
        
        # Import NLTK and download resources
        import nltk
        nltk.data.path.append(NLTK_DIR)
        
        # Only download if not already present
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            nltk.download('vader_lexicon', download_dir=NLTK_DIR, quiet=True)
            
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', download_dir=NLTK_DIR, quiet=True)
            
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', download_dir=NLTK_DIR, quiet=True)
        
        # Import classes only when needed
        from classes import NewsArticle, NewsScraper, SentimentAnalyzer, ArticleQueryEngine, DataVisualizer, TextToSpeechGenerator
        
        # Initialize objects
        scraper = NewsScraper()
        analyzer = SentimentAnalyzer()
        visualizer = DataVisualizer()
        tts_generator = TextToSpeechGenerator()
        
        logger.info("Resources initialized successfully")

@app.route('/api/search', methods=['POST'])
def search_company():
    """Endpoint to search for news about a company"""
    # Initialize resources if not already done
    initialize_resources()
    
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
    # Initialize resources if not already done
    initialize_resources()
    
    data = request.json
    visualization_type = data.get('type', '')
    visualization_data = data.get('data', {})
    
    try:
        # Import base64 here to avoid importing at module level
        import base64
        
        if visualization_type == 'pie_chart':
            chart = visualizer.create_sentiment_pie_chart(visualization_data)
            if chart:
                chart.seek(0)
                encoded = base64.b64encode(chart.getvalue()).decode('utf-8')
                return jsonify({'image': encoded})
        
        elif visualization_type == 'topic_chart':
            chart = visualizer.create_topic_sentiment_chart(visualization_data)
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
    # Initialize resources if not already done
    initialize_resources()
    
    # Import needed modules here instead of at the top
    from classes import NewsArticle
    import base64
    
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
    # Initialize resources if not already done
    initialize_resources()
    
    # Import needed modules here instead of at the top
    from classes import NewsArticle, ArticleQueryEngine
    
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

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint to verify API is running"""
    return jsonify({'status': 'healthy', 'message': 'API service is running'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
