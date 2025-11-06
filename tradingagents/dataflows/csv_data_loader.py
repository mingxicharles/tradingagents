"""
CSV Data Loader for Trading Analysis
Loads data from CSV file for batch testing
"""

import os
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any


class CSVDataLoader:
    """Load and manage CSV trading data"""
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialize CSV data loader
        
        Args:
            csv_path: Path to CSV file. If None, uses default location.
        """
        if csv_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            csv_path = os.path.join(base_dir, "dataflows", "data_cache", "offline_trading_data_sample.csv")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        self.csv_path = csv_path
        self.data = pd.read_csv(csv_path)
        self.data['Date'] = pd.to_datetime(self.data['Date']).dt.date
        
        print(f"Loaded {len(self.data)} rows from {csv_path}")
        print(f"Symbols: {self.data['symbol'].unique().tolist()}")
        print(f"Date range: {self.data['Date'].min()} to {self.data['Date'].max()}")
    
    def get_row_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get a single row by index"""
        if index < 0 or index >= len(self.data):
            return None
        return self.data.iloc[index].to_dict()
    
    def get_data_for_date(self, symbol: str, date: str) -> Optional[Dict[str, Any]]:
        """Get data for specific symbol and date"""
        if isinstance(date, str):
            date = pd.to_datetime(date).date()
        
        mask = (self.data['symbol'] == symbol.upper()) & (self.data['Date'] == date)
        result = self.data[mask]
        
        if len(result) == 0:
            return None
        return result.iloc[0].to_dict()
    
    def get_next_day_data(self, symbol: str, date: str) -> Optional[Dict[str, Any]]:
        """Get next trading day's data"""
        if isinstance(date, str):
            date = pd.to_datetime(date).date()
        
        symbol_data = self.data[self.data['symbol'] == symbol.upper()].copy()
        symbol_data = symbol_data.sort_values('Date')
        
        current_idx = symbol_data[symbol_data['Date'] == date].index
        if len(current_idx) == 0:
            return None
        
        current_position = symbol_data.index.get_loc(current_idx[0])
        if current_position + 1 >= len(symbol_data):
            return None
        
        return symbol_data.iloc[current_position + 1].to_dict()
    
    def get_historical_data(self, symbol: str, date: str, days_back: int = 30) -> pd.DataFrame:
        """Get historical data up to given date"""
        if isinstance(date, str):
            date = pd.to_datetime(date).date()
        
        symbol_data = self.data[self.data['symbol'] == symbol.upper()].copy()
        symbol_data = symbol_data[symbol_data['Date'] <= date]
        symbol_data = symbol_data.sort_values('Date', ascending=False).head(days_back)
        
        return symbol_data.sort_values('Date')
    
    def format_price_data(self, symbol: str, date: str) -> str:
        """Format price data for agent consumption"""
        hist = self.get_historical_data(symbol, date, days_back=30)
        
        if len(hist) == 0:
            return "No historical data available"
        
        current = hist.iloc[-1]
        
        output = f"Stock Price Data for {symbol} (as of {date}):\n\n"
        output += f"Current Price: ${current['Close']:.2f}\n"
        output += f"Day Range: ${current['Low']:.2f} - ${current['High']:.2f}\n"
        output += f"Volume: {int(current['Volume']):,}\n\n"
        
        output += "Recent Price History (last 10 days):\n"
        for _, row in hist.tail(10).iterrows():
            output += f"  {row['Date']}: Open ${row['Open']:.2f}, Close ${row['Close']:.2f}, Volume {int(row['Volume']):,}\n"
        
        return output
    
    def format_technical_indicators(self, symbol: str, date: str) -> str:
        """Format technical indicators for agent consumption"""
        current_data = self.get_data_for_date(symbol, date)
        
        if current_data is None:
            return "No technical data available"
        
        output = f"Technical Indicators for {symbol} (as of {date}):\n\n"
        
        # Moving averages
        if pd.notna(current_data.get('SMA_10')):
            output += f"SMA(10): ${current_data['SMA_10']:.2f}\n"
        if pd.notna(current_data.get('SMA_20')):
            output += f"SMA(20): ${current_data['SMA_20']:.2f}\n"
        if pd.notna(current_data.get('SMA_50')):
            output += f"SMA(50): ${current_data['SMA_50']:.2f}\n"
        
        # MACD
        if pd.notna(current_data.get('MACD')):
            output += f"\nMACD: {current_data['MACD']:.4f}\n"
            output += f"MACD Signal: {current_data['MACD_Signal']:.4f}\n"
            output += f"MACD Histogram: {current_data['MACD_Hist']:.4f}\n"
        
        # RSI
        if pd.notna(current_data.get('RSI')):
            output += f"\nRSI: {current_data['RSI']:.2f}\n"
            if current_data['RSI'] > 70:
                output += "  (Overbought territory)\n"
            elif current_data['RSI'] < 30:
                output += "  (Oversold territory)\n"
        
        # Bollinger Bands
        if pd.notna(current_data.get('BB_Upper')):
            output += f"\nBollinger Bands:\n"
            output += f"  Upper: ${current_data['BB_Upper']:.2f}\n"
            output += f"  Middle: ${current_data['BB_Middle']:.2f}\n"
            output += f"  Lower: ${current_data['BB_Lower']:.2f}\n"
            output += f"  Current Price: ${current_data['Close']:.2f}\n"
        
        return output
    
    def format_fundamental_data(self, symbol: str, date: str) -> str:
        """Format fundamental data for agent consumption"""
        current_data = self.get_data_for_date(symbol, date)
        
        if current_data is None:
            return "No fundamental data available"
        
        output = f"Fundamental Data for {symbol} (as of {date}):\n\n"
        
        if pd.notna(current_data.get('PE_Ratio')):
            output += f"P/E Ratio: {current_data['PE_Ratio']:.2f}\n"
        
        if pd.notna(current_data.get('Market_Cap')):
            output += f"Market Cap: ${current_data['Market_Cap']:,.0f}\n"
        
        if pd.notna(current_data.get('Revenue')):
            output += f"Revenue: ${current_data['Revenue']:,.0f}\n"
        
        if pd.notna(current_data.get('EPS')):
            output += f"EPS: ${current_data['EPS']:.2f}\n"
        
        if not any(pd.notna(current_data.get(k)) for k in ['PE_Ratio', 'Market_Cap', 'Revenue', 'EPS']):
            output += "Limited fundamental data available\n"
        
        return output
    
    def format_news_data(self, symbol: str, date: str) -> str:
        """Format news data for agent consumption"""
        current_data = self.get_data_for_date(symbol, date)
        
        if current_data is None:
            return "No news data available"
        
        output = f"News for {symbol} (as of {date}):\n\n"
        
        if pd.notna(current_data.get('title')) and current_data['title']:
            output += f"Headline: {current_data['title']}\n"
            if pd.notna(current_data.get('source')):
                output += f"Source: {current_data['source']}\n"
            if pd.notna(current_data.get('sentiment')):
                output += f"Sentiment: {current_data['sentiment']}\n"
        else:
            output += "No significant news today\n"
        
        if pd.notna(current_data.get('news_count')):
            output += f"Total news articles: {int(current_data['news_count'])}\n"
        
        return output
    
    def calculate_actual_return(self, symbol: str, date: str) -> Optional[float]:
        """
        Calculate actual return from date to next day
        
        Returns:
            Return percentage (e.g., 2.5 for 2.5% gain) or None if no next day data
        """
        current = self.get_data_for_date(symbol, date)
        next_day = self.get_next_day_data(symbol, date)
        
        if current is None or next_day is None:
            return None
        
        current_close = current['Close']
        next_close = next_day['Close']
        
        return ((next_close - current_close) / current_close) * 100
    
    def get_test_cases(self, symbol: Optional[str] = None, max_cases: Optional[int] = None) -> pd.DataFrame:
        """
        Get all test cases (rows with next day data available)
        
        Args:
            symbol: Filter by symbol. If None, includes all symbols.
            max_cases: Maximum number of cases to return
            
        Returns:
            DataFrame of test cases with actual returns
        """
        test_cases = []
        
        data_to_process = self.data if symbol is None else self.data[self.data['symbol'] == symbol.upper()]
        
        for idx, row in data_to_process.iterrows():
            next_day = self.get_next_day_data(row['symbol'], row['Date'])
            if next_day is not None:
                actual_return = self.calculate_actual_return(row['symbol'], row['Date'])
                test_cases.append({
                    'index': idx,
                    'symbol': row['symbol'],
                    'date': row['Date'],
                    'close': row['Close'],
                    'next_close': next_day['Close'],
                    'actual_return': actual_return,
                    'actual_direction': 'UP' if actual_return > 0 else 'DOWN' if actual_return < 0 else 'FLAT'
                })
        
        result = pd.DataFrame(test_cases)
        
        if max_cases is not None:
            result = result.head(max_cases)
        
        return result


# Global instance
_csv_loader = None


def get_csv_loader(csv_path: Optional[str] = None) -> CSVDataLoader:
    """Get or create CSV loader instance"""
    global _csv_loader
    if _csv_loader is None:
        _csv_loader = CSVDataLoader(csv_path)
    return _csv_loader


def get_stock_price_data_csv(symbol: str, trade_date: str) -> str:
    """Get stock price data from CSV"""
    loader = get_csv_loader()
    return loader.format_price_data(symbol, trade_date)


def get_technical_indicators_csv(symbol: str, trade_date: str) -> str:
    """Get technical indicators from CSV"""
    loader = get_csv_loader()
    return loader.format_technical_indicators(symbol, trade_date)


def get_company_info_csv(symbol: str, trade_date: str) -> str:
    """Get company info from CSV"""
    loader = get_csv_loader()
    return loader.format_fundamental_data(symbol, trade_date)


def get_recent_news_csv(symbol: str, trade_date: str) -> str:
    """Get news from CSV"""
    loader = get_csv_loader()
    return loader.format_news_data(symbol, trade_date)

