from __future__ import annotations

from typing import Dict

from ..config import AgentConfig
from ..llm import LLMClient
from .common import JsonResearchAgent
from .data_agent import DataAwareAgent
from ..dataflows.yfinance_tools import (
    get_stock_price_data,
    get_technical_indicators,
    get_company_info,
    get_recent_news,
)
from ..dataflows.local_data import (
    get_stock_price_data_local,
    get_technical_indicators_local,
    get_company_info_local,
    get_recent_news_local,
)


class JsonDataAwareAgent(DataAwareAgent, JsonResearchAgent):
    """Agent combining data fetching and JSON parsing"""
    pass


def build_agents(client: LLMClient, configs: list[AgentConfig], use_real_data: bool = True, use_offline_data: bool = False) -> Dict[str, JsonResearchAgent]:
    """
    Factory for configured research agents.
    
    Args:
        client: LLM client
        configs: Agent configurations
        use_real_data: Whether to use real data (default True)
        use_offline_data: Whether to use offline/local dataset instead of yfinance (default False)
    
    Returns:
        Dictionary of configured agents
    """
    if not use_real_data:
        # Use original agents without data tools
        return {
            config.name: JsonResearchAgent(config.name, client, config.system_prompt)
            for config in configs
        }
    
    # Choose data source
    if use_offline_data:
        # Use offline/local data
        get_price = get_stock_price_data_local
        get_indicators = get_technical_indicators_local
        get_company = get_company_info_local
        get_news = get_recent_news_local
    else:
        # Use yfinance (online)
        get_price = get_stock_price_data
        get_indicators = get_technical_indicators
        get_company = get_company_info
        get_news = get_recent_news
    
    # Configure data tools for each agent
    agents = {}
    
    for config in configs:
        if config.name == "technical":
            # Technical analyst: price data + technical indicators
            data_tools = [get_price, get_indicators]
        elif config.name == "fundamental":
            # Fundamental analyst: company info + price data
            data_tools = [get_company, get_price]
        elif config.name == "news":
            # News analyst: news + price data
            data_tools = [get_news, get_price]
        else:
            # Default: basic price data
            data_tools = [get_price]
        
        agents[config.name] = JsonDataAwareAgent(
            name=config.name,
            client=client,
            system_prompt=config.system_prompt,
            data_tools=data_tools
        )
    
    return agents
