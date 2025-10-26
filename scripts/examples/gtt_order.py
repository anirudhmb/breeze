#!/usr/bin/env python3
"""
Example: GTT (Good Till Triggered) Orders

This example shows how to place GTT orders for target and stop-loss.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from breeze_client import BreezeTrader

def main():
    """Place GTT orders."""
    # Initialize trader
    trader = BreezeTrader()
    
    print("=" * 60)
    print("  GTT Order Examples")
    print("=" * 60)
    print()
    
    # Example 1: Simple GTT order (single trigger)
    print("1. Simple GTT Order (Target)")
    print("-" * 60)
    print("Place a buy order when price reaches ₹800")
    try:
        response = trader.place_gtt(
            stock="TATAMOTORS",
            quantity=50,
            action="buy",
            trigger_price="800",
            limit_price="805",
            gtt_type="single"
        )
        
        if response.get('Success'):
            gtt_id = response['Success'].get('gtt_order_id')
            print(f"✅ GTT order placed successfully!")
            print(f"   GTT Order ID: {gtt_id}")
            print(f"   Trigger: ₹800")
            print(f"   Limit: ₹805")
        else:
            print(f"❌ GTT order failed: {response}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Example 2: OCO GTT order (target + stop-loss)
    print("2. OCO GTT Order (Target + Stop Loss)")
    print("-" * 60)
    print("Set both target and stop-loss for a position")
    try:
        response = trader.place_gtt(
            stock="TATAMOTORS",
            quantity=50,
            exchange_code="NFO",
            product="futures",
            gtt_type="cover_oco",
            order_details=[
                {
                    'gtt_leg_type': 'target',
                    'action': 'sell',
                    'limit_price': '75',
                    'trigger_price': '72'
                },
                {
                    'gtt_leg_type': 'stoploss',
                    'action': 'sell',
                    'limit_price': '18',
                    'trigger_price': '22'
                }
            ]
        )
        
        if response.get('Success'):
            gtt_id = response['Success'].get('gtt_order_id')
            print(f"✅ OCO GTT order placed successfully!")
            print(f"   GTT Order ID: {gtt_id}")
            print(f"   Target: Sell at ₹72 (limit ₹75)")
            print(f"   Stop Loss: Sell at ₹22 (limit ₹18)")
        else:
            print(f"❌ GTT order failed: {response}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Example 3: View GTT orders
    print("3. View GTT Order Book")
    print("-" * 60)
    try:
        gtt_orders = trader.get_gtt_orders()
        
        if gtt_orders and gtt_orders.get('Success'):
            orders = gtt_orders['Success']
            print(f"Total GTT orders: {len(orders) if isinstance(orders, list) else 1}")
            print()
            
            if isinstance(orders, list):
                for order in orders[:5]:  # Show first 5
                    print(f"• GTT Order ID: {order.get('gtt_order_id')}")
                    print(f"  Stock: {order.get('stock_code')}")
                    print(f"  Status: {order.get('status')}")
                    print()
        else:
            print("No GTT orders found.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    print("=" * 60)
    print("Note: GTT orders remain active until triggered or cancelled")
    print("=" * 60)


if __name__ == "__main__":
    main()

