"""
Centralized Configuration Management

This module provides a type-safe, validated configuration system using Pydantic.
All settings can be overridden via environment variables.
"""

import os
from typing import Dict, List, Optional, Literal
from pathlib import Path
from pydantic import BaseModel, Field, validator

from .symbols import ALL_TRADING_SYMBOLS


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: Literal["openai", "openrouter", "local"] = Field(
        default="openai",
        description="LLM provider to use"
    )
    model: str = Field(
        default="gpt-4o-mini",
        description="Model name to use"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for the provider"
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Custom base URL for API"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=1000,
        ge=1,
        description="Maximum tokens per response"
    )
    timeout: int = Field(
        default=60,
        ge=1,
        description="Request timeout in seconds"
    )

    class Config:
        env_prefix = "LLM_"


class AgentConfig(BaseModel):
    """Agent configuration."""

    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "news": 1.0,
            "technical": 1.2,
            "fundamental": 1.1
        },
        description="Weights for each agent type"
    )
    max_debate_rounds: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Maximum number of debate rounds"
    )
    enable_debate: bool = Field(
        default=True,
        description="Whether to enable agent debates"
    )
    retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of retry attempts for failed agent calls"
    )

    class Config:
        env_prefix = "AGENT_"


class DataConfig(BaseModel):
    """Data source configuration."""

    source: Literal["yfinance", "offline", "csv"] = Field(
        default="yfinance",
        description="Primary data source"
    )
    offline_path: Optional[str] = Field(
        default=None,
        description="Path to offline data file"
    )
    cache_enabled: bool = Field(
        default=True,
        description="Whether to enable data caching"
    )
    cache_ttl_seconds: int = Field(
        default=300,
        ge=0,
        description="Cache time-to-live in seconds"
    )
    days_back: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Number of days of historical data to fetch"
    )

    class Config:
        env_prefix = "DATA_"


class TradingConfig(BaseModel):
    """Main trading system configuration."""

    # Sub-configurations
    llm: LLMConfig = Field(default_factory=LLMConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    data: DataConfig = Field(default_factory=DataConfig)

    # Trading universe
    trading_symbols: List[str] = Field(
        default_factory=lambda: ALL_TRADING_SYMBOLS,
        description="List of symbols to trade"
    )

    # Directories
    signals_dir: Path = Field(
        default=Path("signals"),
        description="Directory to store trading signals"
    )
    logs_dir: Path = Field(
        default=Path("logs"),
        description="Directory to store logs"
    )
    cache_dir: Path = Field(
        default=Path("dataflows/data_cache"),
        description="Directory for data cache"
    )

    # System settings
    enable_parallel: bool = Field(
        default=True,
        description="Whether to run agents in parallel"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level"
    )
    environment: Literal["development", "production", "testing"] = Field(
        default="development",
        description="Runtime environment"
    )

    # Performance
    max_concurrent_requests: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum concurrent API requests"
    )

    @validator('signals_dir', 'logs_dir', 'cache_dir')
    def create_directories(cls, v):
        """Ensure directories exist."""
        if v:
            Path(v).mkdir(parents=True, exist_ok=True)
        return v

    def validate_config(self) -> List[str]:
        """
        Validate configuration and return list of warnings.

        Returns:
            List of validation warnings (empty if all OK)
        """
        warnings = []

        # Check API key if using remote provider
        if self.llm.provider in ["openai", "openrouter"] and not self.llm.api_key:
            api_key_env = "OPENAI_API_KEY" if self.llm.provider == "openai" else "OPENROUTER_API_KEY"
            if not os.getenv(api_key_env):
                warnings.append(
                    f"No API key configured for {self.llm.provider}. "
                    f"Set {api_key_env} environment variable."
                )

        # Check offline data path
        if self.data.source == "offline" and self.data.offline_path:
            if not Path(self.data.offline_path).exists():
                warnings.append(
                    f"Offline data file not found: {self.data.offline_path}"
                )

        # Check agent weights
        if len(self.agent.weights) == 0:
            warnings.append("No agent weights configured")

        return warnings

    class Config:
        env_prefix = "TRADING_"
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global configuration instance
_config: Optional[TradingConfig] = None


def get_config(reload: bool = False) -> TradingConfig:
    """
    Get or create the global configuration instance.

    Args:
        reload: If True, reload configuration from environment

    Returns:
        TradingConfig instance
    """
    global _config

    if _config is None or reload:
        # Load from environment variables
        config_dict = {}

        # LLM configuration
        if os.getenv("OPENAI_API_KEY"):
            config_dict.setdefault("llm", {})["api_key"] = os.getenv("OPENAI_API_KEY")
        if os.getenv("OPENROUTER_API_KEY"):
            config_dict.setdefault("llm", {})["api_key"] = os.getenv("OPENROUTER_API_KEY")
            config_dict.setdefault("llm", {})["provider"] = "openrouter"
        if os.getenv("OPENAI_MODEL"):
            config_dict.setdefault("llm", {})["model"] = os.getenv("OPENAI_MODEL")
        if os.getenv("USE_LOCAL_MODEL") == "true":
            config_dict.setdefault("llm", {})["provider"] = "local"
            if os.getenv("LOCAL_MODEL"):
                config_dict.setdefault("llm", {})["model"] = os.getenv("LOCAL_MODEL")

        # Data configuration
        if os.getenv("DATA_SOURCE"):
            config_dict.setdefault("data", {})["source"] = os.getenv("DATA_SOURCE")

        _config = TradingConfig(**config_dict)

        # Validate and print warnings
        warnings = _config.validate_config()
        if warnings:
            print("⚠️  Configuration warnings:")
            for warning in warnings:
                print(f"   - {warning}")

    return _config


def reset_config():
    """Reset the global configuration (mainly for testing)."""
    global _config
    _config = None
