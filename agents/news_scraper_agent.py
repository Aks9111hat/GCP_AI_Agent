import os, logging, aiohttp
from dotenv import load_dotenv
from pydantic import Field
from typing import AsyncGenerator
from google.genai.types import Content, Part
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
# test
load_dotenv()
logger = logging.getLogger(__name__)

class NewsScraperAgent(BaseAgent):
    api_key: str = Field(default_factory=lambda: os.getenv("NEWS_API_KEY", ""))

    def __init__(self, name="NewsScraperAgent"):
        super().__init__(name=name)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        stocks = ctx.session.state.get("stocks", [])

        # print("🤣",stocks)
        if not stocks or not self.api_key:
            ctx.session.state["news_analysis"] = []
            yield Event(
                author="agent",
                content=Content(parts=[Part(text="No stocks or missing API key.")])
            )
            # yield Event.final_response(text="No stocks or missing API key.")
            return

        all_news = []
        for stock in stocks:
            articles = await self._fetch_articles(stock)
            all_news.append({
                "stock": stock,
                "articles": articles,
                "sentiment": "neutral"  # placeholder
            })

        ctx.session.state["news_analysis"] = all_news
        yield Event(
                author="agent",
                content=Content(parts=[Part(text="News data collected.")])
        )
        # yield Event.final_response(text="News data collected.")

    async def _fetch_articles(self, stock: str):
        url = f"https://newsapi.org/v2/everything?q={stock}&language=en&apiKey={self.api_key}&pageSize=3"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return [{"title": a["title"], "url": a["url"]} for a in data.get("articles", [])]
                return []
