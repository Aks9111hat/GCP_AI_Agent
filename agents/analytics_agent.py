import logging
from typing import AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai.types import Content, Part

logger = logging.getLogger(__name__)

class AnalyticsAgent(BaseAgent):
    def __init__(self, name="AnalyticsAgent"):
        super().__init__(name=name)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        news = ctx.session.state.get("news_analysis", [])
        market = ctx.session.state.get("market_data", [])
        insights = []

        # print("Analytics Agent", market)

        # print("\n News Analysis:", news)
        # for i, stock_data in enumerate(market):
        #     insights.append({
        #         "stock": stock_data["stock"],
        #         "recommendation": "Buy" if stock_data["change"] > 0 else "Hold"
        #     })

        ctx.session.state["stock_insights"] = insights
        yield Event(
            author="agent",
            content=Content(parts=[Part(text="Analytics complete.")])
        )
        # yield Event.final_response(text="Analytics complete.")

# test1