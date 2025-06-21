import os
import google.generativeai as genai
from stock_analyzer import StockAnalyzer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StockAnalysisAgent:
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Initialize stock analyzer
        self.analyzer = StockAnalyzer()
    
    def analyze_stock(self, ticker_symbol, days):
        """Main function to analyze stock and generate AI-powered insights"""
        print(f"📊 Analyzing {ticker_symbol.upper()} for the last {days} days...")
        print("-" * 50)
        
        # Fetch stock data
        stock_data, error = self.analyzer.fetch_stock_data(ticker_symbol, days)
        
        if error:
            return f"❌ Error: {error}"
        
        # Generate summary data for AI analysis
        summary_data = self.analyzer.generate_summary_data()
        
        if not summary_data:
            return "❌ Error: Could not generate analysis data"
        
        # Create AI prompt for analysis
        prompt = f"""
You are a professional stock analyst. Based on the following stock data, provide a comprehensive analysis including:

1. **Executive Summary** - Brief overview of the stock's performance
2. **Technical Analysis** - Analysis of price trends, moving averages, RSI, and support/resistance levels
3. **Risk Assessment** - Volatility analysis and potential risks
4. **Market Position** - How the stock is positioned in its sector/industry
5. **Key Insights** - Important observations and patterns
6. **Investment Perspective** - Potential outlook (but not direct buy/sell advice)

Please provide a well-structured, professional analysis that is informative and easy to understand.

Stock Data:
{summary_data}

Important: This analysis is for informational purposes only and should not be considered as financial advice.
"""
        
        try:
            # Generate AI analysis
            print("🤖 Generating AI-powered analysis...")
            response = self.model.generate_content(prompt)
            
            # Format and return the analysis
            analysis = f"""
{'='*60}
STOCK ANALYSIS REPORT: {ticker_symbol.upper()}
{'='*60}

{response.text}

{'='*60}
Analysis generated using Gemini AI
Disclaimer: This analysis is for informational purposes only.
Not financial advice. Please consult with a financial advisor.
{'='*60}
"""
            return analysis
            
        except Exception as e:
            return f"❌ Error generating AI analysis: {str(e)}"
    
    def run_interactive_mode(self):
        """Run the agent in interactive mode"""
        print("🚀 Welcome to the Stock Analysis Agent!")
        print("Powered by Google Gemini AI")
        print("-" * 40)
        
        while True:
            try:
                # Get user input
                print("\n📈 Stock Analysis Request")
                ticker = input("Enter stock ticker symbol (or 'quit' to exit): ").strip()
                
                if ticker.lower() == 'quit':
                    print("👋 Thank you for using Stock Analysis Agent!")
                    break
                
                if not ticker:
                    print("❌ Please enter a valid ticker symbol")
                    continue
                
                days_input = input("Enter number of days for analysis (default: 30): ").strip()
                
                try:
                    days = int(days_input) if days_input else 30
                    if days <= 0 or days > 365:
                        print("❌ Please enter a number between 1 and 365")
                        continue
                except ValueError:
                    print("❌ Please enter a valid number")
                    continue
                
                # Perform analysis
                result = self.analyze_stock(ticker, days)
                print(result)
                
                # Ask if user wants to continue
                continue_choice = input("\nWould you like to analyze another stock? (y/n): ").strip().lower()
                if continue_choice != 'y':
                    print("👋 Thank you for using Stock Analysis Agent!")
                    break
                    
            except KeyboardInterrupt:
                print("\n👋 Thank you for using Stock Analysis Agent!")
                break
            except Exception as e:
                print(f"❌ An error occurred: {str(e)}")

def main():
    """Main function to run the stock analysis agent"""
    try:
        agent = StockAnalysisAgent()
        agent.run_interactive_mode()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please make sure you have set up your GEMINI_API_KEY in the .env file")
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")

if __name__ == "__main__":
    main()