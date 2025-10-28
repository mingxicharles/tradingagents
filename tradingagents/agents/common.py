from __future__ import annotations

import json
from typing import Any, Dict

from .base import ResearchAgent
from ..models import AgentProposal


class JsonResearchAgent(ResearchAgent):
    """Parses agent responses as JSON with graceful fallbacks."""

    def parse_response(self, content: str) -> AgentProposal:
        def unwrap_code_fence(text: str) -> str:
            stripped = text.strip()
            if not stripped.startswith("```"):
                return stripped
            lines = stripped.splitlines()
            if lines:
                first = lines[0]
                if first.startswith("```"):
                    lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            return "\n".join(lines).strip()

        payload = None
        parse_attempts = [content, unwrap_code_fence(content)]
        for candidate in parse_attempts:
            try:
                payload = json.loads(candidate)
                break
            except json.JSONDecodeError:
                continue
        if payload is None:
            payload = {"action": "HOLD", "conviction": 0.0, "thesis": content}

        def coerce_list(value: Any) -> list[str]:
            if isinstance(value, list):
                return [str(item) for item in value]
            if isinstance(value, str) and value.strip():
                return [value.strip()]
            return []

        try:
            conviction = float(payload.get("conviction", 0.0))
        except (TypeError, ValueError):
            conviction = 0.0
        conviction = max(0.0, min(1.0, conviction))

        return AgentProposal(
            agent=self.name,
            action=str(payload.get("action", "HOLD")).upper(),
            conviction=conviction,
            thesis=str(payload.get("thesis", "")).strip(),
            evidence=coerce_list(payload.get("evidence", [])),
            caveats=coerce_list(payload.get("caveats", [])),
            raw_response=content,
        )
