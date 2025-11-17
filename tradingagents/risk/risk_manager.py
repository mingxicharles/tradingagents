"""
Risk Management System

Comprehensive risk assessment and management for trading decisions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import math

from ..models import FinalDecision, AgentProposal
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RiskAssessment:
    """
    Risk assessment for a trading decision.

    Attributes:
        symbol: Stock symbol
        decision: Original trading decision
        risk_score: Overall risk score (0-100, higher = riskier)
        position_size: Recommended position size (as % of portfolio)
        stop_loss: Recommended stop loss price
        take_profit: Recommended take profit price
        risk_reward_ratio: Risk/reward ratio
        max_loss_amount: Maximum potential loss in dollars
        risk_factors: List of identified risk factors
        risk_approved: Whether risk is acceptable
        rejection_reasons: Reasons if rejected
    """
    symbol: str
    decision: FinalDecision
    risk_score: float
    position_size: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    max_loss_amount: Optional[float] = None
    risk_factors: List[str] = field(default_factory=list)
    risk_approved: bool = True
    rejection_reasons: List[str] = field(default_factory=list)
    assessed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class RiskManager:
    """
    Comprehensive risk management system.

    Evaluates trading decisions for risk and provides:
    - Position sizing recommendations
    - Stop loss and take profit levels
    - Risk/reward analysis
    - Risk constraint enforcement
    """

    def __init__(
        self,
        max_position_size: float = 0.10,  # Max 10% of portfolio per position
        max_portfolio_risk: float = 0.02,  # Max 2% portfolio risk per trade
        min_risk_reward: float = 2.0,      # Minimum 2:1 risk/reward ratio
        max_correlation: float = 0.7,      # Max correlation with existing positions
        max_sector_exposure: float = 0.30,  # Max 30% in single sector
    ):
        """
        Initialize risk manager.

        Args:
            max_position_size: Maximum position size as fraction of portfolio
            max_portfolio_risk: Maximum portfolio risk per trade
            min_risk_reward: Minimum acceptable risk/reward ratio
            max_correlation: Maximum correlation with existing positions
            max_sector_exposure: Maximum sector concentration
        """
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        self.min_risk_reward = min_risk_reward
        self.max_correlation = max_correlation
        self.max_sector_exposure = max_sector_exposure

        logger.info(
            f"RiskManager initialized: "
            f"max_position={max_position_size:.1%}, "
            f"max_risk={max_portfolio_risk:.1%}, "
            f"min_RR={min_risk_reward:.1f}"
        )

    def assess_risk(
        self,
        decision: FinalDecision,
        current_price: float,
        portfolio_value: float = 100000.0,
        existing_positions: Optional[Dict] = None
    ) -> RiskAssessment:
        """
        Perform comprehensive risk assessment.

        Args:
            decision: Trading decision to assess
            current_price: Current stock price
            portfolio_value: Total portfolio value
            existing_positions: Dictionary of existing positions

        Returns:
            RiskAssessment with recommendations and constraints
        """
        logger.info(f"Assessing risk for {decision.symbol} decision")

        existing_positions = existing_positions or {}

        # Calculate risk score
        risk_score = self._calculate_risk_score(decision)

        # Determine position size
        position_size = self._calculate_position_size(
            decision,
            risk_score,
            current_price,
            portfolio_value
        )

        # Calculate stop loss and take profit
        stop_loss, take_profit = self._calculate_stops(
            decision,
            current_price
        )

        # Calculate risk/reward ratio
        risk_reward = self._calculate_risk_reward(
            current_price,
            stop_loss,
            take_profit
        ) if stop_loss and take_profit else None

        # Calculate max loss
        max_loss = self._calculate_max_loss(
            position_size,
            portfolio_value,
            current_price,
            stop_loss
        ) if stop_loss else None

        # Identify risk factors
        risk_factors = self._identify_risk_factors(
            decision,
            risk_score,
            existing_positions
        )

        # Apply risk constraints
        approved, rejection_reasons = self._apply_constraints(
            decision,
            risk_score,
            position_size,
            risk_reward,
            existing_positions
        )

        assessment = RiskAssessment(
            symbol=decision.symbol,
            decision=decision,
            risk_score=risk_score,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=risk_reward,
            max_loss_amount=max_loss,
            risk_factors=risk_factors,
            risk_approved=approved,
            rejection_reasons=rejection_reasons
        )

        logger.info(
            f"Risk assessment complete: "
            f"score={risk_score:.1f}, "
            f"size={position_size:.1%}, "
            f"approved={approved}"
        )

        return assessment

    def _calculate_risk_score(self, decision: FinalDecision) -> float:
        """
        Calculate overall risk score (0-100).

        Higher score = higher risk

        Args:
            decision: Trading decision

        Returns:
            Risk score
        """
        risk_score = 50.0  # Base score

        # Adjust for confidence (low confidence = higher risk)
        confidence_factor = (1.0 - decision.confidence) * 30
        risk_score += confidence_factor

        # Adjust for action type (SELL slightly riskier than BUY in bull market)
        if decision.recommendation == "SELL":
            risk_score += 5
        elif decision.recommendation == "HOLD":
            risk_score -= 10

        # Adjust for evidence quality
        evidence_count = sum(len(ev) for ev in decision.evidence.values())
        if evidence_count < 3:
            risk_score += 15
        elif evidence_count > 10:
            risk_score -= 10

        # Adjust for identified risks
        risk_score += len(decision.risks) * 5

        # Clamp to 0-100
        return max(0.0, min(100.0, risk_score))

    def _calculate_position_size(
        self,
        decision: FinalDecision,
        risk_score: float,
        current_price: float,
        portfolio_value: float
    ) -> float:
        """
        Calculate recommended position size.

        Args:
            decision: Trading decision
            risk_score: Calculated risk score
            current_price: Current price
            portfolio_value: Portfolio value

        Returns:
            Position size as fraction of portfolio
        """
        # Start with max position size
        size = self.max_position_size

        # Scale by confidence
        size *= decision.confidence

        # Scale by risk score (inverse relationship)
        risk_factor = 1.0 - (risk_score / 200.0)  # 0 risk = 1.0, 100 risk = 0.5
        size *= risk_factor

        # Ensure minimum sensible size
        min_size = 0.01  # 1% minimum
        size = max(min_size, min(size, self.max_position_size))

        return size

    def _calculate_stops(
        self,
        decision: FinalDecision,
        current_price: float
    ) -> tuple[Optional[float], Optional[float]]:
        """
        Calculate stop loss and take profit levels.

        Args:
            decision: Trading decision
            current_price: Current price

        Returns:
            Tuple of (stop_loss, take_profit)
        """
        if decision.recommendation == "HOLD":
            return None, None

        # Stop loss calculation
        if decision.recommendation == "BUY":
            # Stop loss below current price
            stop_distance = current_price * 0.05  # 5% stop by default
            # Tighter stop if high conviction
            if decision.confidence > 0.8:
                stop_distance = current_price * 0.03  # 3% stop
            # Wider stop if low conviction
            elif decision.confidence < 0.6:
                stop_distance = current_price * 0.08  # 8% stop

            stop_loss = current_price - stop_distance

            # Take profit (aim for at least 2:1 risk/reward)
            take_profit = current_price + (stop_distance * self.min_risk_reward)

        else:  # SELL
            # Stop loss above current price
            stop_distance = current_price * 0.05
            if decision.confidence > 0.8:
                stop_distance = current_price * 0.03
            elif decision.confidence < 0.6:
                stop_distance = current_price * 0.08

            stop_loss = current_price + stop_distance
            take_profit = current_price - (stop_distance * self.min_risk_reward)

        return stop_loss, take_profit

    def _calculate_risk_reward(
        self,
        current_price: float,
        stop_loss: float,
        take_profit: float
    ) -> float:
        """Calculate risk/reward ratio."""
        risk = abs(current_price - stop_loss)
        reward = abs(take_profit - current_price)

        if risk == 0:
            return 0.0

        return reward / risk

    def _calculate_max_loss(
        self,
        position_size: float,
        portfolio_value: float,
        current_price: float,
        stop_loss: float
    ) -> float:
        """Calculate maximum potential loss."""
        position_value = portfolio_value * position_size
        shares = position_value / current_price
        loss_per_share = abs(current_price - stop_loss)
        return shares * loss_per_share

    def _identify_risk_factors(
        self,
        decision: FinalDecision,
        risk_score: float,
        existing_positions: Dict
    ) -> List[str]:
        """Identify specific risk factors."""
        factors = []

        if risk_score > 70:
            factors.append("High overall risk score")

        if decision.confidence < 0.6:
            factors.append("Low decision confidence")

        if len(decision.evidence) < 2:
            factors.append("Limited supporting evidence")

        if decision.symbol in existing_positions:
            factors.append("Adding to existing position (concentration risk)")

        if len(decision.risks) > 3:
            factors.append(f"Multiple identified risks ({len(decision.risks)})")

        return factors

    def _apply_constraints(
        self,
        decision: FinalDecision,
        risk_score: float,
        position_size: float,
        risk_reward: Optional[float],
        existing_positions: Dict
    ) -> tuple[bool, List[str]]:
        """
        Apply risk constraints.

        Returns:
            Tuple of (approved, rejection_reasons)
        """
        rejection_reasons = []

        # Maximum risk score constraint
        if risk_score > 85:
            rejection_reasons.append(f"Risk score too high: {risk_score:.1f}/100")

        # Minimum confidence constraint
        if decision.confidence < 0.4:
            rejection_reasons.append(f"Confidence too low: {decision.confidence:.1%}")

        # Risk/reward constraint
        if risk_reward and risk_reward < self.min_risk_reward:
            rejection_reasons.append(
                f"Risk/reward ratio below minimum: {risk_reward:.2f} < {self.min_risk_reward:.2f}"
            )

        # Position size constraint
        if position_size > self.max_position_size:
            rejection_reasons.append(
                f"Position size exceeds maximum: {position_size:.1%} > {self.max_position_size:.1%}"
            )

        approved = len(rejection_reasons) == 0

        return approved, rejection_reasons

    def apply_risk_adjustments(self, decision: FinalDecision, assessment: RiskAssessment) -> FinalDecision:
        """
        Apply risk-based adjustments to decision.

        Args:
            decision: Original decision
            assessment: Risk assessment

        Returns:
            Risk-adjusted decision
        """
        if not assessment.risk_approved:
            # Downgrade to HOLD if rejected
            logger.warning(
                f"Risk rejected for {decision.symbol}: {assessment.rejection_reasons}"
            )
            decision.recommendation = "HOLD"
            decision.confidence = 0.5
            decision.risks.extend(assessment.rejection_reasons)

        # Add risk factors to decision
        decision.risks.extend(assessment.risk_factors)

        # Add position sizing recommendation to key factors
        decision.key_factors.append(
            f"Recommended position size: {assessment.position_size:.1%} of portfolio"
        )

        if assessment.stop_loss:
            decision.key_factors.append(
                f"Stop loss: ${assessment.stop_loss:.2f}"
            )

        if assessment.take_profit:
            decision.key_factors.append(
                f"Take profit: ${assessment.take_profit:.2f}"
            )

        if assessment.risk_reward_ratio:
            decision.key_factors.append(
                f"Risk/Reward: {assessment.risk_reward_ratio:.2f}:1"
            )

        return decision
