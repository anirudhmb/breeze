"""
Tests for utility functions
"""

import pytest
from datetime import datetime
from breeze_client.utils import (
    resolve_parameter_aliases,
    format_currency,
    format_percentage,
    validate_stock_code,
    validate_quantity,
    validate_price,
    merge_dicts,
    format_datetime,
    clean_response_data,
    get_market_hours,
    truncate_string,
)


def test_resolve_parameter_aliases():
    """Test parameter alias resolution."""
    params = {
        'type': 'limit',
        'qty': 10,
        'exchange': 'NSE',
        'stop_loss': 100,
    }
    
    resolved = resolve_parameter_aliases(params)
    
    assert resolved['order_type'] == 'limit'
    assert resolved['quantity'] == 10
    assert resolved['exchange_code'] == 'NSE'
    assert resolved['stoploss'] == 100


def test_resolve_parameter_aliases_no_aliases():
    """Test parameter resolution when no aliases present."""
    params = {
        'order_type': 'market',
        'quantity': 5,
    }
    
    resolved = resolve_parameter_aliases(params)
    
    assert resolved['order_type'] == 'market'
    assert resolved['quantity'] == 5


def test_format_currency():
    """Test currency formatting."""
    assert format_currency(1234.56) == '₹1,234.56'
    assert format_currency(1000000) == '₹1,000,000.00'
    assert format_currency(99.9) == '₹99.90'


def test_format_currency_custom_symbol():
    """Test currency formatting with custom symbol."""
    assert format_currency(1234.56, '$') == '$1,234.56'


def test_format_percentage():
    """Test percentage formatting."""
    assert format_percentage(5.5) == '5.50%'
    assert format_percentage(12.345, 1) == '12.3%'
    assert format_percentage(-3.75) == '-3.75%'


def test_validate_stock_code_valid():
    """Test stock code validation with valid codes."""
    assert validate_stock_code('RELIANCE') is True
    assert validate_stock_code('TCS') is True
    assert validate_stock_code('M&M') is True
    assert validate_stock_code('NIFTY-50') is True


def test_validate_stock_code_invalid():
    """Test stock code validation with invalid codes."""
    assert validate_stock_code('') is False
    assert validate_stock_code('   ') is False
    assert validate_stock_code('A' * 25) is False  # Too long
    assert validate_stock_code('STOCK@123') is False  # Invalid char
    assert validate_stock_code(None) is False
    assert validate_stock_code(123) is False


def test_validate_quantity_valid():
    """Test quantity validation with valid values."""
    assert validate_quantity(1) is True
    assert validate_quantity(100) is True
    assert validate_quantity(1000) is True


def test_validate_quantity_invalid():
    """Test quantity validation with invalid values."""
    assert validate_quantity(0) is False
    assert validate_quantity(-10) is False
    assert validate_quantity(1000001) is False
    assert validate_quantity(10.5) is False  # Not an integer
    assert validate_quantity('10') is False  # Not an integer


def test_validate_price_valid():
    """Test price validation with valid values."""
    assert validate_price(100.50) is True
    assert validate_price(0, allow_zero=True) is True
    assert validate_price(1000) is True


def test_validate_price_invalid():
    """Test price validation with invalid values."""
    assert validate_price(-10) is False
    assert validate_price(0, allow_zero=False) is False
    assert validate_price(1000001) is False
    assert validate_price('100') is False  # Not a number


def test_merge_dicts():
    """Test dictionary merging."""
    dict1 = {'a': 1, 'b': 2}
    dict2 = {'b': 3, 'c': 4}
    dict3 = {'a': 5, 'd': 6}
    
    result = merge_dicts(dict1, dict2, dict3)
    
    assert result == {'a': 5, 'b': 3, 'c': 4, 'd': 6}


def test_merge_dicts_with_none():
    """Test dictionary merging with None values."""
    dict1 = {'a': 1}
    dict2 = None
    dict3 = {'b': 2}
    
    result = merge_dicts(dict1, dict2, dict3)
    
    assert result == {'a': 1, 'b': 2}


def test_format_datetime():
    """Test datetime formatting."""
    dt = datetime(2025, 10, 25, 14, 30, 45)
    assert format_datetime(dt) == '2025-10-25 14:30:45'
    assert format_datetime(dt, '%Y-%m-%d') == '2025-10-25'


def test_clean_response_data():
    """Test cleaning response data."""
    data = {
        'order_id': '12345',
        'status': 'complete',
        'quantity': 10,
        'price': None,
        'remarks': '',
    }
    
    cleaned = clean_response_data(data)
    
    assert 'order_id' in cleaned
    assert 'status' in cleaned
    assert 'quantity' in cleaned
    assert 'price' not in cleaned  # None removed
    assert cleaned['remarks'] is None  # Empty string converted to None


def test_get_market_hours():
    """Test getting market hours."""
    nse_hours = get_market_hours('NSE')
    assert nse_hours['open'] == '09:15'
    assert nse_hours['close'] == '15:30'
    
    mcx_hours = get_market_hours('MCX')
    assert mcx_hours['open'] == '09:00'
    assert mcx_hours['close'] == '23:30'


def test_get_market_hours_unknown_exchange():
    """Test getting market hours for unknown exchange."""
    hours = get_market_hours('UNKNOWN')
    assert 'open' in hours
    assert 'close' in hours


def test_truncate_string():
    """Test string truncation."""
    assert truncate_string('Hello World', 20) == 'Hello World'
    assert truncate_string('This is a very long string', 10) == 'This is...'
    assert truncate_string('Short', 10) == 'Short'

