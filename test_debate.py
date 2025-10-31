#!/usr/bin/env python3
"""
Test debate mechanism improvements

This script tests scenarios likely to trigger debates
and shows how agents respond to opposing arguments
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tradingagents.run import execute
from tradingagents.models import ResearchRequest
from tradingagents.config_api import validate_api_setup


async def test_debate_scenarios():
    """Test scenarios that should trigger debates"""
    
    print("=" * 80)
    print("Debate Mechanism Test")
    print("=" * 80)
    
    # Check API
    is_valid, message = validate_api_setup()
    if not is_valid:
        print(f"\n❌ {message}")
        print("Run: python configure_api.py")
        return
    
    print(f"\n✓ {message}\n")
    
    # Test scenarios that might cause disagreement
    scenarios = [
        {
            "symbol": "AAPL",
            "horizon": "1w",
            "context": "Mixed signals: strong fundamentals but weak technicals",
            "description": "Conflicting technical vs fundamental",
        },
        {
            "symbol": "TSLA",
            "horizon": "1d",
            "context": "High volatility after negative news",
            "description": "Negative news vs price action",
        },
        {
            "symbol": "MSFT",
            "horizon": "1w",
            "context": "Recent breakout but overbought conditions",
            "description": "Momentum vs overbought",
        },
    ]
    
    results = []
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*80}")
        print(f"Scenario {i}/{ len(scenarios)}: {scenario['description']}")
        print(f"{'='*80}")
        print(f"Symbol: {scenario['symbol']}")
        print(f"Context: {scenario['context']}")
        print("-" * 80)
        
        try:
            request = ResearchRequest(
                symbol=scenario['symbol'],
                horizon=scenario['horizon'],
                market_context=scenario['context'],
            )
            
            result = await execute(request, use_real_data=True)
            decision = result["decision"]
            
            # Show initial proposals
            print("\nINITIAL PROPOSALS:")
            for name, proposal in decision.proposals.items():
                print(f"  {name:12s}: {proposal.action:4s} (conviction={proposal.conviction:.2f})")
            
            # Show debate results
            if decision.debate:
                debate = decision.debate
                print(f"\nDEBATE OCCURRED:")
                print(f"  Converged: {'Yes ✓' if debate.converged else 'No ✗'}")
                print(f"  Agents changed action: {debate.agents_changed_action}")
                print(f"  Agents changed conviction: {debate.agents_changed_conviction}")
                print(f"  Total conviction shift: {debate.total_conviction_shift:.3f}")
                
                if debate.position_changes:
                    print(f"\n  Position Changes ({len(debate.position_changes)}):")
                    for change in debate.position_changes:
                        if change.change_type == "action":
                            print(f"    • {change.agent}: {change.before_action} → {change.after_action}")
                        elif change.change_type == "conviction":
                            delta_str = f"Δ{change.conviction_delta:+.2f}"
                            print(f"    • {change.agent}: {change.before_conviction:.2f} → {change.after_conviction:.2f} ({delta_str})")
                        else:
                            print(f"    • {change.agent}: {change.before_action} ({change.before_conviction:.2f}) → {change.after_action} ({change.after_conviction:.2f})")
                else:
                    print(f"\n  No position changes (all agents maintained their stance)")
            else:
                print(f"\nNO DEBATE: All agents agreed")
            
            print(f"\nFINAL DECISION: {decision.recommendation} (confidence={decision.confidence:.2f})")
            
            results.append({
                "scenario": scenario['description'],
                "had_debate": decision.debate is not None,
                "converged": decision.debate.converged if decision.debate else None,
                "changes": len(decision.debate.position_changes) if decision.debate else 0,
                "final_decision": decision.recommendation,
                "final_confidence": decision.confidence,
            })
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Summary
    print("\n" + "=" * 80)
    print("DEBATE SUMMARY")
    print("=" * 80)
    
    total_scenarios = len(results)
    scenarios_with_debate = sum(1 for r in results if r["had_debate"])
    scenarios_converged = sum(1 for r in results if r.get("converged"))
    total_changes = sum(r["changes"] for r in results)
    
    print(f"\nTotal scenarios tested: {total_scenarios}")
    print(f"Scenarios with debate: {scenarios_with_debate} ({scenarios_with_debate/total_scenarios*100:.0f}%)")
    if scenarios_with_debate > 0:
        print(f"Debates that converged: {scenarios_converged}/{scenarios_with_debate}")
        print(f"Total position changes: {total_changes}")
        print(f"Average changes per debate: {total_changes/scenarios_with_debate:.1f}")
    
    print("\n" + "=" * 80)
    print("DEBATE MECHANISM IMPROVEMENTS:")
    print("=" * 80)
    print("✓ Agents now see full evidence from opposing positions")
    print("✓ Debate prompts highlight specific counterarguments")
    print("✓ Position changes are tracked for RL training")
    print("✓ Conviction adjustments based on debate quality")
    print("✓ Convergence detection shows debate effectiveness")
    print("\nThese metrics provide rich signals for RL training:")
    print("  - Which agents changed their mind (flexibility)")
    print("  - Magnitude of conviction changes (confidence updates)")
    print("  - Whether debate led to consensus (decision quality)")
    print("  - Evidence strength comparisons (argumentation quality)")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_debate_scenarios())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


