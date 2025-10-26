#!/usr/bin/env python3
"""
Example: Options Trading

This example shows how to trade options contracts.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from breeze_client import BreezeTrader

def main():
    """Trade options."""
    # Initialize trader
    trader = BreezeTrader()
    
    print("=" * 60)
    print("  Options Trading Examples")
    print("=" * 60)
    print()
    
    # Example 1: Buy call option
    print("1. Buy NIFTY Call Option")
    print("-" * 60)
    try:
        response = trader.buy(
            stock="NIFTY",
            quantity=50,  # Lot size
            exchange_code="NFO",
            product="options",
            order_type="limit",
            price=150.50,
            expiry_date="2024-10-31T06:00:00.000Z",
            right="call",
            strike_price="22000"
        )
        
        if response.get('Success'):
            order_id = response['Success'].get('order_id')
            print(f"✅ Call option buy order placed!")
            print(f"   Order ID: {order_id}")
            print(f"   Strike: 22000 CE")
            print(f"   Price: ₹150.50")
        else:
            print(f"❌ Order failed: {response}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Example 2: Sell put option
    print("2. Sell NIFTY Put Option")
    print("-" * 60)
    try:
        response = trader.sell(
            stock="NIFTY",
            quantity=50,
            exchange_code="NFO",
            product="options",
            order_type="limit",
            price=120.00,
            expiry_date="2024-10-31T06:00:00.000Z",
            right="put",
            strike_price="21800"
        )
        
        if response.get('Success'):
            order_id = response['Success'].get('order_id')
            print(f"✅ Put option sell order placed!")
            print(f"   Order ID: {order_id}")
            print(f"   Strike: 21800 PE")
            print(f"   Price: ₹120.00")
        else:
            print(f"❌ Order failed: {response}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Example 3: Option spread (Iron Condor)
    print("3. Iron Condor Spread")
    print("-" * 60)
    print("Placing 4-leg option strategy...")
    
    try:
        expiry = "2024-10-31T06:00:00.000Z"
        
        # Leg 1: Buy OTM Put
        print("   Leg 1: Buy 21700 PE")
        trader.buy(
            "NIFTY", 50, exchange_code="NFO", product="options",
            order_type="limit", price=50.00,
            expiry_date=expiry, right="put", strike_price="21700"
        )
        
        # Leg 2: Sell ATM Put
        print("   Leg 2: Sell 21800 PE")
        trader.sell(
            "NIFTY", 50, exchange_code="NFO", product="options",
            order_type="limit", price=120.00,
            expiry_date=expiry, right="put", strike_price="21800"
        )
        
        # Leg 3: Sell ATM Call
        print("   Leg 3: Sell 22200 CE")
        trader.sell(
            "NIFTY", 50, exchange_code="NFO", product="options",
            order_type="limit", price=125.00,
            expiry_date=expiry, right="call", strike_price="22200"
        )
        
        # Leg 4: Buy OTM Call
        print("   Leg 4: Buy 22300 CE")
        trader.buy(
            "NIFTY", 50, exchange_code="NFO", product="options",
            order_type="limit", price=45.00,
            expiry_date=expiry, right="call", strike_price="22300"
        )
        
        print()
        print("✅ Iron Condor spread orders placed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    print("=" * 60)
    print("Tip: Use trader.get_option_chain() to view all strikes")
    print("=" * 60)


if __name__ == "__main__":
    main()

