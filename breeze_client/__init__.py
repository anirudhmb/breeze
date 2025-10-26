"""
Breeze Trading Client
=====================

A trader-friendly Python wrapper for ICICI Direct's Breeze API.

Simple by default, advanced when needed, nothing hidden.

Usage:
    >>> from breeze_client import BreezeTrader
    >>> trader = BreezeTrader()
    >>> trader.buy("RELIANCE", 10)

For detailed documentation, see: docs/
"""

__version__ = "1.0.0"
__author__ = "Your Name"

# Core infrastructure (Phase 2 - Complete)
from .config_manager import ConfigManager
from .session_manager import SessionManager
from .exceptions import (
    BreezeTraderError,
    ConfigurationError,
    SessionExpiredError,
    SessionNotFoundError,
    OrderValidationError,
    InsufficientFundsError,
    MarketClosedError,
    RateLimitError,
    AuthenticationError,
    InvalidStockCodeError,
    OrderNotFoundError,
    NetworkError,
    WebSocketError,
)

# Main client class (Phases 3, 4, 5 - Complete)
from .client import BreezeTrader

__all__ = [
    # Main client
    "BreezeTrader",
    # Core infrastructure
    "ConfigManager",
    "SessionManager",
    # Exceptions
    "BreezeTraderError",
    "ConfigurationError",
    "SessionExpiredError",
    "SessionNotFoundError",
    "OrderValidationError",
    "InsufficientFundsError",
    "MarketClosedError",
    "RateLimitError",
    "AuthenticationError",
    "InvalidStockCodeError",
    "OrderNotFoundError",
    "NetworkError",
    "WebSocketError",
]

