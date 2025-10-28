from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple, TypedDict

from langgraph.graph import END, StateGraph

from .agents.base import AgentContext, ResearchAgent
from .config import DEFAULT_MAX_DEBATE_ROUNDS, AgentConfig, default_agent_configs
from .models import AgentProposal, DecisionDTO, DebateTranscript, ResearchRequest


class TradingState(TypedDict, total=False):
    request: ResearchRequest
    proposals: Dict[str, AgentProposal]
    errors: Dict[str, str]
    policy_flags: List[str]
    debate_round: int
    debate: Optional[DebateTranscript]
    decision: Optional[DecisionDTO]
    signal_path: Optional[Path]
    next_action: Optional[Literal["debate", "decision", "continue"]]


class TradingOrchestrator:
    """Supervisor that coordinates research agents via LangGraph."""

    def __init__(
        self,
        agents: Dict[str, ResearchAgent],
        agent_configs: List[AgentConfig],
        max_debate_rounds: int = DEFAULT_MAX_DEBATE_ROUNDS,
        retries: int = 2,
        signals_dir: Path | None = None,
    ) -> None:
        self.agents = agents
        self.agent_configs = {config.name: config for config in agent_configs}
        self.max_debate_rounds = max_debate_rounds
        self.retries = retries
        self.signals_dir = signals_dir or Path("signals")
        # Basic equal weighting, overridable per config if needed.
        self.weights = {name: self.agent_configs[name].weight for name in self.agents}

    def build_graph(self) -> StateGraph[TradingState]:
        """Build the LangGraph with explicit routing nodes.
        
        Graph flow:
        1. orchestrator: Fan out to agents in parallel, gather results
        2. policy_check: Evaluate if debate is needed (conditional routing)
        3. debate: Run debate round when conflicts exist
        4. finalize: Produce DecisionDTO from proposals
        5. write_signal: Persist signal to JSON
        """
        graph: StateGraph[TradingState] = StateGraph(TradingState)
        
        # Core orchestration nodes
        graph.add_node("orchestrator", self._orchestrator_node)
        graph.add_node("policy_check", self._policy_check_node)
        graph.add_node("debate", self._debate_node)
        graph.add_node("finalize", self._finalize_node)
        graph.add_node("write_signal", self._write_signal_node)
        
        # Entry point
        graph.set_entry_point("orchestrator")
        
        # Orchestrator always goes to policy check
        graph.add_edge("orchestrator", "policy_check")
        
        # Conditional routing: debate or finalize?
        graph.add_conditional_edges(
            "policy_check",
            self._should_debate,
            {
                "debate": "debate",
                "finalize": "finalize",
            },
        )
        
        # After debate, check again if more debate needed
        graph.add_conditional_edges(
            "debate",
            self._should_continue_debate,
            {
                "debate": "debate",  # Continue debating
                "finalize": "finalize",  # Proceed to decision
            },
        )
        
        # Finalize always writes signal
        graph.add_edge("finalize", "write_signal")
        graph.add_edge("write_signal", END)
        
        return graph

    async def _orchestrator_node(self, state: TradingState) -> TradingState:
        """Fan out to all agents in parallel and gather proposals."""
        request = state["request"]
        proposals = {}
        errors = {}
        
        # Use lock to safely share progress between parallel agents
        lock = asyncio.Lock()
        
        async def run_agent(name: str, agent: ResearchAgent) -> None:
            nonlocal proposals, errors
            last_error = "unknown failure"
            proposal = None
            
            for attempt in range(self.retries):
                try:
                    # Get snapshot of current proposals for peer context
                    async with lock:
                        snapshot = dict(proposals)
                    context = AgentContext(snapshot)
                    
                    proposal = await agent.gather(request, context)
                    async with lock:
                        proposals[name] = proposal
                    return
                except Exception as err:
                    last_error = str(err)
                    if attempt < self.retries - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))
            
            # Convert failure to neutral proposal
            proposal = AgentProposal(
                agent=name,
                action="HOLD",
                conviction=0.0,
                thesis=f"Unable to produce proposal: {last_error}",
                evidence=[],
                caveats=["Failure converted to neutral recommendation"],
                neutral=True,
            )
            async with lock:
                proposals[name] = proposal
            errors[name] = last_error
        
        # Execute all agents in parallel
        await asyncio.gather(*(run_agent(name, agent) for name, agent in self.agents.items()))
        
        policy_flags = self._policy_checks(proposals)
        
        return {
            "proposals": proposals,
            "errors": errors,
            "policy_flags": policy_flags,
            "debate_round": 0,
        }

    async def _policy_check_node(self, state: TradingState) -> TradingState:
        """Check if debate is required based on proposals."""
        proposals = state.get("proposals", {})
        debate_round = state.get("debate_round", 0)
        
        needs_debate = self._requires_debate(proposals) and debate_round < self.max_debate_rounds
        
        return {
            "next_action": "debate" if needs_debate else "finalize",
        }

    async def _debate_node(self, state: TradingState) -> TradingState:
        """Execute a debate round and update proposals."""
        request = state["request"]
        proposals = state.get("proposals", {})
        debate_round = state.get("debate_round", 0)
        
        updated_proposals, debate = await self._run_debate(request, proposals)
        policy_flags = self._policy_checks(updated_proposals)
        
        # Check if more debate rounds needed
        needs_more_debate = self._requires_debate(updated_proposals) and debate_round + 1 < self.max_debate_rounds
        
        return {
            "proposals": updated_proposals,
            "debate": debate,
            "debate_round": debate_round + 1,
            "policy_flags": policy_flags,
            "next_action": "debate" if needs_more_debate else "finalize",
        }

    def _should_debate(self, state: TradingState) -> Literal["debate", "finalize"]:
        """Conditional routing: should we debate or finalize?"""
        action = state.get("next_action", "finalize")
        if action == "debate":
            return "debate"
        return "finalize"

    def _should_continue_debate(self, state: TradingState) -> Literal["debate", "finalize"]:
        """Conditional routing: continue debate or finalize?"""
        action = state.get("next_action", "finalize")
        if action == "debate":
            return "debate"
        return "finalize"

    async def _finalize_node(self, state: TradingState) -> TradingState:
        """Finalize decision from proposals."""
        request = state["request"]
        proposals = state.get("proposals", {})
        debate = state.get("debate")
        policy_flags = state.get("policy_flags", [])
        
        decision = self._finalize_decision(request, proposals, debate, policy_flags)
        
        return {
            "decision": decision,
        }

    async def _write_signal_node(self, state: TradingState) -> TradingState:
        """Write signal to file."""
        decision = state.get("decision")
        if not decision:
            raise RuntimeError("Decision missing before writing signal.")
        path = decision.write_signal(self.signals_dir)
        return {"signal_path": path}

    def _requires_debate(self, proposals: Dict[str, AgentProposal]) -> bool:
        actionable = {p.action.upper() for p in proposals.values() if not p.neutral}
        actionable.discard("HOLD")
        return len(actionable) > 1

    async def _run_debate(
        self,
        request: ResearchRequest,
        proposals: Dict[str, AgentProposal],
    ) -> Tuple[Dict[str, AgentProposal], DebateTranscript]:
        updated = dict(proposals)
        context = AgentContext(proposals)
        transcript_lines: List[str] = []

        async def run_agent(name: str, agent: ResearchAgent) -> None:
            prior = proposals[name]
            debate_instruction = self.agent_configs[name].debate_prompt
            revised = await agent.debate(request, context, prior, debate_instruction)
            updated[name] = revised
            transcript_lines.append(
                f"{name}: action={revised.action} conv={revised.conviction:.2f} thesis={revised.thesis}"
            )

        await asyncio.gather(*(run_agent(name, agent) for name, agent in self.agents.items()))
        transcript = DebateTranscript(summary="\n".join(transcript_lines))
        return updated, transcript

    def _policy_checks(self, proposals: Dict[str, AgentProposal]) -> List[str]:
        flags: List[str] = []
        for proposal in proposals.values():
            if not proposal.evidence:
                flags.append(f"{proposal.agent}:no_evidence")
        if self._requires_debate(proposals):
            flags.append("conflicting_actions")
        return flags

    def _finalize_decision(
        self,
        request: ResearchRequest,
        proposals: Dict[str, AgentProposal],
        debate: Optional[DebateTranscript],
        policy_flags: List[str],
    ) -> DecisionDTO:
        weighted = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        rationale_lines: List[str] = []
        evidence_map: Dict[str, List[str]] = {}

        for name, proposal in proposals.items():
            weight = self.weights.get(name, 1.0)
            action = "HOLD" if proposal.neutral else proposal.action.upper()
            weighted[action] = weighted.get(action, 0.0) + (proposal.conviction * weight)
            rationale_lines.append(f"{name}: {proposal.thesis}")
            evidence_map[name] = list(proposal.evidence)

        max_value = max(weighted.values()) if weighted else 0.0
        top_actions = [action for action, value in weighted.items() if value == max_value]
        if max_value == 0.0:
            recommendation = "HOLD"
        elif "HOLD" in top_actions and len(top_actions) > 1:
            recommendation = "HOLD"
        else:
            recommendation = top_actions[0]
        total_weight = sum(self.weights.values()) or 1.0
        confidence = min(1.0, weighted.get(recommendation, 0.0) / total_weight)
        if recommendation == "HOLD" and max_value == 0.0:
            confidence = 0.0
        if "conflicting_actions" in policy_flags and confidence > 0.6:
            confidence = 0.6  # dampen confidence when teams disagree

        rationale = "\n".join(rationale_lines)
        decision = DecisionDTO(
            symbol=request.symbol,
            horizon=request.horizon,
            recommendation=recommendation,
            confidence=round(confidence, 2),
            rationale=rationale,
            evidence=evidence_map,
            proposals=proposals,
            debate=debate,
        )
        return decision


def build_orchestrator(agents: Dict[str, ResearchAgent]) -> TradingOrchestrator:
    configs = default_agent_configs()
    return TradingOrchestrator(agents=agents, agent_configs=configs)
