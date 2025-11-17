"""
Offline Data Source - Reads from pre-generated parquet files
"""

import os
from typing import Dict, Optional
import pandas as pd
import numpy as np

from .data_source import DataSource, DataSourceFactory, parse_trade_date
from datetime import datetime


class OfflineDataSource(DataSource):
    """Offline data source reading from parquet files."""

    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize offline data source.

        Args:
            data_path: Path to parquet file. If None, uses default location.
        """
        self.name = "offline"
        self._data_cache = None
        self._cache_path = None

        if data_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.data_path = os.path.join(
                base_dir, "dataflows", "data_cache", "offline_trading_data.parquet"
            )
        else:
            self.data_path = data_path

    def _load_data(self):
        """Load offline dataset (cached in memory)."""
        if self._data_cache is not None and self._cache_path == self.data_path:
            return self._data_cache

        if not os.path.exists(self.data_path):
            raise FileNotFoundError(
                f"Offline data file not found: {self.data_path}\n"
                "Please run: python generate_offline_data.py"
            )

        self._data_cache = pd.read_parquet(self.data_path)
        self._data_cache['Date'] = pd.to_datetime(self._data_cache['Date']).dt.date
        self._cache_path = self.data_path

        return self._data_cache

    def get_price_data(
        self,
        symbol: str,
        days_back: int = 90,
        trade_date: Optional[str] = None
    ) -> str:
        """Get stock price data from offline dataset."""
        try:
            df = self._load_data()
            symbol_upper = symbol.upper()
            symbol_df = df[df['symbol'] == symbol_upper].copy()

            if symbol_df.empty:
                return f"Symbol {symbol_upper} not found in offline dataset."

            # Filter by date
            if trade_date:
                try:
                    target_date = parse_trade_date(trade_date).date()
                except ValueError:
                    target_date = symbol_df['Date'].max()
            else:
                target_date = symbol_df['Date'].max()

            # Get data up to target date
            symbol_df = symbol_df[symbol_df['Date'] <= target_date].copy()

            if symbol_df.empty:
                return f"No data available for {symbol_upper} up to {trade_date or 'current date'}"

            # Sort and take last N days
            symbol_df = symbol_df.sort_values('Date')
            symbol_df = symbol_df.tail(min(days_back + 10, len(symbol_df)))

            # Get target row
            target_row = symbol_df.iloc[-1]
            current_price = target_row['Close']

            # Calculate price changes
            if len(symbol_df) >= 2:
                prev_close = symbol_df.iloc[-2]['Close']
                price_change_1d = ((current_price / prev_close) - 1) * 100 if prev_close != 0 else 0.0
            else:
                price_change_1d = 0.0

            price_change_5d = None
            if len(symbol_df) >= 6:
                price_change_5d = ((symbol_df.iloc[-1]['Close'] / symbol_df.iloc[-6]['Close']) - 1) * 100

            price_change_30d = None
            if len(symbol_df) >= 31:
                price_change_30d = ((symbol_df.iloc[-1]['Close'] / symbol_df.iloc[-31]['Close']) - 1) * 100

            # Get indicators if available
            sma_20 = target_row.get('SMA_20', np.nan) if 'SMA_20' in symbol_df.columns else np.nan
            sma_50 = target_row.get('SMA_50', np.nan) if 'SMA_50' in symbol_df.columns else np.nan

            # Volume
            recent_volume = target_row['Volume']
            avg_volume = symbol_df['Volume'].mean()
            volume_ratio = (recent_volume / avg_volume * 100) if avg_volume > 0 else 0

            # Format
            price_change_5d_str = f"{price_change_5d:+.2f}%" if price_change_5d is not None else "N/A"
            price_change_30d_str = f"{price_change_30d:+.2f}%" if price_change_30d is not None else "N/A"
            sma_50_str = f"${sma_50:.2f}" if not pd.isna(sma_50) else "N/A"
            sma_20_diff_str = f"{((current_price / sma_20 - 1) * 100):+.2f}%" if not pd.isna(sma_20) else "N/A"

            actual_date = target_row['Date']
            date_note = ""
            if trade_date and str(actual_date) != trade_date:
                date_note = f"\nNote: {trade_date} not found. Using most recent trading day: {actual_date}"

            report = f"""
=== {symbol_upper} Price Data (Offline Dataset) ===
Analysis Date: {trade_date or actual_date}{date_note}
Data Range: {symbol_df['Date'].min()} to {symbol_df['Date'].max()}

Current Price: ${current_price:.2f}

Price Changes:
  - 1-day change: {price_change_1d:+.2f}%
  - 5-day change: {price_change_5d_str}
  - 30-day change: {price_change_30d_str}

Volume:
  - Current volume: {recent_volume:,.0f}
  - Average volume: {avg_volume:,.0f}
  - Volume ratio: {volume_ratio:.1f}% (current/average)

Technical Indicators:
  - 20-day MA (SMA20): ${sma_20:.2f}
  - 50-day MA (SMA50): {sma_50_str}
  - Price vs SMA20: {sma_20_diff_str}

Last 10 Trading Days:
"""
            # Add last 10 days
            recent = symbol_df.tail(10)[['Open', 'High', 'Low', 'Close', 'Volume']]
            report += recent.to_string()

            return report

        except Exception as e:
            return f"Error loading offline data for {symbol.upper()}: {str(e)}"

    def get_technical_indicators(
        self,
        symbol: str,
        trade_date: Optional[str] = None
    ) -> str:
        """Get technical indicators from offline dataset."""
        try:
            df = self._load_data()
            symbol_upper = symbol.upper()
            symbol_df = df[df['symbol'] == symbol_upper].copy()

            if symbol_df.empty:
                return f"Symbol {symbol_upper} not found in offline dataset."

            # Filter by date
            if trade_date:
                try:
                    target_date = parse_trade_date(trade_date).date()
                except ValueError:
                    target_date = symbol_df['Date'].max()
            else:
                target_date = symbol_df['Date'].max()

            symbol_df = symbol_df[symbol_df['Date'] <= target_date].copy()

            if symbol_df.empty:
                return f"No data available for {symbol_upper}"

            # Get latest row
            latest = symbol_df.iloc[-1]

            # Extract indicators
            rsi = latest.get('RSI', np.nan) if 'RSI' in symbol_df.columns else np.nan
            macd = latest.get('MACD', np.nan) if 'MACD' in symbol_df.columns else np.nan
            macd_signal = latest.get('MACD_signal', np.nan) if 'MACD_signal' in symbol_df.columns else np.nan

            # Format
            rsi_str = f"{rsi:.2f}" if not pd.isna(rsi) else "N/A"
            macd_str = f"{macd:.2f}" if not pd.isna(macd) else "N/A"
            macd_signal_str = f"{macd_signal:.2f}" if not pd.isna(macd_signal) else "N/A"

            report = f"""
=== {symbol_upper} Technical Indicators (Offline) ===

Momentum Indicators:
  - RSI (14): {rsi_str}
  - MACD: {macd_str}
  - MACD Signal: {macd_signal_str}

Note: Limited indicators available in offline dataset.
"""
            return report

        except Exception as e:
            return f"Error loading technical indicators for {symbol.upper()}: {str(e)}"

    def is_available(self) -> bool:
        """Check if offline data file exists."""
        return os.path.exists(self.data_path)

    def get_source_info(self) -> Dict[str, str]:
        """Get information about this data source."""
        return {
            "name": "Offline Dataset",
            "type": "offline",
            "description": "Pre-generated parquet data file",
            "path": self.data_path
        }


# Register this data source
DataSourceFactory.register_source("offline", OfflineDataSource)
DataSourceFactory.register_source("parquet", OfflineDataSource)  # Alias
