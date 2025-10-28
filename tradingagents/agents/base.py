from __future__ import annotations

import textwrap
from abc import ABC, abstractmethod
from typing import Dict, List, Mapping

from ..llm import LLMClient
from ..models import AgentProposal, ResearchRequest


class AgentContext(Mapping[str, AgentProposal]):
    """Read-only view of current agent proposals."""

    def __init__(self, proposals: Dict[str, AgentProposal]):
        self._proposals = proposals

    def __getitem__(self, key: str) -> AgentProposal:
        return self._proposals[key]

    def __iter__(self):
        return iter(self._proposals)

    def __len__(self) -> int:
        return len(self._proposals)

    def get(self, key: str, default=None):
        return self._proposals.get(key, default)

    def summary(self) -> str:
        if not self._proposals:
            return "No peer proposals yet."
        lines: List[str] = []
        for proposal in self._proposals.values():
            lines.append(
                f"- {proposal.agent}: action={proposal.action}, "
                f"conviction={proposal.conviction:.2f}, neutral={proposal.neutral}"
            )
        return "\n".join(lines)


class ResearchAgent(ABC):
    """Abstract agent that wraps LLM prompting."""

    def __init__(self, name: str, client: LLMClient, system_prompt: str) -> None:
        self.name = name
        self.client = client
        self.system_prompt = system_prompt

    async def gather(self, request: ResearchRequest, peers: AgentContext) -> AgentProposal:
        content = await self._call_llm(self.build_prompt(request, peers))
        proposal = self.parse_response(content)
        proposal.agent = self.name
        proposal.ensure_policy_compliance()
        return proposal

    async def debate(
        self,
        request: ResearchRequest,
        peers: AgentContext,
        prior: AgentProposal,
        prompt: str,
    ) -> AgentProposal:
        content = await self._call_llm(self.build_debate_prompt(request, peers, prior, prompt))
        proposal = self.parse_response(content)
        proposal.agent = self.name
        proposal.ensure_policy_compliance()
        return proposal

    async def _call_llm(self, prompt: List[Dict[str, str]]) -> str:
        return await self.client.retrying_complete(prompt, max_tokens=800)

    def build_prompt(self, request: ResearchRequest, peers: AgentContext) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self._request_block(request, peers)},
        ]

    def build_debate_prompt(
        self,
        request: ResearchRequest,
        peers: AgentContext,
        prior: AgentProposal,
        debate_instruction: str,
    ) -> List[Dict[str, str]]:
        # Format full evidence from peers for detailed debate
        peer_details = self._format_peer_evidence(peers, prior)
        
        instruction = textwrap.dedent(
            f"""
            === DEBATE ROUND ===
            
            YOUR ORIGINAL POSITION:
            Action: {prior.action}
            Conviction: {prior.conviction:.2f}
            Thesis: {prior.thesis}
            Evidence:
            {self._format_evidence_list(prior.evidence)}
            Caveats:
            {self._format_evidence_list(prior.caveats)}
            
            {peer_details}
            
            DEBATE DIRECTIVE:
            {debate_instruction}
            
            YOUR TASK:
            1. Review opposing arguments and their specific evidence
            2. Address each key counterargument directly
            3. Strengthen your position OR revise if opposing evidence is compelling
            4. Update your conviction based on debate quality:
               - If your evidence withstands scrutiny → maintain or increase conviction
               - If opponents raise valid concerns → reduce conviction
               - If arguments are balanced → move toward HOLD
            
            Return updated JSON with conviction adjusted based on debate strength.
            """
        ).strip()
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self._request_block(request, peers)},
            {"role": "assistant", "content": prior.raw_response or prior.thesis},
            {"role": "user", "content": instruction},
        ]
    
    def _format_evidence_list(self, items: List[str]) -> str:
        """Format evidence/caveats as bullet list"""
        if not items:
            return "  (none provided)"
        return "\n".join(f"  - {item}" for item in items)
    
    def _format_peer_evidence(self, peers: AgentContext, prior: AgentProposal) -> str:
        """Format detailed peer positions, highlighting opposing views"""
        if not peers:
            return "No peer positions available."
        
        my_action = prior.action.upper()
        opposing = []
        agreeing = []
        
        for peer_name, peer_prop in peers.items():
            if peer_prop.agent == self.name:
                continue  # Skip self
            
            peer_action = peer_prop.action.upper()
            
            # Categorize as opposing or agreeing
            if peer_action != my_action and peer_action != "HOLD" and my_action != "HOLD":
                opposing.append((peer_name, peer_prop))
            else:
                agreeing.append((peer_name, peer_prop))
        
        result = []
        
        if opposing:
            result.append("OPPOSING POSITIONS (focus your rebuttal here):")
            for name, prop in opposing:
                result.append(f"\n{name} argues for {prop.action} (conviction: {prop.conviction:.2f}):")
                result.append(f"  Thesis: {prop.thesis}")
                result.append(f"  Evidence:")
                result.append(self._format_evidence_list(prop.evidence))
        
        if agreeing:
            result.append("\n\nSUPPORTING POSITIONS:")
            for name, prop in agreeing:
                result.append(f"  - {name}: {prop.action} (conviction: {prop.conviction:.2f})")
        
        return "\n".join(result) if result else "No peer positions available."
    
    def _get_role_specific_instructions(self) -> str:
        """Get instructions specific to this agent's role"""
        if self.name == "technical":
            return textwrap.dedent("""
            YOUR ROLE: Technical Analyst
            FOCUS: Price action, technical indicators (RSI, MACD, MA), volume, chart patterns
            AVOID: News sentiment, fundamental metrics (P/E, revenue)
            """).strip()
        elif self.name == "fundamental":
            return textwrap.dedent("""
            YOUR ROLE: Fundamental Analyst
            FOCUS: Valuation (P/E, P/B), financials (revenue, margins), business quality
            AVOID: Technical indicators (RSI, MACD), news headlines
            """).strip()
        elif self.name == "news":
            return textwrap.dedent("""
            YOUR ROLE: News & Sentiment Analyst
            FOCUS: Recent news, regulatory events, sentiment shifts, macro developments
            AVOID: Technical indicators (RSI, MACD), financial ratios (P/E, revenue)
            """).strip()
        else:
            return f"YOUR ROLE: {self.name} analyst"

    def _request_block(self, request: ResearchRequest, peers: AgentContext) -> str:
        # Add role-specific instructions
        role_instructions = self._get_role_specific_instructions()
        
        return textwrap.dedent(
            f"""
            Focus ticker: {request.symbol}
            Horizon: {request.horizon}
            Market context: {request.market_context}
            
            {role_instructions}

            Peer snapshot:
            {peers.summary()}

            Produce a JSON object with keys:
              action: BUY/SELL/HOLD recommendation string
              conviction: float 0-1 for confidence (see scale below)
              thesis: brief paragraph summary
              evidence: array of 2-4 specific bullet strings citing data/reports
              caveats: array of risk warnings

            Conviction Scale (IMPORTANT - use full range):
              0.90-1.00: Exceptional conviction - multiple strong signals align, low downside risk
              0.75-0.89: High conviction - clear directional signals with solid evidence
              0.60-0.74: Moderate conviction - favorable setup but some uncertainty remains
              0.45-0.59: Low conviction - weak signals or mixed evidence
              0.20-0.44: Very low conviction - highly uncertain or contradictory data
              0.00-0.19: No conviction - insufficient data or neutral stance

            Guidance:
              - Default to BUY or SELL. Return HOLD only if evidence is genuinely contradictory or
                insufficient to justify an entry.
              - Tie each evidence bullet to concrete data (price levels, volume %, revenue figures, etc.).
              - Base conviction STRICTLY on evidence strength - don't default to 0.75!
              - Strong technical breakout + volume confirmation = high conviction (0.80-0.90)
              - Single indicator or weak signal = low conviction (0.50-0.65)
              - Conflicting signals or missing key data = very low conviction (0.30-0.50)
              - Keep responses concise and free of Markdown fences.
            """
        ).strip()

    @abstractmethod
    def parse_response(self, content: str) -> AgentProposal:
        ...
