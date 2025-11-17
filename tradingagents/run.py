"""
Main entry point for trading analysis system

This module provides the CLI and programmatic interface for running
the trading analysis pipeline with the new unified configuration and logging.
"""

from __future__ import annotations

import argparse
import asyncio
from typing import Any, Dict, Optional
from pathlib import Path

from .agents import build_agents
from .config import get_config, TradingConfig
from .config.settings import LLMConfig
from .llm import build_client
from .models import DecisionDTO, ResearchRequest
from .orchestrator import TradingOrchestrator
from .utils.logging import setup_logging, get_logger

# Get logger for this module
logger = get_logger(__name__)


async def execute(
    request: ResearchRequest,
    config: Optional[TradingConfig] = None,
) -> Dict[str, Any]:
    """
    Execute trading analysis with new configuration system.

    Args:
        request: Research request with symbol, horizon, context
        config: Optional configuration (uses global config if None)

    Returns:
        Dictionary containing decision and signal path

    Raises:
        RuntimeError: If configuration is invalid
    """
    # Get configuration
    if config is None:
        config = get_config()

    logger.info(
        f"Starting analysis for {request.symbol} "
        f"(horizon={request.horizon}, date={request.trade_date})"
    )

    # Validate configuration
    warnings = config.validate_config()
    if warnings:
        logger.warning("Configuration warnings detected:")
        for warning in warnings:
            logger.warning(f"  - {warning}")

    # Build LLM client
    logger.debug("Building LLM client")
    client = build_client()

    # Build agents with data source from config
    logger.debug(f"Building agents (data_source={config.data.source})")
    from .config import default_agent_configs
    agent_configs = default_agent_configs()

    use_real_data = True
    use_offline_data = (config.data.source == "offline")

    agents = build_agents(
        client,
        agent_configs,
        use_real_data=use_real_data,
        use_offline_data=use_offline_data
    )

    # Create orchestrator
    logger.debug("Creating orchestrator")
    orchestrator = TradingOrchestrator(
        agents=agents,
        agent_configs=agent_configs,
        max_debate_rounds=config.agent.max_debate_rounds,
        signals_dir=config.signals_dir,
        supervisor_client=client,
    )

    # Build and execute graph
    logger.info("Building LangGraph workflow")
    graph = orchestrator.build_graph()
    app = graph.compile()

    logger.info("Executing trading analysis workflow")
    final_state = await app.ainvoke({"request": request})

    decision: DecisionDTO = final_state["decision"]  # type: ignore[index]
    signal_path = final_state.get("signal_path")

    logger.info(
        f"Analysis complete: {decision.recommendation} "
        f"(confidence={decision.confidence:.2f})"
    )

    if signal_path:
        logger.info(f"Signal written to: {signal_path}")

    return {
        "decision": decision,
        "signal_path": signal_path,
        "policy_flags": final_state.get("policy_flags", []),
    }


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Intelligent Multi-Agent Trading Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis with live data
  python -m tradingagents.run AAPL

  # Analyze with specific date and context
  python -m tradingagents.run AAPL --date 2024-01-15 --horizon 1w --context "Post-earnings"

  # Use offline data
  python -m tradingagents.run MSFT --offline-data

  # Enable debug logging
  python -m tradingagents.run NVDA --log-level DEBUG

  # Use custom API key
  python -m tradingagents.run GOOGL --api-key "sk-..."
        """
    )

    # Required arguments
    parser.add_argument(
        "symbol",
        help="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"
    )

    # Analysis parameters
    parser.add_argument(
        "--horizon",
        default="1d",
        choices=["1d", "1w", "1m", "3m", "6m"],
        help="Time horizon for analysis (default: 1d)"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Specific date to analyze (YYYY-MM-DD). If not provided, uses current date"
    )
    parser.add_argument(
        "--context",
        default="",
        help="Market context or scenario guidance for agents"
    )

    # Data source options
    data_group = parser.add_argument_group("Data Source Options")
    data_group.add_argument(
        "--offline-data",
        action="store_true",
        help="Use offline dataset instead of live data"
    )
    data_group.add_argument(
        "--data-source",
        choices=["yfinance", "offline", "csv"],
        help="Explicit data source selection"
    )

    # LLM configuration
    llm_group = parser.add_argument_group("LLM Configuration")
    llm_group.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (overrides environment variable)"
    )
    llm_group.add_argument(
        "--model",
        type=str,
        help="LLM model to use (e.g., gpt-4o-mini, gpt-4)"
    )
    llm_group.add_argument(
        "--local-model",
        type=str,
        help="Use local model (e.g., Qwen/Qwen2.5-7B-Instruct)"
    )
    llm_group.add_argument(
        "--openrouter-key",
        type=str,
        help="OpenRouter API key"
    )

    # System options
    system_group = parser.add_argument_group("System Options")
    system_group.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    system_group.add_argument(
        "--log-file",
        type=str,
        help="Write logs to file (in addition to console)"
    )
    system_group.add_argument(
        "--no-colors",
        action="store_true",
        help="Disable colored console output"
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """
    Main entry point for CLI.

    Args:
        argv: Command-line arguments (None = sys.argv)
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Setup logging first
    log_file = Path(args.log_file) if args.log_file else None
    setup_logging(
        level=args.log_level,
        log_file=log_file,
        use_colors=not args.no_colors
    )

    logger.info("=" * 60)
    logger.info("Trading Analysis System - Starting")
    logger.info("=" * 60)

    # Get/create configuration
    config = get_config()

    # Override configuration from CLI arguments
    import os

    # LLM configuration
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
        config = get_config(reload=True)
        logger.info("✓ API key configured from command line")

    if args.model:
        config.llm.model = args.model
        logger.info(f"✓ Using model: {args.model}")

    if args.local_model:
        os.environ["USE_LOCAL_MODEL"] = "true"
        os.environ["LOCAL_MODEL"] = args.local_model
        config = get_config(reload=True)
        logger.info(f"✓ Using local model: {args.local_model}")

    if args.openrouter_key:
        os.environ["OPENROUTER_API_KEY"] = args.openrouter_key
        config = get_config(reload=True)
        logger.info("✓ Using OpenRouter")

    # Data source configuration
    if args.offline_data or args.data_source == "offline":
        config.data.source = "offline"
        logger.info("✓ Using offline dataset")
    elif args.data_source:
        config.data.source = args.data_source
        logger.info(f"✓ Using data source: {args.data_source}")
    else:
        logger.info(f"✓ Using live market data (Yahoo Finance)")

    # Create request
    request = ResearchRequest(
        symbol=args.symbol.upper(),
        horizon=args.horizon,
        market_context=args.context,
        trade_date=args.date,
    )

    # Log request details
    logger.info(f"Symbol: {request.symbol}")
    logger.info(f"Horizon: {request.horizon}")
    logger.info(f"Date: {request.trade_date}")
    if request.market_context:
        logger.info(f"Context: {request.market_context}")

    # Execute analysis
    try:
        result = asyncio.run(execute(request, config=config))
        decision: DecisionDTO = result["decision"]

        # Display results
        print("\n" + "=" * 60)
        print("TRADING ANALYSIS RESULT")
        print("=" * 60)
        print(f"Symbol: {decision.symbol}")
        print(f"Horizon: {decision.horizon}")
        print(f"\n🎯 Recommendation: {decision.recommendation}")
        print(f"📊 Confidence: {decision.confidence:.1%}")
        print(f"\n💡 Rationale:")
        print(f"{decision.rationale}")

        if decision.evidence:
            print(f"\n📋 Evidence by Agent:")
            for agent, evidence in decision.evidence.items():
                print(f"\n  {agent.upper()}:")
                for item in evidence:
                    print(f"    • {item}")

        if decision.key_factors:
            print(f"\n✨ Key Factors:")
            for factor in decision.key_factors:
                print(f"  • {factor}")

        if decision.risks:
            print(f"\n⚠️  Risks:")
            for risk in decision.risks:
                print(f"  • {risk}")

        # Show signal file location
        signal_path = result.get("signal_path")
        if signal_path:
            print(f"\n💾 Signal saved to: {signal_path}")

        # Show policy flags
        flags = result.get("policy_flags")
        if flags:
            print(f"\n🚩 Policy Flags: {', '.join(flags)}")

        print("=" * 60)

        logger.info("Analysis completed successfully")

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("  1. Check your API key: export OPENAI_API_KEY='your-key'")
        print("  2. Use --log-level DEBUG for more details")
        print("  3. Try --offline-data if live data is unavailable")
        raise


if __name__ == "__main__":
    main()
