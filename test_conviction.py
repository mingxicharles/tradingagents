#!/usr/bin/env python3
"""
Test conviction scoring improvements

This script tests if agents now provide varied conviction scores
based on data strength rather than defaulting to 0.75
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tradingagents.run import execute
from tradingagents.models import ResearchRequest
from tradingagents.config_api import validate_api_setup


async def test_conviction_diversity():
    """Test multiple scenarios to see conviction variation"""
    
    print("=" * 80)
    print("Conviction Score Diversity Test")
    print("=" * 80)
    
    # Check API
    is_valid, message = validate_api_setup()
    if not is_valid:
        print(f"\n❌ {message}")
        print("Run: python configure_api.py")
        return
    
    print(f"\n✓ {message}\n")
    
    # Test different scenarios
    scenarios = [
        ("AAPL", "1w", "Strong uptrend expected"),
        ("AAPL", "1d", "High volatility environment"),
        ("MSFT", "1w", "Earnings beat expected"),
    ]
    
    results = []
    
    for symbol, horizon, context in scenarios:
        print(f"\n[Testing] {symbol} - {horizon} - {context}")
        print("-" * 80)
        
        try:
            request = ResearchRequest(
                symbol=symbol,
                horizon=horizon,
                market_context=context,
            )
            
            result = await execute(request, use_real_data=True)
            decision = result["decision"]
            proposals = decision.proposals
            
            # Collect conviction scores
            convictions = []
            for name, proposal in proposals.items():
                conv = proposal.conviction
                convictions.append(conv)
                print(f"  {name:12s}: action={proposal.action:4s} conviction={conv:.3f}")
            
            results.append({
                "scenario": f"{symbol} {horizon} - {context}",
                "final_confidence": decision.confidence,
                "agent_convictions": convictions,
                "recommendation": decision.recommendation,
            })
            
            print(f"\n  Final Decision: {decision.recommendation} (confidence: {decision.confidence:.3f})")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    # Analyze results
    print("\n" + "=" * 80)
    print("Analysis")
    print("=" * 80)
    
    all_convictions = []
    for r in results:
        all_convictions.extend(r["agent_convictions"])
    
    if all_convictions:
        avg_conv = sum(all_convictions) / len(all_convictions)
        min_conv = min(all_convictions)
        max_conv = max(all_convictions)
        unique_values = len(set(all_convictions))
        
        print(f"\nAgent Conviction Statistics:")
        print(f"  Average: {avg_conv:.3f}")
        print(f"  Range: {min_conv:.3f} - {max_conv:.3f}")
        print(f"  Unique values: {unique_values}")
        print(f"  All values: {[f'{c:.3f}' for c in sorted(all_convictions)]}")
        
        if unique_values == 1 and all_convictions[0] == 0.75:
            print("\n❌ PROBLEM: All convictions are still 0.75!")
            print("   LLM is not using the conviction scale properly.")
        elif unique_values < 3:
            print("\n⚠️  WARNING: Low diversity in conviction scores")
            print("   LLM might still be defaulting to a few values")
        else:
            print("\n✓ GOOD: Conviction scores show diversity")
            print("   LLM is using the full scale based on data quality")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_conviction_diversity())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


