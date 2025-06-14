import os
from dotenv import load_dotenv
import requests
from newspaper import Article

# Load .env variables
load_dotenv()

# Access API key
API_KEY = os.getenv("NEWS_API_KEY")

def get_news_articles(api_key, query, language='en'):
    url = f"https://newsapi.org/v2/everything?q={query}&language={language}&apiKey={api_key}"
    response = requests.get(url)
    data = response.json()
    return data['articles']

def summarize_article(url):
    article = Article(url)
    article.download()
    article.parse()
    article.nlp()
    return {
        'title': article.title,
        'summary': article.summary,
        'text': article.text
    }

if __name__ == "__main__":
    query = "stock market"
    articles = get_news_articles(API_KEY, query)

    for art in articles[:3]:
        print(f"\n🔗 URL: {art['url']}")
        summary = summarize_article(art['url'])
        print(f"📰 Title: {summary['title']}")
        print(f"✏️ Summary: {summary['summary']}")
