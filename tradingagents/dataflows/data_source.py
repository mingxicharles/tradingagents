"""
Unified Data Source Abstraction Layer

This module provides a clean interface for accessing market data from various sources.
All data sources implement the same interface, making it easy to swap between live,
offline, and CSV data sources.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional
import pandas as pd


class DataSource(ABC):
    """
    Abstract base class for market data sources.

    All data sources must implement these methods to provide consistent
    access to price data and technical indicators.
    """

    @abstractmethod
    def get_price_data(
        self,
        symbol: str,
        days_back: int = 90,
        trade_date: Optional[str] = None
    ) -> str:
        """
        Get formatted price data for a symbol.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            days_back: Number of days of historical data to fetch
            trade_date: Specific date to analyze (YYYY-MM-DD format), None for current

        Returns:
            Formatted string with price data suitable for LLM consumption
        """
        pass

    @abstractmethod
    def get_technical_indicators(
        self,
        symbol: str,
        trade_date: Optional[str] = None
    ) -> str:
        """
        Get formatted technical indicators for a symbol.

        Args:
            symbol: Stock ticker symbol
            trade_date: Specific date to analyze (YYYY-MM-DD format), None for current

        Returns:
            Formatted string with technical indicators
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this data source is available and ready to use.

        Returns:
            True if data source is available, False otherwise
        """
        pass

    @abstractmethod
    def get_source_info(self) -> Dict[str, str]:
        """
        Get information about this data source.

        Returns:
            Dictionary with source metadata (name, type, description)
        """
        pass


class DataSourceFactory:
    """
    Factory for creating data source instances.

    This factory makes it easy to switch between different data sources
    based on configuration or runtime conditions.
    """

    _sources = {}

    @classmethod
    def register_source(cls, name: str, source_class: type):
        """
        Register a data source implementation.

        Args:
            name: Name of the data source (e.g., 'yfinance', 'offline', 'csv')
            source_class: Class that implements DataSource
        """
        cls._sources[name] = source_class

    @classmethod
    def create(cls, source_type: str, **kwargs) -> DataSource:
        """
        Create a data source instance.

        Args:
            source_type: Type of data source to create
            **kwargs: Additional arguments to pass to the data source constructor

        Returns:
            DataSource instance

        Raises:
            ValueError: If source_type is not registered
        """
        if source_type not in cls._sources:
            available = ', '.join(cls._sources.keys())
            raise ValueError(
                f"Unknown data source type: {source_type}. "
                f"Available sources: {available}"
            )

        source_class = cls._sources[source_type]
        return source_class(**kwargs)

    @classmethod
    def list_sources(cls) -> list[str]:
        """
        List all registered data sources.

        Returns:
            List of registered source names
        """
        return list(cls._sources.keys())


def parse_trade_date(trade_date: str) -> datetime:
    """
    Parse trade_date string with flexible format handling.
    Supports both "2024-01-15" and "2024-1-15" formats.

    Args:
        trade_date: Date string in YYYY-MM-DD format (with or without leading zeros)

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If date cannot be parsed
    """
    # Try standard format first
    try:
        return datetime.strptime(trade_date, "%Y-%m-%d")
    except ValueError:
        pass

    # Try parsing manually (handles "2024-1-15" format)
    try:
        parts = trade_date.split('-')
        if len(parts) == 3:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            return datetime(year, month, day)
    except (ValueError, IndexError):
        pass

    raise ValueError(
        f"Invalid date format: {trade_date}. Expected YYYY-MM-DD or YYYY-M-D"
    )
