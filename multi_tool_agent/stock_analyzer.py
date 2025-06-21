import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import warnings
warnings.filterwarnings('ignore')

class StockAnalyzer:
    def __init__(self):
        self.stock_data = None
        self.ticker = None
    
    def fetch_stock_data(self, ticker_symbol, days):
        """Fetch stock data for given ticker and number of days"""
        try:
            self.ticker = ticker_symbol.upper()
            
            # Calculate start date
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Fetch data using yfinance
            stock = yf.Ticker(self.ticker)
            self.stock_data = stock.history(start=start_date, end=end_date)
            
            if self.stock_data.empty:
                return None, f"No data found for ticker {self.ticker}"
            
            return self.stock_data, None
            
        except Exception as e:
            return None, f"Error fetching data: {str(e)}"
    
    def calculate_technical_indicators(self):
        """Calculate various technical indicators"""
        if self.stock_data is None or self.stock_data.empty:
            return {}
        
        df = self.stock_data.copy()
        
        # Basic statistics
        current_price = df['Close'].iloc[-1]
        price_change = df['Close'].iloc[-1] - df['Close'].iloc[0]
        price_change_pct = (price_change / df['Close'].iloc[0]) * 100
        
        # Moving averages
        df['MA_5'] = df['Close'].rolling(window=5).mean()
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        df['MA_50'] = df['Close'].rolling(window=min(50, len(df))).mean()
        
        # RSI calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if not rsi.empty else None
        
        # Volatility
        volatility = df['Close'].pct_change().std() * np.sqrt(252) * 100
        
        # Volume analysis
        avg_volume = df['Volume'].mean()
        current_volume = df['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Support and Resistance (simplified)
        recent_high = df['High'].tail(20).max()
        recent_low = df['Low'].tail(20).min()
        
        indicators = {
            'current_price': round(current_price, 2),
            'price_change': round(price_change, 2),
            'price_change_pct': round(price_change_pct, 2),
            'ma_5': round(df['MA_5'].iloc[-1], 2) if not pd.isna(df['MA_5'].iloc[-1]) else None,
            'ma_20': round(df['MA_20'].iloc[-1], 2) if not pd.isna(df['MA_20'].iloc[-1]) else None,
            'ma_50': round(df['MA_50'].iloc[-1], 2) if not pd.isna(df['MA_50'].iloc[-1]) else None,
            'rsi': round(current_rsi, 2) if current_rsi and not pd.isna(current_rsi) else None,
            'volatility': round(volatility, 2),
            'volume_ratio': round(volume_ratio, 2),
            'recent_high': round(recent_high, 2),
            'recent_low': round(recent_low, 2),
            'total_days': len(df)
        }
        
        return indicators
    
    def get_stock_info(self):
        """Get basic stock information"""
        try:
            stock = yf.Ticker(self.ticker)
            info = stock.info
            
            return {
                'company_name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A')
            }
        except:
            return {}
    
    def generate_summary_data(self):
        """Generate a comprehensive summary for AI analysis"""
        if self.stock_data is None:
            return None
        
        indicators = self.calculate_technical_indicators()
        stock_info = self.get_stock_info()
        
        # Create a text summary of recent price action
        recent_data = self.stock_data.tail(5)
        price_trend = "upward" if indicators['price_change'] > 0 else "downward"
        
        summary = f"""
Stock Analysis Data for {self.ticker}:

Company Information:
- Name: {stock_info.get('company_name', 'N/A')}
- Sector: {stock_info.get('sector', 'N/A')}
- Industry: {stock_info.get('industry', 'N/A')}

Price Analysis ({indicators['total_days']} days):
- Current Price: ${indicators['current_price']}
- Price Change: ${indicators['price_change']} ({indicators['price_change_pct']:.2f}%)
- Overall Trend: {price_trend}

Technical Indicators:
- 5-day Moving Average: ${indicators.get('ma_5', 'N/A')}
- 20-day Moving Average: ${indicators.get('ma_20', 'N/A')}
- 50-day Moving Average: ${indicators.get('ma_50', 'N/A')}
- RSI (14-day): {indicators.get('rsi', 'N/A')}
- Volatility (Annualized): {indicators['volatility']:.2f}%

Support/Resistance Levels:
- Recent High (20-day): ${indicators['recent_high']}
- Recent Low (20-day): ${indicators['recent_low']}

Volume Analysis:
- Current Volume Ratio: {indicators['volume_ratio']:.2f}x average

Recent Price Action (Last 5 days):
"""
        
        for i, (date, row) in enumerate(recent_data.iterrows()):
            summary += f"Day {i+1}: Open ${row['Open']:.2f}, Close ${row['Close']:.2f}, Volume {row['Volume']:,.0f}\n"
        
        return summary