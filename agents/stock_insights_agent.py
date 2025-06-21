import logging
from typing import AsyncGenerator
from typing_extensions import override
from pydantic import Field

from google.adk.agents import BaseAgent, ParallelAgent, SequentialAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
# test
logger = logging.getLogger(__name__)

class StockInsightsAgent(BaseAgent):
    stock_parser: LlmAgent
    news_agent: BaseAgent
    market_agent: BaseAgent
    analytics_agent: BaseAgent

    parallel: ParallelAgent
    sequential: SequentialAgent

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, stock_parser: LlmAgent, news_agent: BaseAgent, market_agent: BaseAgent, analytics_agent: BaseAgent):
        # Create sub agents
        parallel = ParallelAgent(
            name="FetchDataInParallel",
            sub_agents=[news_agent, market_agent],
        )

        sequential = SequentialAgent(
            name="FullFlow",
            sub_agents=[parallel, analytics_agent],

        )

        # Pass everything as kwargs to super().__init__, no manual assignments!
        super().__init__(
            name="StockInsightsAgent",
            stock_parser=stock_parser,
            news_agent=news_agent,
            market_agent=market_agent,
            analytics_agent=analytics_agent,
            parallel=parallel,
            sequential=sequential,
            sub_agents=[stock_parser, sequential],
        )

    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        logger.info(f"[{self.name}] Starting stock extraction via LLM")
        async for event in self.stock_parser.run_async(ctx):
            yield event

        stocks = ctx.session.state.get("stocks", [])
        print("🤣 😁", stocks)
        if not stocks:
            logger.warning(f"[{self.name}] No stocks extracted from input.")
            yield Event(author="agent", content=types.Content(parts=[types.Part(text="No stocks found in the prompt.")]))
            return

        logger.info(f"[{self.name}] Stocks extracted: {stocks}")
        logger.info(f"[{self.name}] Running full stock analysis flow.")
        async for event in self.sequential.run_async(ctx):
            yield event
