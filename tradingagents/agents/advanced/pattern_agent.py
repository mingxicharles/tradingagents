"""
Pattern Recognition Agent

This agent identifies chart patterns and technical formations:
- Classic patterns (head & shoulders, double tops/bottoms, triangles)
- Candlestick patterns
- Support/resistance levels
- Fibonacci retracements
- Volume patterns
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import numpy as np

from ..base import ResearchAgent
from ...models import AgentProposal, AnalysisRequest
from ...llm import LLMClient
from ...utils.logging import get_logger

logger = get_logger(__name__)


class PatternRecognitionAgent(ResearchAgent):
    """
    Advanced pattern recognition agent.

    Identifies technical patterns and formations in price data.
    """

    def __init__(self, llm_client: LLMClient, config: Any):
        """Initialize pattern recognition agent."""
        super().__init__(
            name="pattern",
            llm_client=llm_client,
            config=config
        )

    async def analyze(self, request: AnalysisRequest, context: Any = None) -> AgentProposal:
        """
        Perform pattern recognition analysis.

        Args:
            request: Analysis request
            context: Optional market data context

        Returns:
            AgentProposal with pattern-based recommendation
        """
        logger.info(f"Pattern recognition started for {request.symbol}")

        # Detect patterns (would use real price data in production)
        patterns = await self._detect_patterns(request)

        # Analyze patterns with LLM
        analysis = await self._analyze_patterns(request, patterns)

        # Create proposal
        proposal = self._create_proposal(analysis, patterns)

        logger.info(
            f"Pattern analysis complete: {proposal.action} "
            f"(patterns detected: {len(patterns)})"
        )

        return proposal

    async def _detect_patterns(self, request: AnalysisRequest) -> List[Dict[str, Any]]:
        """
        Detect chart patterns.

        Args:
            request: Analysis request

        Returns:
            List of detected patterns
        """
        # In production, this would analyze real price data
        # For now, return simulated patterns
        patterns = []

        # Classic chart patterns
        if hash(request.symbol) % 3 == 0:
            patterns.append({
                "type": "Double Bottom",
                "timeframe": "1w",
                "confidence": 0.75,
                "implications": "Bullish reversal pattern",
                "target": "+8%",
                "support_level": 175.50,
                "neckline": 182.00
            })

        if hash(request.symbol) % 3 == 1:
            patterns.append({
                "type": "Ascending Triangle",
                "timeframe": "1d",
                "confidence": 0.65,
                "implications": "Bullish continuation pattern",
                "target": "+5%",
                "resistance": 185.00,
                "support_trend": "rising"
            })

        # Candlestick patterns
        patterns.append({
            "type": "Bullish Engulfing",
            "timeframe": "1d",
            "confidence": 0.60,
            "implications": "Short-term bullish reversal",
            "location": "near support"
        })

        # Support/Resistance levels
        patterns.append({
            "type": "Key Support Level",
            "level": 178.50,
            "strength": "strong",
            "tests": 3,
            "implications": "Major support zone"
        })

        patterns.append({
            "type": "Resistance Level",
            "level": 190.00,
            "strength": "moderate",
            "tests": 2,
            "implications": "Overhead resistance"
        })

        # Fibonacci levels
        patterns.append({
            "type": "Fibonacci Retracement",
            "level": "61.8%",
            "price": 180.25,
            "significance": "Golden ratio support",
            "recent_reaction": "bounce"
        })

        return patterns

    async def _analyze_patterns(
        self,
        request: AnalysisRequest,
        patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze detected patterns using LLM.

        Args:
            request: Analysis request
            patterns: Detected patterns

        Returns:
            LLM analysis results
        """
        prompt = self._create_pattern_prompt(request, patterns)

        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_client.complete(messages, max_tokens=800)

        return self._parse_llm_response(response)

    def _get_system_prompt(self) -> str:
        """Get system prompt for pattern agent."""
        return """You are an expert PATTERN RECOGNITION ANALYST specializing in technical chart analysis.

YOUR EXCLUSIVE FOCUS:
- Classic chart patterns (head & shoulders, double tops/bottoms, triangles, flags, pennants)
- Candlestick patterns and formations
- Support and resistance levels
- Fibonacci retracements and extensions
- Volume pattern confirmation
- Pattern reliability and confirmation signals

YOU MUST NOT analyze:
- News or sentiment - that's sentiment analyst's job
- Company fundamentals - that's fundamental analyst's job
- Basic indicators only - focus on PATTERNS

Base your recommendation on pattern recognition and technical formations.
Consider:
- Pattern completion and confirmation
- Pattern reliability (historical success rate)
- Volume confirmation
- Location in overall trend
- Multiple pattern confluence"""

    def _create_pattern_prompt(
        self,
        request: AnalysisRequest,
        patterns: List[Dict[str, Any]]
    ) -> str:
        """Create prompt for pattern analysis."""
        patterns_text = "\n".join([
            f"""
Pattern {i+1}: {p.get('type', 'Unknown')}
  - Timeframe: {p.get('timeframe', 'N/A')}
  - Confidence: {p.get('confidence', p.get('strength', 'N/A'))}
  - Implications: {p.get('implications', 'N/A')}
  - Details: {', '.join(f"{k}={v}" for k, v in p.items() if k not in ['type', 'timeframe', 'confidence', 'implications'])}
"""
            for i, p in enumerate(patterns)
        ])

        prompt = f"""Analyze chart patterns for {request.symbol} for {request.horizon} investment.

DETECTED PATTERNS:
{patterns_text}

PATTERN ANALYSIS TASK:
1. Evaluate pattern significance and reliability
2. Check for pattern confluence (multiple patterns confirming same direction)
3. Assess pattern completion status
4. Consider pattern targets and invalidation levels
5. Identify key support/resistance levels
6. Evaluate overall pattern setup quality

{f"MARKET CONTEXT: {request.market_context}" if request.market_context else ""}

OUTPUT FORMAT (JSON):
{{
    "action": "BUY/SELL/HOLD",
    "conviction": 0.0-1.0,
    "thesis": "Pattern-based argument in 1-2 sentences",
    "evidence": [
        "Specific pattern evidence with details",
        "Support/resistance levels",
        "Pattern targets and stops",
        "..."
    ]
}}"""

        return prompt

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response."""
        import json

        try:
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1:
                json_str = response[start:end+1]
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")

        return {
            "action": "HOLD",
            "conviction": 0.5,
            "thesis": "Pattern analysis inconclusive",
            "evidence": []
        }

    def _create_proposal(
        self,
        analysis: Dict[str, Any],
        patterns: List[Dict[str, Any]]
    ) -> AgentProposal:
        """Create agent proposal."""
        return AgentProposal(
            agent=self.name,
            action=analysis.get("action", "HOLD"),
            conviction=float(analysis.get("conviction", 0.5)),
            thesis=analysis.get("thesis", "Pattern analysis"),
            evidence=analysis.get("evidence", []),
            raw_response=str(analysis),
            caveats=[
                "Pattern recognition is probabilistic, not deterministic",
                "Patterns can fail or invalidate",
                f"{len(patterns)} patterns detected (simulated data)"
            ]
        )


def detect_support_resistance(
    prices: np.ndarray,
    window: int = 20
) -> Tuple[List[float], List[float]]:
    """
    Detect support and resistance levels.

    Args:
        prices: Array of price data
        window: Window size for local extrema detection

    Returns:
        Tuple of (support_levels, resistance_levels)
    """
    supports = []
    resistances = []

    # Find local minima (support)
    for i in range(window, len(prices) - window):
        if prices[i] == min(prices[i-window:i+window]):
            supports.append(float(prices[i]))

    # Find local maxima (resistance)
    for i in range(window, len(prices) - window):
        if prices[i] == max(prices[i-window:i+window]):
            resistances.append(float(prices[i]))

    # Cluster nearby levels
    supports = _cluster_levels(supports)
    resistances = _cluster_levels(resistances)

    return supports, resistances


def _cluster_levels(levels: List[float], threshold: float = 0.02) -> List[float]:
    """Cluster nearby price levels."""
    if not levels:
        return []

    levels = sorted(levels)
    clustered = [levels[0]]

    for level in levels[1:]:
        if (level - clustered[-1]) / clustered[-1] > threshold:
            clustered.append(level)

    return clustered


def calculate_fibonacci_levels(high: float, low: float) -> Dict[str, float]:
    """
    Calculate Fibonacci retracement levels.

    Args:
        high: Recent high price
        low: Recent low price

    Returns:
        Dictionary of Fibonacci levels
    """
    diff = high - low

    return {
        "0%": high,
        "23.6%": high - (diff * 0.236),
        "38.2%": high - (diff * 0.382),
        "50%": high - (diff * 0.5),
        "61.8%": high - (diff * 0.618),
        "78.6%": high - (diff * 0.786),
        "100%": low
    }
