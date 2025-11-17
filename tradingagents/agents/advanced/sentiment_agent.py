"""
Advanced Sentiment Analysis Agent

This agent aggregates sentiment from multiple sources:
- News headlines and articles
- Social media (Twitter/X, Reddit)
- Analyst ratings
- Insider trading activity
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio

from ..base import ResearchAgent
from ...models import AgentProposal, AnalysisRequest
from ...llm import LLMClient
from ...utils.logging import get_logger

logger = get_logger(__name__)


class SentimentAgent(ResearchAgent):
    """
    Advanced sentiment analysis agent.

    Analyzes market sentiment from multiple sources and provides
    a comprehensive sentiment score with evidence.
    """

    def __init__(self, llm_client: LLMClient, config: Any):
        """Initialize sentiment agent."""
        super().__init__(
            name="sentiment",
            llm_client=llm_client,
            config=config
        )
        self.sentiment_sources = [
            "news_headlines",
            "social_media",
            "analyst_ratings",
            "insider_trading"
        ]

    async def analyze(self, request: AnalysisRequest, context: Any = None) -> AgentProposal:
        """
        Perform comprehensive sentiment analysis.

        Args:
            request: Analysis request with symbol and parameters
            context: Optional context data

        Returns:
            AgentProposal with sentiment-based recommendation
        """
        logger.info(f"Sentiment analysis started for {request.symbol}")

        # Gather sentiment from multiple sources
        sentiment_data = await self._gather_sentiment_data(request)

        # Analyze with LLM
        analysis = await self._analyze_sentiment(request, sentiment_data)

        # Create proposal
        proposal = self._create_proposal(analysis, sentiment_data)

        logger.info(
            f"Sentiment analysis complete: {proposal.action} "
            f"(conviction={proposal.conviction:.2f})"
        )

        return proposal

    async def _gather_sentiment_data(self, request: AnalysisRequest) -> Dict[str, Any]:
        """
        Gather sentiment data from multiple sources.

        Args:
            request: Analysis request

        Returns:
            Dictionary with sentiment data from various sources
        """
        sentiment_data = {
            "symbol": request.symbol,
            "date": request.trade_date,
            "sources": {}
        }

        # News sentiment (simulated for now - would integrate with NewsAPI, Finnhub, etc.)
        sentiment_data["sources"]["news"] = await self._get_news_sentiment(request.symbol)

        # Social media sentiment (simulated - would integrate with Twitter API, Reddit API)
        sentiment_data["sources"]["social_media"] = await self._get_social_sentiment(request.symbol)

        # Analyst ratings (simulated - would integrate with analyst rating APIs)
        sentiment_data["sources"]["analyst_ratings"] = await self._get_analyst_ratings(request.symbol)

        # Insider trading (simulated - would integrate with SEC filings)
        sentiment_data["sources"]["insider_trading"] = await self._get_insider_activity(request.symbol)

        return sentiment_data

    async def _get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get news sentiment (placeholder for real API integration)."""
        # In production, integrate with NewsAPI, Finnhub, Alpha Vantage
        return {
            "sentiment_score": 0.65,  # -1 to 1
            "article_count": 15,
            "positive_count": 10,
            "negative_count": 3,
            "neutral_count": 2,
            "top_headlines": [
                f"{symbol} reports strong quarterly earnings",
                f"{symbol} announces new product launch",
                "Market volatility affects tech sector"
            ],
            "source": "simulated"
        }

    async def _get_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get social media sentiment (placeholder)."""
        # In production, integrate with Twitter API, Reddit API
        return {
            "sentiment_score": 0.55,
            "mention_count": 1250,
            "positive_mentions": 750,
            "negative_mentions": 300,
            "neutral_mentions": 200,
            "trending": False,
            "top_keywords": ["bullish", "earnings", "growth"],
            "source": "simulated"
        }

    async def _get_analyst_ratings(self, symbol: str) -> Dict[str, Any]:
        """Get analyst ratings (placeholder)."""
        # In production, integrate with analyst rating services
        return {
            "consensus": "Buy",
            "buy_count": 15,
            "hold_count": 5,
            "sell_count": 2,
            "average_price_target": 195.50,
            "recent_upgrades": 3,
            "recent_downgrades": 0,
            "source": "simulated"
        }

    async def _get_insider_activity(self, symbol: str) -> Dict[str, Any]:
        """Get insider trading activity (placeholder)."""
        # In production, integrate with SEC EDGAR filings
        return {
            "net_buying": True,
            "buy_transactions": 5,
            "sell_transactions": 1,
            "net_shares": 50000,
            "recent_activity": "Positive",
            "source": "simulated"
        }

    async def _analyze_sentiment(
        self,
        request: AnalysisRequest,
        sentiment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze sentiment using LLM.

        Args:
            request: Analysis request
            sentiment_data: Gathered sentiment data

        Returns:
            LLM analysis results
        """
        # Create comprehensive prompt
        prompt = self._create_sentiment_prompt(request, sentiment_data)

        # Get LLM analysis
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm_client.complete(messages, max_tokens=800)

        # Parse response
        analysis = self._parse_llm_response(response)

        return analysis

    def _get_system_prompt(self) -> str:
        """Get system prompt for sentiment agent."""
        return """You are an expert SENTIMENT ANALYST specializing in market psychology and crowd behavior.

YOUR EXCLUSIVE FOCUS:
- News sentiment and market narratives
- Social media trends and retail investor sentiment
- Analyst consensus and institutional sentiment
- Insider trading signals (actions speak louder than words)
- Overall market psychology and fear/greed indicators

YOU MUST NOT analyze:
- Technical indicators (RSI, MACD, moving averages) - that's technical analyst's job
- Financial ratios (P/E, revenue, margins) - that's fundamental analyst's job

Base your recommendation ONLY on sentiment analysis and market psychology.
Look for:
- Sentiment divergences (price vs sentiment)
- Sentiment extremes (euphoria or panic)
- Institutional vs retail sentiment differences
- Insider confidence signals"""

    def _create_sentiment_prompt(
        self,
        request: AnalysisRequest,
        sentiment_data: Dict[str, Any]
    ) -> str:
        """Create prompt for sentiment analysis."""
        sources = sentiment_data["sources"]

        prompt = f"""Analyze sentiment for {request.symbol} for {request.horizon} investment.

SENTIMENT DATA:

News Sentiment:
  - Score: {sources['news']['sentiment_score']:.2f} (-1=very negative, +1=very positive)
  - Articles: {sources['news']['article_count']} ({sources['news']['positive_count']} positive, {sources['news']['negative_count']} negative)
  - Top Headlines:
    {chr(10).join(f"    • {h}" for h in sources['news']['top_headlines'])}

Social Media Sentiment:
  - Score: {sources['social_media']['sentiment_score']:.2f}
  - Mentions: {sources['social_media']['mention_count']} ({sources['social_media']['positive_mentions']} positive, {sources['social_media']['negative_mentions']} negative)
  - Trending: {'Yes' if sources['social_media']['trending'] else 'No'}
  - Keywords: {', '.join(sources['social_media']['top_keywords'])}

Analyst Ratings:
  - Consensus: {sources['analyst_ratings']['consensus']}
  - Ratings: {sources['analyst_ratings']['buy_count']} Buy, {sources['analyst_ratings']['hold_count']} Hold, {sources['analyst_ratings']['sell_count']} Sell
  - Price Target: ${sources['analyst_ratings']['average_price_target']:.2f}
  - Recent Changes: {sources['analyst_ratings']['recent_upgrades']} upgrades, {sources['analyst_ratings']['recent_downgrades']} downgrades

Insider Trading:
  - Activity: {sources['insider_trading']['recent_activity']}
  - Net Buying: {'Yes' if sources['insider_trading']['net_buying'] else 'No'}
  - Transactions: {sources['insider_trading']['buy_transactions']} buys, {sources['insider_trading']['sell_transactions']} sells
  - Net Shares: {sources['insider_trading']['net_shares']:,}

{f"MARKET CONTEXT: {request.market_context}" if request.market_context else ""}

TASK:
Provide a sentiment-based recommendation considering:
1. Overall sentiment direction and strength
2. Sentiment divergences or extremes
3. Institutional (analyst) vs retail (social) alignment
4. Insider confidence signals
5. Potential sentiment catalysts or risks

OUTPUT FORMAT (JSON):
{{
    "action": "BUY/SELL/HOLD",
    "conviction": 0.0-1.0,
    "thesis": "Your main sentiment argument in 1-2 sentences",
    "evidence": [
        "Specific sentiment evidence 1",
        "Specific sentiment evidence 2",
        "..."
    ]
}}"""

        return prompt

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured data."""
        import json

        try:
            # Try to extract JSON
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1:
                json_str = response[start:end+1]
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")

        # Fallback
        return {
            "action": "HOLD",
            "conviction": 0.5,
            "thesis": "Sentiment analysis inconclusive",
            "evidence": []
        }

    def _create_proposal(
        self,
        analysis: Dict[str, Any],
        sentiment_data: Dict[str, Any]
    ) -> AgentProposal:
        """Create agent proposal from analysis."""
        return AgentProposal(
            agent=self.name,
            action=analysis.get("action", "HOLD"),
            conviction=float(analysis.get("conviction", 0.5)),
            thesis=analysis.get("thesis", "Sentiment analysis"),
            evidence=analysis.get("evidence", []),
            raw_response=str(analysis),
            caveats=[
                "Sentiment data is simulated (production would use real APIs)",
                "Sentiment can change rapidly",
                "Crowd sentiment can be wrong at extremes"
            ]
        )
