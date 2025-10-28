from __future__ import annotations

import argparse
import asyncio
from typing import Any, Dict

from .agents import build_agents
from .config import default_agent_configs
from .llm import build_client
from .models import DecisionDTO, ResearchRequest
from .orchestrator import TradingOrchestrator


async def execute(request: ResearchRequest) -> Dict[str, Any]:
    client = build_client()
    configs = default_agent_configs()
    agents = build_agents(client, configs)

    orchestrator = TradingOrchestrator(
        agents=agents,
        agent_configs=configs,
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
        "--context",
        default="general market conditions",
        help="Market context or scenario guidance for agents.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    request = ResearchRequest(
        symbol=args.symbol.upper(),
        horizon=args.horizon,
        market_context=args.context,
    )
    result = asyncio.run(execute(request))
    decision: DecisionDTO = result["decision"]

    print(f"Decision: {decision.recommendation} (confidence {decision.confidence})")
    print("Rationale:")
    print(decision.rationale)
    print("Evidence by agent:")
    for agent, evidence in decision.evidence.items():
        bullets = "; ".join(evidence) if evidence else "No evidence provided"
        print(f"  - {agent}: {bullets}")
    signal_path = result.get("signal_path")
    if signal_path:
        print(f"Signal written to {signal_path}")
    flags = result.get("policy_flags") or []
    if flags:
        print("Policy flags:", ", ".join(flags))


if __name__ == "__main__":
    main()
