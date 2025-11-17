"""
Pytest configuration and shared fixtures
"""

import pytest
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

from tradingagents.config import TradingConfig, reset_config
from tradingagents.models import AnalysisRequest, AgentProposal


@pytest.fixture
def test_config():
    """Create a test configuration."""
    reset_config()
    config = TradingConfig(
        llm={"provider": "openai", "model": "gpt-4o-mini", "api_key": "test-key"},
        data={"source": "offline", "cache_enabled": False},
        agent={"max_debate_rounds": 1},
        signals_dir=Path("test_signals"),
        logs_dir=Path("test_logs"),
        environment="testing"
    )
    yield config
    # Cleanup
    reset_config()


@pytest.fixture
def sample_request():
    """Create a sample analysis request."""
    return AnalysisRequest(
        symbol="AAPL",
        horizon="1d",
        market_context="Testing context",
        trade_date="2024-01-15"
    )


@pytest.fixture
def sample_proposal():
    """Create a sample agent proposal."""
    return AgentProposal(
        agent="technical",
        action="BUY",
        conviction=0.75,
        thesis="Strong upward momentum",
        evidence=[
            "Price above 20-day MA",
            "RSI at 65 (bullish)",
            "MACD positive crossover"
        ]
    )


@pytest.fixture
def mock_market_data():
    """Create mock market data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=100)
    data = pd.DataFrame({
        'Date': dates,
        'Open': np.random.uniform(100, 110, 100),
        'High': np.random.uniform(105, 115, 100),
        'Low': np.random.uniform(95, 105, 100),
        'Close': np.random.uniform(100, 110, 100),
        'Volume': np.random.randint(1000000, 10000000, 100),
    })
    data['Close'] = data['Close'].cumsum() / 100 + 100  # Trending data
    return data


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response."""
    return {
        "action": "BUY",
        "conviction": 0.8,
        "thesis": "Strong technical indicators suggest upward movement",
        "evidence": [
            "Price crossed above 50-day moving average",
            "Volume increasing on up days",
            "RSI shows bullish momentum"
        ]
    }


@pytest.fixture
def tmp_signals_dir(tmp_path):
    """Create a temporary signals directory."""
    signals_dir = tmp_path / "signals"
    signals_dir.mkdir()
    return signals_dir
