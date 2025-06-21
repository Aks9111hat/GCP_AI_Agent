from google.adk.agents import LlmAgent
# from utils import GEMINI_MODEL
import os
from dotenv import load_dotenv

load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

stock_parser = LlmAgent(
    name="StockParser",
    model="gemini-1.5-flash",
    instruction="""
Extract stock symbols (like AAPL, TSLA, GOOGL) from the user message.
Respond ONLY with a Python list of strings (e.g., ["AAPL", "TSLA"]). No explanation.
""",
    input_schema=None,
    output_key="stocks",
    # api_key = "AIzaSyAH3vShtRC7W0w4FF9juTcOcAgaD36ueMY"
)
