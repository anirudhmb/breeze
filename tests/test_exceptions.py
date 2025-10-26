"""
Tests for Breeze Trading Client exceptions
"""

import pytest
from breeze_client.exceptions import (
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
    translate_sdk_error,
)


def test_base_exception():
    """Test base exception."""
    error = BreezeTraderError("Test error")
    assert str(error) == "Test error"
    assert error.message == "Test error"
    assert error.original_error is None


def test_base_exception_with_original():
    """Test base exception with original error."""
    original = ValueError("Original error")
    error = BreezeTraderError("Test error", original)
    assert error.original_error is original


def test_configuration_error():
    """Test configuration error."""
    error = ConfigurationError("Missing API key")
    assert "Configuration Error" in str(error)
    assert "Missing API key" in str(error)


def test_session_expired_error():
    """Test session expired error."""
    error = SessionExpiredError()
    assert "Session expired" in str(error)
    assert "login.py" in str(error)


def test_session_not_found_error():
    """Test session not found error."""
    error = SessionNotFoundError()
    assert "No active session" in str(error)
    assert "login.py" in str(error)


def test_order_validation_error():
    """Test order validation error."""
    error = OrderValidationError("Invalid quantity")
    assert "Order Validation Error" in str(error)
    assert "Invalid quantity" in str(error)


def test_insufficient_funds_error():
    """Test insufficient funds error."""
    error = InsufficientFundsError()
    assert "Insufficient funds" in str(error)


def test_market_closed_error():
    """Test market closed error."""
    error = MarketClosedError()
    assert "Market is closed" in str(error)
    assert "9:15 AM" in str(error)


def test_rate_limit_error():
    """Test rate limit error."""
    error = RateLimitError()
    assert "rate limit" in str(error)
    assert "100 calls/minute" in str(error)


def test_authentication_error():
    """Test authentication error."""
    error = AuthenticationError()
    assert "Authentication failed" in str(error)
    assert "API key" in str(error)


def test_invalid_stock_code_error():
    """Test invalid stock code error."""
    error = InvalidStockCodeError("XYZ")
    assert "Invalid stock code" in str(error)
    assert "XYZ" in str(error)


def test_invalid_stock_code_error_with_suggestion():
    """Test invalid stock code error with suggestion."""
    error = InvalidStockCodeError("RELIACE", "RELIANCE")
    assert "RELIACE" in str(error)
    assert "RELIANCE" in str(error)
    assert "Did you mean" in str(error)


def test_order_not_found_error():
    """Test order not found error."""
    error = OrderNotFoundError("ORDER123")
    assert "Order not found" in str(error)
    assert "ORDER123" in str(error)


def test_network_error():
    """Test network error."""
    error = NetworkError()
    assert "Network error" in str(error)
    assert "internet connection" in str(error)


def test_translate_sdk_error_session():
    """Test translating session-related SDK errors."""
    sdk_error = Exception("Invalid session token")
    translated = translate_sdk_error(sdk_error)
    assert isinstance(translated, SessionExpiredError)


def test_translate_sdk_error_authentication():
    """Test translating authentication SDK errors."""
    sdk_error = Exception("Authentication failed")
    translated = translate_sdk_error(sdk_error)
    assert isinstance(translated, AuthenticationError)


def test_translate_sdk_error_insufficient_funds():
    """Test translating insufficient funds SDK errors."""
    sdk_error = Exception("Insufficient funds")
    translated = translate_sdk_error(sdk_error)
    assert isinstance(translated, InsufficientFundsError)


def test_translate_sdk_error_market_closed():
    """Test translating market closed SDK errors."""
    sdk_error = Exception("Market is closed")
    translated = translate_sdk_error(sdk_error)
    assert isinstance(translated, MarketClosedError)


def test_translate_sdk_error_rate_limit():
    """Test translating rate limit SDK errors."""
    sdk_error = Exception("Rate limit exceeded")
    translated = translate_sdk_error(sdk_error)
    assert isinstance(translated, RateLimitError)


def test_translate_sdk_error_network():
    """Test translating network SDK errors."""
    sdk_error = Exception("Connection timeout")
    translated = translate_sdk_error(sdk_error)
    assert isinstance(translated, NetworkError)


def test_translate_sdk_error_generic():
    """Test translating generic SDK errors."""
    sdk_error = Exception("Some unknown error")
    translated = translate_sdk_error(sdk_error)
    assert isinstance(translated, BreezeTraderError)
    assert "Some unknown error" in str(translated)

