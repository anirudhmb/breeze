#!/usr/bin/env python3
"""
Example: View Portfolio & Positions

This example shows how to view your holdings and open positions.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from breeze_client import BreezeTrader

def format_currency(value):
    """Format currency value."""
    try:
        return f"₹{float(value):,.2f}"
    except:
        return value

def main():
    """View portfolio and positions."""
    # Initialize trader
    trader = BreezeTrader()
    
    print("=" * 60)
    print("  Portfolio & Positions")
    print("=" * 60)
    print()
    
    # View portfolio holdings
    print("📊 Portfolio Holdings")
    print("-" * 60)
    try:
        holdings = trader.get_portfolio()
        
        if holdings:
            print(f"Total holdings: {len(holdings)}")
            print()
            
            for holding in holdings[:10]:  # Show first 10
                stock = holding.get('stock_code', 'N/A')
                quantity = holding.get('quantity', '0')
                avg_price = holding.get('average_price', '0')
                current_price = holding.get('market_value', '0')
                
                print(f"• {stock}")
                print(f"  Quantity: {quantity}")
                print(f"  Avg Price: {format_currency(avg_price)}")
                print(f"  Current: {format_currency(current_price)}")
                print()
        else:
            print("No holdings found.")
            
    except Exception as e:
        print(f"❌ Error fetching portfolio: {e}")
    print()
    
    # View open positions
    print("📈 Open Positions")
    print("-" * 60)
    try:
        positions = trader.get_positions()
        
        if positions:
            print(f"Total positions: {len(positions)}")
            print()
            
            for position in positions[:10]:  # Show first 10
                stock = position.get('stock_code', 'N/A')
                quantity = position.get('quantity', '0')
                buy_avg = position.get('average_buy_price', '0')
                sell_avg = position.get('average_sell_price', '0')
                pnl = position.get('profit_loss', '0')
                
                print(f"• {stock}")
                print(f"  Quantity: {quantity}")
                print(f"  Buy Avg: {format_currency(buy_avg)}")
                print(f"  Sell Avg: {format_currency(sell_avg)}")
                print(f"  P&L: {format_currency(pnl)}")
                print()
        else:
            print("No open positions.")
            
    except Exception as e:
        print(f"❌ Error fetching positions: {e}")
    print()
    
    # View funds
    print("💰 Available Funds")
    print("-" * 60)
    try:
        funds = trader.get_funds()
        
        if funds and funds.get('Success'):
            fund_data = funds['Success']
            
            available = fund_data.get('available_margin', '0')
            used = fund_data.get('used_margin', '0')
            
            print(f"Available Margin: {format_currency(available)}")
            print(f"Used Margin: {format_currency(used)}")
        else:
            print("Could not fetch fund details.")
            
    except Exception as e:
        print(f"❌ Error fetching funds: {e}")
    print()
    
    print("=" * 60)


if __name__ == "__main__":
    main()

