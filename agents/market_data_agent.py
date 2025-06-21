import ast
import asyncio
import json
import logging
import requests
import yfinance as yf
import pandas as pd
from typing import List, Dict, Any, AsyncGenerator
from typing_extensions import override

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai.types import Content, Part
# test
logger = logging.getLogger(__name__)

class MarketDataAgent(BaseAgent):
    name: str = "Market_Data_Agent"
    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, name="Market_Data_Agent"):
        super().__init__(name=name)

    def resolve_to_symbol(self, name_or_symbol: str) -> str:
        if len(name_or_symbol) <= 5 and name_or_symbol.isupper():
            return name_or_symbol
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

    def fetch_data(self, symbols, period="5d", interval="1d"):

        print("2nd",symbols,"😁")
        result = {}
        for symbol in symbols:
            print(symbol,"😁")
            try:
                df = yf.download(symbol, period=period, interval=interval)
                df.reset_index(inplace=True)

                print(f"Fetching data for {symbol}...")
                ticker = yf.Ticker(symbol)
                info = ticker.info

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

                result[symbol] = {
                    "summary": summary,
                    "price_data": df.to_dict(orient="records")
                }
            except Exception as e:
                result[symbol] = {"error": str(e)}
        return result
    
    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # stocks = ctx.session.state.get("stocks", [])
        raw_stocks = ctx.session.state.get("stocks", [])
        if not raw_stocks:
            yield Event(
                author="agent",
                content=Content(parts=[Part(text="No stocks provided.")])
            )
            return
        print("Raw stocks:", raw_stocks)
        stocks = []
        if isinstance(raw_stocks, list) and len(raw_stocks) == 1 and isinstance(raw_stocks[0], str):
            try:
                # Handle strings like "['MSFT']\n"
                cleaned = raw_stocks[0].strip()
                stocks = ast.literal_eval(cleaned)
                print("Parsed stocks from stringified list:", stocks)
            except Exception as e:
                print("Failed to parse stocks:", e)
                stocks = [raw_stocks[0].strip()]
            else:
                stocks = raw_stocks

        print("Final resolved stock list:", stocks)
            
        # resolved_symbols = [self.resolve_to_symbol(sym) for sym in stocks]
        # resolved_symbols = list(set(filter(None, stocks)))

        # print(f"Resolved symbols: {resolved_symbols}")
        print("1st ",stocks)
        market_data = self.fetch_data(stocks)
        ctx.session.state["market_data"] = market_data

        # print(market_data)

        summaries = []
        for symbol, data in market_data.items():
            if "error" in data:
                summaries.append(f"❌ {symbol}: {data['error']}")
            else:
                summary_json = json.dumps(data["summary"], indent=2)
                price_data_sample = data.get("price_data", [])
                price_data_str = (
                    json.dumps(price_data_sample[:3], indent=2) + "\n...(truncated)..."
                    if len(price_data_sample) > 3
                    else json.dumps(price_data_sample, indent=2)
                )
                summaries.append(
                    f"✅ {symbol} Summary:\n{summary_json}\n\n"
                    f"📊 Price Data :\n{price_data_str}"
                )

                
        yield Event(
            author="agent",
            content=Content(parts=[Part(text="\n".join(summaries))])
        )
