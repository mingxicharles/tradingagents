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
        instruction = textwrap.dedent(
            f"""
            Original proposal summary:
            action={prior.action}
            conviction={prior.conviction}
            thesis={prior.thesis}
            evidence={prior.evidence}
            caveats={prior.caveats}

            Peer positions:
            {peers.summary()}

            Debate directive:
            {debate_instruction}
            """
        ).strip()
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self._request_block(request, peers)},
            {"role": "assistant", "content": prior.raw_response or prior.thesis},
            {"role": "user", "content": instruction},
        ]

    def _request_block(self, request: ResearchRequest, peers: AgentContext) -> str:
        return textwrap.dedent(
            f"""
            Focus ticker: {request.symbol}
            Horizon: {request.horizon}
            Market context: {request.market_context}

            Peer snapshot:
            {peers.summary()}

            Produce a JSON object with keys:
              action: BUY/SELL/HOLD recommendation string
              conviction: float 0-1 for confidence
              thesis: brief paragraph summary
              evidence: array of 2-4 specific bullet strings citing data/reports
              caveats: array of risk warnings

            Guidance:
              - Default to BUY or SELL. Return HOLD only if the evidence is genuinely contradictory or
                there is insufficient information to justify an entry.
              - Tie each evidence bullet to concrete data (price levels, volume %, revenue figures, etc.).
              - Ensure conviction reflects the strength of backing evidence (>=0.55 for decisive calls).
              - Keep responses concise and free of Markdown fences.
            """
        ).strip()

    @abstractmethod
    def parse_response(self, content: str) -> AgentProposal:
        ...
