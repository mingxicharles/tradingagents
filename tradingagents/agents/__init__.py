from __future__ import annotations

from typing import Dict

from ..config import AgentConfig
from ..llm import LLMClient
from .common import JsonResearchAgent


def build_agents(client: LLMClient, configs: list[AgentConfig]) -> Dict[str, JsonResearchAgent]:
    """Factory for configured research agents."""
    return {config.name: JsonResearchAgent(config.name, client, config.system_prompt) for config in configs}
