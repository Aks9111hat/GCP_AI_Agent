# config.py - Configuration file for Stock Report Generator Agent

import os
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class AgentConfig:
    """Configuration class for the Stock Report Generator Agent"""
    
    # Model Configuration
    PLANNER_PROVIDER: str = os.getenv("PLANNER_PROVIDER", "anthropic")
    PLANNER_MODEL: str = os.getenv("PLANNER_MODEL", "claude-3-5-sonnet-latest")
    WRITER_PROVIDER: str = os.getenv("WRITER_PROVIDER", "anthropic")
    WRITER_MODEL: str = os.getenv("WRITER_MODEL", "claude-3-5-sonnet-latest")
    
    # Search Configuration
    SEARCH_API: str = os.getenv("SEARCH_API", "tavily")
    SEARCH_API_CONFIG: Dict[str, Any] = {
        "tavily": {},
        "exa": {
            "num_results": 10,
            "include_domains": ["finance.yahoo.com", "bloomberg.com", "reuters.com", "marketwatch.com"],
            "max_characters": 8000
        },
        "perplexity": {},
        "arxiv": {"load_max_docs": 5},
        "pubmed": {"top_k_results": 5}
    }
    
    # Performance Configuration
    USE_MULTI_AGENT: bool = os.getenv("USE_MULTI_AGENT", "false").lower() == "true"
    MAX_CONCURRENT_REPORTS: int = int(os.getenv("MAX_CONCURRENT_REPORTS", "5"))
    REPORT_TIMEOUT: int = int(os.getenv("REPORT_TIMEOUT", "300"))  # 5 minutes
    
    # Output Configuration
    DEFAULT_OUTPUT_DIR: str = os.getenv("REPORT_OUTPUT_DIR", "./stock_reports")
    SUPPORTED_FORMATS: List[str] = ["markdown", "html", "json", "pdf"]
    
    # API Keys (ensure these are set in your environment)
    REQUIRED_ENV_VARS: List[str] = [
        "ANTHROPIC_API_KEY",  # or OPENAI_API_KEY, etc.
        "TAVILY_API_KEY",     # or your chosen search API key
    ]