import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from main import StockAnalysisAgent
import pandas as pd


st.set_page_config(
    page_title="Stock Analysis Agent",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'agent' not in st.session_state:
    try:
        st.session_state.agent = StockAnalysisAgent()
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        st.stop()

# Main title
st.title("📈 Stock Analysis Agent")
st.subheader("Powered by Google Gemini AI")

# Sidebar for inputs
st.sidebar.header("Analysis Parameters")

# Input fields
ticker_input = st.sidebar.text_input(
    "Stock Ticker Symbol", 
    placeholder="e.g., AAPL, GOOGL, TSLA",
    help="Enter the stock ticker symbol you want to analyze"
)

days_input = st.sidebar.number_input(
    "Number of Days", 
    min_value=1, 
    max_value=365, 
    value=30,
    help="Number of days to analyze (1-365)"
)

analyze_button = st.sidebar.button("🔍 Analyze Stock", type="primary")

# Main content area
if analyze_button and ticker_input:
    ticker_input = ticker_input.upper().strip()
    
    # Create columns for better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"Analysis for {ticker_input}")
        
        # Show loading spinner
        with st.spinner(f"Analyzing {ticker_input} for the last {days_input} days..."):
            # Fetch stock data first
            stock_data, error = st.session_state.agent.analyzer.fetch_stock_data(ticker_input, days_input)
            
            if error:
                st.error(f"Error fetching data: {error}")
            else:
                # Display stock chart
                st.subheader("📊 Price Chart")
                
                fig = go.Figure()
                
                # Add candlestick chart
                fig.add_trace(go.Candlestick(
                    x=stock_data.index,
                    open=stock_data['Open'],
                    high=stock_data['High'],
                    low=stock_data['Low'],
                    close=stock_data['Close'],
                    name=ticker_input
                ))
                
                # Add moving averages if available
                if len(stock_data) >= 5:
                    ma_5 = stock_data['Close'].rolling(window=5).mean()
                    fig.add_trace(go.Scatter(
                        x=stock_data.index,
                        y=ma_5,
                        mode='lines',
                        name='5-day MA',
                        line=dict(color='orange', width=2)
                    ))
                
                if len(stock_data) >= 20:
                    ma_20 = stock_data['Close'].rolling(window=20).mean()
                    fig.add_trace(go.Scatter(
                        x=stock_data.index,
                        y=ma_20,
                        mode='lines',
                        name='20-day MA',
                        line=dict(color='red', width=2)
                    ))
                
                fig.update_layout(
                    title=f"{ticker_input} Stock Price",
                    xaxis_title="Date",
                    yaxis_title="Price ($)",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Generate AI analysis
                st.subheader("🤖 AI Analysis")
                with st.spinner("Generating AI-powered analysis..."):
                    analysis = st.session_state.agent.analyze_stock(ticker_input, days_input)
                    st.markdown(analysis)
    
    with col2:
        if not error and stock_data is not None:
            # Display key metrics
            st.subheader("📊 Key Metrics")
            
            indicators = st.session_state.agent.analyzer.calculate_technical_indicators()
            stock_info = st.session_state.agent.analyzer.get_stock_info()
            
            # Create metrics display
            st.metric(
                "Current Price", 
                f"${indicators['current_price']}", 
                delta=f"{indicators['price_change_pct']:.2f}%"
            )
            
            if indicators.get('rsi'):
                st.metric("RSI (14-day)", f"{indicators['rsi']:.2f}")
            
            st.metric("Volatility", f"{indicators['volatility']:.2f}%")
            
            if indicators.get('ma_20'):
                st.metric("20-day MA", f"${indicators['ma_20']}")
            
            # Company info
            st.subheader("🏢 Company Info")
            if stock_info.get('company_name', 'N/A') != 'N/A':
                st.write(f"**Company:** {stock_info['company_name']}")
            if stock_info.get('sector', 'N/A') != 'N/A':
                st.write(f"**Sector:** {stock_info['sector']}")
            if stock_info.get('industry', 'N/A') != 'N/A':
                st.write(f"**Industry:** {stock_info['industry']}")
            
            # Volume chart
            st.subheader("📈 Volume")
            volume_fig = px.bar(
                x=stock_data.index, 
                y=stock_data['Volume'], 
                title="Trading Volume"
            )
            volume_fig.update_layout(height=300)
            st.plotly_chart(volume_fig, use_container_width=True)

# Instructions
elif not ticker_input:
    st.info("👈 Please enter a stock ticker symbol in the sidebar to get started!")
    
    st.markdown("""
    ## How to Use This Tool
    
    1. **Enter Stock Symbol**: Type the ticker symbol (e.g., AAPL, GOOGL, TSLA) in the sidebar
    2. **Select Time Period**: Choose how many days you want to analyze (1-365 days)
    3. **Click Analyze**: Hit the "Analyze Stock" button to generate your report
    
    ## Features
    
    - 📊 **Interactive Charts**: Candlestick charts with moving averages
    - 🤖 **AI Analysis**: Comprehensive analysis powered by Google Gemini
    - 📈 **Technical Indicators**: RSI, Moving averages, Volatility metrics
    - 📋 **Company Information**: Sector, industry, and key financial metrics
    - 📊 **Volume Analysis**: Trading volume patterns and trends
    
    ## Sample Tickers to Try
    
    - **AAPL** - Apple Inc.
    - **GOOGL** - Alphabet Inc.
    - **MSFT** - Microsoft Corporation
    - **TSLA** - Tesla Inc.
    - **AMZN** - Amazon.com Inc.
    - **NVDA** - NVIDIA Corporation
    """)

# Footer
st.markdown("---")
st.markdown("**Disclaimer:** This analysis is for informational purposes only and should not be considered as financial advice. Please consult with a financial advisor before making investment decisions.")