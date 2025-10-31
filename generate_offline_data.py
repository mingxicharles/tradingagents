"""
Generate offline dataset for trading agents
Creates a small batch example with synthetic data for testing
"""
import os
import time
import math
import json
import datetime as dt
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# -------------------------------
# CONFIG - Small batch for testing
# -------------------------------
UNIVERSE = ["AAPL", "MSFT", "AMZN"]  # Small set for testing
START = "2024-01-01"
END = "2024-12-31"
OUTPUT_DIR = "dataflows/data_cache"
LOOKAHEAD_SHIFT_DAYS = 1

# -------------------------------
# Generate synthetic price data
# -------------------------------
def generate_synthetic_prices(symbol, start_date, end_date):
    """Generate realistic synthetic OHLCV data"""
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    # Filter to weekdays only (trading days)
    dates = dates[dates.weekday < 5]
    
    # Starting prices by symbol
    base_prices = {"AAPL": 180.0, "MSFT": 380.0, "AMZN": 150.0}
    initial_price = base_prices.get(symbol, 100.0)
    
    # Generate random walk with some trend
    n = len(dates)
    returns = np.random.normal(0.001, 0.02, n)  # ~0.1% daily mean return, 2% volatility
    # Add some trend
    trend = np.linspace(0, 0.3, n)  # ~30% overall trend
    returns += trend / n
    
    prices = [initial_price]
    for r in returns[:-1]:
        prices.append(prices[-1] * (1 + r))
    
    # Generate OHLCV
    data = []
    for i, date in enumerate(dates):
        close = prices[i]
        # High and low around close
        daily_range = close * 0.02  # 2% daily range
        high = close + np.random.uniform(0, daily_range)
        low = close - np.random.uniform(0, daily_range)
        # Open near previous close
        if i > 0:
            open_price = prices[i-1] + np.random.uniform(-daily_range*0.3, daily_range*0.3)
        else:
            open_price = close + np.random.uniform(-daily_range*0.3, daily_range*0.3)
        
        # Volume
        base_volume = 50_000_000 if symbol == "AAPL" else 30_000_000
        volume = int(base_volume * np.random.uniform(0.5, 2.0))
        
        data.append({
            'Date': date.date(),
            'Open': round(open_price, 2),
            'High': round(high, 2),
            'Low': round(low, 2),
            'Close': round(close, 2),
            'Volume': volume
        })
    
    df = pd.DataFrame(data)
    df = df.set_index('Date')
    return df

def compute_indicators(prices_df):
    """Compute technical indicators: SMA, EMA, RSI, MACD"""
    df = prices_df.copy()
    close = df['Close']
    
    # SMA
    df['SMA_10'] = close.rolling(10).mean()
    df['SMA_20'] = close.rolling(20).mean()
    df['SMA_50'] = close.rolling(50).mean()
    
    # EMA
    df['EMA_12'] = close.ewm(span=12, adjust=False).mean()
    df['EMA_26'] = close.ewm(span=26, adjust=False).mean()
    
    # MACD
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # RSI(14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / (loss.replace(0, 1e-9))
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['BB_Middle'] = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    return df

def generate_fundamentals(symbol, dates):
    """Generate synthetic fundamental data (quarterly forward-filled to daily)"""
    # Simulate quarterly reports
    quarters = []
    for year in range(2024, 2025):
        for quarter in [1, 2, 3, 4]:
            quarter_date = pd.Timestamp(f"{year}-{quarter*3}-01")
            if quarter_date >= pd.Timestamp(dates[0]) and quarter_date <= pd.Timestamp(dates[-1]):
                quarters.append({
                    'Date': quarter_date.date(),
                    'PE_Ratio': np.random.uniform(15, 35),
                    'Market_Cap': np.random.uniform(1e12, 3e12),
                    'Revenue': np.random.uniform(50e9, 150e9),
                    'EPS': np.random.uniform(5, 15),
                })
    
    if not quarters:
        return pd.DataFrame(index=dates)
    
    fund_df = pd.DataFrame(quarters)
    fund_df['Date'] = pd.to_datetime(fund_df['Date'])
    fund_df = fund_df.set_index('Date').sort_index()
    
    # Forward fill to daily
    daily_dates = pd.date_range(start=dates[0], end=dates[-1], freq='D')
    daily_dates = daily_dates[daily_dates.weekday < 5]  # Trading days only
    fund_daily = fund_df.reindex(pd.DatetimeIndex(daily_dates), method='ffill')
    fund_daily.index = fund_daily.index.date
    
    return fund_daily

def generate_news(symbol, dates):
    """Generate synthetic news data"""
    news_rows = []
    # Generate news on random days
    news_days = np.random.choice(dates, size=min(20, len(dates)//10), replace=False)
    
    for day in news_days:
        news_rows.append({
            'Date': day,
            'symbol': symbol,
            'title': f"{symbol} reports strong quarterly earnings",
            'source': 'MarketWatch',
            'sentiment': np.random.choice(['positive', 'neutral', 'negative'], p=[0.4, 0.4, 0.2])
        })
    
    if not news_rows:
        return pd.DataFrame()
    
    news_df = pd.DataFrame(news_rows)
    news_df['Date'] = pd.to_datetime(news_df['Date'])
    
    # Aggregate by date
    news_agg = news_df.groupby('Date').agg({
        'title': lambda x: ' | '.join(x.tolist()),
        'source': lambda x: ', '.join(set(x.tolist())),
        'sentiment': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'neutral'
    }).reset_index()
    news_agg['news_count'] = news_df.groupby('Date').size().values
    news_agg['Date'] = news_agg['Date'].dt.date
    
    # Merge to all trading days
    all_dates = pd.date_range(start=dates[0], end=dates[-1], freq='D')
    all_dates = all_dates[all_dates.weekday < 5]
    news_full = pd.DataFrame({'Date': all_dates.date})
    news_full = news_full.merge(news_agg, on='Date', how='left')
    news_full['news_count'] = news_full['news_count'].fillna(0).astype(int)
    news_full['sentiment'] = news_full['sentiment'].fillna('neutral')
    
    return news_full.set_index('Date')

# -------------------------------
# Main generation
# -------------------------------
print("Generating offline dataset...")
os.makedirs(OUTPUT_DIR, exist_ok=True)

all_data = []

for symbol in UNIVERSE:
    print(f"Processing {symbol}...")
    
    # Generate prices
    prices = generate_synthetic_prices(symbol, START, END)
    prices = compute_indicators(prices)
    
    # Generate fundamentals
    fundamentals = generate_fundamentals(symbol, prices.index.tolist())
    
    # Generate news
    news = generate_news(symbol, prices.index.tolist())
    
    # Merge all data
    df = prices.copy()
    if not fundamentals.empty:
        df = df.join(fundamentals, how='left')
    if not news.empty:
        df = df.join(news, how='left')
    
    df['symbol'] = symbol
    df['news_count'] = df['news_count'].fillna(0).astype(int)
    df['sentiment'] = df['sentiment'].fillna('neutral')
    
    # Shift forward-looking data to avoid lookahead
    forward_cols = [c for c in df.columns if c in ['PE_Ratio', 'Market_Cap', 'Revenue', 'EPS', 
                                                    'news_count', 'title', 'source', 'sentiment']]
    if forward_cols:
        df[forward_cols] = df[forward_cols].shift(LOOKAHEAD_SHIFT_DAYS)
    
    all_data.append(df.reset_index())

# Combine all symbols
final_df = pd.concat(all_data, ignore_index=True)
final_df = final_df.dropna(subset=['Close'])
final_df = final_df.sort_values(['symbol', 'Date'])

print(f"\nGenerated dataset:")
print(f"  Rows: {len(final_df):,}")
print(f"  Columns: {len(final_df.columns)}")
print(f"  Symbols: {final_df['symbol'].unique().tolist()}")
print(f"  Date range: {final_df['Date'].min()} to {final_df['Date'].max()}")
print(f"\nFirst few rows:")
print(final_df.head(10))

# Save to parquet
output_path = os.path.join(OUTPUT_DIR, "offline_trading_data.parquet")
final_df.to_parquet(output_path, index=False)
print(f"\n✓ Saved to: {output_path}")

# Also save a CSV sample for inspection
csv_path = os.path.join(OUTPUT_DIR, "offline_trading_data_sample.csv")
final_df.head(100).to_csv(csv_path, index=False)
print(f"✓ Sample CSV saved to: {csv_path}")

print("\nDataset generation complete!")

