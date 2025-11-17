"""
Position Sizing Strategies

Various position sizing algorithms for optimal capital allocation.
"""

from abc import ABC, abstractmethod
from typing import Optional
import math

from ..utils.logging import get_logger

logger = get_logger(__name__)


class PositionSizer(ABC):
    """Abstract base class for position sizing strategies."""

    @abstractmethod
    def calculate_position_size(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss: float,
        confidence: float = 0.5
    ) -> float:
        """
        Calculate position size.

        Args:
            portfolio_value: Total portfolio value
            entry_price: Entry price
            stop_loss: Stop loss price
            confidence: Decision confidence (0-1)

        Returns:
            Position size as fraction of portfolio
        """
        pass


class FixedFractional(PositionSizer):
    """
    Fixed fractional position sizing.

    Risk a fixed percentage of capital on each trade.
    """

    def __init__(self, risk_per_trade: float = 0.02):
        """
        Initialize fixed fractional position sizer.

        Args:
            risk_per_trade: Fraction of portfolio to risk per trade (default 2%)
        """
        self.risk_per_trade = risk_per_trade
        logger.info(f"Fixed fractional sizing: {risk_per_trade:.1%} risk per trade")

    def calculate_position_size(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss: float,
        confidence: float = 0.5
    ) -> float:
        """Calculate position size using fixed fractional method."""
        # Amount to risk
        risk_amount = portfolio_value * self.risk_per_trade

        # Risk per share
        risk_per_share = abs(entry_price - stop_loss)

        if risk_per_share == 0:
            return 0.0

        # Number of shares
        shares = risk_amount / risk_per_share

        # Position value
        position_value = shares * entry_price

        # Position size as fraction of portfolio
        position_size = position_value / portfolio_value

        # Scale by confidence
        position_size *= confidence

        # Cap at 20% of portfolio
        return min(position_size, 0.20)


class KellyCriterion(PositionSizer):
    """
    Kelly Criterion position sizing.

    Optimal position sizing based on win rate and average win/loss.
    """

    def __init__(
        self,
        win_rate: float = 0.55,
        avg_win: float = 1.5,
        avg_loss: float = 1.0,
        fraction: float = 0.25  # Use quarter-Kelly for safety
    ):
        """
        Initialize Kelly Criterion position sizer.

        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average win as multiple of risk
            avg_loss: Average loss as multiple of risk
            fraction: Fraction of Kelly to use (for safety)
        """
        self.win_rate = win_rate
        self.avg_win = avg_win
        self.avg_loss = avg_loss
        self.fraction = fraction

        kelly_pct = self._calculate_kelly_percentage()
        logger.info(
            f"Kelly Criterion: win_rate={win_rate:.1%}, "
            f"kelly={kelly_pct:.1%}, "
            f"fractional_kelly={kelly_pct * fraction:.1%}"
        )

    def _calculate_kelly_percentage(self) -> float:
        """Calculate Kelly percentage."""
        # Kelly formula: f = (bp - q) / b
        # where:
        #   f = fraction to bet
        #   b = odds (avg_win / avg_loss)
        #   p = win probability
        #   q = loss probability (1 - p)

        b = self.avg_win / self.avg_loss
        p = self.win_rate
        q = 1 - p

        kelly = (b * p - q) / b

        # Kelly can be negative (don't bet) or > 1 (bet more than 100%)
        # We'll clamp it to reasonable values
        return max(0.0, min(kelly, 0.5))

    def calculate_position_size(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss: float,
        confidence: float = 0.5
    ) -> float:
        """Calculate position size using Kelly Criterion."""
        # Get base Kelly percentage
        kelly_pct = self._calculate_kelly_percentage()

        # Apply fraction (quarter-Kelly, half-Kelly, etc.)
        fractional_kelly = kelly_pct * self.fraction

        # Scale by confidence
        adjusted_kelly = fractional_kelly * confidence

        # Cap at 20% of portfolio
        return min(adjusted_kelly, 0.20)


class VolatilityAdjusted(PositionSizer):
    """
    Volatility-adjusted position sizing.

    Reduce position size for more volatile securities.
    """

    def __init__(
        self,
        base_risk: float = 0.02,
        target_volatility: float = 0.20  # 20% annualized
    ):
        """
        Initialize volatility-adjusted position sizer.

        Args:
            base_risk: Base risk per trade
            target_volatility: Target volatility level
        """
        self.base_risk = base_risk
        self.target_volatility = target_volatility
        logger.info(
            f"Volatility-adjusted sizing: "
            f"base_risk={base_risk:.1%}, "
            f"target_vol={target_volatility:.1%}"
        )

    def calculate_position_size(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss: float,
        confidence: float = 0.5,
        current_volatility: Optional[float] = None
    ) -> float:
        """Calculate position size adjusted for volatility."""
        # If no volatility provided, use standard fixed fractional
        if current_volatility is None:
            current_volatility = self.target_volatility

        # Volatility adjustment factor
        vol_adjustment = self.target_volatility / current_volatility

        # Adjusted risk
        adjusted_risk = self.base_risk * vol_adjustment

        # Amount to risk
        risk_amount = portfolio_value * adjusted_risk

        # Risk per share
        risk_per_share = abs(entry_price - stop_loss)

        if risk_per_share == 0:
            return 0.0

        # Number of shares
        shares = risk_amount / risk_per_share

        # Position value
        position_value = shares * entry_price

        # Position size as fraction
        position_size = position_value / portfolio_value

        # Scale by confidence
        position_size *= confidence

        # Cap at 20%
        return min(position_size, 0.20)


def optimal_f(
    trades: list[float],
    starting_capital: float = 1.0
) -> float:
    """
    Calculate Optimal F (Ralph Vince).

    Finds the optimal fixed fraction to maximize geometric growth.

    Args:
        trades: List of trade P&L values
        starting_capital: Starting capital

    Returns:
        Optimal f value (fraction to bet)
    """
    if not trades:
        return 0.0

    # Find largest loss
    largest_loss = abs(min(trades))

    if largest_loss == 0:
        return 0.0

    # Test different f values
    best_f = 0.0
    best_twr = 0.0

    for f_pct in range(1, 101):  # Test 1% to 100%
        f = f_pct / 100.0

        # Calculate Terminal Wealth Relative (TWR)
        capital = starting_capital
        for trade in trades:
            # HPR = 1 + (f * trade / largest_loss)
            hpr = 1 + (f * trade / largest_loss)
            capital *= hpr

            if capital <= 0:
                break

        if capital > best_twr:
            best_twr = capital
            best_f = f

    return best_f
