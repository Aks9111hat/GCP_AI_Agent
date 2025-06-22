import ast
import asyncio
import logging
from typing import AsyncGenerator, Optional
from typing_extensions import override
from pydantic import Field
from typing import Any, Dict, List
import yfinance as yf

from google.adk.agents import BaseAgent, ParallelAgent, SequentialAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai.types import Content, Part

logger = logging.getLogger(__name__)

class MarketDataAgent(BaseAgent):
    # Define fields with default None and exclude from serialization
    stock_parser: Optional[LlmAgent] = Field(default=None, exclude=True)
    news_agent: Optional[BaseAgent] = Field(default=None, exclude=True)
    market_agent: Optional[BaseAgent] = Field(default=None, exclude=True)
    analytics_agent: Optional[BaseAgent] = Field(default=None, exclude=True)
    parallel: Optional[ParallelAgent] = Field(default=None, exclude=True)
    sequential: Optional[SequentialAgent] = Field(default=None, exclude=True)

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, name="MarketDataAgent"):
        super().__init__(name=name)

    async def fetch_data_sync(self, stock, period="5d", interval="1d"):
        logger.info(f"[{self.name}] Fetching market data for symbols: {stock}")
        result = {}
        try:
            logger.info(f"[{self.name}] Processing symbol: {stock}")
            ticker = yf.Ticker(stock)

            # print("123",ticker)

            df = yf.download(stock, period=period, interval=interval, progress=False)

            print("456",df)

            df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df.columns]
            df.reset_index(inplace=True)
            if "Date" in df.columns:
                df["Date"] = df["Date"].astype(str)

            price_data_dict = df.to_dict(orient="records")
            info = ticker.info
            print("Nimish",price_data_dict)
            

            summary = {
                "Open": info.get("open"),
                "Previous Close": info.get("previousClose"),
                "High": info.get("dayHigh"),
                "Low": info.get("dayLow"),
                "52W High": info.get("fiftyTwoWeekHigh"),
                "52W Low": info.get("fiftyTwoWeekLow"),
                "Volume": info.get("volume"),
                "Book Value Per Share": info.get("bookValue"),
                "Dividend Rate": info.get("dividendRate"),
                "Dividend Yield": info.get("dividendYield"),
                "Beta": info.get("beta"),
                "P/E Ratio (TTM)": info.get("trailingPE"),
                "Forward P/E": info.get("forwardPE"),
                "EPS (TTM)": info.get("trailingEps"),
                "P/B Ratio": info.get("priceToBook"),
                "Sector": info.get("sector"),
                "Market Cap (USD)": info.get("marketCap"),
                "Enterprise Value": info.get("enterpriseValue"),
                "50D Avg": info.get("fiftyDayAverage"),
            }
            # for row in records:
            #     flat_records.append({
            #         "Date": row.get("Date"),
            #         f"Open_{stock}": row.get("Open"),
            #         f"High_{stock}": row.get("High"),
            #         f"Low_{stock}": row.get("Low"),
            #         f"Close_{stock}": row.get("Close"),
            #         f"Volume_{stock}": row.get("Volume"),
            #     })

            result[stock] = {
                "summary": summary,
                "price_data": price_data_dict
            }
            logger.info(f"[{self.name}] Successfully fetched data for {stock}")
        except Exception as e:
            logger.error(f"[{self.name}] Error fetching data for {stock}: {str(e)}")
            result[stock] = {"error": str(e)}
        return result

    def format_market_summary(self, summary: Dict[str, Any]) -> str:
        def fmt(val):
            if isinstance(val, (int, float)):
                return f"{val:,.2f}" if val >= 1000 else f"{val}"
            return val or "N/A"

        lines = [
            f"\n Sector: {summary.get('Sector', 'N/A')}",
            f"\n Open: ${fmt(summary.get('Open'))}",
            f"\n Previous Close: ${fmt(summary.get('Previous Close'))}",
            f"\n High: ${fmt(summary.get('High'))}",
            f"\n Low: ${fmt(summary.get('Low'))}",
            f"\n Volume: {fmt(summary.get('Volume'))}",
            f"\n Market Cap: ${fmt(summary.get('Market Cap (USD)'))}",
            f"\n EPS (TTM): {fmt(summary.get('EPS (TTM)'))}",
            f"\n P/E Ratio: {fmt(summary.get('P/E Ratio (TTM)'))}",
            f"\n Dividend Yield: {fmt(summary.get('Dividend Yield'))}",
            f"\n Beta: {fmt(summary.get('Beta'))}"
        ]
        return "\n".join(lines)
    
    def format_price_data(self, records: List[Dict[str, Any]]) -> str:

        lines = []
        sample_record = records[0]
        def find_column(patterns):
            for pattern in patterns:
              for key in sample_record.keys():
                if pattern.lower() in key.lower():
                    return key
            return None
        
    
        open_col = find_column(['open'])
        high_col = find_column(['high'])
        low_col = find_column(['low'])
        close_col = find_column(['close'])
        volume_col = find_column(['volume'])
        date_col = find_column(['date'])
    
    # Format each record
        for row in records:
          lines.append(
            f"📅 {row.get(date_col, 'N/A')}:\n"
            f"• Open: ${row.get(open_col, 'N/A')} | High: ${row.get(high_col, 'N/A')} | "
            f"Low: ${row.get(low_col, 'N/A')} | Close: ${row.get(close_col, 'N/A')} | "
            f"Volume: {int(row.get(volume_col, 0)) if row.get(volume_col) else 'N/A':,}"
          )
    
        return "\n\n".join(lines)


    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        try:
            raw_stocks = ctx.session.state["stocks"]
            # raw_stocks = ctx.session.state.get("stocks", [])
            logger.info(f"[{self.name}] Raw stocks from session: {raw_stocks}")

            if not raw_stocks:
                yield Event(author=self.name, content=Content(parts=[Part(text="No stocks provided.")]))
                return

            if isinstance(raw_stocks, str):
                try:
                    raw_stocks = ast.literal_eval(raw_stocks)
                except:
                    raw_stocks = [raw_stocks]
            
            full_market_data = []
            for stock in raw_stocks:
                logger.info(f"[{self.name}] Fetching market data for {stock}")
                stock_data = await self.fetch_data_sync(stock)
                full_market_data.append(stock_data)

            ctx.session.state["market_data"] = full_market_data
            logger.info(f"[{self.name}] Stored market data in session.")

            summaries = []
            for stock_dict in full_market_data:  # each stock_dict is like {'MSFT': {...}}
                for symbol, data in stock_dict.items():
                    if "error" in data:
                        summaries.append(f"\n {symbol}: {data['error']}")
                    else:
                        summary_text = self.format_market_summary(data["summary"])
                        price_text = self.format_price_data(data["price_data"])
                        summaries.append(
                            f"\n {symbol} Market Summary:\n{summary_text}\n\n"
                            f"\n\n Recent Price Data:\n{price_text}"
                        )


            response_text = "\n\n".join(summaries)
            yield Event(author=self.name, content=Content(parts=[Part(text=response_text)]))

        except Exception as e:
            logger.error(f"[{self.name}] Error in market data agent: {str(e)}")
            yield Event(author=self.name, content=Content(parts=[Part(text=f"Error processing market data: {str(e)}")]))
