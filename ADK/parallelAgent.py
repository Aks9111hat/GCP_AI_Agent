from google.adk.agents import ParallelAgent
from market_data_agent.agent import MarketDataAgent
from news_scraper_agent import NewsSummaryAgent

class CombinedMarketNewsAgent(ParallelAgent):
    def __init__(self):
        super().__init__(sub_agents={
            "market": MarketDataAgent(),
            "news": NewsSummaryAgent()
        })
