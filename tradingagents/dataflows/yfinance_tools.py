"""
Fetch real market data using yfinance
"""
from datetime import datetime, timedelta
from typing import Optional
import yfinance as yf
import pandas as pd


def get_stock_price_data(
    symbol: str,
    days_back: int = 90
) -> str:
    """
    Get stock price data (OHLCV)
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT)
        days_back: Number of days of historical data to fetch
    
    Returns:
        Formatted price data string
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        ticker = yf.Ticker(symbol.upper())
        data = ticker.history(start=start_date, end=end_date)
        
        if data.empty:
            return f"Unable to fetch data for {symbol}, possibly invalid ticker symbol."
        
        # Remove timezone info
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        
        # Keep important columns and round
        data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
        for col in ['Open', 'High', 'Low', 'Close']:
            data[col] = data[col].round(2)
        
        # Calculate basic statistics
        current_price = data['Close'].iloc[-1]
        price_change_1d = ((data['Close'].iloc[-1] / data['Close'].iloc[-2]) - 1) * 100
        price_change_5d = ((data['Close'].iloc[-1] / data['Close'].iloc[-6]) - 1) * 100 if len(data) >= 6 else None
        price_change_30d = ((data['Close'].iloc[-1] / data['Close'].iloc[-31]) - 1) * 100 if len(data) >= 31 else None
        
        avg_volume = data['Volume'].mean()
        recent_volume = data['Volume'].iloc[-1]
        volume_ratio = (recent_volume / avg_volume) * 100 if avg_volume > 0 else 0
        
        # Calculate simple technical indicators
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        
        sma_20 = data['SMA_20'].iloc[-1]
        sma_50 = data['SMA_50'].iloc[-1] if len(data) >= 50 else None
        
        # Format SMA50 value
        sma_50_str = f"${sma_50:.2f}" if sma_50 is not None and pd.notna(sma_50) else "N/A"
        
        # Format price changes
        price_change_5d_str = f"{price_change_5d:+.2f}%" if price_change_5d is not None else "N/A"
        price_change_30d_str = f"{price_change_30d:+.2f}%" if price_change_30d is not None else "N/A"
        
        # Build report
        report = f"""
=== {symbol.upper()} Price Data ===
Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}

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
  - Price vs SMA20: {((current_price / sma_20 - 1) * 100):+.2f}%

Last 10 Trading Days:
"""
        # Add last 10 days data table
        recent_data = data.tail(10)[['Open', 'High', 'Low', 'Close', 'Volume']]
        report += recent_data.to_string()
        
        return report
        
    except Exception as e:
        return f"Error fetching data for {symbol}: {str(e)}"


def get_technical_indicators(
    symbol: str,
    days_back: int = 90
) -> str:
    """
    Calculate technical indicators
    
    Args:
        symbol: Stock ticker symbol
        days_back: Number of days of historical data
    
    Returns:
        Technical indicators analysis string
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        ticker = yf.Ticker(symbol.upper())
        data = ticker.history(start=start_date, end=end_date)
        
        if data.empty:
            return f"Unable to fetch data for {symbol}."
        
        # Calculate moving averages
        data['SMA_10'] = data['Close'].rolling(window=10).mean()
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        
        # Calculate RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Calculate MACD
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = exp1 - exp2
        data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
        data['MACD_Hist'] = data['MACD'] - data['Signal']
        
        # Calculate Bollinger Bands
        data['BB_Middle'] = data['Close'].rolling(window=20).mean()
        bb_std = data['Close'].rolling(window=20).std()
        data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
        data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)
        
        # Get latest values
        latest = data.iloc[-1]
        current_price = latest['Close']
        
        # Format SMA50 value
        sma_50_value = latest['SMA_50']
        if pd.notna(sma_50_value):
            sma_50_str = f"${sma_50_value:.2f}"
            sma_50_position = "above" if current_price > sma_50_value else "below"
        else:
            sma_50_str = "N/A"
            sma_50_position = "N/A"
        
        # Determine positions
        sma_10_pos = "above" if current_price > latest['SMA_10'] else "below"
        sma_20_pos = "above" if current_price > latest['SMA_20'] else "below"
        
        # RSI status
        if latest['RSI'] > 70:
            rsi_status = "Overbought (>70)"
        elif latest['RSI'] < 30:
            rsi_status = "Oversold (<30)"
        else:
            rsi_status = "Neutral"
        
        # MACD status
        macd_hist_status = "bullish" if latest['MACD_Hist'] > 0 else "bearish"
        macd_trend = "MACD above signal (bullish)" if latest['MACD'] > latest['Signal'] else "MACD below signal (bearish)"
        
        # Build report
        report = f"""
=== {symbol.upper()} Technical Indicators ===

Moving Averages:
  - SMA10: ${latest['SMA_10']:.2f} ({sma_10_pos})
  - SMA20: ${latest['SMA_20']:.2f} ({sma_20_pos})
  - SMA50: {sma_50_str} ({sma_50_position})

RSI (Relative Strength Index):
  - Current: {latest['RSI']:.2f}
  - Status: {rsi_status}

MACD:
  - MACD line: {latest['MACD']:.2f}
  - Signal line: {latest['Signal']:.2f}
  - Histogram: {latest['MACD_Hist']:.2f} ({macd_hist_status})
  - Trend: {macd_trend}

Bollinger Bands:
  - Upper: ${latest['BB_Upper']:.2f}
  - Middle: ${latest['BB_Middle']:.2f}
  - Lower: ${latest['BB_Lower']:.2f}
  - Position: {((current_price - latest['BB_Lower']) / (latest['BB_Upper'] - latest['BB_Lower']) * 100):.1f}% (0%=lower, 100%=upper)

Trading Signals:
"""
        # Generate trading signals
        signals = []
        
        # Moving average signals
        if current_price > latest['SMA_10'] > latest['SMA_20']:
            signals.append("✓ Short-term MAs aligned bullish")
        elif current_price < latest['SMA_10'] < latest['SMA_20']:
            signals.append("✗ Short-term MAs aligned bearish")
        
        # RSI signals
        if latest['RSI'] > 70:
            signals.append("⚠ RSI overbought, possible pullback")
        elif latest['RSI'] < 30:
            signals.append("✓ RSI oversold, possible bounce")
        
        # MACD signals
        if latest['MACD'] > latest['Signal'] and latest['MACD_Hist'] > 0:
            signals.append("✓ MACD bullish crossover")
        elif latest['MACD'] < latest['Signal'] and latest['MACD_Hist'] < 0:
            signals.append("✗ MACD bearish crossover")
        
        report += "\n".join(f"  {s}" for s in signals) if signals else "  - No clear signals"
        
        return report
        
    except Exception as e:
        return f"Error calculating technical indicators for {symbol}: {str(e)}"


def get_company_info(symbol: str) -> str:
    """
    Get company basic information
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        Company information string
    """
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        if not info or 'symbol' not in info:
            return f"Unable to fetch company info for {symbol}."
        
        report = f"""
=== {symbol.upper()} Company Information ===

Basic Info:
  - Company: {info.get('longName', 'N/A')}
  - Industry: {info.get('industry', 'N/A')}
  - Sector: {info.get('sector', 'N/A')}
  - Country: {info.get('country', 'N/A')}

Valuation Metrics:
  - Market Cap: ${info.get('marketCap', 0) / 1e9:.2f}B
  - P/E Ratio: {info.get('trailingPE', 'N/A')}
  - P/B Ratio: {info.get('priceToBook', 'N/A')}
  - Dividend Yield: {info.get('dividendYield', 0) * 100:.2f}% (if any)

Financial Data:
  - Total Revenue: ${info.get('totalRevenue', 0) / 1e9:.2f}B
  - Gross Margin: {info.get('grossMargins', 0) * 100:.2f}%
  - Operating Margin: {info.get('operatingMargins', 0) * 100:.2f}%
  - Profit Margin: {info.get('profitMargins', 0) * 100:.2f}%

Analyst Targets:
  - Target Price: ${info.get('targetMeanPrice', 'N/A')}
  - Recommendation: {info.get('recommendationKey', 'N/A').upper()}
"""
        return report
        
    except Exception as e:
        return f"Error fetching company info for {symbol}: {str(e)}"


def get_recent_news(symbol: str, max_news: int = 5) -> str:
    """
    Get recent news
    
    Args:
        symbol: Stock ticker symbol
        max_news: Maximum number of news items to return
    
    Returns:
        News summary string
    """
    try:
        ticker = yf.Ticker(symbol.upper())
        news = ticker.news
        
        if not news or len(news) == 0:
            return f"No recent news found for {symbol}."
        
        report = f"=== {symbol.upper()} Recent News ===\n\n"
        
        valid_news_count = 0
        for item in news:
            # Skip items with invalid data
            title = item.get('title', '')
            publisher = item.get('publisher', '')
            timestamp_raw = item.get('providerPublishTime', 0)
            
            # Skip if no valid title or timestamp is too old (before 2020)
            if not title or timestamp_raw < 1577836800:  # Jan 1, 2020
                continue
                
            timestamp = datetime.fromtimestamp(timestamp_raw)
            
            valid_news_count += 1
            report += f"{valid_news_count}. {title}\n"
            report += f"   Source: {publisher if publisher else 'Unknown'} | Time: {timestamp.strftime('%Y-%m-%d %H:%M')}\n\n"
            
            if valid_news_count >= max_news:
                break
        
        if valid_news_count == 0:
            return f"No valid recent news found for {symbol}."
        
        return report
        
    except Exception as e:
        return f"Error fetching news for {symbol}: {str(e)}"

