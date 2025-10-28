#!/usr/bin/env python3
"""
Test real data fetching functionality
"""
import asyncio
from tradingagents.dataflows.yfinance_tools import (
    get_stock_price_data,
    get_technical_indicators,
    get_company_info,
    get_recent_news,
)


def test_data_tools():
    """Test each data tool"""
    print("=" * 60)
    print("Testing Real Data Fetching Tools")
    print("=" * 60)
    
    symbol = "AAPL"
    
    # Test 1: Price data
    print("\n[1/4] Testing price data...")
    price_data = get_stock_price_data(symbol)
    print(price_data[:500])  # Show first 500 characters
    print("...")
    
    # Test 2: Technical indicators
    print("\n[2/4] Testing technical indicators...")
    tech_data = get_technical_indicators(symbol)
    print(tech_data[:500])
    print("...")
    
    # Test 3: Company info
    print("\n[3/4] Testing company info...")
    company_data = get_company_info(symbol)
    print(company_data[:500])
    print("...")
    
    # Test 4: News
    print("\n[4/4] Testing news...")
    news_data = get_recent_news(symbol, max_news=3)
    print(news_data)
    
    print("\n" + "=" * 60)
    print("✅ All data tools tests completed!")
    print("=" * 60)


async def test_agent_with_data():
    """Test Agent with real data"""
    print("\n" + "=" * 60)
    print("Testing Agent Real Data Integration")
    print("=" * 60)
    
    from tradingagents.run import execute
    from tradingagents.models import ResearchRequest
    
    request = ResearchRequest(
        symbol="AAPL",
        horizon="1w",
        market_context="Test with real data"
    )
    
    print("\nRunning with real data...")
    result = await execute(request, use_real_data=True)
    decision = result["decision"]
    
    print(f"\n✓ Decision: {decision.recommendation}")
    print(f"  Confidence: {decision.confidence}")
    print(f"\nEvidence:")
    for agent, evidence in decision.evidence.items():
        print(f"\n  {agent}:")
        if evidence:
            for i, e in enumerate(evidence[:2], 1):  # Show first 2 items only
                print(f"    {i}. {e}")
        else:
            print(f"    No evidence provided")
    
    print("\n" + "=" * 60)
    print("✅ Agent real data integration test completed!")
    print("=" * 60)


async def test_comparison():
    """Compare real data vs fake data"""
    print("\n" + "=" * 60)
    print("Comparison Test: Real Data vs Fake Data")
    print("=" * 60)
    
    from tradingagents.run import execute
    from tradingagents.models import ResearchRequest
    
    request = ResearchRequest(
        symbol="AAPL",
        horizon="1d",
        market_context="Comparison test"
    )
    
    print("\n[1/2] Running with real data mode...")
    result_real = await execute(request, use_real_data=True)
    
    print("[2/2] Running with fake data mode...")
    result_fake = await execute(request, use_real_data=False)
    
    print("\n" + "=" * 60)
    print("Comparison Results")
    print("=" * 60)
    
    # Helper function to safely get evidence
    def get_evidence_sample(evidence_dict, agent_name):
        if agent_name in evidence_dict and evidence_dict[agent_name]:
            return evidence_dict[agent_name][0][:80] + "..."
        return "No evidence provided"
    
    print(f"\nReal Data Mode:")
    print(f"  Recommendation: {result_real['decision'].recommendation}")
    print(f"  Confidence: {result_real['decision'].confidence}")
    print(f"  Technical evidence: {get_evidence_sample(result_real['decision'].evidence, 'technical')}")
    
    print(f"\nFake Data Mode:")
    print(f"  Recommendation: {result_fake['decision'].recommendation}")
    print(f"  Confidence: {result_fake['decision'].confidence}")
    print(f"  Technical evidence: {get_evidence_sample(result_fake['decision'].evidence, 'technical')}")
    
    print("\nObservations:")
    print("  - Real data should cite specific numbers (e.g., 'RSI 65.3')")
    print("  - Fake data might be more vague (e.g., 'RSI shows bullish momentum')")
    
    print("\n" + "=" * 60)
    print("✅ Comparison test completed!")
    print("=" * 60)


async def main():
    """Main test workflow"""
    print("\n" + "=" * 60)
    print("Real Data Integration Test Suite")
    print("=" * 60)
    
    print("\nSelect test:")
    print("1. Test data tools")
    print("2. Test Agent integration")
    print("3. Compare real vs fake data")
    print("4. Run all tests")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
    except KeyboardInterrupt:
        print("\nTest cancelled")
        return
    
    if choice == "1":
        test_data_tools()
    elif choice == "2":
        await test_agent_with_data()
    elif choice == "3":
        await test_comparison()
    elif choice == "4":
        test_data_tools()
        await test_agent_with_data()
        await test_comparison()
    else:
        print("Invalid choice")
    
    print("\nTests completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")

