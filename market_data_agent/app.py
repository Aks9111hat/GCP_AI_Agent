import asyncio
import base64
from agent import MarketDataAgent

def read_csv(file_path):
    with open(file_path, "r") as f:
        return f.read()

def read_pdf_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

async def main():
    print("=== 📈 Market Data Agent Tester ===")
    mode = input("Choose input mode [manual/csv/pdf]: ").strip()

    agent = MarketDataAgent()

    inputs = {
        "period": "5d",       # You can change this to "1mo", "3mo", etc.
        "interval": "1d",     # Daily data. Use "1h" for hourly, etc.
    }

    if mode == "manual":
        user_input = input("Enter one or more company names or stock symbols (comma-separated): ").strip()
        if not user_input:
            print("❌ You must enter at least one company name or symbol.")
            return
            
        company_list = [name.strip() for name in user_input.split(",") if name.strip()]
        if not company_list:
            print("❌ No valid company names or symbols detected.")
            return

        inputs["symbols"] = company_list

    elif mode == "csv":
        path = input("Enter path to CSV file: ").strip()
        inputs["csv_content"] = read_csv(path)

    elif mode == "pdf":
        path = input("Enter path to PDF file: ").strip()
        inputs["pdf_content"] = read_pdf_base64(path)

    else:
        print("❌ Invalid input mode.")
        return

    print("\n🔍 Running MarketDataAgent...\n")
    result = await agent.run(inputs)

    for symbol, data in result.items():
        print(f"\n📈 Symbol: {symbol}\n")
        if "error" in data:
            print(f"  ❌ Error fetching data: {data['error']}")
        else:
            print("  📊 Summary (based on historical data):")
            print("     - Derived from the downloaded historical stock prices")
            print("     - Period selected:", inputs["period"])
            print("     - Interval selected:", inputs["interval"])
            for k, v in data["summary"].items():
                print(f"    • {k}: {v}")

            print("\n  📅 Price Data (Raw historical prices):")
            print("     - Each row is a price record (Open, High, Low, Close, Volume) for a date")
            print("     - Showing first 3 rows only:\n")
            for row in data["price_data"][:3]:
                print(f"    - {row}")

if __name__ == "__main__":
    asyncio.run(main())
