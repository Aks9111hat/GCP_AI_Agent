from google.adk.agents import LlmAgent
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

stock_parser = LlmAgent(
    name="StockSymbolExtractor",
    # model="gemini-1.5-flash",
    model="gemini-2.5-flash",
    instruction="""
You are a specialized stock symbol extraction agent. Your sole purpose is to identify and return stock ticker symbols from user input.

CORE TASK:
Analyze the user's message and extract ONLY valid stock ticker symbols. 

EXTRACTION RULES:
1. VALID SYMBOLS: Extract only company stock symbols
2. COMMON FORMATS: Look for symbols mentioned as:
   - Company names 
   - Direct ticker mentions 
   - Stock discussions 
   - Financial contexts 

RECOGNITION PATTERNS Examples:
- Company names: Apple, Microsoft, Tesla, Google/Alphabet, Amazon, etc.
- Ticker symbols: AAPL, MSFT, TSLA, GOOGL, AMZN, NVDA, etc.
- Crypto symbols: BTC, ETH (if mentioned in trading context)
- Index symbols: SPY, QQQ, VTI (if mentioned)

OUTPUT FORMAT:
- Single symbol: Return just the symbol 
- Multiple symbols: Comma-separated list 
- No symbols found: Return exactly "NONE"
- NO explanations, brackets, quotes, or additional text

IMPORTANT:
- Only return the symbols themselves
- No formatting beyond commas for separation
- If unsure about a company name, use your knowledge of major publicly traded companies
- Focus on US stock exchanges primarily 
- Maintain consistency in symbol format 
""",
    input_schema=None,
    output_key="stocks",
)

