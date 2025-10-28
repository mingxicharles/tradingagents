#!/usr/bin/env python3
"""
Test Agent Role Separation

Verify that technical, fundamental, and news agents analyze different aspects
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tradingagents.run import execute
from tradingagents.models import ResearchRequest
from tradingagents.config_api import validate_api_setup


def analyze_agent_focus(proposal, agent_name):
    """Analyze what an agent focused on based on their evidence"""
    evidence_text = " ".join(proposal.evidence).lower()
    thesis_text = proposal.thesis.lower()
    full_text = evidence_text + " " + thesis_text
    
    # Keywords for each domain
    technical_keywords = [
        'rsi', 'macd', 'moving average', 'ma', 'sma', 'ema',
        'bollinger', 'support', 'resistance', 'breakout',
        'volume', 'momentum', 'overbought', 'oversold',
        'chart pattern', 'trend', 'crossover'
    ]
    
    fundamental_keywords = [
        'p/e', 'pe ratio', 'p/b', 'price-to-earnings',
        'revenue', 'earnings', 'profit', 'margin',
        'valuation', 'balance sheet', 'debt',
        'market cap', 'growth', 'financial'
    ]
    
    news_keywords = [
        'news', 'headline', 'announcement', 'reported',
        'regulatory', 'policy', 'sentiment', 'event',
        'media', 'coverage', 'published', 'article'
    ]
    
    # Count keyword matches
    technical_count = sum(1 for kw in technical_keywords if kw in full_text)
    fundamental_count = sum(1 for kw in fundamental_keywords if kw in full_text)
    news_count = sum(1 for kw in news_keywords if kw in full_text)
    
    return {
        "technical": technical_count,
        "fundamental": fundamental_count,
        "news": news_count,
    }


async def test_role_separation():
    """Test that agents focus on their respective domains"""
    
    print("=" * 80)
    print("Agent Role Separation Test")
    print("=" * 80)
    
    # Check API
    is_valid, message = validate_api_setup()
    if not is_valid:
        print(f"\n❌ {message}")
        print("Run: python configure_api.py")
        return
    
    print(f"\n✓ {message}\n")
    
    # Test with a stock
    symbol = "AAPL"
    print(f"Testing with: {symbol}")
    print("-" * 80)
    
    try:
        request = ResearchRequest(
            symbol=symbol,
            horizon="1w",
            market_context="general market conditions",
        )
        
        result = await execute(request, use_real_data=True)
        decision = result["decision"]
        proposals = decision.proposals
        
        print("\nAGENT ANALYSIS:\n")
        
        role_scores = {}
        
        for agent_name, proposal in proposals.items():
            print(f"{agent_name.upper()} AGENT:")
            print(f"  Action: {proposal.action} (conviction: {proposal.conviction:.2f})")
            print(f"  Thesis: {proposal.thesis[:100]}...")
            print(f"\n  Evidence:")
            for i, evidence in enumerate(proposal.evidence, 1):
                print(f"    {i}. {evidence}")
            
            # Analyze what they focused on
            focus = analyze_agent_focus(proposal, agent_name)
            role_scores[agent_name] = focus
            
            print(f"\n  Keyword Analysis:")
            print(f"    Technical keywords: {focus['technical']}")
            print(f"    Fundamental keywords: {focus['fundamental']}")
            print(f"    News keywords: {focus['news']}")
            print()
        
        # Evaluation
        print("\n" + "=" * 80)
        print("ROLE SEPARATION EVALUATION")
        print("=" * 80)
        
        issues = []
        
        # Check technical agent
        tech_focus = role_scores.get("technical", {})
        if tech_focus.get("technical", 0) < tech_focus.get("fundamental", 0):
            issues.append("⚠️  Technical agent used more fundamental keywords than technical")
        if tech_focus.get("technical", 0) < tech_focus.get("news", 0):
            issues.append("⚠️  Technical agent used more news keywords than technical")
        if tech_focus.get("technical", 0) >= 2:
            print("✓ Technical agent focused on technical analysis")
        else:
            issues.append("⚠️  Technical agent didn't use enough technical keywords")
        
        # Check fundamental agent
        fund_focus = role_scores.get("fundamental", {})
        if fund_focus.get("fundamental", 0) < fund_focus.get("technical", 0):
            issues.append("⚠️  Fundamental agent used more technical keywords than fundamental")
        if fund_focus.get("fundamental", 0) < fund_focus.get("news", 0):
            issues.append("⚠️  Fundamental agent used more news keywords than fundamental")
        if fund_focus.get("fundamental", 0) >= 2:
            print("✓ Fundamental agent focused on fundamental analysis")
        else:
            issues.append("⚠️  Fundamental agent didn't use enough fundamental keywords")
        
        # Check news agent
        news_focus = role_scores.get("news", {})
        if news_focus.get("news", 0) < news_focus.get("technical", 0):
            issues.append("⚠️  News agent used more technical keywords than news")
        if news_focus.get("news", 0) < news_focus.get("fundamental", 0):
            issues.append("⚠️  News agent used more fundamental keywords than news")
        if news_focus.get("news", 0) >= 1:
            print("✓ News agent focused on news analysis")
        else:
            issues.append("⚠️  News agent didn't use enough news keywords")
        
        print()
        
        if issues:
            print("\nISSUES FOUND:")
            for issue in issues:
                print(f"  {issue}")
            print("\nThe agents may still be overlapping in their analysis.")
            print("This could be due to:")
            print("  1. LLM not following role instructions strictly")
            print("  2. Limited data causing agents to use similar information")
            print("  3. Prompts need further refinement")
        else:
            print("\n✓ All agents appear to be focused on their respective domains!")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS:")
        print("=" * 80)
        print("If agents are still overlapping, try:")
        print("  1. Use a stronger LLM (GPT-4 better than GPT-3.5)")
        print("  2. Add more explicit data filtering in yfinance_tools.py")
        print("  3. Increase temperature to get more diverse responses")
        print("  4. Review actual evidence to see if they're using their data correctly")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(test_role_separation())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

