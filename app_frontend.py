# app_frontend.py
# Standard Library Imports
import json
import os
from io import BytesIO


# Third-Party Imports
import base64
import requests
import pandas as pd
import streamlit as st


# Streamlit UI
st.set_page_config(
    page_title="Company Sentiment Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API endpoint

if os.environ.get("SPACE_ID"):
    API_URL = "http://localhost:5000/api"
else:
    # Local development
    API_URL = "http://localhost:5000/api"

# Custom CSS - 
st.markdown("""
<style>
/* Add your custom CSS here */
.main-title {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1E88E5;
    margin-bottom: 0.5rem;
}
.subtitle {
    font-size: 1.2rem;
    color: #666;
    margin-bottom: 2rem;
}
.section-title {
    font-size: 1.8rem;
    font-weight: bold;
    margin: 1.5rem 0 1rem 0;
    color: #333;
}
.card {
    background-color: white;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border-left: 5px solid #ccc;
}
.card.positive {
    border-left-color: #4CAF50;
}
.card.neutral {
    border-left-color: #FFC107;
}
.card.negative {
    border-left-color: #F44336;
}
.article-title {
    font-size: 1.2rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}
.article-source {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 0.5rem;
}
.article-summary {
    font-size: 1rem;
    margin-bottom: 0.5rem;
}
.sentiment-badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: bold;
}
.badge-positive {
    background-color: rgba(76, 175, 80, 0.2);
    color: #2E7D32;
}
.badge-neutral {
    background-color: rgba(255, 193, 7, 0.2);
    color: #F57F17;
}
.badge-negative {
    background-color: rgba(244, 67, 54, 0.2);
    color: #C62828;
}
.metric-card {
    background-color: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    text-align: center;
}
.metric-value {
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}
.metric-label {
    font-size: 1rem;
    color: #666;
}
.topic-tag {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    background-color: rgba(30, 136, 229, 0.1);
    color: #1976D2;
    border-radius: 4px;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
}
.topic-tag.positive {
    background-color: rgba(76, 175, 80, 0.1);
    color: #2E7D32;
}
.topic-tag.negative {
    background-color: rgba(244, 67, 54, 0.1);
    color: #C62828;
}
.topic-tag.neutral {
    background-color: rgba(255, 193, 7, 0.1);
    color: #F57F17;
}
.action-button {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    background-color: #E3F2FD;
    color: #1976D2;
    border-radius: 4px;
    font-size: 0.9rem;
    cursor: pointer;
    text-decoration: none;
    border: none;
}
.action-button:hover {
    background-color: #BBDEFB;
}
<style>
    h1 {font-size: 24px !important;}
    h2 {font-size: 22px !important;}
    h3 {font-size: 20px !important;}
    p, li {font-size: 16px !important; line-height: 1.5;}
</style>

            


""", unsafe_allow_html=True)

# Initialize session state
if 'articles' not in st.session_state:
    st.session_state.articles = []
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'summary' not in st.session_state:
    st.session_state.summary = None
if 'company_name' not in st.session_state:
    st.session_state.company_name = ""

# App title
st.markdown('<h1 class="main-title">Company Sentiment Analyzer</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Analyze news sentiment about any company in real-time</p>', unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Settings")

# Company search
company_name = st.sidebar.text_input("Enter Company Name", value=st.session_state.company_name, placeholder="e.g., Apple, Tesla, Microsoft")
num_articles = 10

# Search button
search_pressed = st.sidebar.button("Analyze Sentiment")

# About section in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    "This app analyzes news sentiment for any company in real-time. "
    "It scrapes news articles, performs sentiment analysis, and "
    "visualizes the results to help you understand how a company "
    "is being portrayed in the media."
)

# Main workflow
if search_pressed and company_name:
    st.session_state.company_name = company_name
    
    with st.spinner(f"Searching for news about {company_name}..."):
        # API request to search for news
        try:
            response = requests.post(
                f"{API_URL}/search",
                json={"company_name": company_name, "num_articles": num_articles}
            )
            
            if response.status_code == 200:
                data = response.json()
                st.session_state.articles = data['articles']
                st.session_state.analysis_result = data['analysis_result']
                st.session_state.summary = data['summary']
            else:
                st.error(f"Error: {response.json().get('error', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error connecting to API: {str(e)}")

# Display results if available
if st.session_state.articles and st.session_state.analysis_result:
    # Create tabs for different views
    tabs = st.tabs(["Overview", "Articles", "Visualizations", "Audio Summary"])
    
    with tabs[0]:  # Overview tab
        st.markdown(f'<h2 class="section-title">Sentiment Analysis Results for {st.session_state.company_name}</h2>', unsafe_allow_html=True)
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: {'#4CAF50' if st.session_state.analysis_result['average_score'] > 0 else '#F44336' if st.session_state.analysis_result['average_score'] < 0 else '#FFC107'}">
                        {st.session_state.analysis_result['average_score']}
                    </div>
                    <div class="metric-label">Average Sentiment (-1 to 1)</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{st.session_state.analysis_result['sentiment_distribution']['positive']}%</div>
                    <div class="metric-label">Positive Articles</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
        with col3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{len(st.session_state.articles)}</div>
                    <div class="metric-label">Total Articles Analyzed</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        # Summary
        st.markdown(f'<h3 class="section-title">Summary</h3>', unsafe_allow_html=True)
        st.markdown(st.session_state.summary.replace('\n', '<br>'), unsafe_allow_html=True)
        
        # Common topics
        if st.session_state.analysis_result['common_topics']:
            st.markdown(f'<h3 class="section-title">Common Topics</h3>', unsafe_allow_html=True)
            topics_html = ""
            for topic in st.session_state.analysis_result['common_topics'][:8]:
                topic_sentiment = st.session_state.analysis_result['topic_sentiment'].get(topic, {}).get('avg_score', 0)
                color_class = "positive" if topic_sentiment > 0.1 else "negative" if topic_sentiment < -0.1 else "neutral"
                topics_html += f'<span class="topic-tag {color_class}">{topic}</span>'
            st.markdown(topics_html, unsafe_allow_html=True)
    
    with tabs[1]:  # Articles tab
        st.markdown(f'<h2 class="section-title">News Articles</h2>', unsafe_allow_html=True)
        
        # Create query interface
        col1, col2, col3 = st.columns([3, 2, 2])
        
        with col1:
            query_text = st.text_input("Search articles", placeholder="Enter keywords...")
        
        with col2:
            sentiment_filter = st.selectbox(
                "Filter by sentiment",
                ["all", "positive", "neutral", "negative"]
            )
        
        with col3:
            # Get all unique topics
            all_topics = set()
            for article in st.session_state.articles:
                all_topics.update(article['topics'])
            
            topic_filter = st.selectbox(
                "Filter by topic",
                ["all"] + sorted(list(all_topics))
            )
        
        # Apply filters using API
        if query_text or sentiment_filter != "all" or topic_filter != "all":
            try:
                filter_response = requests.post(
                    f"{API_URL}/filter_articles",
                    json={
                        "articles": st.session_state.articles,
                        "query_text": query_text,
                        "sentiment_filter": sentiment_filter,
                        "topic_filter": topic_filter
                    }
                )
                
                if filter_response.status_code == 200:
                    filtered_articles = filter_response.json()['filtered_articles']
                else:
                    st.error(f"Error filtering articles: {filter_response.json().get('error', 'Unknown error')}")
                    filtered_articles = st.session_state.articles
            except Exception as e:
                st.error(f"Error connecting to API: {str(e)}")
                filtered_articles = st.session_state.articles
        else:
            filtered_articles = st.session_state.articles
        
        # Display query results
        if not filtered_articles:
            st.info("No articles match your search criteria.")
        else:
            st.write(f"Showing {len(filtered_articles)} articles")
        
        # Display articles
        for article in filtered_articles:
            # Determine card class based on sentiment
            card_class = f"card {article['sentiment_label']}"
            
            # Escape quotes in title and URL for JavaScript
            safe_title = article['title'].replace('"', '\\"').replace("'", "\\'")
            safe_url = article['url'].replace('"', '\\"').replace("'", "\\'")
            safe_source = article['source'].replace('"', '\\"').replace("'", "\\'")
            
            # Create HTML for article card
            article_html = f"""
            <div class="{card_class}">
                <div class="article-title">{article['title']}</div>
                <div class="article-source">{article['source']} {article['date'] if article['date'] else ''}</div>
                <div class="article-summary">{article['summary']}</div>
                <div style="margin-top: 0.5rem;">
                    <span class="sentiment-badge badge-{article['sentiment_label']}">
                        {article['sentiment_label'].capitalize()} ({article['sentiment_score']:.2f})
                    </span>
                </div>
                <div style="margin-top: 0.5rem; margin-bottom: 0.5rem;">
                    <strong>Topics:</strong> {''.join([f'<span class="topic-tag">{topic}</span>' for topic in article['topics']])}
                </div>
                <div style="display: flex; gap: 10px;">
                    <a href="{article['url']}" target="_blank" class="action-button">Read Full Article</a>
                    
                    
                
            </div>
            """
            st.markdown(article_html, unsafe_allow_html=True)
    
    with tabs[2]:  # Visualizations tab
        st.markdown(f'<h2 class="section-title">Sentiment Visualizations</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Request pie chart visualization from API
            try:
                viz_response = requests.post(
                    f"{API_URL}/generate_visualization",
                    json={
                        "type": "pie_chart",
                        "data": st.session_state.analysis_result['sentiment_distribution']
                    }
                )
                
                if viz_response.status_code == 200:
                    # Display the returned image
                    image_data = base64.b64decode(viz_response.json()['image'])
                    st.image(BytesIO(image_data), use_column_width=True)
                else:
                    st.error("Failed to generate pie chart")
            except Exception as e:
                st.error(f"Error generating visualization: {str(e)}")
        
        with col2:
            # Request topic sentiment chart from API
            try:
                viz_response = requests.post(
                    f"{API_URL}/generate_visualization",
                    json={
                        "type": "topic_chart",
                        "data": st.session_state.analysis_result['topic_sentiment']
                    }
                )
                
                if viz_response.status_code == 200 and 'image' in viz_response.json():
                    # Display the returned image
                    image_data = base64.b64decode(viz_response.json()['image'])
                    st.image(BytesIO(image_data), use_column_width=True)
                else:
                    st.info("Not enough topic data to generate visualization.")
            except Exception as e:
                st.error(f"Error generating visualization: {str(e)}")
    
    with tabs[3]:  # Audio Summary tab
        st.markdown(f'<h2 class="section-title">Audio Summary</h2>', unsafe_allow_html=True)
        
        if st.session_state.summary:
            with st.spinner("Generating audio summary in Hindi..."):
                # Request audio generation from API
                try:
                    audio_response = requests.post(
                        f"{API_URL}/generate_audio",
                        json={
                            "company_name": st.session_state.company_name,
                            "analysis_result": st.session_state.analysis_result,
                            "articles": st.session_state.articles
                        }
                    )
                    
                    if audio_response.status_code == 200 and 'audio' in audio_response.json():
                        # Display the audio
                        audio_data = base64.b64decode(audio_response.json()['audio'])
                        st.audio(BytesIO(audio_data), format="audio/mp3")
                        
                        # Download button
                        audio_download = BytesIO(audio_data)
                        st.download_button(
                            label="Download Hindi Audio Summary",
                            data=audio_download,
                            file_name=f"{st.session_state.company_name.replace(' ', '_')}_hindi_summary.mp3",
                            mime="audio/mp3"
                        )
                    else:
                        st.error("Failed to generate audio summary. Please try again.")
                except Exception as e:
                    st.error(f"Error generating audio: {str(e)}")
        
        # Display text version of the summary as well
        st.markdown("### Text Summary (English)")
        st.markdown(st.session_state.summary.replace('\n', '<br>'), unsafe_allow_html=True)

else:
    # Display instructions when no search has been performed
    st.markdown("""
    ### How to Use This App
    1. Enter a company name in the sidebar
    2. Adjust the number of articles to analyze (more articles = more accurate results)
    3. Click "Analyze Sentiment" to start the analysis
    
    ### What You'll Get
    - Real-time news sentiment analysis
    - Visual representation of sentiment distribution
    - Topic analysis showing what aspects of the company are being discussed
    - Downloadable audio summary of the analysis
    
    Enter a company name to get started!
    """)

