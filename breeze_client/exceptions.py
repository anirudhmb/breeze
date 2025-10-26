"""
Breeze Trading Client - Custom Exceptions

User-friendly exceptions that translate technical errors into plain English.
"""


class BreezeTraderError(Exception):
    """Base exception for all Breeze Trading Client errors."""
    
    def __init__(self, message: str, original_error: Exception = None):
        """
        Initialize exception with message and optional original error.
        
        Args:
            message: User-friendly error message
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.original_error = original_error
    
    def __str__(self):
        return self.message


class ConfigurationError(BreezeTraderError):
    """Configuration file or environment variable issues."""
    
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(f"❌ Configuration Error: {message}", original_error)


class SessionExpiredError(BreezeTraderError):
    """Session token has expired."""
    
    def __init__(self, message: str = None):
        if message is None:
            message = (
                "Session expired! Please run: python scripts/login.py\n"
                "Session tokens are valid for 24 hours or until midnight."
            )
        super().__init__(f"❌ {message}")


class SessionNotFoundError(BreezeTraderError):
    """Session token file not found."""
    
    def __init__(self):
        message = (
            "No active session found! Please run: python scripts/login.py\n"
            "You need to login once per day to generate a session token."
        )
        super().__init__(f"❌ {message}")


class OrderValidationError(BreezeTraderError):
    """Order parameter validation failed."""
    
    def __init__(self, message: str):
        super().__init__(f"❌ Order Validation Error: {message}")


class InsufficientFundsError(BreezeTraderError):
    """Not enough funds to place the order."""
    
    def __init__(self, message: str = None):
        if message is None:
            message = "Insufficient funds for this order. Please check your account balance."
        super().__init__(f"❌ {message}")


class MarketClosedError(BreezeTraderError):
    """Market is currently closed."""
    
    def __init__(self, message: str = None):
        if message is None:
            message = (
                "Market is closed. Trading hours:\n"
                "  Equity: 9:15 AM - 3:30 PM (Mon-Fri)\n"
                "  F&O: 9:15 AM - 3:30 PM (Mon-Fri)"
            )
        super().__init__(f"❌ {message}")


class RateLimitError(BreezeTraderError):
    """API rate limit exceeded."""
    
    def __init__(self, message: str = None):
        if message is None:
            message = (
                "API rate limit exceeded!\n"
                "Limits: 100 calls/minute, 5000 calls/day\n"
                "Please wait a moment before trying again."
            )
        super().__init__(f"❌ {message}")


class AuthenticationError(BreezeTraderError):
    """Authentication with API failed."""
    
    def __init__(self, message: str = None):
        if message is None:
            message = (
                "Authentication failed! Please check:\n"
                "  1. API key and secret key are correct in config.yaml\n"
                "  2. Session token is valid (run: python scripts/login.py)\n"
                "  3. Your Breeze API account is active"
            )
        super().__init__(f"❌ {message}")


class InvalidStockCodeError(BreezeTraderError):
    """Invalid or unknown stock code."""
    
    def __init__(self, stock_code: str, suggestion: str = None):
        message = f"Invalid stock code: '{stock_code}'"
        if suggestion:
            message += f"\nDid you mean '{suggestion}'?"
        super().__init__(f"❌ {message}")


class OrderNotFoundError(BreezeTraderError):
    """Order ID not found."""
    
    def __init__(self, order_id: str):
        message = f"Order not found: {order_id}"
        super().__init__(f"❌ {message}")


class NetworkError(BreezeTraderError):
    """Network connectivity issues."""
    
    def __init__(self, message: str = None):
        if message is None:
            message = (
                "Network error! Please check:\n"
                "  1. Your internet connection\n"
                "  2. ICICI Direct API status\n"
                "  3. Firewall/proxy settings"
            )
        super().__init__(f"❌ {message}")


class WebSocketError(BreezeTraderError):
    """WebSocket connection issues."""
    
    def __init__(self, message: str):
        super().__init__(f"❌ WebSocket Error: {message}")


def translate_sdk_error(error: Exception) -> BreezeTraderError:
    """
    Translate SDK errors into user-friendly exceptions.
    
    Args:
        error: Original SDK exception
        
    Returns:
        BreezeTraderError: Translated exception
    """
    error_msg = str(error).lower()
    
    # Session/Authentication errors
    if any(x in error_msg for x in ['session', 'token', 'expired', 'invalid session']):
        return SessionExpiredError()
    
    if any(x in error_msg for x in ['authentication', 'unauthorized', 'invalid credentials']):
        return AuthenticationError()
    
    # Order-related errors
    if 'insufficient funds' in error_msg or 'insufficient balance' in error_msg:
        return InsufficientFundsError()
    
    if 'market closed' in error_msg or 'market is closed' in error_msg:
        return MarketClosedError()
    
    if 'invalid stock' in error_msg or 'invalid symbol' in error_msg:
        return InvalidStockCodeError("Unknown")
    
    if 'order not found' in error_msg:
        return OrderNotFoundError("Unknown")
    
    # Rate limiting
    if 'rate limit' in error_msg or 'too many requests' in error_msg:
        return RateLimitError()
    
    # Network errors
    if any(x in error_msg for x in ['connection', 'timeout', 'network']):
        return NetworkError(str(error))
    
    # Default: wrap in base exception
    return BreezeTraderError(f"API Error: {str(error)}", error)

