import os
import ast
import logging
import aiohttp
from dotenv import load_dotenv
from pydantic import Field
from typing import List, AsyncGenerator
from google.genai.types import Content, Part
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

load_dotenv()
logger = logging.getLogger(__name__)

# test1

class NewsScraperAgent(BaseAgent):
    api_key: str = Field(default_factory=lambda: os.getenv("NEWS_API_KEY", ""))

    def __init__(self, name="NewsScraperAgent"):
        super().__init__(name=name)

    # def parse_stocks_from_session(self, raw_stocks) -> List[str]:
    #     """Simple stock parsing for comma-separated format"""
    #     if not raw_stocks:
    #         return []
        
    #     # Convert to string and split by comma
    #     stocks_str = str(raw_stocks).strip()
    #     if stocks_str and stocks_str != "NONE":
    #         return [stock.strip().upper() for stock in stocks_str.split(",") if stock.strip()]
        
    #     return []

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        try:
            raw_stocks = ctx.session.state.get("stocks", [])
            logger.info(f"[{self.name}] Raw stocks from session: {raw_stocks}")

            if not raw_stocks:
                ctx.session.state["news_analysis"] = []
                yield Event(
                    author=self.name,
                    content=Content(parts=[Part(text="No stocks provided for news analysis.")])
                )
                return

            if not self.api_key:
                ctx.session.state["news_analysis"] = []
                yield Event(
                    author=self.name,
                    content=Content(parts=[Part(text="Missing NEWS_API_KEY for news analysis.")])
                )
                return

            # Parse stocks using standardized logic
            # stocks = self.parse_stocks_from_session(raw_stocks)
            logger.info(f"[{self.name}] Parsed stocks: {raw_stocks}")
            
            # if not raw_stocks:
            #     ctx.session.state["news_analysis"] = []
            #     yield Event(
            #         author=self.name,
            #         content=Content(parts=[Part(text="Could not parse any valid stock symbols for news.")])
            #     )
            #     return

            # Fetch news for all stocks
            all_news = []
            news_summaries = []
            
            for stock in raw_stocks:
                logger.info(f"[{self.name}] Fetching news for {stock}")
                articles = await self._fetch_articles(stock)
                
                news_data = {
                    "stock": stock,
                    "articles": articles,
                    "sentiment": "neutral"  # placeholder - you can add sentiment analysis later
                }
                all_news.append(news_data)
                
                # # Create summary for response
                # if articles:
                #     article_titles = [f"• {article['title']}" for article in articles[:3]]
                #     news_summaries.append(
                #         f"📰 {stock} News ({len(articles)} articles):\n" + "\n".join(article_titles)
                #     )
                # else:
                #     news_summaries.append(f"📰 {stock}: No recent news found")

            for news in all_news:
                stock = news["stock"]
                articles = news["articles"]
                if not articles:
                    news_summaries.append(f"📰 {stock}: No recent news found.\n")
                    continue
                
                article_lines = []
                for idx, article in enumerate(articles, start=1):
                    article_lines.append(
                        f"{idx}. {article['title']} ({article['source']})\n🔗 {article['url']}\n🕒 {article['publishedAt']}"
                )
                
                stock_block = f"📰 News for {stock} ({len(articles)} articles):\n" + "\n\n".join(article_lines)
                news_summaries.append(stock_block)

            # Store in session state
            ctx.session.state["news_analysis"] = all_news
            logger.info(f"[{self.name}] News analysis stored in session state for {len(raw_stocks)} stocks")

            # Generate response
            response_text = f"News analysis completed for {len(raw_stocks)} stocks:\n\n" + "\n\n".join(news_summaries)
            
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text=response_text)])
            )
            
        except Exception as e:
            logger.error(f"[{self.name}] Error in news scraper agent: {str(e)}")
            ctx.session.state["news_analysis"] = []
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text=f"Error processing news data: {str(e)}")])
            )

    async def _fetch_articles(self, stock: str):
        """Fetch news articles for a given stock symbol"""
        url = f"https://newsapi.org/v2/everything?q={stock}&language=en&apiKey={self.api_key}&pageSize=5&sortBy=publishedAt"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get("articles", [])
                        return [
                            {
                                "title": article["title"], 
                                "url": article["url"],
                                "publishedAt": article.get("publishedAt", ""),
                                "source": article.get("source", {}).get("name", "Unknown")
                            } 
                            for article in articles
                        ]
                    else:
                        logger.warning(f"[{self.name}] News API returned status {response.status} for {stock}")
                        return []
        except Exception as e:
            logger.error(f"[{self.name}] Error fetching news for {stock}: {str(e)}")
            return []