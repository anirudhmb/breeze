"""
Breeze Trading Client - Utility Functions

Helper functions for parameter handling, logging, validation, etc.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional


# Parameter aliases mapping
# Maps trader-friendly names to SDK parameter names
PARAMETER_ALIASES = {
    # Order parameters
    'type': 'order_type',
    'exchange': 'exchange_code',
    'qty': 'quantity',
    'product_type': 'product',
    'stop_loss': 'stoploss',
    'sl': 'stoploss',
    'disclosed_qty': 'disclosed_quantity',
    
    # Time validity
    'valid_till': 'validity',
    
    # Options parameters
    'expiry': 'expiry_date',
    'strike': 'strike_price',
    'option_type': 'right',
    
    # GTT parameters
    'trigger': 'trigger_price',
    'limit': 'limit_price',
}


def resolve_parameter_aliases(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert parameter aliases to SDK parameter names.
    
    Allows users to use trader-friendly parameter names like 'type' 
    instead of 'order_type'.
    
    Args:
        kwargs: Dictionary of parameters with potential aliases
        
    Returns:
        Dictionary with aliases resolved to SDK names
        
    Examples:
        >>> resolve_parameter_aliases({'type': 'limit', 'qty': 10})
        {'order_type': 'limit', 'quantity': 10}
    """
    resolved = {}
    
    for key, value in kwargs.items():
        # Use alias if it exists, otherwise keep original key
        resolved_key = PARAMETER_ALIASES.get(key, key)
        resolved[resolved_key] = value
    
    return resolved


def setup_logging(
    level: str = 'INFO',
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        log_format: Optional custom log format
        date_format: Optional custom date format
        
    Returns:
        Configured logger instance
    """
    if log_format is None:
        log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    
    if date_format is None:
        date_format = '%Y-%m-%d %H:%M:%S'
    
    # Get or create logger
    logger = logging.getLogger('breeze_client')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def format_currency(amount: float, currency: str = '₹') -> str:
    """
    Format currency amount with proper symbols.
    
    Args:
        amount: Amount to format
        currency: Currency symbol (default: ₹)
        
    Returns:
        Formatted currency string
        
    Examples:
        >>> format_currency(1234.56)
        '₹1,234.56'
    """
    return f"{currency}{amount:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format percentage value.
    
    Args:
        value: Percentage value (e.g., 5.5 for 5.5%)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
        
    Examples:
        >>> format_percentage(5.5)
        '5.50%'
    """
    return f"{value:.{decimals}f}%"


def validate_stock_code(stock_code: str) -> bool:
    """
    Basic validation of stock code format.
    
    Args:
        stock_code: Stock symbol to validate
        
    Returns:
        True if format looks valid, False otherwise
        
    Note:
        This is basic format validation only. Use SDK for actual validation.
    """
    if not stock_code or not isinstance(stock_code, str):
        return False
    
    # Basic checks: alphanumeric, reasonable length
    stock_code = stock_code.strip().upper()
    
    if len(stock_code) < 1 or len(stock_code) > 20:
        return False
    
    # Allow letters, numbers, and some special chars (&, -)
    if not all(c.isalnum() or c in '&-' for c in stock_code):
        return False
    
    return True


def validate_quantity(quantity: int) -> bool:
    """
    Validate order quantity.
    
    Args:
        quantity: Order quantity
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(quantity, int):
        return False
    
    if quantity <= 0:
        return False
    
    if quantity > 1000000:  # Reasonable upper limit
        return False
    
    return True


def validate_price(price: float, allow_zero: bool = True) -> bool:
    """
    Validate price value.
    
    Args:
        price: Price to validate
        allow_zero: Whether to allow zero price (for market orders)
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(price, (int, float)):
        return False
    
    if not allow_zero and price <= 0:
        return False
    
    if allow_zero and price < 0:
        return False
    
    if price > 1000000:  # Reasonable upper limit
        return False
    
    return True


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries, with later dicts overriding earlier ones.
    
    Args:
        *dicts: Variable number of dictionaries to merge
        
    Returns:
        Merged dictionary
        
    Examples:
        >>> merge_dicts({'a': 1}, {'b': 2}, {'a': 3})
        {'a': 3, 'b': 2}
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def format_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format datetime object to string.
    
    Args:
        dt: Datetime object
        format_str: Format string
        
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)


def parse_iso_datetime(dt_str: str) -> datetime:
    """
    Parse ISO 8601 datetime string.
    
    Args:
        dt_str: ISO 8601 datetime string
        
    Returns:
        Datetime object
        
    Examples:
        >>> parse_iso_datetime('2025-10-25T09:15:00.000Z')
        datetime.datetime(2025, 10, 25, 9, 15, tzinfo=timezone.utc)
    """
    # Remove milliseconds if present
    if '.' in dt_str:
        dt_str = dt_str.split('.')[0] + 'Z'
    
    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))


def clean_response_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and format SDK response data for easier consumption.
    
    Args:
        data: Raw SDK response
        
    Returns:
        Cleaned response data
    """
    # Remove None values
    cleaned = {k: v for k, v in data.items() if v is not None}
    
    # Convert empty strings to None
    for key, value in cleaned.items():
        if value == '':
            cleaned[key] = None
    
    return cleaned


def get_market_hours(exchange: str = 'NSE') -> Dict[str, str]:
    """
    Get market hours for a given exchange.
    
    Args:
        exchange: Exchange code (NSE, BSE, NFO, MCX, etc.)
        
    Returns:
        Dictionary with 'open' and 'close' times
    """
    market_hours = {
        'NSE': {'open': '09:15', 'close': '15:30'},
        'BSE': {'open': '09:15', 'close': '15:30'},
        'NFO': {'open': '09:15', 'close': '15:30'},
        'MCX': {'open': '09:00', 'close': '23:30'},
        'NDX': {'open': '09:00', 'close': '17:00'},
    }
    
    return market_hours.get(exchange.upper(), {'open': '09:15', 'close': '15:30'})


def is_market_open(exchange: str = 'NSE') -> bool:
    """
    Check if market is currently open.
    
    Note: This is a basic check. For accurate info, query the API.
    
    Args:
        exchange: Exchange code
        
    Returns:
        True if market should be open, False otherwise
    """
    now = datetime.now()
    
    # Check if weekend
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Get market hours
    hours = get_market_hours(exchange)
    open_time = datetime.strptime(hours['open'], '%H:%M').time()
    close_time = datetime.strptime(hours['close'], '%H:%M').time()
    
    current_time = now.time()
    
    return open_time <= current_time <= close_time


def truncate_string(s: str, max_length: int = 50) -> str:
    """
    Truncate string to maximum length.
    
    Args:
        s: String to truncate
        max_length: Maximum length
        
    Returns:
        Truncated string with '...' if needed
    """
    if len(s) <= max_length:
        return s
    return s[:max_length-3] + '...'

