"""
Trading Agents Module

Simplified agents for LLM-driven controller architecture.
"""

from .simple_agent import (
    TradingAgent,
    create_news_agent,
    create_technical_agent,
    create_fundamental_agent
)

from ..llm import LLMClient
from typing import Dict, List, Callable


def build_agents(
    llm_client: LLMClient,
    use_real_data: bool = True,
    use_offline_data: bool = False,
    use_csv_data: bool = False
) -> Dict[str, TradingAgent]:
    """
    Build all trading agents with appropriate data tools.
    
    Args:
        llm_client: LLM client for agents
        use_real_data: Whether to use real market data
        use_offline_data: Whether to use offline/local data instead of live data
        use_csv_data: Whether to use CSV data for batch testing
        
    Returns:
        Dictionary of agent name to agent instance
    """
    # Import data tools
    if use_real_data:
        if use_csv_data:
            # Use CSV data loader
            from ..dataflows.csv_data_loader import (
                get_stock_price_data_csv as get_price,
                get_technical_indicators_csv as get_indicators,
                get_company_info_csv as get_company,
                get_recent_news_csv as get_news_data
            )
        elif use_offline_data:
            # Use offline/local data
            from ..dataflows.local_data import (
                get_stock_price_data_local as get_price,
                get_technical_indicators_local as get_indicators,
                get_company_info_local as get_company,
                get_recent_news_local as get_news_data
            )
        else:
            # Use live yfinance data
            from ..dataflows.yfinance_tools import (
                get_stock_price_data as get_price,
                get_technical_indicators as get_indicators,
                get_company_info as get_company,
                get_recent_news as get_news_data
            )
        
        # Configure data tools for each agent type
        news_tools = [get_news_data, get_price]
        technical_tools = [get_price, get_indicators]
        fundamental_tools = [get_company, get_price]
    else:
        # No real data - agents use knowledge base only
        news_tools = []
        technical_tools = []
        fundamental_tools = []
    
    # Build agents
    agents = {
        "news": create_news_agent(llm_client, news_tools),
        "technical": create_technical_agent(llm_client, technical_tools),
        "fundamental": create_fundamental_agent(llm_client, fundamental_tools)
    }
    
    return agents


__all__ = [
    "TradingAgent",
    "build_agents",
    "create_news_agent",
    "create_technical_agent",
    "create_fundamental_agent"
]
