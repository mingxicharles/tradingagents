"""
Performance Metrics Calculation

Calculate trading performance metrics like Sharpe ratio, Sortino ratio,
maximum drawdown, win rate, etc.
"""

from typing import List, Dict
import numpy as np
from dataclasses import dataclass, field


@dataclass
class PerformanceMetrics:
    """
    Comprehensive trading performance metrics.

    Attributes:
        total_return: Total return percentage
        annualized_return: Annualized return percentage
        sharpe_ratio: Sharpe ratio (risk-adjusted return)
        sortino_ratio: Sortino ratio (downside risk-adjusted)
        max_drawdown: Maximum drawdown percentage
        win_rate: Winning trades percentage
        profit_factor: Ratio of gross profit to gross loss
        average_win: Average winning trade return
        average_loss: Average losing trade return
        total_trades: Total number of trades
        winning_trades: Number of winning trades
        losing_trades: Number of losing trades
    """
    total_return: float = 0.0
    annualized_return: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    calmar_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    consecutive_wins: int = 0
    consecutive_losses: int = 0


def calculate_metrics(
    returns: List[float],
    trades: List[Dict],
    risk_free_rate: float = 0.02
) -> PerformanceMetrics:
    """
    Calculate comprehensive performance metrics.

    Args:
        returns: List of period returns
        trades: List of trade dictionaries with P&L
        risk_free_rate: Risk-free rate for Sharpe calculation

    Returns:
        PerformanceMetrics object
    """
    if not returns or not trades:
        return PerformanceMetrics()

    returns_arr = np.array(returns)

    # Total and annualized returns
    total_return = ((1 + returns_arr).prod() - 1) * 100
    periods_per_year = 252  # Trading days
    num_periods = len(returns)
    years = num_periods / periods_per_year
    annualized_return = (((1 + total_return/100) ** (1/years)) - 1) * 100 if years > 0 else 0

    # Sharpe ratio
    excess_returns = returns_arr - (risk_free_rate / periods_per_year)
    sharpe_ratio = (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(periods_per_year) if np.std(excess_returns) > 0 else 0

    # Sortino ratio (using downside deviation)
    downside_returns = returns_arr[returns_arr < 0]
    downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
    sortino_ratio = (np.mean(excess_returns) / downside_std) * np.sqrt(periods_per_year) if downside_std > 0 else 0

    # Maximum drawdown
    cumulative = (1 + returns_arr).cumprod()
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    max_drawdown = abs(drawdowns.min()) * 100

    # Calmar ratio
    calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0

    # Trade statistics
    trade_returns = [t.get('return_pct', 0) for t in trades]
    winning_trades = [r for r in trade_returns if r > 0]
    losing_trades = [r for r in trade_returns if r < 0]

    total_trades = len(trades)
    num_wins = len(winning_trades)
    num_losses = len(losing_trades)
    win_rate = (num_wins / total_trades * 100) if total_trades > 0 else 0

    # Average win/loss
    avg_win = np.mean(winning_trades) if winning_trades else 0
    avg_loss = np.mean(losing_trades) if losing_trades else 0

    # Largest win/loss
    largest_win = max(winning_trades) if winning_trades else 0
    largest_loss = min(losing_trades) if losing_trades else 0

    # Profit factor
    gross_profit = sum(winning_trades) if winning_trades else 0
    gross_loss = abs(sum(losing_trades)) if losing_trades else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

    # Consecutive wins/losses
    consecutive_wins = max_consecutive(trade_returns, positive=True)
    consecutive_losses = max_consecutive(trade_returns, positive=False)

    return PerformanceMetrics(
        total_return=total_return,
        annualized_return=annualized_return,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        max_drawdown=max_drawdown,
        calmar_ratio=calmar_ratio,
        win_rate=win_rate,
        profit_factor=profit_factor,
        average_win=avg_win,
        average_loss=avg_loss,
        largest_win=largest_win,
        largest_loss=largest_loss,
        total_trades=total_trades,
        winning_trades=num_wins,
        losing_trades=num_losses,
        consecutive_wins=consecutive_wins,
        consecutive_losses=consecutive_losses
    )


def max_consecutive(returns: List[float], positive: bool = True) -> int:
    """Calculate maximum consecutive wins or losses."""
    if not returns:
        return 0

    max_consecutive = 0
    current_consecutive = 0

    for ret in returns:
        if (positive and ret > 0) or (not positive and ret < 0):
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0

    return max_consecutive


def calculate_sharpe_ratio(
    returns: np.ndarray,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252
) -> float:
    """Calculate Sharpe ratio."""
    excess_returns = returns - (risk_free_rate / periods_per_year)
    if np.std(excess_returns) == 0:
        return 0.0
    return (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(periods_per_year)


def calculate_max_drawdown(returns: np.ndarray) -> float:
    """Calculate maximum drawdown."""
    cumulative = (1 + returns).cumprod()
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    return abs(drawdowns.min())
