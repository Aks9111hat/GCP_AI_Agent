import logging
from typing import AsyncGenerator, Optional
from typing_extensions import override
from pydantic import Field

from google.adk.agents import BaseAgent, ParallelAgent, SequentialAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

logger = logging.getLogger(__name__)

class StockInsightsAgent(BaseAgent):
    # Define fields with default None and exclude from serialization
    stock_parser: Optional[LlmAgent] = Field(default=None, exclude=True)
    news_agent: Optional[BaseAgent] = Field(default=None, exclude=True)
    market_agent: Optional[BaseAgent] = Field(default=None, exclude=True)
    analytics_agent: Optional[BaseAgent] = Field(default=None, exclude=True)
    parallel: Optional[ParallelAgent] = Field(default=None, exclude=True)
    sequential: Optional[SequentialAgent] = Field(default=None, exclude=True)

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, stock_parser: LlmAgent, news_agent: BaseAgent, market_agent: BaseAgent, analytics_agent: BaseAgent):
        # Create sub agents first
        parallel = ParallelAgent(
            name="FetchDataInParallel",
            sub_agents=[news_agent, market_agent],
        )

        sequential = SequentialAgent(
            name="FullFlow",
            sub_agents=[stock_parser, parallel, analytics_agent],
        )

        # Call super().__init__ with only the standard BaseAgent parameters
        super().__init__(
            name="StockInsightsAgent",
            sub_agents=[sequential]
        )
        
        # Set the field values
        self.stock_parser = stock_parser
        self.news_agent = news_agent
        self.market_agent = market_agent
        self.analytics_agent = analytics_agent
        self.parallel = parallel
        self.sequential = sequential

    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        logger.info(f"[{self.name}] Running full stock analysis flow.")
        async for event in self.sequential.run_async(ctx):
            yield event
            
        stocks = ctx.session.state.get("stocks", [])
        print("🤣 😁", stocks)
        if not stocks:
            logger.warning(f"[{self.name}] No stocks extracted from input.")
            yield Event(author="agent", content=types.Content(parts=[types.Part(text="No stocks found in the prompt.")]))
            return