"""
Debug script to verify data flow to agents
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tradingagents.llm import build_llm_client
from tradingagents.models import AnalysisRequest
from tradingagents.agents.simple_agent import create_news_agent
from tradingagents.dataflows.csv_data_loader import (
    get_csv_loader,
    get_recent_news_csv,
    get_stock_price_data_csv
)


async def main():
    # Initialize CSV loader with clean data
    csv_path = "dataflows/data_cache/offline_trading_data_AAPL_2024-11-12_2025-01-11_clean.csv"
    loader = get_csv_loader(csv_path)
    print(f"Loaded CSV: {loader.csv_path}\n")
    
    # Test data fetching directly
    print("="*70)
    print("DIRECT DATA TOOL TEST")
    print("="*70)
    
    symbol = "AAPL"
    trade_date = "2024-11-12"
    
    print(f"\nTesting: {symbol} on {trade_date}\n")
    
    # Test news
    print("--- News Data ---")
    news_data = get_recent_news_csv(symbol, trade_date)
    print(news_data[:500])
    print("...\n")
    
    # Test price
    print("--- Price Data ---")
    price_data = get_stock_price_data_csv(symbol, trade_date)
    print(price_data[:500])
    print("...\n")
    
    # Now test through agent
    print("="*70)
    print("AGENT DATA FETCH TEST")
    print("="*70)
    
    llm_client = build_llm_client()
    agent = create_news_agent(llm_client, [get_recent_news_csv, get_stock_price_data_csv])
    
    request = AnalysisRequest(
        symbol=symbol,
        horizon="1d",
        trade_date=trade_date,
        market_context="Test"
    )
    
    # Manually call _fetch_data to see what agent gets
    print(f"\nFetching data through agent...")
    data_context = await agent._fetch_data(request)
    
    print("\n--- Data Context Received by Agent ---")
    print(data_context[:800])
    print("...")
    
    # Now try full analysis
    print("\n" + "="*70)
    print("FULL AGENT ANALYSIS TEST")
    print("="*70)
    
    proposal = await agent.analyze(request)
    
    print(f"\nAgent Proposal:")
    print(f"  Action: {proposal.action}")
    print(f"  Conviction: {proposal.conviction}")
    print(f"  Thesis: {proposal.thesis[:200]}...")
    print(f"  Evidence: {len(proposal.evidence)} items")
    for i, ev in enumerate(proposal.evidence[:3], 1):
        print(f"    {i}. {ev[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())

