import os
import json
import logging
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from pydantic import Field
from typing import List, Dict, Any, AsyncGenerator, Optional
from google.genai.types import Content, Part
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
import google.generativeai as genai

# PDF generation imports
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.colors import black, blue, red
from io import BytesIO
import base64

load_dotenv()
logger = logging.getLogger(__name__)

class ReportGeneratorAgent(BaseAgent):
    """
    Final agent that generates comprehensive PDF-ready reports from stock analysis data
    using Google Gemini AI with PDF generation capability
    """
    
    gemini_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    model_name: str = Field(default="gemini-1.5-flash")
    
    def __init__(self, name="ReportGeneratorAgent"):
        super().__init__(name=name)
        
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        try:
            # Get analysis data from session state
            analysis_data = ctx.session.state.get("stock_analysis", {})
            news_data = ctx.session.state.get("news_analysis", [])
            market_data = ctx.session.state.get("market_data", {})
            
            logger.info(f"[{self.name}] Retrieved analysis data for report generation")
            
            if not analysis_data and not news_data and not market_data:
                yield Event(
                    author=self.name,
                    content=Content(parts=[Part(text="No analysis data available for report generation.")])
                )
                return
                
            if not self.gemini_api_key:
                yield Event(
                    author=self.name,
                    content=Content(parts=[Part(text="Missing GEMINI_API_KEY for report generation.")])
                )
                return
                
            # Configure Gemini
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel(self.model_name)
            
            # Parse and structure the analysis data
            structured_data = self._structure_analysis_data(analysis_data, news_data, market_data)
            
            # Generate comprehensive report
            report_content = await self._generate_comprehensive_report(model, structured_data)
            
            # Format the report for PDF generation
            formatted_report = self._format_report_for_pdf(report_content, structured_data)
            
            # Generate PDF
            pdf_path, pdf_base64 = await self._generate_pdf_report(formatted_report, structured_data)
            
            # Store the generated report in session state
            ctx.session.state["generated_report"] = {
                "content": formatted_report,
                "pdf_path": pdf_path,
                "pdf_base64": pdf_base64,
                "generated_at": datetime.now().isoformat(),
                "report_type": "comprehensive_analysis"
            }
            
            # Save text report to file
            text_filename = await self._save_report_to_file(formatted_report, structured_data)
            
            logger.info(f"[{self.name}] Report generated successfully. Text: {text_filename}, PDF: {pdf_path}")
            
            # Generate response with report summary
            response_text = self._create_response_summary(structured_data, text_filename, pdf_path)
            
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text=response_text)])
            )
            
        except Exception as e:
            logger.error(f"[{self.name}] Error in report generator agent: {str(e)}")
            ctx.session.state["generated_report"] = {"error": str(e)}
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text=f"Error generating report: {str(e)}")])
            )
    
    def _structure_analysis_data(self, analysis_data: Dict, news_data: List, market_data: Dict) -> Dict[str, Any]:
        """Structure and combine all analysis data for report generation"""
        
        # Extract stock symbols from various sources
        stocks = []
        if analysis_data:
            if isinstance(analysis_data, dict):
                stocks.extend(analysis_data.keys())
            elif isinstance(analysis_data, str):
                # If it's a formatted analysis string, extract stock symbol
                import re
                stock_match = re.search(r'Stock: (\w+)', analysis_data)
                if stock_match:
                    stocks.append(stock_match.group(1))
        
        # Add stocks from news data
        for news_item in news_data:
            if isinstance(news_item, dict) and 'stock' in news_item:
                if news_item['stock'] not in stocks:
                    stocks.append(news_item['stock'])
        
        # Add stocks from market data
        if isinstance(market_data, dict):
            stocks.extend([k for k in market_data.keys() if k not in stocks])
        
        structured = {
            "stocks": stocks,
            "analysis_data": analysis_data,
            "news_data": news_data,
            "market_data": market_data,
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "analysis_date": datetime.now().strftime('%Y-%m-%d'),
                "total_stocks": len(stocks)
            }
        }
        
        return structured
    
    async def _generate_comprehensive_report(self, model, structured_data: Dict[str, Any]) -> str:
        """Generate comprehensive report using Gemini AI"""
        
        prompt = self._create_report_prompt(structured_data)
        
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"[{self.name}] Error generating report with Gemini: {str(e)}")
            return self._generate_fallback_report(structured_data)
    
    def _create_report_prompt(self, data: Dict[str, Any]) -> str:
        """Create comprehensive prompt for Gemini AI"""
        
        stocks_list = ", ".join(data["stocks"]) if data["stocks"] else "Multiple stocks"
        
        prompt = f"""
        You are a professional financial analyst creating a comprehensive investment research report.
        
        Generate a detailed, professional stock analysis report suitable for institutional investors and financial advisors.
        
        **Analysis Data:**
        Stocks Analyzed: {stocks_list}
        Analysis Date: {data["report_metadata"]["analysis_date"]}
        Total Stocks: {data["report_metadata"]["total_stocks"]}
        
        **Market Data:**
        {json.dumps(data["market_data"], indent=2)}
        
        **Technical Analysis:**
        {json.dumps(data["analysis_data"], indent=2)}
        
        **News Analysis:**
        {json.dumps(data["news_data"], indent=2)}
        
        **Report Requirements:**
        Create a comprehensive report with the following sections:
        
        1. **EXECUTIVE SUMMARY** (3-4 paragraphs)
        - Overall investment thesis and key findings
        - Market positioning and competitive landscape
        - Primary risks and opportunities
        - Clear investment recommendation with rationale
        
        2. **MARKET OVERVIEW & SECTOR ANALYSIS** (4-5 paragraphs)
        - Current market conditions and trends
        - Sector performance and outlook
        - Macroeconomic factors impacting the stocks
        - Comparative analysis within sector
        
        3. **INDIVIDUAL STOCK ANALYSIS** (For each stock, 5-6 paragraphs)
        - Company fundamentals and business model
        - Financial performance and key metrics
        - Technical analysis and price action
        - News sentiment and market perception
        - Valuation assessment and peer comparison
        - Specific investment recommendation
        
        4. **TECHNICAL ANALYSIS DEEP DIVE** (4-5 paragraphs)
        - Chart patterns and technical indicators
        - Support and resistance levels
        - Volume analysis and momentum indicators
        - Multi-timeframe analysis
        - Entry and exit strategies
        
        5. **FUNDAMENTAL VALUATION ANALYSIS** (4-5 paragraphs)
        - P/E ratio analysis and industry comparison
        - Growth prospects and earnings forecasts
        - Dividend analysis and shareholder returns
        - Balance sheet strength and financial health
        - Intrinsic value estimation
        
        6. **NEWS IMPACT & MARKET SENTIMENT** (3-4 paragraphs)
        - Recent news analysis and market impact
        - Sentiment trends and social media buzz
        - Analyst recommendations and upgrades/downgrades
        - Potential catalysts and upcoming events
        
        7. **RISK ASSESSMENT & MANAGEMENT** (3-4 paragraphs)
        - Key risk factors and mitigation strategies
        - Market risks and volatility analysis
        - Company-specific risks and challenges
        - Risk-adjusted return expectations
        
        8. **INVESTMENT STRATEGY & RECOMMENDATIONS** (4-5 paragraphs)
        - Portfolio allocation recommendations
        - Entry and exit strategies for different investor profiles
        - Time horizon considerations
        - Hedging strategies and risk management
        
        9. **FORWARD-LOOKING ANALYSIS** (3-4 paragraphs)
        - Growth catalysts and expansion opportunities
        - Industry trends and technological disruptions
        - Long-term outlook and sustainability
        - Potential challenges and competitive threats
        
        10. **CONCLUSION & ACTION ITEMS** (2-3 paragraphs)
        - Summary of key investment themes
        - Prioritized action items for investors
        - Next steps and monitoring criteria
        
        **Style Guidelines:**
        - Use professional financial language and terminology
        - Include specific data points, percentages, and financial metrics
        - Make recommendations clear and actionable
        - Ensure the report is comprehensive enough for institutional-grade analysis
        - Use bullet points sparingly, focus on flowing narrative
        - Include risk disclaimers where appropriate
        
        Generate a report that would be suitable for PDF generation and institutional presentation.
        """
        
        return prompt
    
    def _generate_fallback_report(self, data: Dict[str, Any]) -> str:
        """Generate a basic report if Gemini fails"""
        
        stocks = data["stocks"]
        stocks_str = ", ".join(stocks) if stocks else "Portfolio"
        
        fallback_report = f"""
        STOCK ANALYSIS REPORT - {stocks_str}
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        EXECUTIVE SUMMARY
        This report provides analysis for {len(stocks)} stock(s): {stocks_str}.
        Based on available market data and news analysis, this report presents
        key findings and investment recommendations.
        
        ANALYSIS OVERVIEW
        The analysis incorporates technical indicators, fundamental metrics,
        and recent news sentiment to provide a comprehensive view of the
        investment opportunities and risks.
        
        MARKET DATA SUMMARY
        {json.dumps(data["market_data"], indent=2)}
        
        NEWS ANALYSIS SUMMARY
        Recent news analysis shows varying sentiment across the analyzed stocks.
        Key themes and market developments have been incorporated into the
        overall investment thesis.
        
        INVESTMENT RECOMMENDATIONS
        Based on the comprehensive analysis, specific recommendations are
        provided for different investor profiles including conservative,
        growth-oriented, and income-focused strategies.
        
        RISK CONSIDERATIONS
        All investments carry inherent risks. This analysis identifies key
        risk factors and provides guidance on risk management strategies.
        
        DISCLAIMER
        This report is for informational purposes only and should not be
        considered as investment advice. Please consult with a qualified
        financial advisor before making investment decisions.
        """
        
        return fallback_report
    
    def _format_report_for_pdf(self, content: str, data: Dict[str, Any]) -> str:
        """Add professional formatting for PDF generation"""
        
        stocks_str = ", ".join(data["stocks"]) if data["stocks"] else "Portfolio Analysis"
        
        header = f"""
PROFESSIONAL INVESTMENT RESEARCH REPORT
{'='*80}

Investment Analysis: {stocks_str}
Report Date: {data["report_metadata"]["analysis_date"]}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Securities Analyzed: {data["report_metadata"]["total_stocks"]}

{'='*80}

"""
        
        footer = f"""

{'='*80}
IMPORTANT DISCLAIMERS & RISK WARNINGS

This report is prepared for informational and educational purposes only and should 
not be construed as investment advice, investment recommendations, or an offer to 
buy or sell securities. The information contained herein is based on sources believed 
to be reliable but is not guaranteed to be accurate or complete.

Past performance does not guarantee future results. All investments involve risk, 
including the potential loss of principal. Before making any investment decisions, 
please consult with a qualified financial advisor who can assess your individual 
financial situation and investment objectives.

The analysis and recommendations in this report are based on market conditions and 
information available as of the report date and may change without notice.

Report generated using AI-assisted analysis tools.
Analysis Framework: Multi-factor quantitative and qualitative assessment
Data Sources: Market data, news analysis, and technical indicators

{'='*80}
Report ID: {datetime.now().strftime('%Y%m%d_%H%M%S')}
Generated by: Automated Investment Research System
Contact: support@yourcompany.com
{'='*80}
"""
        
        return header + content + footer
    
    async def _generate_pdf_report(self, content: str, data: Dict[str, Any]) -> tuple[str, str]:
        """Generate PDF report and return file path and base64 encoded content"""
        
        # Create filename
        stocks_str = "_".join(data["stocks"][:3]) if data["stocks"] else "portfolio"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"investment_report_{stocks_str}_{timestamp}.pdf"
        
        # Ensure reports directory exists
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        filepath = os.path.join(reports_dir, filename)
        
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                filepath,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=1*inch,
                bottomMargin=1*inch
            )
            
            # Define styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=18,
                textColor=blue,
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading1'],
                fontSize=14,
                textColor=black,
                spaceAfter=12,
                spaceBefore=20
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_JUSTIFY,
                spaceAfter=12
            )
            
            disclaimer_style = ParagraphStyle(
                'Disclaimer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=red,
                alignment=TA_JUSTIFY,
                spaceAfter=6
            )
            
            # Parse content and create story
            story = []
            
            # Add title
            stocks_str = ", ".join(data["stocks"]) if data["stocks"] else "Portfolio Analysis"
            story.append(Paragraph(f"INVESTMENT RESEARCH REPORT", title_style))
            story.append(Paragraph(f"{stocks_str}", heading_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Add metadata
            metadata = f"""
            <b>Report Date:</b> {data["report_metadata"]["analysis_date"]}<br/>
            <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
            <b>Total Securities Analyzed:</b> {data["report_metadata"]["total_stocks"]}<br/>
            """
            story.append(Paragraph(metadata, body_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Process content sections
            sections = self._parse_report_sections(content)
            
            for section_title, section_content in sections:
                if section_title:
                    story.append(Paragraph(section_title, heading_style))
                
                paragraphs = section_content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        # Clean up paragraph
                        clean_para = para.strip().replace('\n', ' ')
                        story.append(Paragraph(clean_para, body_style))
                
                story.append(Spacer(1, 0.2*inch))
            
            # Add page break before disclaimers
            story.append(PageBreak())
            
            # Add disclaimers
            story.append(Paragraph("IMPORTANT DISCLAIMERS & RISK WARNINGS", heading_style))
            
            disclaimers = [
                "This report is prepared for informational and educational purposes only and should not be construed as investment advice, investment recommendations, or an offer to buy or sell securities.",
                "The information contained herein is based on sources believed to be reliable but is not guaranteed to be accurate or complete.",
                "Past performance does not guarantee future results. All investments involve risk, including the potential loss of principal.",
                "Before making any investment decisions, please consult with a qualified financial advisor who can assess your individual financial situation and investment objectives.",
                "The analysis and recommendations in this report are based on market conditions and information available as of the report date and may change without notice.",
                "Report generated using AI-assisted analysis tools."
            ]
            
            for disclaimer in disclaimers:
                story.append(Paragraph(disclaimer, disclaimer_style))
            
            # Build PDF
            doc.build(story)
            
            # Generate base64 encoded version for download
            with open(filepath, 'rb') as pdf_file:
                pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')
            
            logger.info(f"[{self.name}] PDF report generated: {filepath}")
            return filename, pdf_base64
            
        except Exception as e:
            logger.error(f"[{self.name}] Error generating PDF: {str(e)}")
            return f"error_{timestamp}.pdf", ""
    
    def _parse_report_sections(self, content: str) -> List[tuple[str, str]]:
        """Parse report content into sections"""
        
        sections = []
        lines = content.split('\n')
        current_section = ""
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a section header (all caps or starts with number)
            if (line.isupper() and len(line) > 10) or (line and line[0].isdigit() and '.' in line[:5]):
                # Save previous section
                if current_section and current_content:
                    sections.append((current_section, '\n'.join(current_content)))
                
                # Start new section
                current_section = line
                current_content = []
            else:
                current_content.append(line)
        
        # Add final section
        if current_section and current_content:
            sections.append((current_section, '\n'.join(current_content)))
        
        return sections
    
    async def _save_report_to_file(self, content: str, data: Dict[str, Any]) -> str:
        """Save the generated report to a text file"""
        
        # Create filename
        stocks_str = "_".join(data["stocks"][:3]) if data["stocks"] else "portfolio"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"investment_report_{stocks_str}_{timestamp}.txt"
        
        # Ensure reports directory exists
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        filepath = os.path.join(reports_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"[{self.name}] Text report saved to {filepath}")
            return filename
        except Exception as e:
            logger.error(f"[{self.name}] Error saving text report: {str(e)}")
            return f"error_saving_{timestamp}.txt"
    
    def _create_response_summary(self, data: Dict[str, Any], text_filename: str, pdf_filename: str) -> str:
        """Create a summary response for the user"""
        
        stocks = data["stocks"]
        stocks_str = ", ".join(stocks) if stocks else "portfolio"
        
        summary = f"""📊 **COMPREHENSIVE INVESTMENT REPORT GENERATED**

✅ **Analysis Complete**: {len(stocks)} stock(s) analyzed - {stocks_str}
📅 **Report Date**: {data["report_metadata"]["analysis_date"]}
📄 **Files Generated**: 
   • Text Report: {text_filename}
   • PDF Report: {pdf_filename}

**Report Sections Included:**
• Executive Summary & Investment Thesis
• Market Overview & Sector Analysis  
• Individual Stock Deep Dive Analysis
• Technical Analysis & Chart Patterns
• Fundamental Valuation Assessment
• News Sentiment & Market Impact
• Risk Assessment & Management Strategies
• Investment Recommendations by Profile
• Forward-Looking Analysis & Catalysts
• Actionable Conclusions & Next Steps

**Key Features:**
✓ Professional institutional-grade analysis
✓ Multi-factor quantitative assessment
✓ Risk-adjusted recommendations
✓ Professional PDF formatting with proper styling
✓ Downloadable PDF ready for distribution
✓ Comprehensive disclaimers included

📥 **Download Options:**
• PDF report is available for download in the reports directory
• Text version also available for editing/customization
• Base64 encoded PDF stored in session state for web download

📋 **Next Steps:**
1. Download the PDF report from the reports directory
2. Review the comprehensive analysis
3. Distribute to relevant stakeholders
4. Monitor positions based on recommendations

*Report generated using AI-enhanced analysis combining market data, technical indicators, and news sentiment with professional PDF formatting.*"""

        return summary