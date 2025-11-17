"""
Backtesting Engine

Simulate trading strategies on historical data.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
import asyncio

from ..models import AnalysisRequest, FinalDecision
from ..risk import PortfolioTracker, RiskManager
from .metrics import PerformanceMetrics, calculate_metrics
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BacktestResults:
    """Results from a backtest run."""
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    metrics: PerformanceMetrics
    trades: List[Dict] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)
    portfolio: Optional[Dict] = None


class BacktestEngine:
    """
    Backtesting engine for trading strategies.

    Simulates trading on historical data with realistic execution,
    risk management, and performance tracking.
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,  # 0.1% commission
        slippage: float = 0.0005,   # 0.05% slippage
    ):
        """
        Initialize backtest engine.

        Args:
            initial_capital: Starting capital
            commission: Commission rate per trade
            slippage: Slippage rate
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

        self.portfolio = PortfolioTracker(initial_capital, name="Backtest Portfolio")
        self.risk_manager = RiskManager()

        logger.info(
            f"Backtest engine initialized: "
            f"capital=${initial_capital:,.2f}, "
            f"commission={commission:.2%}, "
            f"slippage={slippage:.2%}"
        )

    async def run_backtest(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        strategy_func: Callable,
        **kwargs
    ) -> BacktestResults:
        """
        Run backtest simulation.

        Args:
            symbols: List of symbols to trade
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD)
            strategy_func: Strategy function that generates decisions
            **kwargs: Additional arguments for strategy

        Returns:
            BacktestResults with performance metrics
        """
        logger.info(
            f"Starting backtest: {start_date} to {end_date}, "
            f"{len(symbols)} symbols"
        )

        equity_curve = []
        daily_returns = []

        # Simulate trading day by day
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")

        while current_date <= end_date_dt:
            date_str = current_date.strftime("%Y-%m-%d")

            # Record daily equity
            equity_curve.append({
                "date": date_str,
                "equity": self.portfolio.total_value,
                "cash": self.portfolio.cash,
                "positions_value": self.portfolio.positions_value
            })

            # Calculate daily return
            if len(equity_curve) > 1:
                prev_equity = equity_curve[-2]["equity"]
                daily_return = (self.portfolio.total_value - prev_equity) / prev_equity
                daily_returns.append(daily_return)

            # Generate trading signals for each symbol
            for symbol in symbols:
                await self._process_symbol(
                    symbol,
                    date_str,
                    strategy_func,
                    **kwargs
                )

            current_date += timedelta(days=1)

        # Calculate final metrics
        metrics = calculate_metrics(
            returns=daily_returns,
            trades=self.portfolio.closed_positions
        )

        results = BacktestResults(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=self.portfolio.total_value,
            metrics=metrics,
            trades=self.portfolio.closed_positions,
            equity_curve=equity_curve,
            portfolio=self.portfolio.get_portfolio_summary()
        )

        logger.info(
            f"Backtest complete: "
            f"return={metrics.total_return:.2f}%, "
            f"sharpe={metrics.sharpe_ratio:.2f}, "
            f"max_dd={metrics.max_drawdown:.2f}%"
        )

        return results

    async def _process_symbol(
        self,
        symbol: str,
        date: str,
        strategy_func: Callable,
        **kwargs
    ):
        """Process trading logic for a single symbol on a specific date."""
        try:
            # Generate trading decision using strategy
            request = AnalysisRequest(symbol=symbol, trade_date=date)
            decision = await strategy_func(request, **kwargs)

            if not isinstance(decision, FinalDecision):
                return

            # Get current price (would fetch from historical data in production)
            current_price = self._get_historical_price(symbol, date)

            if current_price is None:
                return

            # Apply risk management
            risk_assessment = self.risk_manager.assess_risk(
                decision,
                current_price,
                self.portfolio.total_value,
                {p.symbol: p for p in self.portfolio.positions.values()}
            )

            if not risk_assessment.risk_approved:
                logger.debug(f"Trade rejected for {symbol}: {risk_assessment.rejection_reasons}")
                return

            # Execute trade based on decision
            if decision.recommendation == "BUY":
                self._execute_buy(symbol, current_price, risk_assessment)
            elif decision.recommendation == "SELL":
                self._execute_sell(symbol, current_price)

        except Exception as e:
            logger.error(f"Error processing {symbol} on {date}: {e}")

    def _execute_buy(self, symbol: str, price: float, risk_assessment):
        """Execute buy order with slippage and commission."""
        # Apply slippage
        execution_price = price * (1 + self.slippage)

        # Calculate position size
        position_value = self.portfolio.total_value * risk_assessment.position_size
        shares = position_value / execution_price

        # Apply commission
        commission_cost = position_value * self.commission
        total_cost = (shares * execution_price) + commission_cost

        if total_cost <= self.portfolio.cash:
            self.portfolio.add_position(
                symbol,
                shares,
                execution_price,
                stop_loss=risk_assessment.stop_loss,
                take_profit=risk_assessment.take_profit
            )

    def _execute_sell(self, symbol: str, price: float):
        """Execute sell order with slippage and commission."""
        if symbol not in self.portfolio.positions:
            return

        # Apply slippage
        execution_price = price * (1 - self.slippage)

        # Close position
        pnl = self.portfolio.close_position(symbol, execution_price)

    def _get_historical_price(self, symbol: str, date: str) -> Optional[float]:
        """Get historical price (placeholder - would integrate with data source)."""
        # In production, fetch from historical database
        # For now, return simulated price
        import random
        base_price = hash(symbol) % 200 + 50
        return base_price * (1 + random.uniform(-0.02, 0.02))
