
🏢 **Company Sentiment Analyzer** <br>
A **Flask + Streamlit**-based web application for analyzing sentiment on companies using **Natural Language Processing (NLP)** techniques. <br>

🚀 Features <br>
**✅ Sentiment Analysis** - Uses NLP models to analyze sentiment from user-provided text. <br>
**✅ Multilingual Support** - Uses `googletrans` for language translation. <br>
**✅ Text-to-Speech (TTS)** - Converts analyzed sentiment to speech using `gTTS`. <br>
**✅ Web Scraping** - Extracts data from the web using `BeautifulSoup`. <br>
**✅ Interactive Visualization** - Generates insights using `Matplotlib` and `Seaborn`. <br>
**✅ User-friendly UI** - Built with `Streamlit` for an interactive frontend.<br>

🛠 Tech Stack <br>
**Backend:** Flask + Gunicorn <br>
**Frontend:** Streamlit <br>
**NLP:** NLTK, Google Translate <br>
**Web Scraping:** BeautifulSoup <br>
**Database:** Pandas (for data handling) <br>
**Deployment:** Docker Project Structure <br>

📂 Project Structure
```
📁 Company Sentiment Analyzer
├── .github/            # GitHub workflows and configurations
├── .gitignore          # Files to be ignored by Git
├── Dockerfile          # Docker configuration for the application
├── Documentation.md    # Additional documentation
├── README.md           # Main documentation file
├── api.py              # Flask API backend
├── app_frontend.py     # Streamlit frontend
├── classes.py          # Core classes and models
├── requirements.txt    # Project dependencies
└── start.sh            # Startup script for Flask and Streamlit
```
🔧 Installation & Setup
**1️⃣ Clone this repository:**
```bash
git clone https://github.com/your-username/company-sentiment-analyzer.git
cd company-sentiment-analyzer
```
**2️⃣ Install dependencies:**
```bash
pip install -r requirements.txt
```
**3️⃣ Run the Flask API:**
```bash
gunicorn -w 2 -b 0.0.0.0:5000 api:app
```
**4️⃣ Start the Streamlit frontend:**
```bash
streamlit run app_frontend.py --server.port 8501 --server.address 0.0.0.0
```
🐳 Docker Deployment
**Build and run the container using Docker:**
```bash
docker build -t sentiment-analyzer .
docker run -p 5000:5000 -p 8501:8501 sentiment-analyzer
```
