#!/usr/bin/env python3
"""
Example: Live Data Streaming

This example shows how to stream live market data using WebSocket.

WARNING: This is a blocking operation. Press Ctrl+C to stop.
"""

import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from breeze_client import BreezeTrader

def on_tick(tick_data):
    """
    Callback function for handling tick data.
    
    Args:
        tick_data: Dictionary containing tick information
    """
    # Extract relevant fields (structure may vary)
    stock = tick_data.get('stock', tick_data.get('symbol', 'N/A'))
    ltp = tick_data.get('ltp', tick_data.get('last_price', 'N/A'))
    volume = tick_data.get('volume', 'N/A')
    
    print(f"[{time.strftime('%H:%M:%S')}] {stock}: ₹{ltp} | Vol: {volume}")


def main():
    """Stream live market data."""
    # Initialize trader
    trader = BreezeTrader()
    
    print("=" * 60)
    print("  Live Data Streaming")
    print("=" * 60)
    print()
    print("Streaming live data for: RELIANCE, TCS, INFY")
    print("Press Ctrl+C to stop...")
    print()
    print("-" * 60)
    
    try:
        # Connect WebSocket
        trader.ws_connect()
        print("✅ WebSocket connected")
        print()
        
        # Subscribe to live feeds
        trader.subscribe_feeds(
            stocks=["RELIANCE", "TCS", "INFY"],
            on_tick=on_tick,
            interval="1second",
            exchange_code="NSE"
        )
        
        # Keep running (this is blocking)
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print()
        print("-" * 60)
        print("⏹️  Streaming stopped by user")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        # Disconnect WebSocket
        try:
            trader.ws_disconnect()
            print("✅ WebSocket disconnected")
        except:
            pass
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()

