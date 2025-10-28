from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ResearchRequest:
    """Request payload provided to the orchestrator."""

    symbol: str
    horizon: str
    market_context: str = "general"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentProposal:
    """Structured output from a research agent."""

    agent: str
    action: str
    conviction: float
    thesis: str
    evidence: List[str] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)
    raw_response: Optional[str] = None
    neutral: bool = False

    def ensure_policy_compliance(self) -> None:
        """Force neutral proposals when no evidence is provided."""
        self.conviction = max(0.0, min(self.conviction, 1.0))
        if not self.evidence:
            self.neutral = True
            if self.action.lower() != "hold":
                self.action = "HOLD"
            if self.conviction > 0:
                self.conviction = min(self.conviction, 0.3)


@dataclass
class PositionChange:
    """Tracks how an agent's position changed during debate"""
    agent: str
    change_type: str  # "action", "conviction", or "both"
    before_action: str
    after_action: str
    before_conviction: float
    after_conviction: float
    conviction_delta: float


@dataclass
class DebateTranscript:
    """Captures optional debate round outputs with detailed tracking."""

    summary: str
    position_changes: List[PositionChange] = field(default_factory=list)
    agents_changed_action: int = 0
    agents_changed_conviction: int = 0
    total_conviction_shift: float = 0.0
    converged: bool = False
    concessions: Dict[str, str] = field(default_factory=dict)


@dataclass
class DecisionDTO:
    """
    Final decision emitted by the orchestrator.

    Serves as the fixed contract for future RL integrations.
    """

    symbol: str
    horizon: str
    recommendation: str
    confidence: float
    rationale: str
    evidence: Dict[str, List[str]]
    proposals: Dict[str, AgentProposal]
    debate: Optional[DebateTranscript] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_signal(self) -> Dict[str, object]:
        return {
            "symbol": self.symbol,
            "horizon": self.horizon,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "generated_at": self.generated_at.isoformat(),
        }

    def write_signal(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"{self.symbol.lower()}_{self.generated_at.strftime('%Y%m%dT%H%M%SZ')}.json"
        output_path = directory / filename
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(self.to_signal(), handle, indent=2)
        return output_path

    def to_json(self) -> str:
        def serialize(obj: object) -> object:
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, AgentProposal):
                data = asdict(obj)
                data["evidence"] = list(obj.evidence)
                data["caveats"] = list(obj.caveats)
                return data
            if isinstance(obj, DebateTranscript):
                return asdict(obj)
            return obj

        return json.dumps(asdict(self), default=serialize, indent=2)
