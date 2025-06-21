# integration_manager.py - Integration with your existing agents

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from stock_report_agent import (
    StockReportGeneratorAgent, 
    StockData, 
    NewsData, 
    ReportConfiguration, 
    ReportType
)

logger = logging.getLogger(__name__)

class StockAnalysisPipeline:
    """
    Integration manager that connects your News Scraper, Market Data, and Report Generator agents
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.report_agent = StockReportGeneratorAgent(
            planner_provider=config.PLANNER_PROVIDER,
            planner_model=config.PLANNER_MODEL,
            writer_provider=config.WRITER_PROVIDER,
            writer_model=config.WRITER_MODEL,
            search_api=config.SEARCH_API,
            use_multi_agent=config.USE_MULTI_AGENT
        )
        
        # Store for caching and batch processing
        self.pending_reports = {}
        self.completed_reports = {}
    
    def validate_environment(self) -> bool:
        """Validate required environment variables are set"""
        missing_vars = []
        for var in self.config.REQUIRED_ENV_VARS:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return False
        return True
    
    async def process_stock_analysis(self, 
                                   stock_symbol: str,
                                   market_data: Dict[str, Any],
                                   news_data: Dict[str, Any],
                                   report_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main integration point: Process data from your other agents and generate report
        """
        
        try:
            # Convert input data to structured format
            stock_data = self._convert_market_data(stock_symbol, market_data)
            news_data_obj = self._convert_news_data(news_data)
            
            # Configure report based on input or defaults
            config = self._create_report_config(report_config)
            
            # Generate report
            logger.info(f"Processing analysis for {stock_symbol}")
            report = await self.report_agent.generate_report(
                stock_data, news_data_obj, config
            )
            
            # Store in completed reports
            self.completed_reports[stock_symbol] = report
            
            return report
            
        except Exception as e:
            logger.error(f"Error processing analysis for {stock_symbol}: {e}")
            return {
                "error": str(e),
                "stock_symbol": stock_symbol,
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
    
    def _convert_market_data(self, symbol: str, market_data: Dict[str, Any]) -> StockData:
        """Convert your Market Data Agent output to StockData format"""
        
        return StockData(
            symbol=symbol,
            current_price=float(market_data.get("current_price", 0)),
            price_change=float(market_data.get("price_change", 0)),
            price_change_percent=float(market_data.get("price_change_percent", 0)),
            volume=int(market_data.get("volume", 0)),
            market_cap=market_data.get("market_cap"),
            pe_ratio=market_data.get("pe_ratio"),
            dividend_yield=market_data.get("dividend_yield"),
            beta=market_data.get("beta"),
            moving_averages=market_data.get("moving_averages"),
            support_resistance=market_data.get("support_resistance")
        )
    
    def _convert_news_data(self, news_data: Dict[str, Any]) -> NewsData:
        """Convert your News Scraper Agent output to NewsData format"""
        
        return NewsData(
            headlines=news_data.get("headlines", []),
            sentiment_scores=news_data.get("sentiment_scores", []),
            news_articles=news_data.get("articles", []),
            key_events=news_data.get("key_events", []),
            analyst_ratings=news_data.get("analyst_ratings", []),
            social_sentiment=news_data.get("social_sentiment")
        )
    
    def _create_report_config(self, config_dict: Optional[Dict[str, Any]]) -> ReportConfiguration:
        """Create report configuration from input parameters"""
        
        if not config_dict:
            config_dict = {}
        
        return ReportConfiguration(
            report_type=ReportType(config_dict.get("report_type", "comprehensive")),
            target_audience=config_dict.get("target_audience", "general"),
            time_horizon=config_dict.get("time_horizon", "medium_term"),
            risk_tolerance=config_dict.get("risk_tolerance", "moderate"),
            include_charts=config_dict.get("include_charts", True),
            include_comparisons=config_dict.get("include_comparisons", True),
            custom_sections=config_dict.get("custom_sections"),
            output_format=config_dict.get("output_format", "markdown")
        )
    
    async def batch_process_stocks(self, 
                                 stock_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple stocks concurrently"""
        
        # Limit concurrent processing
        semaphore = asyncio.Semaphore(self.config.MAX_CONCURRENT_REPORTS)
        
        async def process_with_semaphore(request):
            async with semaphore:
                return await self.process_stock_analysis(
                    request["symbol"],
                    request["market_data"],
                    request["news_data"],
                    request.get("report_config")
                )
        
        tasks = [process_with_semaphore(req) for req in stock_requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [result if not isinstance(result, Exception) else {"error": str(result)} 
                for result in results]
    
    def get_quick_summary(self, stock_symbol: str, 
                         market_data: Dict[str, Any], 
                         news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get quick summary without full report generation"""
        
        stock_data = self._convert_market_data(stock_symbol, market_data)
        news_data_obj = self._convert_news_data(news_data)
        
        return self.report_agent.generate_quick_summary(stock_data, news_data_obj)
    
    def export_reports(self, 
                      symbols: List[str], 
                      output_format: str = "json",
                      output_dir: Optional[str] = None) -> List[str]:
        """Export completed reports to files"""
        
        if not output_dir:
            output_dir = self.config.DEFAULT_OUTPUT_DIR
        
        exported_files = []
        
        for symbol in symbols:
            if symbol in self.completed_reports:
                report = self.completed_reports[symbol]
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{symbol}_report_{timestamp}.{output_format}"
                filepath = os.path.join(output_dir, filename)