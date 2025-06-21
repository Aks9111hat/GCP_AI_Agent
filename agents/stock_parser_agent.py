from google.adk.agents import LlmAgent
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

stock_parser = LlmAgent(
    name="StockParser",
    model="gemini-1.5-flash",
    instruction="""
You are a stock symbol extractor. Extract all stock ticker symbols from the user's message.

Rules:
- Extract only valid stock symbols (3-5 capital letters like AAPL, MSFT, GOOGL, TSLA)
- Return symbols as a simple comma-separated list
- If only one symbol, return just that symbol
- No brackets, no quotes, no explanations
- If no symbols found, return "NONE"

Examples:
Input: "What's AAPL doing today?"
Output: AAPL

Input: "Compare MSFT and GOOGL performance"
Output: MSFT,GOOGL

Input: "I want to analyze TSLA, AAPL, and NVDA"
Output: TSLA,AAPL,NVDA

Input: "How is the market today?"
Output: NONE
""",
    input_schema=None,
    output_key="stocks",
)