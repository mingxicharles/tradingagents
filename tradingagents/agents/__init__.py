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


class JsonDataAwareAgent(DataAwareAgent, JsonResearchAgent):
    """Agent combining data fetching and JSON parsing"""
    pass


def build_agents(client: LLMClient, configs: list[AgentConfig], use_real_data: bool = True) -> Dict[str, JsonResearchAgent]:
    """
    Factory for configured research agents.
    
    Args:
        client: LLM client
        configs: Agent configurations
        use_real_data: Whether to use real data (default True)
    
    Returns:
        Dictionary of configured agents
    """
    if not use_real_data:
        # Use original agents without data tools
        return {
            config.name: JsonResearchAgent(config.name, client, config.system_prompt)
            for config in configs
        }
    
    # Configure data tools for each agent
    agents = {}
    
    for config in configs:
        if config.name == "technical":
            # Technical analyst: price data + technical indicators
            data_tools = [get_stock_price_data, get_technical_indicators]
        elif config.name == "fundamental":
            # Fundamental analyst: company info + price data
            data_tools = [get_company_info, get_stock_price_data]
        elif config.name == "news":
            # News analyst: news + price data
            data_tools = [get_recent_news, get_stock_price_data]
        else:
            # Default: basic price data
            data_tools = [get_stock_price_data]
        
        agents[config.name] = JsonDataAwareAgent(
            name=config.name,
            client=client,
            system_prompt=config.system_prompt,
            data_tools=data_tools
        )
    
    return agents
