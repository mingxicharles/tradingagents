from __future__ import annotations

import argparse
import asyncio
from typing import Any, Dict, Optional

from .agents import build_agents
from .config import default_agent_configs
from .llm import build_client
from .models import DecisionDTO, ResearchRequest
from .orchestrator import TradingOrchestrator
from .config_api import validate_api_setup


async def execute(
    request: ResearchRequest,
    use_real_data: bool = True,
    use_offline_data: bool = False,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute trading analysis
    
    Args:
        request: Research request
        use_real_data: Whether to use real market data (default True)
        api_key: Optional OpenAI API key (can also use environment variable)
    
    Returns:
        Dictionary containing decision and signal path
    """
    # Set API key if provided
    if api_key:
        import os
        os.environ["OPENAI_API_KEY"] = api_key
    
    # Validate API setup
    is_valid, message = validate_api_setup()
    if not is_valid:
        raise RuntimeError(f"API not configured: {message}")
    
    client = build_client()
    configs = default_agent_configs()
    
    # Check for offline data flag  
    use_offline = use_offline_data
    
    agents = build_agents(client, configs, use_real_data=use_real_data, use_offline_data=use_offline)

    orchestrator = TradingOrchestrator(
        agents=agents,
        agent_configs=configs,
        supervisor_client=client,
    )
    graph = orchestrator.build_graph()
    app = graph.compile()
    final_state = await app.ainvoke({"request": request})
    decision: DecisionDTO = final_state["decision"]  # type: ignore[index]
    return {
        "decision": decision,
        "signal_path": final_state.get("signal_path"),
        "policy_flags": final_state.get("policy_flags", []),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the LangGraph trading research supervisor with Qwen."
    )
    parser.add_argument("symbol", help="Ticker symbol, e.g. AAPL")
    parser.add_argument(
        "--horizon",
        default="1d",
        help="Time horizon for the analysis (default: 1d)",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Specific date to analyze (YYYY-MM-DD format, e.g., 2024-01-15). If not provided, uses current date.",
    )
    parser.add_argument(
        "--context",
        default="general market conditions",
        help="Market context or scenario guidance for agents.",
    )
    parser.add_argument(
        "--no-real-data",
        action="store_true",
        help="Disable real data fetching (agents will rely on LLM knowledge only)",
    )
    parser.add_argument(
        "--offline-data",
        action="store_true",
        help="Use offline/local dataset instead of yfinance (requires generate_offline_data.py)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (overrides environment variable)",
    )
    parser.add_argument(
        "--local-model",
        type=str,
        help="Use local model instead (e.g., Qwen/Qwen2.5-7B-Instruct)",
    )
    parser.add_argument(
        "--openrouter-key",
        type=str,
        help="OpenRouter API key",
    )
    parser.add_argument(
        "--openrouter-model",
        type=str,
        default="openai/gpt-3.5-turbo",
        help="OpenRouter model to use (default: openai/gpt-3.5-turbo)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    
    # Configure API if specified
    if args.local_model:
        import os
        os.environ["USE_LOCAL_MODEL"] = "true"
        os.environ["LOCAL_MODEL"] = args.local_model
        print(f"✓ Using local model: {args.local_model}")
    elif args.openrouter_key:
        import os
        os.environ["USE_OPENROUTER"] = "true"
        os.environ["OPENROUTER_API_KEY"] = args.openrouter_key
        os.environ["OPENROUTER_MODEL"] = args.openrouter_model
        print(f"✓ Using OpenRouter")
        print(f"  Model: {args.openrouter_model}")
    elif args.api_key:
        import os
        os.environ["OPENAI_API_KEY"] = args.api_key
        print(f"✓ API key configured")
    
    use_real_data = not args.no_real_data
    use_offline_data = args.offline_data
    
    if use_real_data:
        date_info = f" on {args.date}" if args.date else ""
        data_source = "offline dataset" if use_offline_data else "real market data"
        print(f"✓ Analyzing {args.symbol} with {data_source}{date_info}")
    else:
        print(f"⚠ Analyzing {args.symbol} using LLM knowledge only (no real data)")
    
    request = ResearchRequest(
        symbol=args.symbol.upper(),
        horizon=args.horizon,
        market_context=args.context,
        trade_date=args.date,
    )
    
    try:
        result = asyncio.run(execute(request, use_real_data=use_real_data, use_offline_data=use_offline_data, api_key=args.api_key))
        decision: DecisionDTO = result["decision"]
    except RuntimeError as e:
        print(f"\n❌ Error: {e}")
        print("\nTo configure API:")
        print("  1. Set environment variable: export OPENAI_API_KEY='your-key'")
        print("  2. Use command line: python run.py AAPL --api-key 'your-key'")
        print("  3. Use OpenRouter: python run.py AAPL --openrouter-key 'your-key' --openrouter-model 'openai/gpt-4'")
        print("  4. Use local model: python run.py AAPL --local-model 'Qwen/Qwen2.5-7B-Instruct'")
        return

    print(f"\nDecision: {decision.recommendation} (confidence {decision.confidence})")
    print("Rationale:")
    print(decision.rationale)
    print("\nEvidence by agent:")
    for agent, evidence in decision.evidence.items():
        bullets = "; ".join(evidence) if evidence else "No evidence provided"
        print(f"  - {agent}: {bullets}")
    
    # Show debate information if debate occurred
    if decision.debate:
        debate = decision.debate
        print("\n" + "=" * 60)
        print("DEBATE SUMMARY")
        print("=" * 60)
        print(f"Converged: {'Yes' if debate.converged else 'No'}")
        print(f"Agents changed action: {debate.agents_changed_action}")
        print(f"Agents changed conviction: {debate.agents_changed_conviction}")
        print(f"Total conviction shift: {debate.total_conviction_shift:.3f}")
        
        if debate.position_changes:
            print("\nPosition Changes:")
            for change in debate.position_changes:
                if change.change_type == "action":
                    print(f"  {change.agent}: {change.before_action} → {change.after_action}")
                elif change.change_type == "conviction":
                    print(f"  {change.agent}: conviction {change.before_conviction:.2f} → {change.after_conviction:.2f} (Δ{change.conviction_delta:+.2f})")
                else:  # both
                    print(f"  {change.agent}: {change.before_action} (conv={change.before_conviction:.2f}) → {change.after_action} (conv={change.after_conviction:.2f})")
    
    signal_path = result.get("signal_path")
    if signal_path:
        print(f"\nSignal written to {signal_path}")
    flags = result.get("policy_flags") or []
    if flags:
        print("Policy flags:", ", ".join(flags))


if __name__ == "__main__":
    main()
