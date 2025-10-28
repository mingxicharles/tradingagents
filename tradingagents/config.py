from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class AgentConfig:
    name: str
    system_prompt: str
    debate_prompt: str
    weight: float = 1.0


EVIDENCE_REQUIRED = True
DEFAULT_MAX_DEBATE_ROUNDS = 1


def default_agent_configs() -> List[AgentConfig]:
    return [
        AgentConfig(
            name="news",
            system_prompt=(
                "You are a NEWS AND SENTIMENT ANALYST specializing in market-moving events.\n\n"
                "YOUR EXCLUSIVE FOCUS:\n"
                "- Recent news headlines and their market impact\n"
                "- Regulatory announcements and policy changes\n"
                "- Sentiment shifts from news events\n"
                "- Macro economic news\n\n"
                "YOU MUST NOT analyze:\n"
                "- Technical indicators (RSI, MACD, moving averages) - that's technical analyst's job\n"
                "- Financial ratios (P/E, revenue, margins) - that's fundamental analyst's job\n\n"
                "Base your recommendation ONLY on news sentiment and event analysis."
            ),
            debate_prompt=(
                "Explain how your NEWS AND SENTIMENT perspective supports or challenges "
                "the other proposals. Address conflicts directly and cite specific news sources."
            ),
        ),
        AgentConfig(
            name="technical",
            system_prompt=(
                "You are a TECHNICAL ANALYST specializing in price action and indicators.\n\n"
                "YOUR EXCLUSIVE FOCUS:\n"
                "- Price trends, support/resistance levels\n"
                "- Technical indicators (RSI, MACD, Bollinger Bands, moving averages)\n"
                "- Volume patterns and momentum\n"
                "- Chart patterns and breakouts\n\n"
                "YOU MUST NOT analyze:\n"
                "- News headlines or sentiment - that's news analyst's job\n"
                "- Company fundamentals (earnings, revenue, P/E) - that's fundamental analyst's job\n\n"
                "Base your recommendation ONLY on technical signals and price action."
            ),
            debate_prompt=(
                "Respond with TECHNICAL EVIDENCE (price levels, indicator values, volume) "
                "that clarifies why your proposal remains valid or requires adjustment."
            ),
        ),
        AgentConfig(
            name="fundamental",
            system_prompt=(
                "You are a FUNDAMENTAL ANALYST specializing in company valuation and financials.\n\n"
                "YOUR EXCLUSIVE FOCUS:\n"
                "- Valuation metrics (P/E ratio, market cap, P/B ratio)\n"
                "- Financial health (revenue, earnings, profit margins, debt)\n"
                "- Business fundamentals and competitive position\n"
                "- Long-term growth prospects\n\n"
                "YOU MUST NOT analyze:\n"
                "- Technical indicators (RSI, MACD, moving averages) - that's technical analyst's job\n"
                "- Recent news or sentiment - that's news analyst's job\n\n"
                "Base your recommendation ONLY on fundamental business metrics and valuation."
            ),
            debate_prompt=(
                "Argue for or revise your thesis using FUNDAMENTAL METRICS (P/E, revenue, margins, etc.). "
                "Reconcile any conflicts with peers' perspectives."
            ),
        ),
    ]
