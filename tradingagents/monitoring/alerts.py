"""
Alert Management System

Send alerts via multiple channels (email, Slack, Discord, etc.)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from ..utils.logging import get_logger

logger = get_logger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert message."""
    level: AlertLevel
    title: str
    message: str
    details: Optional[Dict] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class AlertChannel(ABC):
    """Abstract base class for alert channels."""

    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send alert through this channel.

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully
        """
        pass


class EmailAlertChannel(AlertChannel):
    """Send alerts via email."""

    def __init__(self, smtp_config: Optional[Dict] = None):
        """Initialize email alert channel."""
        self.smtp_config = smtp_config or {}
        logger.info("Email alert channel initialized")

    async def send_alert(self, alert: Alert) -> bool:
        """Send email alert (placeholder)."""
        # In production, integrate with SMTP server
        logger.info(
            f"[EMAIL ALERT] {alert.level.value.upper()}: {alert.title} - {alert.message}"
        )
        return True


class SlackAlertChannel(AlertChannel):
    """Send alerts to Slack."""

    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize Slack alert channel."""
        self.webhook_url = webhook_url
        logger.info("Slack alert channel initialized")

    async def send_alert(self, alert: Alert) -> bool:
        """Send Slack alert (placeholder)."""
        # In production, use Slack webhook API
        logger.info(
            f"[SLACK ALERT] {alert.level.value.upper()}: {alert.title} - {alert.message}"
        )
        return True


class DiscordAlertChannel(AlertChannel):
    """Send alerts to Discord."""

    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize Discord alert channel."""
        self.webhook_url = webhook_url
        logger.info("Discord alert channel initialized")

    async def send_alert(self, alert: Alert) -> bool:
        """Send Discord alert (placeholder)."""
        # In production, use Discord webhook API
        logger.info(
            f"[DISCORD ALERT] {alert.level.value.upper()}: {alert.title} - {alert.message}"
        )
        return True


class AlertManager:
    """
    Centralized alert management.

    Manages multiple alert channels and routing logic.
    """

    def __init__(self):
        """Initialize alert manager."""
        self.channels: List[AlertChannel] = []
        logger.info("Alert manager initialized")

    def add_channel(self, channel: AlertChannel):
        """Add an alert channel."""
        self.channels.append(channel)
        logger.info(f"Added alert channel: {channel.__class__.__name__}")

    async def send_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        details: Optional[Dict] = None
    ):
        """
        Send alert to all configured channels.

        Args:
            level: Alert severity level
            title: Alert title
            message: Alert message
            details: Optional additional details
        """
        alert = Alert(
            level=level,
            title=title,
            message=message,
            details=details
        )

        logger.info(f"Sending alert: [{level.value}] {title}")

        # Send to all channels
        for channel in self.channels:
            try:
                await channel.send_alert(alert)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.__class__.__name__}: {e}")

    async def info(self, title: str, message: str, details: Optional[Dict] = None):
        """Send info-level alert."""
        await self.send_alert(AlertLevel.INFO, title, message, details)

    async def warning(self, title: str, message: str, details: Optional[Dict] = None):
        """Send warning-level alert."""
        await self.send_alert(AlertLevel.WARNING, title, message, details)

    async def error(self, title: str, message: str, details: Optional[Dict] = None):
        """Send error-level alert."""
        await self.send_alert(AlertLevel.ERROR, title, message, details)

    async def critical(self, title: str, message: str, details: Optional[Dict] = None):
        """Send critical-level alert."""
        await self.send_alert(AlertLevel.CRITICAL, title, message, details)
