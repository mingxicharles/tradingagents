"""
Simplified Agent Implementation

Agents focus solely on analysis, not on workflow control.
The LLM Controller handles all orchestration.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional

from ..llm import LLMClient
from ..models import AnalysisRequest, AgentProposal


class TradingAgent:
    """
    Base class for trading analysis agents.
    
    Agents are specialists that:
    1. Fetch relevant data
    2. Analyze that data from their perspective
    3. Provide recommendations with evidence
    4. Participate in debates when asked
    
    They do NOT control workflow or orchestration.
    """
    
    def __init__(
        self,
        name: str,
        llm_client: LLMClient,
        system_prompt: str,
        data_tools: Optional[List[Callable]] = None
    ):
        """
        Initialize agent.
        
        Args:
            name: Agent name (e.g., 'news', 'technical')
            llm_client: LLM client for analysis
            system_prompt: System prompt defining agent's role and expertise
            data_tools: Optional list of data fetching functions
        """
        self.name = name
        self.llm = llm_client
        self.system_prompt = system_prompt
        self.data_tools = data_tools or []
    
    async def analyze(
        self,
        request: AnalysisRequest,
        specific_task: Optional[str] = None
    ) -> AgentProposal:
        """
        Perform analysis and return proposal.
        
        Args:
            request: Analysis request
            specific_task: Optional specific task from controller
            
        Returns:
            Agent's proposal with recommendation and evidence
        """
        # Fetch data
        data_context = await self._fetch_data(request)
        
        # Create analysis prompt
        prompt = self._create_analysis_prompt(request, data_context, specific_task)
        
        # Get LLM analysis
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm.complete(messages, max_tokens=800)
        
        # Parse response into proposal
        proposal = self._parse_proposal(response)
        
        return proposal
    
    async def debate(
        self,
        initial_proposal: AgentProposal,
        peer_proposals: Dict[str, AgentProposal],
        debate_focus: str,
        specific_instruction: str,
        request: AnalysisRequest
    ) -> AgentProposal:
        """
        Participate in debate and potentially revise proposal.
        
        Args:
            initial_proposal: Agent's initial proposal
            peer_proposals: Other agents' proposals
            debate_focus: What to focus on in debate
            specific_instruction: Specific instruction from controller
            request: Original analysis request
            
        Returns:
            Revised (or unchanged) proposal
        """
        # Format peer arguments
        peer_summary = self._format_peer_proposals(peer_proposals, initial_proposal)
        
        # Create debate prompt
        prompt = f"""You are participating in a structured debate about {request.symbol}.

YOUR INITIAL POSITION:
- Action: {initial_proposal.action}
- Conviction: {initial_proposal.conviction:.2f}
- Thesis: {initial_proposal.thesis}
- Evidence: {', '.join(initial_proposal.evidence[:3])}

OTHER ANALYSTS' POSITIONS:
{peer_summary}

DEBATE FOCUS: {debate_focus}

MODERATOR INSTRUCTION: {specific_instruction}

TASK:
Consider the counterarguments and evidence from other analysts.
You may:
1. Defend your position with additional evidence
2. Adjust your conviction based on new insights
3. Change your recommendation if convinced by strong arguments

Respond with updated analysis in JSON format:
{{
    "action": "BUY/SELL/HOLD",
    "conviction": 0.0-1.0,
    "thesis": "Your updated thesis",
    "evidence": ["Evidence point 1", "Evidence point 2", ...],
    "changes_made": "What changed from your initial position and why"
}}

Base your response on your area of expertise: {self.name} analysis."""

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm.complete(messages, max_tokens=800)
        
        # Parse revised proposal
        revised_proposal = self._parse_proposal(response)
        
        return revised_proposal
    
    async def _fetch_data(self, request: AnalysisRequest) -> str:
        """
        Fetch relevant data using available tools.
        
        Args:
            request: Analysis request
            
        Returns:
            Formatted data context string
        """
        if not self.data_tools:
            return "No real-time data available. Use your knowledge base."
        
        data_results = []
        
        for tool in self.data_tools:
            try:
                # Call data tool
                result = await asyncio.to_thread(
                    tool,
                    request.symbol,
                    request.trade_date
                )
                data_results.append(f"{tool.__name__}:\n{result}\n")
            except Exception as e:
                data_results.append(f"{tool.__name__}: Error - {str(e)}\n")
        
        return "\n".join(data_results) if data_results else "No data fetched."
    
    def _create_analysis_prompt(
        self,
        request: AnalysisRequest,
        data_context: str,
        specific_task: Optional[str]
    ) -> str:
        """Create the analysis prompt."""
        prompt = f"""Analyze {request.symbol} for a {request.horizon} investment decision.

MARKET CONTEXT: {request.market_context or 'General market conditions'}

{f'SPECIFIC TASK: {specific_task}' if specific_task else ''}

AVAILABLE DATA:
{data_context}

ANALYSIS REQUIREMENTS:
1. Recommendation: BUY, SELL, or HOLD
2. Conviction: 0.0 to 1.0 based on evidence strength
   - 0.8-1.0: Strong, well-supported signal
   - 0.6-0.8: Moderate signal with good evidence
   - 0.4-0.6: Weak signal or mixed indicators
   - 0.0-0.4: Very weak or insufficient evidence
3. Thesis: Your main argument (1-2 sentences)
4. Evidence: Specific data points supporting your thesis (cite exact numbers)

IMPORTANT - CONVICTION SCORING:
- Base conviction on EVIDENCE STRENGTH, not default values
- Strong technical breakout + volume = high conviction (0.75-0.85)
- Single weak indicator = low conviction (0.45-0.60)
- Missing key data = very low conviction (0.20-0.40)

OUTPUT FORMAT (JSON):
{{
    "action": "BUY/SELL/HOLD",
    "conviction": e.g. 0.75,
    "thesis": "Brief thesis statement",
    "evidence": [
        "Specific evidence with exact numbers from data",
        "Another piece of evidence",
        "..."
    ]
}}

Focus ONLY on your area of expertise ({self.name} analysis).
Do NOT analyze aspects outside your domain."""

        return prompt
    
    def _format_peer_proposals(
        self,
        peer_proposals: Dict[str, AgentProposal],
        own_proposal: AgentProposal
    ) -> str:
        """Format peer proposals for debate context."""
        lines = []
        
        # Separate opposing and supporting
        opposing = []
        supporting = []
        
        for name, prop in peer_proposals.items():
            if self._is_opposing(own_proposal.action, prop.action):
                opposing.append((name, prop))
            else:
                supporting.append((name, prop))
        
        # Format opposing arguments (focus here)
        if opposing:
            lines.append("OPPOSING POSITIONS (address these):")
            for name, prop in opposing:
                lines.append(f"\n{name.upper()}:")
                lines.append(f"  Recommends: {prop.action} (conviction: {prop.conviction:.2f})")
                lines.append(f"  Thesis: {prop.thesis}")
                if prop.evidence:
                    lines.append(f"  Evidence:")
                    for ev in prop.evidence[:3]:
                        lines.append(f"    - {ev}")
        
        # Format supporting arguments
        if supporting:
            lines.append("\nSUPPORTING POSITIONS:")
            for name, prop in supporting:
                lines.append(f"  {name}: {prop.action} (conviction: {prop.conviction:.2f})")
        
        return "\n".join(lines) if lines else "No peer proposals available."
    
    def _is_opposing(self, action1: str, action2: str) -> bool:
        """Check if two actions are opposing."""
        action1 = action1.upper()
        action2 = action2.upper()
        
        if action1 == action2:
            return False
        
        # BUY vs SELL is opposing
        if (action1 == "BUY" and action2 == "SELL") or \
           (action1 == "SELL" and action2 == "BUY"):
            return True
        
        # HOLD is mildly opposing to active positions
        return (action1 in ["BUY", "SELL"] and action2 == "HOLD") or \
               (action1 == "HOLD" and action2 in ["BUY", "SELL"])
    
    def _parse_proposal(self, response: str) -> AgentProposal:
        """
        Parse LLM response into AgentProposal.
        
        Args:
            response: LLM response (should contain JSON)
            
        Returns:
            AgentProposal object
        """
        try:
            # Try to parse JSON from response
            data = self._extract_json(response)
            
            return AgentProposal(
                agent=self.name,
                action=data.get("action", "HOLD"),
                conviction=float(data.get("conviction", 0.5)),
                thesis=data.get("thesis", "No thesis provided"),
                evidence=data.get("evidence", []),
                neutral=False
            )
        except Exception as e:
            # Fallback: return neutral proposal
            return AgentProposal(
                agent=self.name,
                action="HOLD",
                conviction=0.0,
                thesis=f"Failed to parse response: {str(e)}",
                evidence=[],
                neutral=True
            )
    
    def _extract_json(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        # Try direct parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON in text
        start = response.find('{')
        end = response.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            json_str = response[start:end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Failed to extract
        raise ValueError("Could not extract JSON from response")


def create_news_agent(llm_client: LLMClient, data_tools: List[Callable]) -> TradingAgent:
    """Create a news and sentiment analyst."""
    system_prompt = """You are a NEWS AND SENTIMENT ANALYST specializing in market-moving events.

YOUR EXCLUSIVE FOCUS:
- Recent news headlines and their market impact
- Regulatory announcements and policy changes  
- Sentiment shifts from news events
- Macro economic news affecting the sector

YOU MUST NOT ANALYZE:
- Technical indicators (RSI, MACD, moving averages) - that's the technical analyst's job
- Financial ratios (P/E, revenue, margins) - that's the fundamental analyst's job

Base your recommendation ONLY on news sentiment and event analysis.
Provide specific news sources and dates in your evidence."""

    return TradingAgent(
        name="news",
        llm_client=llm_client,
        system_prompt=system_prompt,
        data_tools=data_tools
    )


def create_technical_agent(llm_client: LLMClient, data_tools: List[Callable]) -> TradingAgent:
    """Create a technical analyst."""
    system_prompt = """You are a TECHNICAL ANALYST specializing in price action and indicators.

YOUR EXCLUSIVE FOCUS:
- Price trends, support/resistance levels
- Technical indicators (RSI, MACD, Bollinger Bands, moving averages)
- Volume patterns and momentum
- Chart patterns and breakouts

YOU MUST NOT ANALYZE:
- News headlines or sentiment - that's the news analyst's job
- Company fundamentals (earnings, revenue, P/E) - that's the fundamental analyst's job

Base your recommendation ONLY on technical signals and price action.
Cite specific indicator values and price levels in your evidence."""

    return TradingAgent(
        name="technical",
        llm_client=llm_client,
        system_prompt=system_prompt,
        data_tools=data_tools
    )


def create_fundamental_agent(llm_client: LLMClient, data_tools: List[Callable]) -> TradingAgent:
    """Create a fundamental analyst."""
    system_prompt = """You are a FUNDAMENTAL ANALYST specializing in company valuation and financials.

YOUR EXCLUSIVE FOCUS:
- Valuation metrics (P/E ratio, market cap, P/B ratio)
- Financial health (revenue, earnings, profit margins, debt)
- Business fundamentals and competitive position
- Long-term growth prospects

YOU MUST NOT ANALYZE:
- Technical indicators (RSI, MACD, moving averages) - that's the technical analyst's job
- Recent news or sentiment - that's the news analyst's job

Base your recommendation ONLY on fundamental business metrics and valuation.
Cite specific financial metrics and ratios in your evidence."""

    return TradingAgent(
        name="fundamental",
        llm_client=llm_client,
        system_prompt=system_prompt,
        data_tools=data_tools
    )

