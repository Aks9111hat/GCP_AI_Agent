import logging
from typing import AsyncGenerator
from typing_extensions import override
from pydantic import Field

from google.adk.agents import BaseAgent, ParallelAgent, SequentialAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

logger = logging.getLogger(__name__)

class StockInsightsAgent(BaseAgent):
    stock_parser: LlmAgent
    news_agent: BaseAgent
    market_agent: BaseAgent
    analytics_agent: BaseAgent

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, stock_parser: LlmAgent, news_agent: BaseAgent, market_agent: BaseAgent, analytics_agent: BaseAgent):
        # Pass everything as kwargs to super().__init__
        super().__init__(
            name="StockInsightsAgent",
            stock_parser=stock_parser,
            news_agent=news_agent,
            market_agent=market_agent,
            analytics_agent=analytics_agent,
        )

    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        logger.info(f"[{self.name}] Starting stock analysis flow")
        
        # Step 1: Extract stocks using LLM agent
        logger.info(f"[{self.name}] Step 1: Extracting stock symbols")
        async for event in self.stock_parser.run_async(ctx):
            yield event

        # Check if stocks were extracted and parse them properly
        stocks_raw = ctx.session.state.get("stocks", "")
        
        # Parse the stocks string to get actual list
        stocks = []
        if stocks_raw:
            stocks_str = stocks_raw.strip()
            if stocks_str and stocks_str != "NONE":
                # Split by comma and clean up each symbol
                stocks = [symbol.strip().upper() for symbol in stocks_str.split(",") if symbol.strip()]
        
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
        # Step 2: Run news and market agents in parallel
        logger.info(f"[{self.name}] Step 2: Fetching news and market data in parallel")
        
        # Create parallel agent with the stocks already in context
        parallel = ParallelAgent(
            name="FetchDataInParallel",
            sub_agents=[self.news_agent, self.market_agent],
        )
        
        async for event in parallel.run_async(ctx):
            yield event

        # Step 3: Run analytics agent with all collected data
        logger.info(f"[{self.name}] Step 3: Running analytics on collected data")
        async for event in self.analytics_agent.run_async(ctx):
            yield event

        logger.info(f"[{self.name}] Stock analysis flow completed")