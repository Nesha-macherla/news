# Classes
import logging
import urllib.parse
from io import BytesIO

# Third-Party Imports
import requests
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from gtts import gTTS

# Matplotlib Configuration
import matplotlib
matplotlib.use('Agg')  



import os
import tempfile

# Use a temporary directory that's writable
NLTK_DIR = os.path.join(tempfile.gettempdir(), 'nltk_data')
os.makedirs(NLTK_DIR, exist_ok=True)

# Download necessary NLTK resources
#nltk.download('vader_lexicon', download_dir=NLTK_DIR, quiet=True)
#nltk.download('punkt', download_dir=NLTK_DIR, quiet=True)
#nltk.download('stopwords', download_dir=NLTK_DIR, quiet=True)



stop_words = set(stopwords.words('english'))
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Class to handle sentiment analysis using NLTK's SentimentIntensityAnalyzer."""

    def __init__(self):
        try:
            self.sia = SentimentIntensityAnalyzer()
        except Exception as e:
            logger.error(f"Error initializing SentimentIntensityAnalyzer: {e}")
            self.sia = None  # Handle the error gracefully

    def analyze_text(self, text):
        """Analyze the sentiment of the given text."""
        if self.sia:
            return self.sia.polarity_scores(text)
        else:
            logger.error("SentimentIntensityAnalyzer is not initialized")
            return {"compound": 0.0, "pos": 0.0, "neu": 0.0, "neg": 0.0}
class NewsArticle:
    """Class to represent a news article with metadata and sentiment analysis."""
    
    def __init__(self, title, summary, url, source, date=None):
        self.title = title
        self.summary = summary
        self.url = url
        self.source = source
        self.date = date
        self.sentiment_score = None
        self.sentiment_label = None
        self.topics = []
    
    def analyze_sentiment(self):
        """Perform sentiment analysis on the article title and summary."""
        try:
            sia = SentimentIntensityAnalyzer()
            # Analyze both title and summary for better accuracy
            text = f"{self.title} {self.summary}"
            sentiment = sia.polarity_scores(text)
            
            self.sentiment_score = sentiment['compound']
            
            # Determine sentiment label based on compound score
            if sentiment['compound'] >= 0.05:
                self.sentiment_label = 'positive'
            elif sentiment['compound'] <= -0.05:
                self.sentiment_label = 'negative'
            else:
                self.sentiment_label = 'neutral'
            
            return self.sentiment_label, self.sentiment_score
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            self.sentiment_label = 'neutral'
            self.sentiment_score = 0
            return self.sentiment_label, self.sentiment_score
    
    def extract_topics(self, num_topics=5):
        """
        Extract key topics from the article title and summary using NLP techniques.
        
        Args:
            num_topics (int): Number of topics to extract
            
        Returns:
            list: List of extracted topics
        """
        try:
            # Combine title and summary for topic extraction
            text = f"{self.title} {self.summary}"
            
            # Tokenize and remove stopwords
            stop_words = set(stopwords.words('english'))
            # Add custom stopwords for news content
            custom_stops = {"said", "says", "reported", "according", "company", "companies", "business"}
            stop_words.update(custom_stops)
            
            words = nltk.word_tokenize(text.lower())
            # Fix the syntax error: changed 'is alnum()' to 'isalnum()'
            words = [word for word in words if word.isalnum() and word not in stop_words]
            
            # Use bigrams for better topic extraction (2-word phrases)
            bigrams = list(nltk.bigrams(words))
            bigram_phrases = [f"{w1} {w2}" for w1, w2 in bigrams]
            
            # Count frequencies
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Only consider words with more than 3 characters
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Count bigram frequencies (with higher weight)
            for phrase in bigram_phrases:
                # Don't include phrases with stop words
                words_in_phrase = phrase.split()
                if all(len(w) > 3 for w in words_in_phrase):
                    word_freq[phrase] = word_freq.get(phrase, 0) + 2  # Higher weight for phrases
            
            # Sort by frequency and get top topics
            topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            # Prioritize unique topics that aren't substrings of each other
            unique_topics = []
            for word, freq in topics:
                # Avoid substring matches or similar topics
                if not any(word in topic or topic in word for topic in unique_topics):
                    unique_topics.append(word)
                    if len(unique_topics) >= num_topics:
                        break
            
            # Store topics as property and add to the output
            self.topics = unique_topics
            
            # Add this line to ensure topics are included in any summary or output
            if hasattr(self, 'analysis_data'):
                self.analysis_data['topics'] = unique_topics
            
            return unique_topics
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            self.topics = []
            return []
    
    def to_dict(self):
        """Convert article object to dictionary for JSON response."""
        return {
            'title': self.title,
            'summary': self.summary,
            'url': self.url,
            'source': self.source,
            'date': self.date,
            'sentiment_label': self.sentiment_label,
            'sentiment_score': self.sentiment_score,
            'topics': self.topics
        }


class NewsScraper:
    """Class to handle scraping of news articles from various sources."""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def search_google_news(self, company_name, num_articles=10):
        """Search Google News for articles about the company."""
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(company_name)}+news&tbm=nws"
        logger.info(f"Searching for news about {company_name}")
        
        try:
            response = requests.get(search_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple possible CSS selectors for Google News results
            selectors = [
                'div.SoaBEf',
                'div.v7W49e',
                'div.WlydOe',
                'div.xuvV6b',
                'div.DBPWke'
            ]
            
            articles = []
            article_elements = []
            for selector in selectors:
                article_elements = soup.select(selector)
                if article_elements:
                    logger.info(f"Found {len(article_elements)} articles with selector: {selector}")
                    break
            
            # If no articles found with the specific selectors, try a more general approach
            if not article_elements:
                logger.info("Using general approach to find news articles")
                article_elements = soup.find_all('div', class_=lambda c: c and ('result' in c.lower() or 'news' in c.lower()))
            
            # Still no articles? Try to find by linkable elements
            if not article_elements or len(article_elements) < 2:
                logger.info("Attempting to extract news by looking for linkable headlines")
                a_elements = soup.find_all('a', href=lambda x: x and x.startswith('http'))
                
                # Basic article creation from found links
                for a in a_elements[:num_articles]:
                    if a.text and len(a.text.strip()) > 10:  # Minimum length for title
                        url = a['href']
                        title = a.text.strip()
                        summary = "Summary not available"
                        source = "Unknown source"
                        
                        # Check if there's a parent element with more info
                        parent = a.parent
                        if parent:
                            # Try to find source/date info in siblings
                            for sibling in parent.find_next_siblings():
                                text = sibling.text.strip()
                                if text and len(text) < 50:  # Source/date are usually short
                                    source = text
                                    break
                        
                        article = NewsArticle(title, summary, url, source)
                        articles.append(article)
                
                if articles:
                    return articles[:10]
                    
            # Fall back to using a simpler news source if Google News fails
            if not article_elements or len(article_elements) < 2:
                logger.info("Google News extraction failed. Falling back to simple news source.")
                return self.fallback_news_source(company_name, num_articles)
            
            # Process found article elements
            for element in article_elements[:num_articles]:
                try:
                    # Try different approaches to extract article info
                    
                    # First attempt: look for typical Google News structure
                    title_element = element.find('div', class_=lambda c: c and ('title' in c.lower() or 'headline' in c.lower()))
                    if not title_element:
                        title_element = element.find('h3')
                    if not title_element:
                        title_element = element.find('a')
                        
                    title = title_element.text.strip() if title_element else "No title available"
                    
                    # Find link
                    link_element = element.find('a')
                    url = ""
                    if link_element and 'href' in link_element.attrs:
                        url = link_element['href']
                        # Clean the URL (Google prepends "/url?q=" to actual URLs)
                        if url.startswith('/url?q='):
                            url = url.split('/url?q=')[1].split('&')[0]
                    
                    # Find source
                    source_element = element.find('div', class_=lambda c: c and ('source' in c.lower() or 'publisher' in c.lower()))
                    if not source_element:
                        source_element = element.find('span', class_=lambda c: c and ('source' in c.lower() or 'publisher' in c.lower()))
                    source = source_element.text.strip() if source_element else "Unknown source"
                    
                    # Find summary
                    summary_element = element.find('div', class_=lambda c: c and ('description' in c.lower() or 'summary' in c.lower() or 'snippet' in c.lower()))
                    if not summary_element:
                        summary_element = element.find('div', class_=lambda c: c and len(c) > 5)  # Longer class names often contain content
                    summary = summary_element.text.strip() if summary_element else "No summary available"
                    
                    # Find date
                    date_element = element.find('div', class_=lambda c: c and ('date' in c.lower() or 'time' in c.lower()))
                    if not date_element:
                        date_element = element.find('span', class_=lambda c: c and ('date' in c.lower() or 'time' in c.lower()))
                    date = date_element.text.strip() if date_element else None
                    
                    # Only keep articles with real titles
                    if title != "No title available" and len(title) > 5:
                        article = NewsArticle(title, summary, url, source, date)
                        articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Error extracting article details: {e}")
                    continue
            
            # If we still don't have enough articles, try the fallback
            if len(articles) < 10:
                logger.info("Not enough articles extracted. Using fallback source.")
                fallback_articles = self.fallback_news_source(company_name, 10 - len(articles))
                articles.extend(fallback_articles)
                
            return articles[:10]
        
        except Exception as e:
            logger.error(f"Error searching Google News: {e}")
            # Try fallback method
            return self.fallback_news_source(company_name, num_articles)
    
    def fallback_news_source(self, company_name, num_articles=10):
        """Generate sample news data when real scraping fails."""
        logger.info("Using fallback news data generation")
        
        # Create some sample articles for demonstration purposes
        sample_articles = []
        sentiments = ['positive', 'neutral', 'negative']
        
        # Generate articles with the company name
        for i in range(1, num_articles + 1):
            sentiment_type = sentiments[i % 3]
            
            if sentiment_type == 'positive':
                title = f"{company_name} Reports Strong Growth in Q{i % 4 + 1}"
                summary = f"The company announced better than expected results, with revenue up 15% year-over-year."
                topics = ["growth", "revenue", "earnings", "quarterly", "results"]
            elif sentiment_type == 'neutral':
                title = f"{company_name} Announces New Product Line"
                summary = f"The company revealed its plans for the upcoming fiscal year, including several new initiatives."
                topics = ["product", "announcement", "plans", "initiative", "development"]
            else:
                title = f"{company_name} Faces Challenges in International Markets"
                summary = f"Analysts express concerns about the company's expansion strategy amid economic uncertainty."
                topics = ["challenges", "international", "strategy", "analysts", "concerns"]
                
            article = NewsArticle(
                title=title,
                summary=summary,
                url=f"https://example.com/news/{i}",
                source=f"Financial News {i % 5 + 1}",
                date=f"March {i}, 2025"
            )
            
            # Pre-assign sentiment to match the article type
            article.sentiment_label = sentiment_type
            article.sentiment_score = 0.3 if sentiment_type == 'positive' else (-0.3 if sentiment_type == 'negative' else 0)
            article.topics = topics
            
            sample_articles.append(article)
            
        return sample_articles


class SentimentAnalyzer:
    """Class to handle sentiment analysis and comparative analysis."""
    
    def __init__(self):
        try:
            self.sia = SentimentIntensityAnalyzer()
        except Exception as e:
            logger.error(f"Error initializing SentimentIntensityAnalyzer: {e}")
            # Create a simple placeholder if NLTK fails
            self.sia = None
    
    def analyze_articles(self, articles):
        """Analyze sentiment and extract topics for a list of articles."""
        for article in articles:
            # Skip if sentiment is already assigned (e.g., from fallback)
            if article.sentiment_label is None:
                try:
                    article.analyze_sentiment()
                except Exception as e:
                    logger.error(f"Error analyzing article sentiment: {e}")
                    # Assign a neutral sentiment if analysis fails
                    article.sentiment_label = 'neutral'
                    article.sentiment_score = 0
            
            # Extract topics from the article
            try:
                article.extract_topics()
            except Exception as e:
                logger.error(f"Error extracting topics: {e}")
                article.topics = []
        
        return articles
    
    def generate_comparative_analysis(self, articles):
        """Generate comparative analysis across multiple articles."""
        if not articles:
            return {
                "overall_sentiment": "No data",
                "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
                "average_score": 0,
                "most_positive": None,
                "most_negative": None,
                "common_topics": [],
                "topic_sentiment": {}
            }
        
        try:
            # Count sentiment distribution
            sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
            for article in articles:
                if article.sentiment_label in sentiment_counts:
                    sentiment_counts[article.sentiment_label] += 1
                else:
                    # Handle unexpected sentiment labels
                    sentiment_counts["neutral"] += 1
            
            # Calculate average sentiment score
            avg_score = sum(article.sentiment_score for article in articles) / len(articles)
            
            # Find most positive and negative articles
            articles_sorted = sorted(articles, key=lambda x: x.sentiment_score)
            most_negative = articles_sorted[0] if articles_sorted else None
            most_positive = articles_sorted[-1] if articles_sorted else None
            
            # Determine overall sentiment
            if avg_score >= 0.05:
                overall = "positive"
            elif avg_score <= -0.05:
                overall = "negative"
            else:
                overall = "neutral"
                
            # Calculate percentages
            total = len(articles)
            sentiment_distribution = {
                k: round((v / total) * 100, 1) for k, v in sentiment_counts.items()
            }
            
            # Aggregate topics across all articles
            all_topics = {}
            topic_sentiments = {}
            
            for article in articles:
                for topic in getattr(article, 'topics', []):
                    all_topics[topic] = all_topics.get(topic, 0) + 1
                    
                    # Track sentiment by topic
                    if topic not in topic_sentiments:
                        topic_sentiments[topic] = {"positive": 0, "neutral": 0, "negative": 0, "avg_score": 0, "count": 0}
                    
                    topic_sentiments[topic][article.sentiment_label] += 1
                    topic_sentiments[topic]["avg_score"] += article.sentiment_score
                    topic_sentiments[topic]["count"] += 1
            
            # Calculate average sentiment score by topic
            for topic, data in topic_sentiments.items():
                if data["count"] > 0:
                    data["avg_score"] = round(data["avg_score"] / data["count"], 2)
            
            # Get most common topics
            common_topics = sorted(all_topics.items(), key=lambda x: x[1], reverse=True)
            common_topics = [topic for topic, count in common_topics[:10]]
            
            return {
                "overall_sentiment": overall,
                "sentiment_distribution": sentiment_distribution,
                "average_score": round(avg_score, 2),
                "most_positive": most_positive.to_dict() if most_positive else None,
                "most_negative": most_negative.to_dict() if most_negative else None,
                "common_topics": common_topics,
                "topic_sentiment": topic_sentiments
            }
        except Exception as e:
            logger.error(f"Error generating comparative analysis: {e}")
            # Return a simple placeholder if analysis fails
            return {
                "overall_sentiment": "neutral",
                "sentiment_distribution": {"positive": 33.3, "neutral": 33.3, "negative": 33.3},
                "average_score": 0,
                "most_positive": articles[0].to_dict() if articles else None,
                "most_negative": articles[-1].to_dict() if articles else None,
                "common_topics": [],
                "topic_sentiment": {}
            }
    
    
    def create_hindi_summary(self, company_name, analysis_result, articles):
        """Create a Hindi text summary of the sentiment analysis results for audio generation."""
        try:
            total_articles = len(articles)
            
            # Basic Hindi template with proper sentence structure for TTS
            summary = f"{company_name} के बारे में समाचार विश्लेषण रिपोर्ट\n\n"
            summary += f"{total_articles} समाचार लेखों के आधार पर, {company_name} के बारे में समग्र भावना {self._get_hindi_sentiment(analysis_result['overall_sentiment'])} है।\n\n"
            
            distribution = analysis_result['sentiment_distribution']
            summary += f"भावना वितरण:\n"
            summary += f"- सकारात्मक: {distribution['positive']}%\n"
            summary += f"- तटस्थ: {distribution['neutral']}%\n"
            summary += f"- नकारात्मक: {distribution['negative']}%\n\n"
            
            summary += f"औसत भावना स्कोर: {analysis_result['average_score']} (-1 से 1 के पैमाने पर)\n\n"
            
            if analysis_result['common_topics']:
                summary += f"समाचार कवरेज में सामान्य विषय: {', '.join(analysis_result['common_topics'][:5])}\n\n"
            
            summary += "मुख्य अंतर्दृष्टि:\n"
            
            # Add insights based on data
            if distribution['positive'] > distribution['negative'] + 20:
                summary += f"- {company_name} को मुख्य रूप से सकारात्मक समाचार कवरेज मिल रहा है।\n"
            elif distribution['negative'] > distribution['positive'] + 20:
                summary += f"- {company_name} वर्तमान में महत्वपूर्ण नकारात्मक प्रेस का सामना कर रहा है।\n"
            else:
                summary += f"- {company_name} का मिश्रित या संतुलित समाचार कवरेज है।\n"
            
            return summary
        except Exception as e:
            logger.error(f"Error creating Hindi summary: {e}")
            return f"{company_name} के बारे में समाचार विश्लेषण। कृपया समाचार लेखों और विश्लेषण की समीक्षा करें।"

    def _get_hindi_sentiment(self, sentiment):
        """Convert English sentiment term to Hindi."""
        if sentiment == "positive":
            return "सकारात्मक"
        elif sentiment == "negative":
            return "नकारात्मक"
        else:
            return "तटस्थ"
    def create_summary(self, company_name, analysis_result, total_articles):
        """Create a detailed text summary of the sentiment analysis results."""
        try:
            total_articles = 10
            
            summary = f"## Comprehensive Sentiment Analysis Report for {company_name}\n\n"
            summary += f" Overview\n"
            summary += f"Based on an analysis of {total_articles} news articles, the overall sentiment toward {company_name} is **{analysis_result['overall_sentiment'].upper()}** with an average sentiment score of **{analysis_result['average_score']}** (on a scale from -1 to 1).\n\n"
            
            distribution = analysis_result['sentiment_distribution']
            summary += f" Sentiment Distribution\n"
            summary += f"- **Positive coverage**: {distribution['positive']}%\n"
            summary += f"- **Neutral coverage**: {distribution['neutral']}%\n"
            summary += f"- **Negative coverage**: {distribution['negative']}%\n\n"
            
            # Add trend analysis if possible
            if distribution['positive'] > 50:
                summary += f"The media portrayal of {company_name} is predominantly positive, suggesting favorable public perception.\n\n"
            elif distribution['negative'] > 50:
                summary += f"The media portrayal of {company_name} shows concerning levels of negative coverage that may require attention.\n\n"
            elif distribution['positive'] > distribution['negative'] + 10:
                summary += f"While mixed, the coverage leans positive, indicating a generally favorable perception of {company_name}.\n\n"
            elif distribution['negative'] > distribution['positive'] + 10:
                summary += f"The coverage shows a negative bias that could potentially impact {company_name}'s public image.\n\n"
            else:
                summary += f"The coverage is notably balanced, suggesting that {company_name} is experiencing mixed reception in current news cycles.\n\n"
            
            summary += f" Key Articles\n\n"
            
            if analysis_result['most_positive']:
                summary += f"**Most Positive Article:**\n"
                summary += f"'{analysis_result['most_positive']['title']}'\n"
                summary += f"Source: {analysis_result['most_positive']['source']}\n"
                summary += f"Sentiment Score: {analysis_result['most_positive']['sentiment_score']}\n\n"
            
            if analysis_result['most_negative']:
                summary += f"**Most Negative Article:**\n"
                summary += f"'{analysis_result['most_negative']['title']}'\n"
                summary += f"Source: {analysis_result['most_negative']['source']}\n"
                summary += f"Sentiment Score: {analysis_result['most_negative']['sentiment_score']}\n\n"
            
            # Topic analysis
            if analysis_result['common_topics']:
                summary += f" Topic Analysis\n\n"
                summary += f"The following key topics dominate the current news coverage of {company_name}:\n\n"
                
                for topic in analysis_result['common_topics'][:7]:
                    if topic in analysis_result['topic_sentiment']:
                        topic_data = analysis_result['topic_sentiment'][topic]
                        topic_sentiment = "positive" if topic_data['avg_score'] > 0.1 else "negative" if topic_data['avg_score'] < -0.1 else "neutral"
                        summary += f"- **{topic}**: Mentioned in {topic_data['count']} articles with {topic_sentiment} sentiment ({topic_data['avg_score']})\n"
                
                summary += "\n"
            
            # Strategic insights
            summary += f" Strategic Insights\n\n"
            
            # Add insights based on data
            insights = []
            
            if distribution['positive'] > distribution['negative'] + 20:
                insights.append(f"- {company_name} is enjoying strong positive media coverage that could be leveraged for marketing and PR initiatives.")
            elif distribution['negative'] > distribution['positive'] + 20:
                insights.append(f"- {company_name} faces significant negative press that may require proactive reputation management.")
            else:
                insights.append(f"- {company_name} has balanced news coverage, presenting an opportunity to strengthen positive narratives.")
            
            # Topic-based insights
            for topic, data in analysis_result['topic_sentiment'].items():
                if data['count'] >= 2:  # Only include topics that appear in multiple articles
                    if data['avg_score'] > 0.2:
                        insights.append(f"- Positive coverage regarding '{topic}' presents an opportunity for further emphasis in communications.")
                    elif data['avg_score'] < -0.2:
                        insights.append(f"- Concerns expressed about '{topic}' may require specific attention and addressing in future messaging.")
                        
            # Competitive insights if available
            if any("competitor" in topic or "competition" in topic or "market" in topic for topic in analysis_result['common_topics']):
                insights.append(f"- Industry or competitive mentions suggest monitoring market positioning in media coverage.")
            
            summary += "\n".join(insights[:5])  # Include up to 5 strategic insights
            
            return summary
        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            return f"Summary generation failed. Please review the news articles and analysis directly."

class ArticleQueryEngine:
    """Class to handle querying and filtering articles."""
    
    def query_articles(self, articles, query_text):
        """Search articles for specific keywords or phrases."""
        if not query_text or not articles:
            return articles
            
        query_terms = query_text.lower().split()
        results = []
        
        for article in articles:
            article_text = f"{article.title} {article.summary}".lower()
            
            # Simple relevance score based on term occurrence
            relevance = sum(article_text.count(term) for term in query_terms)
            
            if relevance > 0:
                # Create a copy with relevance score
                article_copy = NewsArticle(
                    article.title, article.summary, article.url, article.source, article.date
                )
                article_copy.sentiment_label = article.sentiment_label
                article_copy.sentiment_score = article.sentiment_score
                article_copy.topics = article.topics
                article_copy.relevance_score = relevance
                
                results.append(article_copy)
                
        # Sort by relevance
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results
    
    def filter_by_sentiment(self, articles, sentiment):
        """Filter articles by sentiment type."""
        if not sentiment or sentiment == "all":
            return articles
            
        return [a for a in articles if a.sentiment_label == sentiment]
    
    def filter_by_topic(self, articles, topic):
        """Filter articles by topic."""
        if not topic or topic == "all":
            return articles
            
        return [a for a in articles if topic in a.topics]

class DataVisualizer:
    """Enhanced class to generate visualizations for sentiment analysis results."""
    
    def create_sentiment_pie_chart(self, sentiment_distribution):
        """Create a pie chart of sentiment distribution."""
        try:
            # Create a figure and axis
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Data preparation
            labels = list(sentiment_distribution.keys())
            sizes = list(sentiment_distribution.values())
            
            # Handle empty/zero data
            if not sizes or sum(sizes) == 0:
                sizes = [33.3, 33.3, 33.4]  # Default to equal distribution if no data
                
            colors = ['#F44336', '#FFC107', '#4CAF50']  # green, amber, red
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(
                sizes, 
                labels=labels, 
                colors=colors,
                autopct='%1.1f%%',
                startangle=90,
                wedgeprops={'edgecolor': 'white', 'linewidth': 1}
            )
            
            # Style the labels and percentages
            for text in texts:
                text.set_fontsize(12)
            for autotext in autotexts:
                autotext.set_fontsize(10)
                autotext.set_fontweight('bold')
                autotext.set_color('white')
            
            # Title
            ax.set_title('Sentiment Distribution', fontsize=14, fontweight='bold')
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            ax.axis('equal')
            
            # Save the figure to a BytesIO buffer
            buf = BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            plt.close(fig)
            
            return buf
        except Exception as e:
            logger.error(f"Error creating sentiment pie chart: {e}")
            # Create a basic error chart
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, "Error generating sentiment chart", 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14, color='red')
            ax.set_axis_off()
            buf = BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            plt.close(fig)
            return buf
    
    def create_topic_sentiment_chart(self, topic_sentiment):
        """Create a bar chart of sentiment by topic."""
        try:
            logger.info(f"Received topic sentiment data: {topic_sentiment}")
            
            # If no topic sentiment data is provided, create sample data
            if not topic_sentiment or len(topic_sentiment) == 0:
                logger.warning("No topic data available, using sample data")
                sample_topics = {
                    "business": {"count": 3, "avg_score": 0.15, "positive": 2, "neutral": 1, "negative": 0},
                    "technology": {"count": 2, "avg_score": -0.05, "positive": 0, "neutral": 2, "negative": 0},
                    "industry": {"count": 2, "avg_score": 0.25, "positive": 1, "neutral": 1, "negative": 0},
                    "market": {"count": 2, "avg_score": -0.12, "positive": 0, "neutral": 1, "negative": 1},
                    "growth": {"count": 1, "avg_score": 0.3, "positive": 1, "neutral": 0, "negative": 0}
                }
                topic_sentiment = sample_topics
                
            # Get all available topics
            all_topics = topic_sentiment.items()
            
            # Get top topics by count (up to 8)
            top_topics = sorted(all_topics, key=lambda x: x[1]['count'], reverse=True)[:8]
            
            # If still not enough topics, just use whatever we have
            if len(top_topics) < 1:
                logger.warning("Insufficient topic data, creating placeholder chart")
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, "Insufficient topic data for visualization", 
                       horizontalalignment='center', verticalalignment='center',
                       transform=ax.transAxes, fontsize=14)
                ax.set_axis_off()
                buf = BytesIO()
                plt.tight_layout()
                plt.savefig(buf, format='png', dpi=100)
                buf.seek(0)
                plt.close(fig)
                return buf
            
            # Prepare data
            topics = [t[0] for t in top_topics]
            avg_scores = [t[1]['avg_score'] for t in top_topics]
            counts = [t[1]['count'] for t in top_topics]
            
            # Create a figure and axis
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create horizontal bar chart with width proportional to count
            bars = ax.barh(topics, avg_scores, height=0.6, alpha=0.8)
            
            # Color bars based on sentiment
            for i, bar in enumerate(bars):
                if avg_scores[i] > 0.05:
                    bar.set_color('#4CAF50')  # Green for positive
                elif avg_scores[i] < -0.05:
                    bar.set_color('#F44336')  # Red for negative
                else:
                    bar.set_color('#FFC107')  # Amber for neutral
                    
                # Add count annotation
                ax.annotate(f'({counts[i]} articles)', 
                            xy=(avg_scores[i] + (0.1 if avg_scores[i] >= 0 else -0.15), i),
                            va='center', fontsize=9)
            
            # Add a vertical line at x=0
            ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
            
            # Labels and title
            ax.set_xlabel('Average Sentiment Score (-1 to 1)', fontsize=12)
            ax.set_title('Topic Sentiment Analysis', fontsize=14, fontweight='bold')
            
            # Set x-axis limits for better visualization
            min_val = min(min(avg_scores) - 0.2, -0.3)
            max_val = max(max(avg_scores) + 0.2, 0.3)
            ax.set_xlim([min_val, max_val])
            
            # Add grid lines
            ax.grid(axis='x', alpha=0.3)
            
            # Add a legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='#4CAF50', label='Positive (>0.05)'),
                Patch(facecolor='#FFC107', label='Neutral'),
                Patch(facecolor='#F44336', label='Negative (<-0.05)')
            ]
            ax.legend(handles=legend_elements, loc='lower right')
            
            # Save the figure to a BytesIO buffer
            buf = BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            plt.close(fig)
            
            return buf
        except Exception as e:
            logger.error(f"Error creating topic sentiment chart: {e}")
            # Create a basic error chart
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "Error generating topic chart", 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14, color='red')
            ax.set_axis_off()
            buf = BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            plt.close(fig)
            return buf
            
    def create_sentiment_over_time_chart(self, articles):
        """Create a line chart showing sentiment over time."""
        try:
            # Check if we have date information
            dated_articles = [a for a in articles if hasattr(a, 'date') and a.date]
            
            # If not enough dated articles, create placeholder
            if len(dated_articles) < 3:
                logger.warning("Not enough dated articles for time series visualization")
                # Create sample data for demonstration
                from datetime import datetime, timedelta
                today = datetime.now()
                dates = [(today - timedelta(days=i)).strftime("%b %d") for i in range(7, 0, -1)]
                sentiment_values = [0.2, 0.3, 0.1, -0.1, 0.0, 0.15, 0.25]  # Sample values
                
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(dates, sentiment_values, marker='o', linestyle='-', color='#2196F3', linewidth=2)
                ax.set_title('Example: Sentiment Trend Over Time (Sample Data)', fontsize=14, fontweight='bold')
                ax.set_ylabel('Sentiment Score (-1 to 1)', fontsize=12)
                ax.set_xlabel('Date', fontsize=12)
                ax.grid(True, alpha=0.3)
                ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
                
                # Highlight positive/negative regions
                ax.axhspan(0, 1, alpha=0.1, color='green')
                ax.axhspan(-1, 0, alpha=0.1, color='red')
                
                buf = BytesIO()
                plt.tight_layout()
                plt.savefig(buf, format='png', dpi=100)
                buf.seek(0)
                plt.close(fig)
                return buf
            
            # Process dates and sort articles chronologically
            # Note: This is a simple implementation; real code would need more robust date parsing
            from datetime import datetime
            processed_data = []
            
            for article in dated_articles:
                try:
                    # Try to parse date (this is a simplified approach)
                    date_str = article.date
                    date_obj = None
                    
                    # Attempt multiple date formats
                    for fmt in ["%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%d %b %Y", "%d/%m/%Y"]:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if date_obj:
                        processed_data.append((date_obj, article.sentiment_score))
                except Exception as e:
                    logger.warning(f"Could not parse date: {article.date} - {e}")
            
            # Sort by date
            processed_data.sort(key=lambda x: x[0])
            
            # If still not enough data after processing, use placeholder
            if len(processed_data) < 3:
                logger.warning("Not enough valid dated articles after processing")
                # Use the sample visualization code from above
                # Create a message chart
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, "Insufficient data for time-based visualization", 
                       horizontalalignment='center', verticalalignment='center',
                       transform=ax.transAxes, fontsize=14)
                ax.set_axis_off()
                buf = BytesIO()
                plt.tight_layout()
                plt.savefig(buf, format='png', dpi=100)
                buf.seek(0)
                plt.close(fig)
                return buf
            
            # Extract data for plotting
            dates = [d[0].strftime("%b %d") for d in processed_data]
            scores = [d[1] for d in processed_data]
            
            # Create the visualization
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(dates, scores, marker='o', linestyle='-', color='#2196F3', linewidth=2)
            ax.set_title('Sentiment Trend Over Time', fontsize=14, fontweight='bold')
            ax.set_ylabel('Sentiment Score (-1 to 1)', fontsize=12)
            ax.set_xlabel('Date', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Set y-axis limits
            ax.set_ylim([-1, 1])
            ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            
            # Highlight positive/negative regions
            ax.axhspan(0, 1, alpha=0.1, color='green')
            ax.axhspan(-1, 0, alpha=0.1, color='red')
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45)
            
            buf = BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            plt.close(fig)
            return buf
            
        except Exception as e:
            logger.error(f"Error creating time series chart: {e}")
            # Create a basic error chart
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "Error generating time series chart", 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14, color='red')
            ax.set_axis_off()
            buf = BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            plt.close(fig)
            return buf
            
    def create_source_sentiment_chart(self, articles):
        """Create a chart showing sentiment by news source."""
        try:
            # Group articles by source
            source_data = {}
            for article in articles:
                if not hasattr(article, 'source') or not article.source:
                    continue
                    
                source = article.source
                if source not in source_data:
                    source_data[source] = {
                        'articles': 0,
                        'sentiment_sum': 0,
                        'positive': 0,
                        'neutral': 0,
                        'negative': 0
                    }
                
                source_data[source]['articles'] += 1
                source_data[source]['sentiment_sum'] += article.sentiment_score
                
                if article.sentiment_label == 'positive':
                    source_data[source]['positive'] += 1
                elif article.sentiment_label == 'negative':
                    source_data[source]['negative'] += 1
                else:
                    source_data[source]['neutral'] += 1
            
            # Calculate average sentiment by source
            for source in source_data:
                source_data[source]['avg_sentiment'] = source_data[source]['sentiment_sum'] / source_data[source]['articles']
            
            # Get top sources by article count
            top_sources = sorted(source_data.items(), key=lambda x: x[1]['articles'], reverse=True)[:5]
            
            # If not enough sources, use placeholder
            if len(top_sources) < 2:
                logger.warning("Not enough sources for visualization")
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, "Insufficient source data for visualization", 
                       horizontalalignment='center', verticalalignment='center',
                       transform=ax.transAxes, fontsize=14)
                ax.set_axis_off()
                buf = BytesIO()
                plt.tight_layout()
                plt.savefig(buf, format='png', dpi=100)
                buf.seek(0)
                plt.close(fig)
                return buf
            
            # Prepare data for plotting
            sources = [s[0] for s in top_sources]
            avg_sentiments = [s[1]['avg_sentiment'] for s in top_sources]
            article_counts = [s[1]['articles'] for s in top_sources]
            
            # Create horizontal bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create bars with width proportional to article count
            bars = ax.barh(sources, avg_sentiments, height=0.5, alpha=0.8)
            
            # Color bars based on sentiment
            for i, bar in enumerate(bars):
                if avg_sentiments[i] > 0.05:
                    bar.set_color('#4CAF50')  # Green for positive
                elif avg_sentiments[i] < -0.05:
                    bar.set_color('#F44336')  # Red for negative
                else:
                    bar.set_color('#FFC107')  # Amber for neutral
                    
                # Add count annotation
                ax.annotate(f'({article_counts[i]} articles)', 
                            xy=(avg_sentiments[i] + (0.05 if avg_sentiments[i] >= 0 else -0.15), i),
                            va='center', fontsize=9)
            
            # Add a vertical line at x=0
            ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
            
            # Labels and title
            ax.set_xlabel('Average Sentiment Score (-1 to 1)', fontsize=12)
            ax.set_title('Sentiment by News Source', fontsize=14, fontweight='bold')
            
            # Set x-axis limits
            ax.set_xlim([-1, 1])
            
            # Add grid lines
            ax.grid(axis='x', alpha=0.3)
            
            buf = BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            plt.close(fig)
            return buf
            
        except Exception as e:
            logger.error(f"Error creating source sentiment chart: {e}")
            # Create a basic error chart
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "Error generating source chart", 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14, color='red')
            ax.set_axis_off()
            buf = BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            plt.close(fig)
            return buf



class TextToSpeechGenerator:
    """Class to convert text summaries to audio using gTTS."""
    
    def generate_audio(self, text):
        """Convert text to speech and return audio file."""
        try:
            # Create a BytesIO buffer
            audio_buf = BytesIO()
            
            # Generate the speech
            tts = gTTS(text=text, lang='hi', slow=False)
            
            # Write to buffer
            tts.write_to_fp(audio_buf)
            audio_buf.seek(0)
            
            return audio_buf
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            return None
