#!/usr/bin/env python3
"""
Example: Simple Order Placement

This example shows how to place basic buy and sell orders.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from breeze_client import BreezeTrader

def main():
    """Place simple orders."""
    # Initialize trader
    trader = BreezeTrader()
    
    print("=" * 60)
    print("  Simple Order Examples")
    print("=" * 60)
    print()
    
    # Example 1: Simple market buy order
    print("1. Market Buy Order")
    print("-" * 60)
    try:
        response = trader.buy("RELIANCE", 10)
        print(f"✅ Order placed successfully!")
        if response.get('Success'):
            print(f"   Order ID: {response['Success'].get('order_id')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Example 2: Simple market sell order
    print("2. Market Sell Order")
    print("-" * 60)
    try:
        response = trader.sell("TCS", 5)
        print(f"✅ Order placed successfully!")
        if response.get('Success'):
            print(f"   Order ID: {response['Success'].get('order_id')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Example 3: Limit buy order
    print("3. Limit Buy Order")
    print("-" * 60)
    try:
        response = trader.buy(
            "INFY",
            quantity=20,
            order_type="limit",
            price=1450.50
        )
        print(f"✅ Limit order placed successfully!")
        if response.get('Success'):
            print(f"   Order ID: {response['Success'].get('order_id')}")
            print(f"   Price: ₹1450.50")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Example 4: Limit sell order with validity
    print("4. Limit Sell Order with IOC Validity")
    print("-" * 60)
    try:
        response = trader.sell(
            "WIPRO",
            quantity=15,
            order_type="limit",
            price=450.00,
            validity="IOC"  # Immediate or Cancel
        )
        print(f"✅ Limit order with IOC placed successfully!")
        if response.get('Success'):
            print(f"   Order ID: {response['Success'].get('order_id')}")
            print(f"   Price: ₹450.00")
            print(f"   Validity: IOC")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    print("=" * 60)
    print("Tip: Use trader.get_orders() to view all your orders")
    print("=" * 60)


if __name__ == "__main__":
    main()

