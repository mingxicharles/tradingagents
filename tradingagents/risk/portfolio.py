"""
Portfolio Tracking and Management

Track positions, calculate metrics, and manage portfolio state.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Position:
    """
    Represents a portfolio position.

    Attributes:
        symbol: Stock symbol
        shares: Number of shares
        entry_price: Average entry price
        current_price: Current market price
        entry_date: Date position was opened
        stop_loss: Stop loss price
        take_profit: Take profit price
        unrealized_pnl: Unrealized profit/loss
        unrealized_pnl_pct: Unrealized P&L percentage
    """
    symbol: str
    shares: float
    entry_price: float
    current_price: float
    entry_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    @property
    def market_value(self) -> float:
        """Current market value of position."""
        return self.shares * self.current_price

    @property
    def cost_basis(self) -> float:
        """Total cost basis."""
        return self.shares * self.entry_price

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss."""
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized P&L percentage."""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100

    @property
    def is_winner(self) -> bool:
        """Whether position is currently profitable."""
        return self.unrealized_pnl > 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "shares": self.shares,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "entry_date": self.entry_date,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "market_value": self.market_value,
            "cost_basis": self.cost_basis,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
        }


class PortfolioTracker:
    """
    Portfolio tracking and management.

    Tracks positions, cash, and calculates portfolio metrics.
    """

    def __init__(
        self,
        initial_cash: float = 100000.0,
        name: str = "Trading Portfolio"
    ):
        """
        Initialize portfolio tracker.

        Args:
            initial_cash: Starting cash amount
            name: Portfolio name
        """
        self.name = name
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Dict] = []
        self.transaction_history: List[Dict] = []

        logger.info(f"Portfolio initialized: {name}, cash=${initial_cash:,.2f}")

    @property
    def total_value(self) -> float:
        """Total portfolio value (cash + positions)."""
        positions_value = sum(p.market_value for p in self.positions.values())
        return self.cash + positions_value

    @property
    def positions_value(self) -> float:
        """Total value of all positions."""
        return sum(p.market_value for p in self.positions.values())

    @property
    def total_return(self) -> float:
        """Total return since inception."""
        return self.total_value - self.initial_cash

    @property
    def total_return_pct(self) -> float:
        """Total return percentage."""
        if self.initial_cash == 0:
            return 0.0
        return (self.total_return / self.initial_cash) * 100

    @property
    def cash_pct(self) -> float:
        """Cash as percentage of total portfolio."""
        if self.total_value == 0:
            return 100.0
        return (self.cash / self.total_value) * 100

    @property
    def num_positions(self) -> int:
        """Number of open positions."""
        return len(self.positions)

    @property
    def largest_position_pct(self) -> float:
        """Largest position as % of portfolio."""
        if not self.positions:
            return 0.0
        largest = max(p.market_value for p in self.positions.values())
        return (largest / self.total_value) * 100 if self.total_value > 0 else 0.0

    def add_position(
        self,
        symbol: str,
        shares: float,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """
        Add or increase a position.

        Args:
            symbol: Stock symbol
            shares: Number of shares to buy
            price: Purchase price
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price

        Returns:
            True if successful, False if insufficient cash
        """
        cost = shares * price

        if cost > self.cash:
            logger.warning(
                f"Insufficient cash for {symbol}: "
                f"need ${cost:,.2f}, have ${self.cash:,.2f}"
            )
            return False

        if symbol in self.positions:
            # Average up/down existing position
            existing = self.positions[symbol]
            total_shares = existing.shares + shares
            total_cost = existing.cost_basis + cost
            avg_price = total_cost / total_shares

            existing.shares = total_shares
            existing.entry_price = avg_price
            existing.current_price = price

            logger.info(f"Added to {symbol}: {shares} shares @ ${price:.2f}")
        else:
            # New position
            self.positions[symbol] = Position(
                symbol=symbol,
                shares=shares,
                entry_price=price,
                current_price=price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            logger.info(f"Opened {symbol}: {shares} shares @ ${price:.2f}")

        # Deduct cash
        self.cash -= cost

        # Record transaction
        self.transaction_history.append({
            "type": "BUY",
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "amount": cost,
            "timestamp": datetime.now().isoformat()
        })

        return True

    def close_position(
        self,
        symbol: str,
        price: float,
        shares: Optional[float] = None
    ) -> Optional[float]:
        """
        Close or reduce a position.

        Args:
            symbol: Stock symbol
            price: Sale price
            shares: Number of shares to sell (None = all)

        Returns:
            Realized P&L, or None if position doesn't exist
        """
        if symbol not in self.positions:
            logger.warning(f"Cannot close {symbol}: position does not exist")
            return None

        position = self.positions[symbol]

        if shares is None or shares >= position.shares:
            # Close entire position
            shares_to_sell = position.shares
            proceeds = shares_to_sell * price
            cost_basis = position.cost_basis
            realized_pnl = proceeds - cost_basis

            # Record closed position
            self.closed_positions.append({
                "symbol": symbol,
                "shares": shares_to_sell,
                "entry_price": position.entry_price,
                "exit_price": price,
                "entry_date": position.entry_date,
                "exit_date": datetime.now().strftime("%Y-%m-%d"),
                "realized_pnl": realized_pnl,
                "realized_pnl_pct": (realized_pnl / cost_basis) * 100
            })

            # Remove position
            del self.positions[symbol]

            logger.info(
                f"Closed {symbol}: {shares_to_sell} shares @ ${price:.2f}, "
                f"P&L: ${realized_pnl:,.2f}"
            )
        else:
            # Partial close
            shares_to_sell = shares
            proceeds = shares_to_sell * price
            cost_basis = shares_to_sell * position.entry_price
            realized_pnl = proceeds - cost_basis

            # Reduce position
            position.shares -= shares_to_sell
            position.current_price = price

            logger.info(
                f"Reduced {symbol}: sold {shares_to_sell} shares @ ${price:.2f}, "
                f"P&L: ${realized_pnl:,.2f}"
            )

        # Add cash
        proceeds = shares_to_sell * price
        self.cash += proceeds

        # Record transaction
        self.transaction_history.append({
            "type": "SELL",
            "symbol": symbol,
            "shares": shares_to_sell,
            "price": price,
            "amount": proceeds,
            "realized_pnl": realized_pnl,
            "timestamp": datetime.now().isoformat()
        })

        return realized_pnl

    def update_prices(self, prices: Dict[str, float]):
        """
        Update current prices for all positions.

        Args:
            prices: Dictionary of symbol -> current_price
        """
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.current_price = prices[symbol]

    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary."""
        return {
            "name": self.name,
            "total_value": self.total_value,
            "cash": self.cash,
            "cash_pct": self.cash_pct,
            "positions_value": self.positions_value,
            "num_positions": self.num_positions,
            "total_return": self.total_return,
            "total_return_pct": self.total_return_pct,
            "largest_position_pct": self.largest_position_pct,
            "positions": {
                symbol: pos.to_dict()
                for symbol, pos in self.positions.items()
            }
        }

    def save_to_file(self, filepath: Path):
        """Save portfolio state to file."""
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "portfolio": self.get_portfolio_summary(),
            "closed_positions": self.closed_positions,
            "transaction_history": self.transaction_history,
            "saved_at": datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Portfolio saved to {filepath}")

    @classmethod
    def load_from_file(cls, filepath: Path) -> 'PortfolioTracker':
        """Load portfolio state from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        portfolio_data = data['portfolio']

        tracker = cls(
            initial_cash=portfolio_data['total_value'] - portfolio_data['positions_value'],
            name=portfolio_data['name']
        )

        # Restore positions
        for symbol, pos_data in portfolio_data['positions'].items():
            tracker.positions[symbol] = Position(
                symbol=symbol,
                shares=pos_data['shares'],
                entry_price=pos_data['entry_price'],
                current_price=pos_data['current_price'],
                entry_date=pos_data['entry_date'],
                stop_loss=pos_data.get('stop_loss'),
                take_profit=pos_data.get('take_profit')
            )

        tracker.closed_positions = data.get('closed_positions', [])
        tracker.transaction_history = data.get('transaction_history', [])

        logger.info(f"Portfolio loaded from {filepath}")

        return tracker
