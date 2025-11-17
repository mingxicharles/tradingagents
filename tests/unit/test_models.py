"""
Unit tests for data models
"""

import pytest
from datetime import datetime

from tradingagents.models import (
    AnalysisRequest,
    AgentProposal,
    FinalDecision,
    DebateTranscript,
    PositionChange
)


class TestAnalysisRequest:
    """Tests for AnalysisRequest model."""

    def test_create_request(self):
        """Test creating an analysis request."""
        request = AnalysisRequest(symbol="AAPL", horizon="1d")
        assert request.symbol == "AAPL"
        assert request.horizon == "1d"
        assert request.trade_date is not None  # Should default to current date

    def test_symbol_uppercase(self):
        """Test that symbol is converted to uppercase."""
        request = AnalysisRequest(symbol="aapl", horizon="1d")
        assert request.symbol == "AAPL"

    def test_custom_trade_date(self):
        """Test custom trade date."""
        request = AnalysisRequest(symbol="AAPL", horizon="1w", trade_date="2024-01-15")
        assert request.trade_date == "2024-01-15"


class TestAgentProposal:
    """Tests for AgentProposal model."""

    def test_create_proposal(self):
        """Test creating an agent proposal."""
        proposal = AgentProposal(
            agent="technical",
            action="BUY",
            conviction=0.75,
            thesis="Bullish momentum",
            evidence=["RSI > 50", "Price > MA"]
        )
        assert proposal.agent == "technical"
        assert proposal.action == "BUY"
        assert proposal.conviction == 0.75

    def test_action_uppercase(self):
        """Test that action is converted to uppercase."""
        proposal = AgentProposal(
            agent="news",
            action="buy",
            conviction=0.6,
            thesis="Positive news"
        )
        assert proposal.action == "BUY"

    def test_conviction_clamping(self):
        """Test that conviction is clamped to [0, 1]."""
        proposal1 = AgentProposal(
            agent="fundamental",
            action="SELL",
            conviction=1.5,  # Too high
            thesis="Overvalued"
        )
        assert proposal1.conviction == 1.0

        proposal2 = AgentProposal(
            agent="fundamental",
            action="SELL",
            conviction=-0.5,  # Too low
            thesis="Overvalued"
        )
        assert proposal2.conviction == 0.0

    def test_ensure_policy_compliance_with_evidence(self):
        """Test policy compliance when evidence is present."""
        proposal = AgentProposal(
            agent="technical",
            action="BUY",
            conviction=0.8,
            thesis="Strong buy",
            evidence=["Good signal"]
        )
        compliant = proposal.ensure_policy_compliance()
        assert compliant.action == "BUY"
        assert not compliant.neutral

    def test_ensure_policy_compliance_without_evidence(self):
        """Test policy compliance when evidence is missing."""
        proposal = AgentProposal(
            agent="technical",
            action="BUY",
            conviction=0.8,
            thesis="Strong buy",
            evidence=[]  # No evidence
        )
        compliant = proposal.ensure_policy_compliance()
        assert compliant.action == "HOLD"
        assert compliant.neutral
        assert compliant.conviction == 0.5

    def test_to_dict(self):
        """Test conversion to dictionary."""
        proposal = AgentProposal(
            agent="news",
            action="HOLD",
            conviction=0.5,
            thesis="Neutral"
        )
        data = proposal.to_dict()
        assert isinstance(data, dict)
        assert data["agent"] == "news"
        assert data["action"] == "HOLD"


class TestFinalDecision:
    """Tests for FinalDecision model."""

    def test_create_decision(self):
        """Test creating a final decision."""
        decision = FinalDecision(
            symbol="AAPL",
            horizon="1d",
            recommendation="BUY",
            confidence=0.8,
            rationale="Strong technical and fundamental signals"
        )
        assert decision.symbol == "AAPL"
        assert decision.recommendation == "BUY"
        assert decision.confidence == 0.8

    def test_save_decision(self, tmp_signals_dir):
        """Test saving decision to file."""
        decision = FinalDecision(
            symbol="AAPL",
            horizon="1d",
            recommendation="BUY",
            confidence=0.75,
            rationale="Test decision"
        )
        filepath = decision.save(tmp_signals_dir)
        assert filepath.exists()
        assert filepath.name.startswith("aapl_")
        assert filepath.suffix == ".json"

    def test_write_signal(self, tmp_signals_dir):
        """Test write_signal method."""
        decision = FinalDecision(
            symbol="MSFT",
            horizon="1w",
            recommendation="HOLD",
            confidence=0.5,
            rationale="Wait and see"
        )
        filepath = decision.write_signal(tmp_signals_dir)
        assert filepath.exists()


class TestDebateTranscript:
    """Tests for DebateTranscript model."""

    def test_create_transcript(self):
        """Test creating a debate transcript."""
        transcript = DebateTranscript()
        assert transcript.rounds == 0
        assert len(transcript.exchanges) == 0
        assert not transcript.consensus_reached

    def test_add_exchange(self):
        """Test adding an exchange to the transcript."""
        transcript = DebateTranscript()
        proposal = AgentProposal(
            agent="technical",
            action="BUY",
            conviction=0.7,
            thesis="Test"
        )
        transcript.add_exchange(1, "technical", "I recommend BUY", proposal)
        assert len(transcript.exchanges) == 1
        assert transcript.exchanges[0]["agent"] == "technical"


class TestPositionChange:
    """Tests for PositionChange model."""

    def test_create_position_change(self):
        """Test creating a position change."""
        change = PositionChange(
            agent="fundamental",
            old_action="HOLD",
            new_action="BUY",
            old_conviction=0.5,
            new_conviction=0.8,
            reason="New earnings data"
        )
        assert change.agent == "fundamental"
        assert change.old_action == "HOLD"
        assert change.new_action == "BUY"

    def test_action_changed_property(self):
        """Test action_changed property."""
        change1 = PositionChange(
            agent="news",
            old_action="BUY",
            new_action="SELL",
            old_conviction=0.7,
            new_conviction=0.6
        )
        assert change1.action_changed

        change2 = PositionChange(
            agent="news",
            old_action="BUY",
            new_action="BUY",
            old_conviction=0.7,
            new_conviction=0.9
        )
        assert not change2.action_changed

    def test_conviction_delta_property(self):
        """Test conviction_delta property."""
        change = PositionChange(
            agent="technical",
            old_action="HOLD",
            new_action="BUY",
            old_conviction=0.5,
            new_conviction=0.8
        )
        assert change.conviction_delta == pytest.approx(0.3)
