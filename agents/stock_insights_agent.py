import logging
from typing import AsyncGenerator
from typing_extensions import override
from pydantic import Field
import requests
from google.genai.types import Content, Part
from google.adk.agents import BaseAgent, ParallelAgent, SequentialAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

logger = logging.getLogger(__name__)
# test1

class StockInsightsAgent(BaseAgent):
    stock_parser: LlmAgent
    news_agent: BaseAgent
    market_agent: BaseAgent
    analytics_agent: BaseAgent
    report_agent: BaseAgent

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, stock_parser: LlmAgent, news_agent: BaseAgent, market_agent: BaseAgent, analytics_agent: BaseAgent,report_agent: BaseAgent):
        # Pass everything as kwargs to super().__init__
        super().__init__(
            name="StockInsightsAgent",
            stock_parser=stock_parser,
            news_agent=news_agent,
            market_agent=market_agent,
            analytics_agent=analytics_agent,
            report_agent=report_agent,
        )

    def resolve_to_symbol(self, name_or_symbol: str) -> str:
        # if len(name_or_symbol) <= 5 and name_or_symbol.isupper():
        #     return name_or_symbol
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/113.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json",
                "Connection": "keep-alive"
            }
            r = requests.get(f"https://query1.finance.yahoo.com/v1/finance/search?q={name_or_symbol}", headers=headers)
            j = r.json()
            if j.get("quotes"):
                return j["quotes"][0]["symbol"]
        except:
            pass
        return None

    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        logger.info(f"[{self.name}] Starting stock analysis flow")
        
        # Step 1: Extract stocks using LLM agent
        logger.info(f"[{self.name}] Step 1: Extracting stock symbols")
        async for event in self.stock_parser.run_async(ctx):
            yield event

        # Check if stocks were extracted and parse them properly
        event_text = ctx.session.events[-1].content.parts[0].text  # or just event.text
        try:
            parsed_output = eval(event_text)  # OR json.loads if it's JSON
            ctx.session.state["stocks"] = parsed_output.get("stocks", [])
            ctx.session.state["search_queries"] = parsed_output.get("search_queries", [])
        except Exception as e:
            logger.error(f"Failed to parse LLM output: {e}")
            yield Event(author=self.name, content=Content(parts=[Part(text="Error extracting stock info.")]))
            return
        
        # parsed = ctx.session.state.get("StockSymbolExtractor", {})

        # print(ctx, "My stateeeeeee")
        # stocks_raw = parsed.get("stocks", [])
        stocks_raw = ctx.session.state["stocks"]

        
        print(stocks_raw, "Stocks raw data")
        # Parse the stocks string to get actual list
        # stocks = []
        # if stocks_raw:
        #     stocks_str = stocks_raw.strip()
        #     if stocks_str and stocks_str != "NONE":
        #         # Split by comma and clean up each symbol
        #         stocks = [symbol.strip().upper() for symbol in stocks_str.split(",") if symbol.strip()]
        
        stocks = [self.resolve_to_symbol(sym) for sym in stocks_raw]

        stocks = list(set(filter(None, stocks)))

        if not stocks:
            logger.warning(f"[{self.name}] No stocks extracted from input.")
            yield Event(
                author=self.name, 
                content=types.Content(parts=[types.Part(text="No stocks found in the prompt.")])
            )
            return

        logger.info(f"[{self.name}] Stocks extracted: {stocks}")

        print(f"[{self.name}] Stocks extracted: {stocks}")
        
        # Store parsed stocks as proper list in session state for other agents to use
        ctx.session.state["stocks"] = stocks
        # parsed["stocks"] = stocks
        # Step 2: Run news and market agents in parallel
        logger.info(f"[{self.name}] Step 2: Fetching news and market data in parallel")
        
        # Create parallel agent with the stocks already in context
        parallel = ParallelAgent(
            name="FetchDataInParallel",
            sub_agents=[
                self.news_agent.model_copy(deep=True),
                self.market_agent.model_copy(deep=True)
            ],
        )
        
        async for event in parallel.run_async(ctx):
            yield event

        # Step 3: Run analytics agent with all collected data
        logger.info(f"[{self.name}] Step 3: Running analytics on collected data")
        async for event in self.analytics_agent.run_async(ctx):
            yield event

        logger.info(f"[{self.name}] Stock analysis flow completed")

         # Step 4: Run analytics agent with all collected data
        logger.info(f"[{self.name}] Step 3: Running analytics on collected data")
        async for event in self.report_agent.run_async(ctx):
            yield event

        logger.info(f"[{self.name}] Stock analysis flow completed")
        