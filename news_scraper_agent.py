from google.adk.agents import BaseAgent
import os
import asyncio
import aiohttp
from newspaper import Article
from dotenv import load_dotenv
import nltk
import logging

# Load .env variables
load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")

# Ensure required NLTK data is available
# try:
#     nltk.download('punkt')
# except Exception as e:
#     logging.warning(f"Failed to download nltk 'punkt': {e}")

class NewsSummaryAgent(BaseAgent):
    def __init__(self):
        super().__init__()

    async def fetch_articles(self, query: str, language: str = "en") -> list:
        """Fetch news articles asynchronously using aiohttp"""
        url = f"https://newsapi.org/v2/everything?q={query}&language={language}&apiKey={API_KEY}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('articles', [])
                    else:
                        logging.warning(f"News API returned status {response.status}")
        except Exception as e:
            logging.error(f"Error fetching articles: {e}")
        return []

    async def summarize_article(self, url: str) -> dict:
        """Download and summarize article asynchronously"""
        def _sync_summarize(url):
            try:
                try:
                    nltk.download('punkt')
                except Exception as e:
                    logging.warning(f"Failed to download nltk 'punkt': {e}")
                article = Article(url)
                article.download()
                article.parse()
                try:
                    article.nlp()
                    summary = article.summary
                except Exception as nlp_error:
                    logging.warning(f"NLP failed for {url}: {nlp_error}")
                    sentences = article.text.split('.')[:3]
                    summary = '. '.join(sentences) + '.' if sentences else "Summary unavailable"
                return {
                    'title': article.title,
                    'summary': summary,
                    'text': article.text,
                    'url': url
                }
            except Exception as e:
                logging.warning(f"Article processing failed for {url}: {e}")
                return {
                    'title': "Error loading article",
                    'summary': f"Could not process article: {str(e)}",
                    'text': "",
                    'url': url
                }

        return await asyncio.to_thread(_sync_summarize, url)

    async def run(self, inputs: dict) -> dict:
        query = inputs.get("query", "GAIL India Limited")

        if not API_KEY:
            return {
                "error": "❌ NEWS_API_KEY not found. Please set it in .env file."
            }

        articles = await self.fetch_articles(query)

        if not articles:
            return {"error": f"No articles found for query: {query}"}

        first_n = articles[:3]
        tasks = [self.summarize_article(a["url"]) for a in first_n]
        summaries = await asyncio.gather(*tasks)

        return {"news_summaries": summaries}
