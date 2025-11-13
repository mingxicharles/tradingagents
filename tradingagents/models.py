"""
Data Models for LLM-Driven Trading Analysis

All data structures used in the trading analysis system.
Designed to be simple, serializable, and suitable for RL training.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AnalysisRequest:
    """
    Request for trading analysis.
    
    Attributes:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        horizon: Time horizon for analysis (e.g., '1d', '1w', '1m')
        market_context: Optional context about current market conditions
        trade_date: Specific date to analyze (defaults to current date)
    """
    symbol: str
    horizon: str = "1d"
    market_context: str = ""
    trade_date: Optional[str] = None
    
    def __post_init__(self):
        self.symbol = self.symbol.upper()
        if not self.trade_date:
            self.trade_date = datetime.now().strftime("%Y-%m-%d")


@dataclass
class AgentProposal:
    """
    Proposal from a single agent.

    Attributes:
        agent: Agent name (e.g., 'news', 'technical', 'fundamental')
        action: Recommended action ('BUY', 'SELL', 'HOLD')
        conviction: Confidence level (0.0 to 1.0)
        thesis: Main argument/thesis
        evidence: List of supporting evidence
        neutral: Whether this is a neutral/fallback proposal
        caveats: List of risk warnings and caveats
        raw_response: Optional raw LLM response text
    """
    agent: str
    action: str
    conviction: float
    thesis: str
    evidence: List[str] = field(default_factory=list)
    neutral: bool = False
    caveats: List[str] = field(default_factory=list)
    raw_response: Optional[str] = None

    def __post_init__(self):
        self.action = self.action.upper()
        self.conviction = max(0.0, min(1.0, self.conviction))  # Clamp to [0, 1]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ControllerPlan:
    """
    Analysis plan created by LLM controller.
    
    Attributes:
        selected_agents: List of agent names to use
        execution_mode: How to execute ('parallel' or 'sequential')
        agent_tasks: Specific tasks for each agent
        reasoning: Controller's reasoning for this plan
    """
    selected_agents: List[str]
    execution_mode: str = "parallel"
    agent_tasks: Dict[str, str] = field(default_factory=dict)
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class EvaluationResult:
    """
    Evaluation of agent proposals by LLM controller.
    
    Attributes:
        has_conflict: Whether there are conflicting recommendations
        conflict_description: Description of the conflicts
        recommend_debate: Whether debate is recommended
        debate_focus: What should be debated
        consensus_points: Points where agents agree
        credibility_ranking: Credibility score for each agent
        reasoning: Controller's evaluation reasoning
    """
    has_conflict: bool
    conflict_description: str = ""
    recommend_debate: bool = False
    debate_focus: str = ""
    consensus_points: List[str] = field(default_factory=list)
    credibility_ranking: Dict[str, float] = field(default_factory=dict)
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PositionChange:
    """
    Records how an agent's position changed during debate.

    Attributes:
        agent: Agent name
        change_type: Type of change ('action', 'conviction', or 'both')
        before_action: Action before debate
        after_action: Action after debate
        before_conviction: Conviction before debate
        after_conviction: Conviction after debate
        conviction_delta: Change in conviction
    """
    agent: str
    change_type: str
    before_action: str
    after_action: str
    before_conviction: float
    after_conviction: float
    conviction_delta: float


@dataclass
class DebateTranscript:
    """
    Transcript of a debate round.

    Attributes:
        summary: Text summary of debate
        position_changes: List of position changes
        agents_changed_action: Number of agents that changed their action
        agents_changed_conviction: Number of agents that changed conviction
        total_conviction_shift: Total absolute conviction change
        converged: Whether debate converged to agreement
    """
    summary: str
    position_changes: List[PositionChange] = field(default_factory=list)
    agents_changed_action: int = 0
    agents_changed_conviction: int = 0
    total_conviction_shift: float = 0.0
    converged: bool = False


@dataclass
class DecisionDTO:
    """
    Decision Data Transfer Object used by orchestrator.

    This is the output format from the orchestrator workflow.
    Simpler than FinalDecision, focused on immediate trading signal.

    Attributes:
        symbol: Stock ticker
        horizon: Time horizon
        recommendation: Final recommendation ('BUY', 'SELL', 'HOLD')
        confidence: Confidence level (0.0 to 1.0)
        rationale: Detailed explanation
        evidence: Evidence map by agent
        proposals: All agent proposals
        debate: Optional debate transcript
    """
    symbol: str
    horizon: str
    recommendation: str
    confidence: float
    rationale: str
    evidence: Dict[str, List[str]] = field(default_factory=dict)
    proposals: Dict[str, AgentProposal] = field(default_factory=dict)
    debate: Optional[DebateTranscript] = None

    def __post_init__(self):
        self.recommendation = self.recommendation.upper()
        self.confidence = max(0.0, min(1.0, self.confidence))

    def write_signal(self, output_dir: Path) -> Path:
        """
        Write decision to signal file.

        Args:
            output_dir: Directory to write signal

        Returns:
            Path to written signal file
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
        filename = f"{self.symbol.lower()}_{timestamp}.json"
        filepath = output_dir / filename

        # Create signal payload
        signal = {
            "symbol": self.symbol,
            "horizon": self.horizon,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Add debate info if present
        if self.debate:
            signal["debate"] = {
                "converged": self.debate.converged,
                "agents_changed_action": self.debate.agents_changed_action,
                "agents_changed_conviction": self.debate.agents_changed_conviction,
                "total_conviction_shift": self.debate.total_conviction_shift,
            }

        with open(filepath, 'w') as f:
            json.dump(signal, f, indent=2)

        return filepath


@dataclass
class DebateRecord:
    """
    Record of debate process.

    Attributes:
        rounds: Number of debate rounds
        history: Complete debate history
        converged: Whether debate converged to agreement
    """
    rounds: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)
    converged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class FinalDecision:
    """
    Final investment decision.
    
    This is the main output of the system and serves as the
    contract for downstream systems (execution, RL training, etc.).
    
    Attributes:
        symbol: Stock ticker
        horizon: Time horizon
        recommendation: Final recommendation ('BUY', 'SELL', 'HOLD')
        confidence: Confidence level (0.0 to 1.0)
        rationale: Detailed explanation
        key_factors: Key factors driving the decision
        risks: Identified risks and caveats
        agent_weights: Weight given to each agent
        agent_proposals: All agent proposals
        evaluation: Evaluation result
        timestamp: Decision timestamp (ISO format)
    """
    symbol: str
    horizon: str
    recommendation: str
    confidence: float
    rationale: str
    key_factors: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    agent_weights: Dict[str, float] = field(default_factory=dict)
    agent_proposals: Dict[str, AgentProposal] = field(default_factory=dict)
    evaluation: Optional[EvaluationResult] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def __post_init__(self):
        self.recommendation = self.recommendation.upper()
        self.confidence = max(0.0, min(1.0, self.confidence))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "symbol": self.symbol,
            "horizon": self.horizon,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "key_factors": self.key_factors,
            "risks": self.risks,
            "agent_weights": self.agent_weights,
            "timestamp": self.timestamp
        }
        
        # Add agent proposals
        data["agent_proposals"] = {
            name: prop.to_dict() for name, prop in self.agent_proposals.items()
        }
        
        # Add evaluation if present
        if self.evaluation:
            data["evaluation"] = self.evaluation.to_dict()
        
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def save(self, output_dir: Path) -> Path:
        """
        Save decision to JSON file.
        
        Args:
            output_dir: Directory to save to
            
        Returns:
            Path to saved file
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.symbol.lower()}_{timestamp}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(self.to_json())
        
        return filepath


@dataclass
class Trajectory:
    """
    Complete decision-making trajectory for RL training.
    
    Records every step of the decision process:
    - Planning
    - Agent execution  
    - Evaluation
    - Debate (if any)
    - Final decision
    
    This provides the state-action-reward data needed for RL.
    """
    steps: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, step_name: str, data: Any):
        """
        Add a step to the trajectory.
        
        Args:
            step_name: Name of the step (e.g., 'plan', 'evaluation')
            data: Step data (will be converted to dict if possible)
        """
        step = {
            "step": step_name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": self._serialize(data)
        }
        self.steps.append(step)
    
    def _serialize(self, data: Any) -> Any:
        """Convert data to serializable format."""
        if hasattr(data, 'to_dict'):
            return data.to_dict()
        elif isinstance(data, dict):
            return {k: self._serialize(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize(item) for item in data]
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            return str(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "steps": self.steps,
            "metadata": self.metadata,
            "total_steps": len(self.steps)
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def save(self, output_dir: Path, symbol: str = "unknown"):
        """
        Save trajectory to file.
        
        Args:
            output_dir: Directory to save to
            symbol: Stock symbol (for filename)
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trajectory_{symbol.lower()}_{timestamp}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(self.to_json())
        
        return filepath


def load_decision(filepath: Path) -> FinalDecision:
    """
    Load a decision from JSON file.
    
    Args:
        filepath: Path to decision JSON file
        
    Returns:
        FinalDecision object
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Reconstruct agent proposals
    agent_proposals = {}
    for name, prop_data in data.get("agent_proposals", {}).items():
        agent_proposals[name] = AgentProposal(**prop_data)
    
    # Reconstruct evaluation
    evaluation = None
    if "evaluation" in data:
        evaluation = EvaluationResult(**data["evaluation"])
    
    return FinalDecision(
        symbol=data["symbol"],
        horizon=data["horizon"],
        recommendation=data["recommendation"],
        confidence=data["confidence"],
        rationale=data["rationale"],
        key_factors=data.get("key_factors", []),
        risks=data.get("risks", []),
        agent_weights=data.get("agent_weights", {}),
        agent_proposals=agent_proposals,
        evaluation=evaluation,
        timestamp=data.get("timestamp", "")
    )


def load_trajectory(filepath: Path) -> Trajectory:
    """
    Load a trajectory from JSON file.
    
    Args:
        filepath: Path to trajectory JSON file
        
    Returns:
        Trajectory object
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    trajectory = Trajectory()
    trajectory.steps = data.get("steps", [])
    trajectory.metadata = data.get("metadata", {})
    
    return trajectory


# Aliases for backward compatibility and convenience
# Note: DecisionDTO and FinalDecision are now separate classes!
# - DecisionDTO: Used by orchestrator (simpler, for immediate signals)
# - FinalDecision: Used by controller (richer, for RL training)
ResearchRequest = AnalysisRequest
