#!/usr/bin/env python3
"""
Quick test to verify API configuration and basic functionality
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tradingagents.config_api import print_api_status, validate_api_setup


def main():
    print("=" * 80)
    print("TradingAgents Configuration Test")
    print("=" * 80)
    
    # 1. Check API status
    print("\n[1/4] Checking API configuration...")
    print_api_status()
    
    is_valid, message = validate_api_setup()
    if not is_valid:
        print(f"\n❌ {message}")
        print("\nTo configure, run:")
        print("  python configure_api.py")
        return
    
    print(f"\n✓ {message}")
    
    # 2. Test data tools import
    print("\n[2/4] Testing data tools import...")
    try:
        from tradingagents.dataflows.yfinance_tools import (
            get_stock_price_data,
            get_technical_indicators,
            get_company_info,
            get_recent_news
        )
        print("✓ Data tools imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Run: pip install yfinance pandas")
        return
    
    # 3. Test LLM client
    print("\n[3/4] Testing LLM client...")
    try:
        from tradingagents.llm import build_client
        client = build_client()
        print(f"✓ LLM client created: {type(client).__name__}")
    except Exception as e:
        print(f"❌ Client error: {e}")
        return
    
    # 4. Test agent creation
    print("\n[4/4] Testing agent creation...")
    try:
        from tradingagents.agents import build_agents
        from tradingagents.config import default_agent_configs
        
        configs = default_agent_configs()
        agents = build_agents(client, configs, use_real_data=True)
        print(f"✓ Created {len(agents)} agents with real data support")
        
        for name, agent in agents.items():
            tools_count = len(getattr(agent, 'data_tools', []))
            print(f"  - {name}: {tools_count} data tools")
    
    except Exception as e:
        print(f"❌ Agent error: {e}")
        return
    
    # Success
    print("\n" + "=" * 80)
    print("✓ All tests passed!")
    print("=" * 80)
    print("\nYour setup is ready. Try running:")
    print("  python run.py AAPL --horizon 1w")
    print("\nOr for a full test:")
    print("  python test_real_data.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


