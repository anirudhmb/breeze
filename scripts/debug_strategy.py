#!/usr/bin/env python3
"""
Debug Script for MA+RSI Strategy

This script helps identify why "No data returned from API" error occurs.
Run this before running the main strategy to diagnose issues.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from breeze_client import BreezeTrader


def debug_connection():
    """Test 1: Check if BreezeTrader can connect."""
    print("=" * 70)
    print("  DEBUG TEST 1: Connection")
    print("=" * 70)
    
    try:
        trader = BreezeTrader()
        print("✓ BreezeTrader initialized successfully")
        return trader
    except Exception as e:
        print(f"✗ Failed to initialize BreezeTrader: {e}")
        print("\n💡 Solution:")
        print("  1. Make sure you have config.yaml or .env with credentials")
        print("  2. Run: python scripts/login.py (required daily)")
        return None


def debug_api_call(trader, stock="RELIANCE", exchange="NSE"):
    """Test 2: Try to fetch historical data with detailed error reporting."""
    print("\n" + "=" * 70)
    print(f"  DEBUG TEST 2: Fetching Data for {stock}")
    print("=" * 70)
    
    to_date = datetime.now()
    from_date = to_date - timedelta(days=40)
    
    print(f"\nParameters:")
    print(f"  Stock: {stock}")
    print(f"  Exchange: {exchange}")
    print(f"  Interval: 1day")
    print(f"  From: {from_date.strftime('%Y-%m-%d')}")
    print(f"  To: {to_date.strftime('%Y-%m-%d')}")
    
    try:
        print(f"\nCalling API...")
        data = trader.get_historical_data(
            stock=stock,
            interval="1day",
            from_date=from_date.strftime("%Y-%m-%d"),
            to_date=to_date.strftime("%Y-%m-%d"),
            exchange_code=exchange
        )
        
        if data and len(data) > 0:
            print(f"✓ SUCCESS! Received {len(data)} data points")
            print(f"\nSample data (first record):")
            print(f"  {data[0]}")
            return True
        else:
            print(f"✗ API returned empty data")
            print(f"\n💡 Possible causes:")
            print(f"  1. Stock symbol '{stock}' might be incorrect")
            print(f"  2. No trading data for this date range (market closed?)")
            print(f"  3. Exchange '{exchange}' might be wrong")
            return False
            
    except Exception as e:
        print(f"✗ API call failed with error:")
        print(f"  {type(e).__name__}: {e}")
        print(f"\n💡 Common causes:")
        print(f"  1. Session expired - run: python scripts/login.py")
        print(f"  2. Invalid stock symbol")
        print(f"  3. Wrong exchange code")
        print(f"  4. Network/API issues")
        return False


def debug_multiple_stocks():
    """Test 3: Try multiple stock symbols to identify valid ones."""
    print("\n" + "=" * 70)
    print("  DEBUG TEST 3: Testing Multiple Stocks")
    print("=" * 70)
    
    try:
        trader = BreezeTrader()
    except Exception as e:
        print(f"✗ Cannot initialize trader: {e}")
        return
    
    test_stocks = [
        ("RELIANCE", "NSE"),
        ("TCS", "NSE"),
        ("INFY", "NSE"),
        ("SBIN", "NSE"),
        ("NIFTY", "NSE"),
    ]
    
    to_date = datetime.now()
    from_date = to_date - timedelta(days=10)
    
    print(f"\nTesting stocks with recent 10 days data...")
    print(f"From: {from_date.strftime('%Y-%m-%d')} To: {to_date.strftime('%Y-%m-%d')}")
    print()
    
    working_stocks = []
    
    for stock, exchange in test_stocks:
        try:
            data = trader.get_historical_data(
                stock=stock,
                interval="1day",
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d"),
                exchange_code=exchange
            )
            
            if data and len(data) > 0:
                print(f"  ✓ {stock:10s} - {len(data)} days")
                working_stocks.append((stock, exchange))
            else:
                print(f"  ✗ {stock:10s} - No data")
                
        except Exception as e:
            print(f"  ✗ {stock:10s} - Error: {e}")
    
    if working_stocks:
        print(f"\n✓ Working stocks: {', '.join([s[0] for s in working_stocks])}")
        print(f"\n💡 Update strategy_config.yaml with these stocks")
    else:
        print(f"\n✗ No stocks returned data")
        print(f"\n💡 Check:")
        print(f"  1. Run: python scripts/login.py")
        print(f"  2. Verify your API credentials")
        print(f"  3. Check market is open/recent trading days")


def debug_date_range():
    """Test 4: Test different date ranges."""
    print("\n" + "=" * 70)
    print("  DEBUG TEST 4: Testing Date Ranges")
    print("=" * 70)
    
    try:
        trader = BreezeTrader()
    except Exception as e:
        print(f"✗ Cannot initialize trader: {e}")
        return
    
    stock = "RELIANCE"
    exchange = "NSE"
    
    # Test different date ranges
    date_ranges = [
        ("Last 5 days", 5),
        ("Last 10 days", 10),
        ("Last 30 days", 30),
        ("Last 60 days", 60),
    ]
    
    print(f"\nTesting {stock} with different date ranges...")
    print()
    
    for label, days in date_ranges:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days + 5)  # Extra buffer
        
        try:
            data = trader.get_historical_data(
                stock=stock,
                interval="1day",
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d"),
                exchange_code=exchange
            )
            
            if data and len(data) > 0:
                print(f"  ✓ {label:15s} - {len(data)} days received")
            else:
                print(f"  ✗ {label:15s} - No data")
                
        except Exception as e:
            print(f"  ✗ {label:15s} - Error: {e}")


def main():
    """Run all debug tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  MA+RSI Strategy Debug Tool".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # Test 1: Connection
    trader = debug_connection()
    if not trader:
        print("\n⚠️  Fix connection issues before proceeding")
        return
    
    # Test 2: Single stock API call
    success = debug_api_call(trader, "RELIANCE", "NSE")
    
    if not success:
        # Test 3: Try multiple stocks
        debug_multiple_stocks()
        
        # Test 4: Try different date ranges
        debug_date_range()
    
    print("\n" + "=" * 70)
    print("  Debug Complete")
    print("=" * 70)
    print("\n💡 Next Steps:")
    print("  1. If session expired: python scripts/login.py")
    print("  2. If stock symbols wrong: update strategy_config.yaml")
    print("  3. If dates wrong: adjust days_to_fetch in config")
    print("  4. Run strategy: python scripts/examples/ma_rsi_strategy.py")
    print()


if __name__ == "__main__":
    main()

