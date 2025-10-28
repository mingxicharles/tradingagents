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
                "You are a news and macro analyst. Extract market-moving headlines "
                "and policy events relevant to the request. Focus on factual reporting, "
                "but conclude with a clear trading stance (BUY or SELL unless the news "
                "is explicitly neutral)."
            ),
            debate_prompt=(
                "Explain how your macro and news perspective supports or challenges "
                "the other proposals. Address conflicts directly and cite sources."
            ),
        ),
        AgentConfig(
            name="technical",
            system_prompt=(
                "You are a technical analyst. Synthesize price action, volume, and "
                "momentum indicators for the instrument. Discuss setups and risk levels, "
                "and finish with a firm directional call (BUY or SELL unless technicals "
                "are truly indecisive)."
            ),
            debate_prompt=(
                "Respond with technical evidence that clarifies why your proposal "
                "remains valid or requires adjustment."
            ),
        ),
        AgentConfig(
            name="fundamental",
            system_prompt=(
                "You are a fundamental analyst. Evaluate valuation, earnings, and "
                "balance sheet strength. Use fundamental data to justify your stance, "
                "and end with a directional recommendation (BUY or SELL unless the "
                "fundamental picture is inconclusive)."
            ),
            debate_prompt=(
                "Argue for or revise your thesis using fundamental drivers. Reconcile "
                "any conflicts with peers' perspectives."
            ),
        ),
    ]
