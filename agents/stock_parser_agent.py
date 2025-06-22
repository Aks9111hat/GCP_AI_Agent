from google.adk.agents import LlmAgent
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

# instruction = """
# You are an intelligent stock symbol extraction agent. Your goal is to extract:
# 1. `stocks`: Valid stock ticker symbols like AAPL, TSLA, MSFT.
# 2. `search_queries`: Corresponding search-friendly company names or keywords (e.g., "Apple Inc", "Tesla Motors").

# Format your response as a Python dictionary with two keys:
# - 'stocks': a list of valid stock symbols
# - 'search_queries': a list of search-friendly company names

# Example:
# {
#   "stocks": ["AAPL", "TSLA"],
#   "search_queries": ["Apple Inc", "Tesla Motors"]
# }

# RULES:
# - Return "NONE" for both lists if nothing relevant is found.
# - Keep both lists aligned: search_queries[i] should correspond to stocks[i].
# """

instruction = """
You are an intelligent stock symbol extraction agent.

Your task is to analyze the given text and extract relevant stock-related entities, with a focus on:

1. *stocks*: Valid stock ticker symbols (e.g., "AAPL", "TSLA", "MSFT").
2. *search_queries*: Corresponding News API ready query strings that combine the stock symbol and official company name. These should be formatted as:
   '(COMPANY NAME) AND ("stock market" OR "earnings" OR "share price" OR "investors")'

IMPORTANT:
If unsure about a company name, use your knowledge of major publicly traded companies
Focus on US,India stock exchanges primarily 
Maintain consistency in symbol format 
---

### Output Format:
Return a Python dictionary with exactly two keys:
- 'stocks': A list of valid stock ticker symbols.
- 'search_queries': A list of News API friendly query strings, aligned with the stocks list.

*Each query string in search_queries must match the corresponding stock symbol at the same index in stocks.*

---

### Example Output:

```python
{
  "stocks": ["AAPL", "TSLA"],
  "search_queries": [
    '("Apple Inc.") AND ("stock market" OR "earnings" OR "share price" OR "investors")',
    '("Tesla, Inc.") AND ("stock market" OR "earnings" OR "share price" OR "investors")'
  ]
}
"""

class StockExtractionOutput(BaseModel):
    stocks: List[str]
    search_queries: List[str]

stock_parser = LlmAgent(
    name="StockSymbolExtractor",
    # model="gemini-1.5-flash",
    model="gemini-2.5-flash",
    instruction=instruction,
#     instruction="""
# You are a specialized stock symbol extraction agent. Your sole purpose is to identify and return stock ticker symbols from user input.

# CORE TASK:
# Analyze the user's message and extract ONLY valid stock ticker symbols. 

# EXTRACTION RULES:
# 1. VALID SYMBOLS: Extract only company stock symbols
# 2. COMMON FORMATS: Look for symbols mentioned as:
#    - Company names 
#    - Direct ticker mentions 
#    - Stock discussions 
#    - Financial contexts 

# RECOGNITION PATTERNS Examples:
# - Company names: Apple, Microsoft, Tesla, Google/Alphabet, Amazon, etc.
# - Ticker symbols: AAPL, MSFT, TSLA, GOOGL, AMZN, NVDA, etc.
# - Crypto symbols: BTC, ETH (if mentioned in trading context)
# - Index symbols: SPY, QQQ, VTI (if mentioned)

# OUTPUT FORMAT:
# - Single symbol: Return just the symbol 
# - Multiple symbols: Comma-separated list 
# - No symbols found: Return exactly "NONE"
# - NO explanations, brackets, quotes, or additional text

# IMPORTANT:
# - Only return the symbols themselves
# - No formatting beyond commas for separation
# - If unsure about a company name, use your knowledge of major publicly traded companies
# - Focus on US stock exchanges primarily 
# - Maintain consistency in symbol format 
# """,
    input_schema=None,
    output_schema=StockExtractionOutput,
)

