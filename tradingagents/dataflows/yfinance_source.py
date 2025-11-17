"""
YFinance Data Source - Live market data from Yahoo Finance
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import yfinance as yf
import pandas as pd
import numpy as np

from .data_source import DataSource, DataSourceFactory, parse_trade_date


class YFinanceDataSource(DataSource):
    """Live market data source using yfinance."""

    def __init__(self):
        """Initialize YFinance data source."""
        self.name = "yfinance"

    def get_price_data(
        self,
        symbol: str,
        days_back: int = 90,
        trade_date: Optional[str] = None
    ) -> str:
        """Get stock price data from Yahoo Finance."""
        try:
            if trade_date:
                try:
                    target_date = parse_trade_date(trade_date)
                    end_date = target_date + timedelta(days=1)
                except ValueError:
                    target_date = datetime.now()
                    end_date = target_date + timedelta(days=1)
            else:
                target_date = datetime.now()
                end_date = target_date + timedelta(days=1)

            start_date = end_date - timedelta(days=days_back + 5)

            ticker = yf.Ticker(symbol.upper())
            data = ticker.history(start=start_date, end=end_date)

            if trade_date:
                target_date_only = target_date.date()
                data = data[data.index.date <= target_date_only]

            if data.empty:
                return f"No price data available for {symbol.upper()}"

            # Get recent data
            current_price = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2] if len(data) >= 2 else current_price
            price_change_1d = ((current_price / prev_close) - 1) * 100 if prev_close != 0 else 0.0

            # Multi-period changes
            price_change_5d = None
            if len(data) >= 6:
                price_change_5d = ((data['Close'].iloc[-1] / data['Close'].iloc[-6]) - 1) * 100

            price_change_30d = None
            if len(data) >= 31:
                price_change_30d = ((data['Close'].iloc[-1] / data['Close'].iloc[-31]) - 1) * 100

            # Volume
            recent_volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume'].mean()
            volume_ratio = (recent_volume / avg_volume * 100) if avg_volume > 0 else 0

            # Format
            price_change_5d_str = f"{price_change_5d:+.2f}%" if price_change_5d is not None else "N/A"
            price_change_30d_str = f"{price_change_30d:+.2f}%" if price_change_30d is not None else "N/A"

            # Get latest date
            latest_date = data.index[-1].strftime('%Y-%m-%d')

            report = f"""
=== {symbol.upper()} Price Data (Live - Yahoo Finance) ===
Latest Data: {latest_date}
Data Range: {data.index[0].strftime('%Y-%m-%d')} to {latest_date}

Current Price: ${current_price:.2f}

Price Changes:
  - 1-day change: {price_change_1d:+.2f}%
  - 5-day change: {price_change_5d_str}
  - 30-day change: {price_change_30d_str}

Volume:
  - Current volume: {recent_volume:,.0f}
  - Average volume: {avg_volume:,.0f}
  - Volume ratio: {volume_ratio:.1f}% (current/average)

Last 10 Trading Days:
"""
            # Add last 10 days
            recent = data.tail(10)[['Open', 'High', 'Low', 'Close', 'Volume']]
            report += recent.to_string()

            return report

        except Exception as e:
            return f"Error fetching price data for {symbol.upper()}: {str(e)}"

    def get_technical_indicators(
        self,
        symbol: str,
        trade_date: Optional[str] = None
    ) -> str:
        """Get technical indicators from Yahoo Finance data."""
        try:
            if trade_date:
                try:
                    target_date = parse_trade_date(trade_date)
                    end_date = target_date + timedelta(days=1)
                except ValueError:
                    target_date = datetime.now()
                    end_date = target_date + timedelta(days=1)
            else:
                target_date = datetime.now()
                end_date = target_date + timedelta(days=1)

            # Fetch enough data for technical indicators (200 days for 200-day MA)
            start_date = end_date - timedelta(days=250)

            ticker = yf.Ticker(symbol.upper())
            data = ticker.history(start=start_date, end=end_date)

            if trade_date:
                target_date_only = target_date.date()
                data = data[data.index.date <= target_date_only]

            if data.empty:
                return f"No data available for technical indicators: {symbol.upper()}"

            # Calculate technical indicators
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()

            # RSI calculation
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))

            # MACD
            ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
            data['MACD'] = ema_12 - ema_26
            data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

            # Bollinger Bands
            data['BB_Middle'] = data['Close'].rolling(window=20).mean()
            bb_std = data['Close'].rolling(window=20).std()
            data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
            data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)

            # Get latest values
            latest = data.iloc[-1]
            current_price = latest['Close']

            # Format indicators
            sma_20 = latest.get('SMA_20', np.nan)
            sma_50 = latest.get('SMA_50', np.nan)
            sma_200 = latest.get('SMA_200', np.nan)
            rsi = latest.get('RSI', np.nan)
            macd = latest.get('MACD', np.nan)
            macd_signal = latest.get('MACD_Signal', np.nan)
            bb_upper = latest.get('BB_Upper', np.nan)
            bb_lower = latest.get('BB_Lower', np.nan)

            # Format values
            sma_20_str = f"${sma_20:.2f} ({((current_price/sma_20-1)*100):+.2f}% from price)" if not pd.isna(sma_20) else "N/A"
            sma_50_str = f"${sma_50:.2f} ({((current_price/sma_50-1)*100):+.2f}% from price)" if not pd.isna(sma_50) else "N/A"
            sma_200_str = f"${sma_200:.2f} ({((current_price/sma_200-1)*100):+.2f}% from price)" if not pd.isna(sma_200) else "N/A"

            if not pd.isna(rsi):
                rsi_str = f"{rsi:.2f} {'(Oversold)' if rsi < 30 else '(Overbought)' if rsi > 70 else '(Neutral)'}"
            else:
                rsi_str = "N/A"

            macd_str = f"{macd:.2f}" if not pd.isna(macd) else "N/A"
            macd_signal_str = f"{macd_signal:.2f}" if not pd.isna(macd_signal) else "N/A"

            if not pd.isna(macd) and not pd.isna(macd_signal):
                macd_hist_str = f"{(macd - macd_signal):.2f} {'(Bullish)' if macd > macd_signal else '(Bearish)'}"
            else:
                macd_hist_str = "N/A"

            bb_upper_str = f"${bb_upper:.2f}" if not pd.isna(bb_upper) else "N/A"
            bb_lower_str = f"${bb_lower:.2f}" if not pd.isna(bb_lower) else "N/A"

            if not pd.isna(bb_upper) and not pd.isna(bb_lower):
                if current_price > (bb_upper * 0.98):
                    bb_pos_str = "Near Upper (potential resistance)"
                elif current_price < (bb_lower * 1.02):
                    bb_pos_str = "Near Lower (potential support)"
                else:
                    bb_pos_str = "Middle range"
            else:
                bb_pos_str = "N/A"

            report = f"""
=== {symbol.upper()} Technical Indicators (Live) ===

Moving Averages:
  - SMA 20-day: {sma_20_str}
  - SMA 50-day: {sma_50_str}
  - SMA 200-day: {sma_200_str}

Momentum Indicators:
  - RSI (14): {rsi_str}
  - MACD: {macd_str}
  - MACD Signal: {macd_signal_str}
  - MACD Histogram: {macd_hist_str}

Bollinger Bands:
  - Upper Band: {bb_upper_str}
  - Lower Band: {bb_lower_str}
  - Position: {bb_pos_str}
"""
            return report

        except Exception as e:
            return f"Error calculating technical indicators for {symbol.upper()}: {str(e)}"

    def is_available(self) -> bool:
        """Check if YFinance is available."""
        try:
            # Try to fetch a simple stock to verify connectivity
            test = yf.Ticker("AAPL")
            info = test.history(period="1d")
            return not info.empty
        except Exception:
            return False

    def get_source_info(self) -> Dict[str, str]:
        """Get information about this data source."""
        return {
            "name": "Yahoo Finance",
            "type": "live",
            "description": "Live market data from Yahoo Finance",
            "provider": "yfinance"
        }


# Register this data source
DataSourceFactory.register_source("yfinance", YFinanceDataSource)
DataSourceFactory.register_source("live", YFinanceDataSource)  # Alias
