import logging
from typing import AsyncGenerator, Dict, List, Any
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai.types import Content, Part
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalyticsAgent(BaseAgent):
    def __init__(self, name="AnalyticsAgent"):
        super().__init__(name=name)
    
    def _extract_stock_data(self, market_data: List) -> Dict:
        """Extract stock data from the nested structure"""
        try:
            if not market_data or not isinstance(market_data, list):
                return {}
            
            stock_entry = market_data[0]
            for symbol, data in stock_entry.items():
                if isinstance(data, dict) and 'summary' in data:
                    return {
                        'symbol': symbol,
                        'data': data['summary'],
                        'price_history': data.get('price_data', [])
                    }
            return {}
        except Exception as e:
            logger.error(f"Error extracting stock data: {e}")
            return {}
    
    def _analyze_technical_indicators(self, stock_data: Dict) -> Dict:
        """Comprehensive technical analysis"""
        try:
            data = stock_data.get('data', {})
            price_history = stock_data.get('price_history', [])
            symbol = stock_data.get('symbol', '')
            
            current_price = data.get('Open', 0)
            previous_close = data.get('Previous Close', 0)
            high_52w = data.get('52W High', 0)
            low_52w = data.get('52W Low', 0)
            volume = data.get('Volume', 0)
            
            # Dynamic volume calculation based on actual symbol
            if price_history:
                volume_key = f'Volume_{symbol}'
                recent_volumes = [day.get(volume_key, 0) for day in price_history[-5:] if day.get(volume_key, 0) > 0]
                avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else volume
            else:
                avg_volume = volume
            
            # Price performance calculations
            change_percent = ((current_price - previous_close) / previous_close) * 100 if previous_close > 0 else 0
            year_high_distance = ((high_52w - current_price) / high_52w) * 100 if high_52w > 0 else 0
            year_low_distance = ((current_price - low_52w) / low_52w) * 100 if low_52w > 0 else 0
            
            # Volume analysis
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1
            volume_signal = "High" if volume_ratio > 1.5 else "Above Average" if volume_ratio > 1.2 else "Normal"
            
            # Trend analysis from recent data using dynamic keys
            if len(price_history) >= 3:
                close_key = f'Close_{symbol}'
                recent_closes = [day.get(close_key, 0) for day in price_history[-3:] if day.get(close_key, 0) > 0]
                if len(recent_closes) >= 3:
                    trend = "Uptrend" if recent_closes[-1] > recent_closes[0] else "Downtrend" if recent_closes[-1] < recent_closes[0] else "Sideways"
                else:
                    trend = "Insufficient data"
            else:
                trend = "Insufficient data"
            
            # Support and resistance levels using dynamic keys
            if price_history:
                high_key = f'High_{symbol}'
                low_key = f'Low_{symbol}'
                recent_highs = [day.get(high_key, 0) for day in price_history[-5:] if day.get(high_key, 0) > 0]
                recent_lows = [day.get(low_key, 0) for day in price_history[-5:] if day.get(low_key, 0) > 0]
                resistance = max(recent_highs) if recent_highs else data.get('High', 0)
                support = min(recent_lows) if recent_lows else data.get('Low', 0)
            else:
                resistance = data.get('High', 0)
                support = data.get('Low', 0)
            
            return {
                "price_change_percent": round(change_percent, 2),
                "momentum": "Bullish" if change_percent > 1 else "Bearish" if change_percent < -1 else "Neutral",
                "year_high_distance": round(year_high_distance, 1),
                "year_low_distance": round(year_low_distance, 1),
                "volume_signal": volume_signal,
                "volume_ratio": round(volume_ratio, 2),
                "trend": trend,
                "support_level": round(support, 2),
                "resistance_level": round(resistance, 2),
                "position_strength": "Strong" if year_low_distance > 50 else "Moderate" if year_low_distance > 20 else "Weak"
            }
        except Exception as e:
            logger.error(f"Error in technical analysis: {e}")
            return {"error": "Technical analysis failed"}
    
    def _analyze_fundamental_metrics(self, stock_data: Dict) -> Dict:
        """Comprehensive fundamental analysis"""
        try:
            data = stock_data.get('data', {})
            
            # Key metrics
            pe_ratio = data.get('P/E Ratio (TTM)', 0)
            forward_pe = data.get('Forward P/E', 0)
            eps = data.get('EPS (TTM)', 0)
            pb_ratio = data.get('P/B Ratio', 0)
            dividend_yield = data.get('Dividend Yield', 0)
            beta = data.get('Beta', 1.0)
            market_cap = data.get('Market Cap (USD)', 0)
            
            # Valuation assessment
            if pe_ratio > 35:
                valuation = "Expensive"
                valuation_score = 2
            elif pe_ratio > 20:
                valuation = "Fair Value"
                valuation_score = 3
            elif pe_ratio > 15:
                valuation = "Attractive"
                valuation_score = 4
            else:
                valuation = "Undervalued"
                valuation_score = 5
            
            # Growth prospects
            growth_outlook = "Strong" if forward_pe < pe_ratio and eps > 10 else "Moderate" if eps > 5 else "Weak"
            
            # Risk assessment
            if beta > 1.3:
                risk_level = "High Volatility"
            elif beta > 1.1:
                risk_level = "Above Market Risk"
            elif beta > 0.9:
                risk_level = "Market Risk"
            else:
                risk_level = "Low Volatility"
            
            # Dividend analysis
            if dividend_yield > 3:
                dividend_rating = "High Yield"
            elif dividend_yield > 1:
                dividend_rating = "Moderate Yield"
            else:
                dividend_rating = "Growth Focus"
            
            # Market cap category
            if market_cap > 1000000000000:  # >$1T
                size_category = "Mega Cap"
                stability_score = 5
            elif market_cap > 200000000000:  # >$200B
                size_category = "Large Cap"
                stability_score = 4
            else:
                size_category = "Mid Cap"
                stability_score = 3
            
            return {
                "pe_ratio": pe_ratio,
                "forward_pe": forward_pe,
                "eps": eps,
                "valuation": valuation,
                "valuation_score": valuation_score,
                "growth_outlook": growth_outlook,
                "risk_level": risk_level,
                "beta": beta,
                "dividend_yield": dividend_yield,
                "dividend_rating": dividend_rating,
                "size_category": size_category,
                "stability_score": stability_score,
                "pb_ratio": pb_ratio
            }
        except Exception as e:
            logger.error(f"Error in fundamental analysis: {e}")
            return {"error": "Fundamental analysis failed"}
    
    def _analyze_news_sentiment(self, news_data: List) -> Dict:
        """Advanced news sentiment analysis"""
        try:
            if not news_data:
                return {"sentiment": "Neutral", "impact": "No recent news"}
            
            # Sentiment keywords
            positive_words = ['growth', 'strong', 'beat', 'profit', 'increase', 'bullish', 'upgrade', 'outperform', 'buy', 'gains']
            negative_words = ['decline', 'loss', 'weak', 'miss', 'decrease', 'bearish', 'downgrade', 'underperform', 'sell', 'falls']
            neutral_words = ['analysis', 'report', 'update', 'position', 'hold']
            
            sentiment_score = 0
            total_articles = len(news_data)
            themes = []
            
            for article in news_data:
                title = article.get('title', '').lower()
                
                # Count sentiment words
                positive_count = sum(1 for word in positive_words if word in title)
                negative_count = sum(1 for word in negative_words if word in title)
                
                if positive_count > negative_count:
                    sentiment_score += 1
                elif negative_count > positive_count:
                    sentiment_score -= 1
                
                # Extract themes
                if any(word in title for word in ['dividend', 'yield']):
                    themes.append('Dividend Focus')
                if any(word in title for word in ['position', 'investment', 'portfolio']):
                    themes.append('Institutional Interest')
                if any(word in title for word in ['competition', 'vs', 'compared']):
                    themes.append('Competitive Analysis')
                if any(word in title for word in ['earnings', 'profit', 'revenue']):
                    themes.append('Financial Performance')
            
            # Overall sentiment
            if sentiment_score > 1:
                overall_sentiment = "Positive"
            elif sentiment_score < -1:
                overall_sentiment = "Negative"
            else:
                overall_sentiment = "Neutral"
            
            return {
                "sentiment": overall_sentiment,
                "sentiment_score": sentiment_score,
                "total_articles": total_articles,
                "key_themes": list(set(themes)),
                "impact": f"{overall_sentiment} sentiment across {total_articles} recent articles"
            }
        except Exception as e:
            logger.error(f"Error in news analysis: {e}")
            return {"sentiment": "Unknown", "impact": "News analysis failed"}
    
    def _generate_investment_recommendations(self, technical: Dict, fundamental: Dict, news: Dict) -> Dict:
        """Generate comprehensive investment recommendations"""
        try:
            # Scoring system (1-5, 5 being best)
            technical_score = 3  # Default neutral
            if technical.get("momentum") == "Bullish" and technical.get("volume_signal") in ["High", "Above Average"]:
                technical_score = 4
            elif technical.get("momentum") == "Bearish":
                technical_score = 2
            
            fundamental_score = fundamental.get("valuation_score", 3)
            stability_score = fundamental.get("stability_score", 3)
            
            news_score = 3  # Default neutral
            if news.get("sentiment") == "Positive":
                news_score = 4
            elif news.get("sentiment") == "Negative":
                news_score = 2
            
            # Overall score
            overall_score = (technical_score + fundamental_score + news_score + stability_score) / 4
            
            # Generate recommendations for different investor types
            recommendations = {}
            
            # Conservative investors
            if stability_score >= 4 and fundamental.get("beta", 1) < 1.2:
                if overall_score >= 3.5:
                    recommendations["conservative"] = {"action": "BUY", "confidence": "High", "rationale": "Stable large-cap with solid fundamentals"}
                else:
                    recommendations["conservative"] = {"action": "HOLD", "confidence": "Medium", "rationale": "Wait for better entry point"}
            else:
                recommendations["conservative"] = {"action": "AVOID", "confidence": "High", "rationale": "Too volatile for conservative approach"}
            
            # Growth investors
            if fundamental.get("growth_outlook") == "Strong" and technical.get("momentum") == "Bullish":
                recommendations["growth"] = {"action": "BUY", "confidence": "High", "rationale": "Strong growth potential with positive momentum"}
            elif overall_score >= 3.2:
                recommendations["growth"] = {"action": "HOLD", "confidence": "Medium", "rationale": "Moderate growth potential"}
            else:
                recommendations["growth"] = {"action": "WAIT", "confidence": "Medium", "rationale": "Limited growth catalysts"}
            
            # Income investors
            dividend_yield = fundamental.get("dividend_yield", 0)
            if dividend_yield > 2:
                recommendations["income"] = {"action": "BUY", "confidence": "High", "rationale": "Attractive dividend yield with stability"}
            elif dividend_yield > 0.5:
                recommendations["income"] = {"action": "CONSIDER", "confidence": "Medium", "rationale": "Modest dividend with growth potential"}
            else:
                recommendations["income"] = {"action": "AVOID", "confidence": "High", "rationale": "Insufficient dividend yield"}
            
            # Overall recommendation
            if overall_score >= 4:
                overall_action = "STRONG BUY"
            elif overall_score >= 3.5:
                overall_action = "BUY"
            elif overall_score >= 2.5:
                overall_action = "HOLD"
            else:
                overall_action = "CONSIDER SELLING"
            
            return {
                "overall_score": round(overall_score, 2),
                "overall_action": overall_action,
                "technical_score": technical_score,
                "fundamental_score": fundamental_score,
                "news_score": news_score,
                "recommendations": recommendations
            }
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {"overall_action": "HOLD", "error": "Recommendation generation failed"}
    
    def _get_sector_info(self, symbol: str) -> str:
        """Get sector information based on stock symbol"""
        # Common sector mappings - can be expanded or made dynamic
        sector_map = {
            'MSFT': 'Technology',
            'AAPL': 'Technology', 
            'GOOGL': 'Technology',
            'AMZN': 'Consumer Discretionary',
            'TSLA': 'Consumer Discretionary',
            'JPM': 'Financial Services',
            'JNJ': 'Healthcare',
            'PG': 'Consumer Staples',
            'XOM': 'Energy',
            'KO': 'Consumer Staples'
        }
        return sector_map.get(symbol, 'General Market')
    
    def _generate_comprehensive_report(self, symbol: str, technical: Dict, fundamental: Dict, news: Dict, recommendations: Dict) -> str:
        """Generate a comprehensive 1-page analysis report"""
        
        sector = self._get_sector_info(symbol)
        
        # Header
        report = f"""
🏢 **COMPREHENSIVE STOCK ANALYSIS REPORT**
═══════════════════════════════════════════════

**Stock:** {symbol} | **Sector:** {sector} | **Analysis Date:** {datetime.now().strftime('%Y-%m-%d')}
**Overall Rating:** {recommendations.get('overall_action', 'HOLD')} | **Score:** {recommendations.get('overall_score', 0)}/5.0

"""
        
        # Executive Summary
        report += f"""
📊 **EXECUTIVE SUMMARY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{symbol} shows {technical.get('momentum', 'neutral')} momentum with {fundamental.get('valuation', 'fair')} valuation.
Current price action indicates {technical.get('trend', 'sideways')} trend with {news.get('sentiment', 'neutral')} market sentiment.
The stock is positioned {technical.get('position_strength', 'moderately')} within its 52-week range.

"""
        
        # Technical Analysis Section
        report += f"""
📈 **TECHNICAL ANALYSIS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• **Price Movement:** {technical.get('price_change_percent', 0):+.2f}% ({technical.get('momentum', 'Neutral')})
• **Volume Analysis:** {technical.get('volume_signal', 'Normal')} ({technical.get('volume_ratio', 1):.2f}x average)
• **Trend Direction:** {technical.get('trend', 'Unknown')}
• **Support Level:** ${technical.get('support_level', 'N/A')}
• **Resistance Level:** ${technical.get('resistance_level', 'N/A')}
• **52W Position:** {technical.get('year_low_distance', 0):.1f}% above yearly low, {technical.get('year_high_distance', 0):.1f}% below yearly high
• **Technical Strength:** {technical.get('position_strength', 'Moderate')}

"""
        
        # Fundamental Analysis Section
        report += f"""
💼 **FUNDAMENTAL ANALYSIS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• **Valuation:** {fundamental.get('valuation', 'Unknown')} (P/E: {fundamental.get('pe_ratio', 'N/A')})
• **Forward P/E:** {fundamental.get('forward_pe', 'N/A')} (Growth outlook: {fundamental.get('growth_outlook', 'Unknown')})
• **Earnings Power:** ${fundamental.get('eps', 'N/A')} EPS (TTM)
• **Dividend Profile:** {fundamental.get('dividend_rating', 'Unknown')} ({fundamental.get('dividend_yield', 0):.1f}% yield)
• **Risk Level:** {fundamental.get('risk_level', 'Unknown')} (Beta: {fundamental.get('beta', 'N/A')})
• **Market Position:** {fundamental.get('size_category', 'Unknown')} company
• **Book Value:** P/B Ratio of {fundamental.get('pb_ratio', 'N/A')}

"""
        
        # News & Sentiment Section
        report += f"""
📰 **NEWS & MARKET SENTIMENT**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• **Overall Sentiment:** {news.get('sentiment', 'Unknown')} ({news.get('total_articles', 0)} recent articles analyzed)
• **Key Themes:** {', '.join(news.get('key_themes', ['None identified']))}
• **Market Impact:** {news.get('impact', 'Unknown')}
• **Sentiment Score:** {news.get('sentiment_score', 0):+d}/±{news.get('total_articles', 0)}

"""
        
        # Investment Recommendations Section
        report += f"""
🎯 **INVESTMENT RECOMMENDATIONS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        for investor_type, rec in recommendations.get('recommendations', {}).items():
            report += f"• **{investor_type.title()} Investors:** {rec.get('action', 'HOLD')} (Confidence: {rec.get('confidence', 'Medium')})\n"
            report += f"  Rationale: {rec.get('rationale', 'Standard market conditions')}\n\n"
        
        # Risk Factors & Key Levels
        report += f"""
⚠️ **KEY RISK FACTORS & LEVELS TO WATCH**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• **Stop Loss Level:** Below ${technical.get('support_level', 'N/A')} (Support break)
• **Profit Target:** Above ${technical.get('resistance_level', 'N/A')} (Resistance break)
• **Volatility Risk:** {fundamental.get('risk_level', 'Unknown')} based on Beta {fundamental.get('beta', 'N/A')}
• **Valuation Risk:** {fundamental.get('valuation', 'Unknown')} at current P/E levels
• **Volume Confirmation:** Watch for {technical.get('volume_signal', 'normal')} volume continuation

"""
        
        # Final Score Breakdown
        report += f"""
📋 **ANALYSIS SCORE BREAKDOWN**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Technical Score: {recommendations.get('technical_score', 0)}/5 ⭐
• Fundamental Score: {recommendations.get('fundamental_score', 0)}/5 ⭐
• News Sentiment: {recommendations.get('news_score', 0)}/5 ⭐
• **Overall Rating: {recommendations.get('overall_score', 0)}/5.0 ⭐**

**Final Recommendation: {recommendations.get('overall_action', 'HOLD')}**

═══════════════════════════════════════════════
*Disclaimer: This analysis is for informational purposes only and should not be considered as financial advice. 
Please consult with a financial advisor before making investment decisions.*
        """
        
        return report.strip()
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        try:
            # Get data from session state
            market_data = ctx.session.state.get("market_data", [])
            news_data = ctx.session.state.get("news_analysis", [])
            
            logger.info(f"Processing comprehensive analysis for {len(market_data)} stocks")
            
            # Extract stock data
            stock_data = self._extract_stock_data(market_data)
            
            if not stock_data:
                yield Event(
                    author="agent",
                    content=Content(parts=[Part(text="❌ No valid stock data found for comprehensive analysis.")])
                )
                return
            
            # Perform comprehensive analysis
            technical_analysis = self._analyze_technical_indicators(stock_data)
            fundamental_analysis = self._analyze_fundamental_metrics(stock_data)
            news_analysis = self._analyze_news_sentiment(news_data)
            recommendations = self._generate_investment_recommendations(technical_analysis, fundamental_analysis, news_analysis)
            
            # Generate comprehensive report
            comprehensive_report = self._generate_comprehensive_report(
                stock_data.get('symbol', 'Unknown'),
                technical_analysis,
                fundamental_analysis,
                news_analysis,
                recommendations
            )
            
            # Store comprehensive insights
            ctx.session.state["stock_insights"] = {
                "symbol": stock_data.get('symbol', 'Unknown'),
                "technical_analysis": technical_analysis,
                "fundamental_analysis": fundamental_analysis,
                "news_analysis": news_analysis,
                "recommendations": recommendations,
                "comprehensive_report": comprehensive_report,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # Send the comprehensive report
            yield Event(
                author="agent",
                content=Content(parts=[Part(text=comprehensive_report)])
            )
            
        except Exception as e:
            logger.error(f"Error in comprehensive analytics: {e}")
            yield Event(
                author="agent",
                content=Content(parts=[Part(text=f"❌ Comprehensive analysis failed: {str(e)}")])
            )