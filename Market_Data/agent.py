# from adk.agent import BaseAgent
import io
import re
import yfinance as yf
import pandas as pd
import requests
import base64
# import fitz  # PyMuPDF
# from google.cloud import aiplatform


class MarketDataAgent():
    def __init__(self):
        return

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
        result = {}
        for symbol in symbols:
            try:
                df = yf.download(symbol, period=period, interval=interval)
                df.reset_index(inplace=True)

                ticker = yf.Ticker(symbol)
                info = ticker.info

                print(info)

                summary = {
                    "Market Cap": info.get("marketCap"),
                    "Beta": info.get("beta"),
                    "Day High": info.get("dayHigh"),
                    "Day Low": info.get("dayLow"),
                    "52W High": info.get("fiftyTwoWeekHigh"),
                    "52W Low": info.get("fiftyTwoWeekLow"),
                    "Book Value": info.get("bookValue"),
                    "Dividend Yield": info.get("dividendYield"),
                    "P/E Ratio": info.get("trailingPE"),
                    "EPS (TTM)": info.get("trailingEps"),
                    "P/B Ratio": info.get("priceToBook"),
                    "Volume": info.get("volume"),
                    "Avg Volume": info.get("averageVolume"),
                    "Sector": info.get("sector"),
                }

                result[symbol] = {
                    "summary": summary,
                    "price_data": df.to_dict(orient="records")
                }
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


    def run(self, inputs: dict) -> dict:
        period = inputs.get("period", "5d")
        interval = inputs.get("interval", "1d")

        symbols = inputs.get("symbols", [])
        nlp_query = inputs.get("nlp_query")
        csv_content = inputs.get("csv_content")
        pdf_base64 = inputs.get("pdf_content")

        if csv_content:
            symbols += self.extract_from_csv(csv_content)

        if pdf_base64:
            try:
                pdf_bytes = base64.b64decode(pdf_base64)
                symbols += self.extract_from_pdf(pdf_bytes)
            except Exception as e:
                print("Base64 decode error:", e)

        resolved_symbols = [self.resolve_to_symbol(sym) for sym in symbols]
        resolved_symbols = list(set(filter(None, resolved_symbols)))  # Remove None + duplicates

        return self.fetch_data(resolved_symbols, period, interval)
