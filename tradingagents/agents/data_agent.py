"""
Base class for agents with data fetching support
"""
from __future__ import annotations

import textwrap
from typing import Dict, List, Callable, Optional
from datetime import datetime, timedelta

from .base import ResearchAgent
from ..models import AgentProposal, ResearchRequest
from .base import AgentContext


class DataAwareAgent(ResearchAgent):
    """
    Agent with real data fetching support
    
    Fetches real data using tools before analysis
    """
    
    def __init__(
        self,
        name: str,
        client,
        system_prompt: str,
        data_tools: Optional[List[Callable]] = None
    ) -> None:
        super().__init__(name, client, system_prompt)
        self.data_tools = data_tools or []
    
    async def gather(self, request: ResearchRequest, peers: AgentContext) -> AgentProposal:
        """Collect data and generate proposal"""
        # 1. Fetch real data first
        market_data = await self._fetch_market_data(request)
        
        # 2. Generate analysis based on real data
        content = await self._call_llm(
            self.build_prompt_with_data(request, peers, market_data)
        )
        
        # 3. Parse and return
        proposal = self.parse_response(content)
        proposal.agent = self.name
        proposal.ensure_policy_compliance()
        return proposal
    
    async def _fetch_market_data(self, request: ResearchRequest) -> str:
        """
        Call data tools to fetch market data
        
        Returns:
            Formatted market data string
        """
        if not self.data_tools:
            return "No data tools available."
        
        data_parts = []
        for tool in self.data_tools:
            try:
                # Call data tool (synchronous function)
                data = tool(request.symbol)
                data_parts.append(data)
            except Exception as e:
                data_parts.append(f"Data fetch failed ({tool.__name__}): {str(e)}")
        
        return "\n\n".join(data_parts)
    
    def build_prompt_with_data(
        self,
        request: ResearchRequest,
        peers: AgentContext,
        market_data: str
    ) -> List[Dict[str, str]]:
        """Build prompt with real data included"""
        
        # Add role-specific instructions
        role_instructions = self._get_role_specific_instructions()
        
        user_content = textwrap.dedent(
            f"""
            Focus ticker: {request.symbol}
            Horizon: {request.horizon}
            Market context: {request.market_context}
            
            === REAL MARKET DATA ===
            {market_data}
            === END OF MARKET DATA ===
            
            {role_instructions}
            
            Peer snapshot:
            {peers.summary()}
            
            Based on the REAL MARKET DATA above, produce a JSON object with keys:
              action: BUY/SELL/HOLD recommendation string
              conviction: float 0-1 for confidence (see scale below)
              thesis: brief paragraph summary
              evidence: array of 2-4 specific bullet strings citing REAL DATA from above
              caveats: array of risk warnings
            
            Conviction Scale (use full range based on data quality):
              0.90-1.00: Exceptional - multiple strong signals align perfectly (e.g., RSI<30 + strong uptrend + high volume)
              0.75-0.89: High - clear directional trend with solid confirmation (e.g., breakout + volume)
              0.60-0.74: Moderate - favorable but some uncertainty (e.g., single indicator signal)
              0.45-0.59: Low - weak signals or mixed indicators (e.g., RSI neutral + choppy price)
              0.20-0.44: Very low - contradictory or unclear data
              0.00-0.19: None - insufficient data
            
            IMPORTANT:
              - Evidence MUST cite EXACT numbers from real data above (e.g., "RSI: 65.32", "Price: $178.45")
              - Base conviction on DATA STRENGTH - don't just use 0.75!
              - Strong aligned signals = 0.80-0.90, single indicator = 0.60-0.70, weak/mixed = 0.40-0.55
              - Default to BUY or SELL based on data, HOLD only if contradictory
              - Keep responses concise and free of Markdown fences
            """
        ).strip()
        
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content},
        ]
    
    def _get_role_specific_instructions(self) -> str:
        """Get instructions specific to this agent's role"""
        if self.name == "technical":
            return textwrap.dedent("""
            YOUR ANALYSIS SCOPE (Technical Analyst):
            ==========================================
            ANALYZE ONLY:
            - Price action: trends, support/resistance, breakouts
            - Technical indicators: RSI, MACD, Bollinger Bands, Moving Averages
            - Volume patterns and momentum signals
            - Chart patterns and technical setups
            
            IGNORE:
            - News headlines or sentiment (not your domain)
            - Company fundamentals like P/E, revenue, earnings (not your domain)
            
            Your evidence MUST cite specific technical data:
            - Example: "RSI at 65.3 shows momentum but not overbought"
            - Example: "Price broke $175 resistance with 2x normal volume"
            - Example: "MACD crossover indicates bullish momentum"
            """).strip()
        
        elif self.name == "fundamental":
            return textwrap.dedent("""
            YOUR ANALYSIS SCOPE (Fundamental Analyst):
            ==========================================
            ANALYZE ONLY:
            - Valuation metrics: P/E ratio, P/B ratio, market cap
            - Financial health: revenue, earnings, margins, debt levels
            - Business quality: competitive position, growth prospects
            - Intrinsic value vs current price
            
            IGNORE:
            - Technical indicators like RSI, MACD, moving averages (not your domain)
            - Recent news or sentiment (not your domain)
            
            Your evidence MUST cite specific fundamental data:
            - Example: "P/E ratio of 25 vs industry average of 30 indicates undervaluation"
            - Example: "Revenue grew 15% YoY with improving margins"
            - Example: "Strong balance sheet with debt-to-equity of 0.3"
            """).strip()
        
        elif self.name == "news":
            return textwrap.dedent("""
            YOUR ANALYSIS SCOPE (News & Sentiment Analyst):
            ==========================================
            ANALYZE ONLY:
            - Recent news headlines and their market impact
            - Regulatory announcements and policy changes
            - Sentiment shifts from news events
            - Macro economic developments
            
            IGNORE:
            - Technical indicators like RSI, MACD (not your domain)
            - Company financials like P/E, revenue (not your domain)
            
            Your evidence MUST cite specific news events:
            - Example: "Positive earnings surprise announced on [date]"
            - Example: "New product launch garnering positive media coverage"
            - Example: "Regulatory approval removes major overhang"
            """).strip()
        
        else:
            # Default/fallback
            return "IMPORTANT: Focus on your specialized domain and cite specific data."

