import base64
from agent import MarketDataAgent

def read_csv(file_path):
    with open(file_path, "r") as f:
        return f.read()

def read_pdf_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

if __name__ == "__main__":
    print("=== Market Data Agent Tester ===")
    mode = input("Choose input mode [manual/csv/pdf]: ").strip()

    agent = MarketDataAgent()

    inputs = {
        "period": "5d",
        "interval": "1d",
    }

    if mode == "manual":
        user_input = input("Enter one or more company names or stock symbols (comma-separated): ").strip()
        if not user_input:
            print("❌ You must enter at least one company name or symbol.")
            exit(1)
            
        # Handles both single and multiple inputs safely
        company_list = [name.strip() for name in user_input.split(",") if name.strip()]
        if not company_list:
            print("❌ No valid company names or symbols detected.")
            exit(1)

        inputs["symbols"] = company_list
    elif mode == "csv":
        path = input("Enter path to CSV file: ").strip()
        inputs["csv_content"] = read_csv(path)

    elif mode == "pdf":
        path = input("Enter path to PDF file: ").strip()
        inputs["pdf_content"] = read_pdf_base64(path)

    else:
        print("❌ Invalid input mode.")
        exit(1)

    print("\n🔍 Running agent...\n")
    result = agent.run(inputs)

    print(result)
    for symbol, data in result.items():
        print(f"\n📈 {symbol}:\n")
        if "error" in data:
            print(f"  ❌ Error: {data['error']}")
        else:
            for row in data[:3]:  # Show first 3 records
                print(f"  {row}")
