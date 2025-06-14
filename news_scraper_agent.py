import requests
from newspaper import Article

# Example: Use NewsAPI to get news articles
def get_news_articles(api_key, query, language='en'):
    url = f"https://newsapi.org/v2/everything?q={query}&language={language}&apiKey={api_key}"
    response = requests.get(url)
    data = response.json()
    return data['articles']

# Example: Summarize using newspaper3k
def summarize_article(url):
    article = Article(url)
    article.download()
    article.parse()
    article.nlp()
    summary = article.summary
    return {
        'title': article.title,
        'summary': summary,
        'text': article.text
    }

# Example: Simple runner
if __name__ == "__main__":
    API_KEY = "YOUR_NEWSAPI_KEY"  # Replace with your API key
    query = "financial markets"
    articles = get_news_articles(API_KEY, query)
    
    for art in articles[:5]:  # limit to first 5 for now
        print(f"🔗 URL: {art['url']}")
        summary = summarize_article(art['url'])
        print(f"📰 Title: {summary['title']}")
        print(f"✏️ Summary: {summary['summary']}\n{'-'*40}")
