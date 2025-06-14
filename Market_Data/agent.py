# from adk.agent import BaseAgent
import os
import io
import re
import yfinance as yf
import pandas as pd
import requests
import base64
import fitz  # PyMuPDF
# from google.cloud import aiplatform


class MarketDataAgent():
    def __init__(self):
        return
        # self.project = os.getenv("PROJECT_ID")
        # self.location = os.getenv("LOCATION", "us-central1")
        # aiplatform.init(project=self.project, location=self.location)
        # self.model = aiplatform.TextGenerationModel.from_pretrained("text-bison")

    def resolve_symbols_via_vertex(self, query: str) -> list:
        prompt = f"""
        Extract and return a Python list of stock ticker symbols (e.g., ["AAPL", "TSLA", "GOOG"])
        based on this query about the stock market:

        Query: "{query}"
        """
        try:
            response = self.model.predict(prompt=prompt, temperature=0.3, max_output_tokens=256)
            return eval(response.text.strip())
        except:
            return []

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
            if j["quotes"]:
                return j["quotes"][0]["symbol"]
        except:
            pass
        return None

    def fetch_data(self, symbols, period="5d", interval="1d"):
        result = {}
        for symbol in symbols:
            try:
                df = yf.download(symbol, period=period, interval=interval)
                df.reset_index(inplace=True)
                result[symbol] = df.to_dict(orient="records")
            except Exception as e:
                result[symbol] = {"error": str(e)}
        return result

    def extract_from_csv(self, content: str) -> list:
        try:
            df = pd.read_csv(io.StringIO(content))
            if "Symbol" in df.columns:
                return df["Symbol"].dropna().tolist()
            elif "Company" in df.columns:
                return [self.resolve_to_symbol(name) for name in df["Company"].dropna()]
        except Exception as e:
            print("CSV read error:", e)
        return []

    def extract_from_pdf(self, pdf_bytes: bytes) -> list:
        try:
            if len(pdf_bytes) > 2 * 1024 * 1024:  # 2 MB limit
                print("PDF too large")
                return []

            symbols = set()
            with fitz.open("pdf", pdf_bytes) as doc:
                for page in doc:
                    text = page.get_text()
                    matches = re.findall(r'\b[A-Z]{1,5}\b', text)
                    for token in matches:
                        if self.resolve_to_symbol(token):
                            symbols.add(token)
            return list(symbols)
        except Exception as e:
            print("PDF parse error:", e)
            return []

    def run(self, inputs: dict) -> dict:
        period = inputs.get("period", "5d")
        interval = inputs.get("interval", "1d")

        symbols = inputs.get("symbols", [])
        nlp_query = inputs.get("nlp_query")
        csv_content = inputs.get("csv_content")
        pdf_base64 = inputs.get("pdf_content")

        # if nlp_query:
        #     symbols += self.resolve_symbols_via_vertex(nlp_query)

        if csv_content:
            symbols += self.extract_from_csv(csv_content)

        if pdf_base64:
            try:
                pdf_bytes = base64.b64decode(pdf_base64)
                symbols += self.extract_from_pdf(pdf_bytes)
            except Exception as e:
                print("Base64 decode error:", e)

        print(symbols)
        resolved_symbols = [self.resolve_to_symbol(sym) for sym in symbols]


        resolved_symbols = list(set(filter(None, resolved_symbols)))  # Remove None + duplicates

        print(resolved_symbols)

        return self.fetch_data(resolved_symbols, period, interval)
