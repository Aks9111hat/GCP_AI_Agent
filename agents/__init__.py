from agents.news_scraper_agent import NewsScraperAgent
from agents.market_data_agent import MarketDataAgent
from agents.analytics_agent import AnalyticsAgent
from agents.stock_insights_agent import StockInsightsAgent
from agents.stock_parser_agent import stock_parser  
from agents.report_generator_agent import ReportGeneratorAgent

root_agent = StockInsightsAgent(
    stock_parser=stock_parser,                 
    news_agent=NewsScraperAgent(),
    market_agent=MarketDataAgent(),
    analytics_agent=AnalyticsAgent(),
    report_agent=ReportGeneratorAgent(),
)
