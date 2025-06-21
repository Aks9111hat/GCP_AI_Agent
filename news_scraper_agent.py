import os
from dotenv import load_dotenv
import requests
from newspaper import Article
import nltk

# Download required NLTK data
try:
    nltk.download('punkt')
    nltk.download('punkt_tab')  # Required for newer NLTK versions
except Exception as e:
    print(f"Warning: Could not download NLTK data: {e}")

# Load .env variables
load_dotenv()

# Access API key
API_KEY = os.getenv("NEWS_API_KEY")

def get_news_articles(api_key, query, language='en'):
    """Fetch news articles from NewsAPI"""
    url = f"https://newsapi.org/v2/everything?q={query}&language={language}&apiKey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        return data.get('articles', [])
    except requests.RequestException as e:
        print(f"Error fetching news: {e}")
        return []

def summarize_article(url):
    """Extract and summarize article content"""
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        # Try to generate summary with NLP
        try:
            article.nlp()
            summary = article.summary
        except Exception as nlp_error:
            print(f"NLP processing failed for {url}: {nlp_error}")
            # Fallback: create a simple summary from first few sentences
            text = article.text
            sentences = text.split('.')[:3]  # Get first 3 sentences
            summary = '. '.join(sentences) + '.' if sentences else "Summary unavailable"
        
        return {
            'title': article.title,
            'summary': summary,
            'text': article.text,
            'url': url
        }
    except Exception as e:
        print(f"Error processing article {url}: {e}")
        return {
            'title': "Error loading article",
            'summary': f"Could not process article: {str(e)}",
            'text': "",
            'url': url
        }

def main():
    """Main function to run the news scraper"""
    if not API_KEY:
        print("❌ Error: NEWS_API_KEY not found in environment variables")
        print("Please make sure your .env file contains: NEWS_API_KEY=your_api_key_here")
        return
    
    query = "Google"
    print(f"🔍 Fetching news articles for: '{query}'")
    
    articles = get_news_articles(API_KEY, query)
    
    if not articles:
        print("❌ No articles found or error occurred")
        return
    
    print(f"📰 Found {len(articles)} articles. Processing first 3...")
    
    for i, art in enumerate(articles[:3], 1):
        print(f"\n{'='*60}")
        print(f"📄 Article {i}/3")
        print(f"🔗 URL: {art['url']}")
        
        summary = summarize_article(art['url'])
        print(f"📰 Title: {summary['title']}")
        print(f"✏️ Summary: {summary['summary']}")
        
        # Optional: Show word count
        word_count = len(summary['text'].split()) if summary['text'] else 0
        print(f"📊 Word count: {word_count}")

if __name__ == "__main__":
    main()