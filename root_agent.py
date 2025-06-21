# GCP_AI_Agent/root_agent.py
from google.adk.agents import SequentialAgent
from agents.news_scraper_agent import NewsScraperAgent
from agents.market_data_agent import MarketDataAgent
from agents.analytics_agent import AnalyticsAgent

root_agent = SequentialAgent(
    name="StockAnalysisRootAgent",
    agents=[
        NewsScraperAgent(),
        MarketDataAgent(),
        AnalyticsAgent()
    ]
)
def create_agent():
    """Create the root agent for stock analysis."""
    return root_agent