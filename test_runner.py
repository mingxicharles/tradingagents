#!/usr/bin/env python3
"""
Simple test runner to verify the trading agents pipeline works.
"""

import sys
import os
import asyncio

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from tradingagents.llm import build_client
        from tradingagents.orchestrator import TradingOrchestrator
        from tradingagents.models import ResearchRequest
        from tradingagents.run import execute
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_api_key():
    """Test that API key is set."""
    print("\nChecking API key...")
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("✗ No API key found in environment")
        print("  Set with: export OPENAI_API_KEY='your-key'")
        return False
    print(f"✓ API key found: {api_key[:10]}...")
    return True


async def test_api_call():
    """Test a simple API call."""
    print("\nTesting API call...")
    try:
        from tradingagents.llm import build_client
        client = build_client()
        print(f"  Client type: {type(client).__name__}")
        
        response = await client.complete([
            {"role": "user", "content": "Reply with only 'test'"}
        ], max_tokens=10)
        print(f"✓ API call successful: {response}")
        return True
    except Exception as e:
        print(f"✗ API call failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pipeline():
    """Test the full pipeline."""
    print("\nTesting full pipeline...")
    try:
        from tradingagents.models import ResearchRequest
        from tradingagents.run import execute
        
        request = ResearchRequest(
            symbol="AAPL",
            horizon="1d",
            market_context="test"
        )
        
        print("  Running pipeline...")
        result = await execute(request)
        
        decision = result["decision"]
        print(f"✓ Pipeline successful!")
        print(f"  Decision: {decision.recommendation}")
        print(f"  Confidence: {decision.confidence}")
        print(f"  Signal path: {result.get('signal_path')}")
        return True
    except Exception as e:
        print(f"✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Trading Agents Pipeline Test")
    print("=" * 60)
    
    if not test_imports():
        sys.exit(1)
    
    if not test_api_key():
        sys.exit(1)
    
    if not await test_api_call():
        sys.exit(1)
    
    if not await test_pipeline():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ All tests passed! Your setup is working.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())



