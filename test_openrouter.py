#!/usr/bin/env python3
"""
Test OpenRouter integration

Verify that OpenRouter API works correctly
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tradingagents.run import execute
from tradingagents.models import ResearchRequest
from tradingagents.config_api import print_api_status, validate_api_setup


async def test_openrouter():
    """Test OpenRouter API"""
    
    print("=" * 80)
    print("OpenRouter Integration Test")
    print("=" * 80)
    
    # Check if OpenRouter is configured
    use_openrouter = os.environ.get("USE_OPENROUTER", "false").lower() == "true"
    
    if not use_openrouter:
        print("\n⚠️  OpenRouter not configured!")
        print("\nTo use OpenRouter, set:")
        print("  export USE_OPENROUTER=true")
        print("  export OPENROUTER_API_KEY='sk-or-v1-your-key'")
        print("  export OPENROUTER_MODEL='anthropic/claude-3.5-sonnet'")
        print("\nOr use command line:")
        print("  python run.py AAPL --openrouter-key 'your-key' --openrouter-model 'anthropic/claude-3.5-sonnet'")
        return
    
    # Print API status
    print_api_status()
    
    # Validate setup
    is_valid, message = validate_api_setup()
    if not is_valid:
        print(f"\n❌ {message}")
        return
    
    print(f"\n✓ {message}\n")
    
    # Test analysis
    symbol = "AAPL"
    print(f"Testing OpenRouter with {symbol}...")
    print("-" * 80)
    
    try:
        request = ResearchRequest(
            symbol=symbol,
            horizon="1w",
            market_context="general market conditions",
        )
        
        print("\nRunning analysis...")
        result = await execute(request, use_real_data=True)
        decision = result["decision"]
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        
        print(f"\nDecision: {decision.recommendation}")
        print(f"Confidence: {decision.confidence:.2f}")
        print(f"\nRationale:")
        print(decision.rationale)
        
        print(f"\nEvidence by agent:")
        for agent_name, evidence_list in decision.evidence.items():
            print(f"\n  {agent_name.upper()}:")
            for evidence in evidence_list:
                print(f"    - {evidence}")
        
        # Check if debate occurred
        if decision.debate:
            print(f"\n" + "=" * 80)
            print("DEBATE INFO")
            print("=" * 80)
            print(f"Converged: {decision.debate.converged}")
            print(f"Position changes: {len(decision.debate.position_changes)}")
        
        print("\n" + "=" * 80)
        print("✓ OpenRouter test completed successfully!")
        print("=" * 80)
        
        # Show token/cost info if available
        model = os.environ.get("OPENROUTER_MODEL", "unknown")
        print(f"\nModel used: {model}")
        print("Note: Check OpenRouter dashboard for detailed usage and cost")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("TROUBLESHOOTING")
        print("=" * 80)
        print("\n1. Check your OpenRouter API key:")
        print("   https://openrouter.ai/keys")
        print("\n2. Verify the model name:")
        print("   https://openrouter.ai/docs#models")
        print("\n3. Check your OpenRouter credit balance")
        print("\n4. Try a different model:")
        print("   export OPENROUTER_MODEL='openai/gpt-3.5-turbo'")


if __name__ == "__main__":
    try:
        asyncio.run(test_openrouter())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


