#!/usr/bin/env python3
"""
Example: Market Data Access

This example shows how to get real-time quotes and historical data.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from breeze_client import BreezeTrader

def main():
    """Fetch market data."""
    # Initialize trader
    trader = BreezeTrader()
    
    print("=" * 60)
    print("  Market Data Examples")
    print("=" * 60)
    print()
    
    # Example 1: Get real-time quote
    print("1. Real-Time Quote")
    print("-" * 60)
    try:
        quote = trader.get_quote("RELIANCE")
        
        if quote and quote.get('Success'):
            data = quote['Success']
            print(f"Stock: RELIANCE")
            print(f"LTP: ₹{data.get('last_traded_price', 'N/A')}")
            print(f"Open: ₹{data.get('open', 'N/A')}")
            print(f"High: ₹{data.get('high', 'N/A')}")
            print(f"Low: ₹{data.get('low', 'N/A')}")
            print(f"Close: ₹{data.get('previous_close', 'N/A')}")
            print(f"Volume: {data.get('volume', 'N/A')}")
        else:
            print(f"Could not fetch quote: {quote}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Example 2: Get historical data (daily)
    print("2. Historical Data (Daily)")
    print("-" * 60)
    try:
        data = trader.get_historical_data(
            stock="NIFTY",
            interval="1day",
            from_date="2024-10-01",
            to_date="2024-10-25",
            exchange_code="NSE"
        )
        
        if data:
            print(f"Fetched {len(data)} days of data")
            print()
            print("Recent 5 days:")
            for candle in data[-5:]:
                date = candle.get('datetime', 'N/A')
                open_price = candle.get('open', 'N/A')
                close_price = candle.get('close', 'N/A')
                high = candle.get('high', 'N/A')
                low = candle.get('low', 'N/A')
                
                print(f"  {date}: O={open_price} H={high} L={low} C={close_price}")
        else:
            print("No data returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Example 3: Get historical data (intraday)
    print("3. Historical Data (5-minute intraday)")
    print("-" * 60)
    try:
        data = trader.get_historical_data(
            stock="RELIANCE",
            interval="5minute",
            from_date="2024-10-25",
            to_date="2024-10-25",
            exchange_code="NSE"
        )
        
        if data:
            print(f"Fetched {len(data)} 5-minute candles")
            print()
            print("Recent 5 candles:")
            for candle in data[-5:]:
                time = candle.get('datetime', 'N/A')
                close_price = candle.get('close', 'N/A')
                volume = candle.get('volume', 'N/A')
                
                print(f"  {time}: Close={close_price}, Volume={volume}")
        else:
            print("No data returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Example 4: Get option chain
    print("4. Option Chain Data")
    print("-" * 60)
    try:
        option_chain = trader.get_option_chain(
            stock_code="NIFTY",
            exchange_code="NFO",
            product_type="options",
            expiry_date="2024-10-31T06:00:00.000Z"
        )
        
        if option_chain and option_chain.get('Success'):
            print("✅ Option chain fetched successfully")
            print("   (Data structure varies - check API docs for details)")
        else:
            print(f"Could not fetch option chain: {option_chain}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    print("=" * 60)
    print("Tip: Historical data can be used for backtesting strategies")
    print("=" * 60)


if __name__ == "__main__":
    main()

