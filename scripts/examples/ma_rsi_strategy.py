#!/usr/bin/env python3
"""
MA + RSI Momentum Breakout/Breakdown Strategy (Long & Short)

A config-driven momentum trading strategy that:
- LONG: Buys when RSI crosses into overbought zone during uptrends
- SHORT: Sells when RSI crosses below threshold during downtrends
- Tracks both LONG and SHORT positions independently
- Exits based on trend reversal, momentum changes, or support/resistance breaks

Entry Logic (LONG):
  - Short MA > Long MA (uptrend)
  - Previous RSI < rsi_long_entry (e.g., 70)
  - Current RSI >= rsi_long_entry (momentum breakout)

Exit Logic (LONG):
  - Short MA < Long MA (trend reversal) OR
  - Previous RSI > 50 AND Current RSI < 50 (momentum weakening) OR
  - Current Close < Long MA (support broken)

Entry Logic (SHORT):
  - Short MA < Long MA (downtrend)
  - Previous RSI > rsi_short_entry (e.g., 40)
  - Current RSI < rsi_short_entry (momentum breakdown)

Exit Logic (SHORT):
  - Short MA > Long MA (trend reversal) OR
  - Previous RSI < rsi_short_exit AND Current RSI > rsi_short_exit (momentum recovering) OR
  - Current Close > Long MA (resistance broken)

Features:
- Trial/Live mode toggle (safe testing)
- Long & Short position tracking
- Historical data caching (CSV)
- Multi-stock support
- P&L tracking (accounts for SHORT profit calculation)
- Clear signal reporting

Usage:
    python ma_rsi_strategy.py
    
Configuration:
    Edit strategy_config.yaml to customize parameters
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import yaml
import pandas as pd
import numpy as np

from breeze_client import BreezeTrader


class MAStrategyRunner:
    """Runner for MA + RSI trading strategy."""
    
    def __init__(self, config_path: str = 'strategy_config.yaml'):
        """
        Initialize strategy runner.
        
        Args:
            config_path: Path to strategy configuration file
        """
        self.config = self._load_config(config_path)
        self.trader = None
        self.cache_dir = Path(self.config['strategy']['data']['cache_directory'])
        
        # Position tracking: {stock: {'in_position': bool, 'position_type': 'LONG'/'SHORT', 'entry_price': float}}
        self.positions = {}
        
        # Create cache directory if enabled
        if self.config['strategy']['data']['cache_enabled']:
            self.cache_dir.mkdir(exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load strategy configuration from YAML file."""
        config_file = Path(__file__).parent.parent.parent / config_path
        
        if not config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_file}\n"
                "Please create strategy_config.yaml in the project root."
            )
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _initialize_trader(self) -> None:
        """Initialize BreezeTrader client."""
        try:
            self.trader = BreezeTrader()
            print("✓ Connected to Breeze API")
        except Exception as e:
            print(f"✗ Failed to connect to Breeze API: {e}")
            raise
    
    def _get_cache_filepath(self, stock: str) -> Path:
        """Get cache file path for a stock."""
        return self.cache_dir / f"{stock}_historical.csv"
    
    def _load_cached_data(self, stock: str) -> Optional[pd.DataFrame]:
        """
        Load cached historical data if available and recent.
        
        Args:
            stock: Stock symbol
            
        Returns:
            DataFrame with historical data or None if cache invalid
        """
        if not self.config['strategy']['data']['cache_enabled']:
            return None
        
        cache_file = self._get_cache_filepath(stock)
        
        if not cache_file.exists():
            return None
        
        try:
            df = pd.read_csv(cache_file, parse_dates=['datetime'])
            
            # Check if cache is recent (updated today)
            if df.empty:
                return None
            
            last_date = pd.to_datetime(df['datetime'].max())
            today = pd.Timestamp.now().normalize()
            
            # If last date is today or yesterday (for weekend), use cache
            if (today - last_date).days <= 2:
                return df
            
            print(f"  Cache expired (last update: {last_date.date()})")
            return None
            
        except Exception as e:
            print(f"  Warning: Could not load cache: {e}")
            return None
    
    def _save_to_cache(self, stock: str, df: pd.DataFrame) -> None:
        """Save historical data to cache."""
        if not self.config['strategy']['data']['cache_enabled']:
            return
        
        cache_file = self._get_cache_filepath(stock)
        
        try:
            df.to_csv(cache_file, index=False)
        except Exception as e:
            print(f"  Warning: Could not save to cache: {e}")
    
    def _fetch_historical_data(self, stock: str) -> pd.DataFrame:
        """
        Fetch historical data from Breeze API or cache.
        
        Args:
            stock: Stock symbol
            
        Returns:
            DataFrame with OHLCV data
        """
        # Try to load from cache first
        df = self._load_cached_data(stock)
        if df is not None:
            print(f"  ✓ Loaded from cache ({len(df)} days)")
            return df
        
        # Fetch from API
        days = self.config['strategy']['data']['days_to_fetch']
        interval = self.config['strategy']['data']['interval']
        exchange = self.config['strategy']['trading']['exchange']
        
        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days + 10)  # Extra buffer for holidays
        
        try:
            print(f"  Fetching data from Breeze API...")
            print(f"  Parameters: stock={stock}, exchange={exchange}, interval={interval}")
            print(f"  Date range: {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}")
            
            data = self.trader.get_historical_data(
                stock=stock,
                interval=interval,
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d"),
                exchange_code=exchange
            )
            
            if not data or len(data) == 0:
                print(f"  ✗ API returned empty data for {stock}")
                print(f"  💡 Try:")
                print(f"     1. Different stock symbol (check exact symbol on ICICI)")
                print(f"     2. Different exchange (BSE instead of NSE)")
                print(f"     3. Shorter date range (10 days)")
                print(f"     4. Run 'python scripts/login.py' if session expired")
                raise ValueError(f"No data returned from API for {stock}")
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Parse datetime
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
            
            # Ensure numeric columns
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Sort by date
            df = df.sort_values('datetime').reset_index(drop=True)
            
            # Save to cache
            self._save_to_cache(stock, df)
            
            print(f"  ✓ Fetched {len(df)} days of data")
            return df
            
        except ValueError as e:
            # Re-raise ValueError with suggestions already printed
            raise
        except Exception as e:
            print(f"  ✗ API Error: {type(e).__name__}: {e}")
            print(f"  💡 Common fixes:")
            print(f"     1. Session expired: python scripts/login.py")
            print(f"     2. Check credentials in config.yaml")
            print(f"     3. Verify internet connection")
            raise Exception(f"Failed to fetch historical data for {stock}: {e}")
    
    def _calculate_sma(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return df['close'].rolling(window=period).mean()
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss
        
        Args:
            df: DataFrame with 'close' prices
            period: RSI period (default 14)
            
        Returns:
            Series with RSI values
        """
        # Calculate price changes
        delta = df['close'].diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _generate_signal(
        self, 
        ma_short: float, 
        ma_long: float, 
        rsi: float,
        prev_rsi: float,
        current_close: float,
        current_position_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate trading signal based on momentum breakout/breakdown strategy.
        
        LONG ENTRY:
        - Short MA > Long MA (uptrend)
        - Previous RSI < rsi_long_entry (e.g., 70)
        - Current RSI >= rsi_long_entry (momentum breakout)
        
        LONG EXIT (any one triggers):
        - Short MA < Long MA (trend reversal)
        - Previous RSI > 50 AND Current RSI < 50 (momentum weakening)
        - Current Close < Long MA (support broken)
        
        SHORT ENTRY:
        - Short MA < Long MA (downtrend)
        - Previous RSI > rsi_short_entry (e.g., 40)
        - Current RSI < rsi_short_entry (momentum breakdown)
        
        SHORT EXIT (any one triggers):
        - Short MA > Long MA (trend reversal)
        - Previous RSI < rsi_short_exit AND Current RSI > rsi_short_exit (momentum recovering)
        - Current Close > Long MA (resistance broken)
        
        Args:
            ma_short: Current short MA
            ma_long: Current long MA
            rsi: Current RSI
            prev_rsi: Previous RSI
            current_close: Current closing price
            current_position_type: Current position ('LONG', 'SHORT', or None)
            
        Returns:
            Tuple of (signal, reason) where signal is BUY/SELL/SHORT/COVER/HOLD
        """
        rsi_long_entry = self.config['strategy']['indicators']['rsi_long_entry']
        rsi_short_entry = self.config['strategy']['indicators']['rsi_short_entry']
        rsi_short_exit = self.config['strategy']['indicators']['rsi_short_exit']
        
        uptrend = ma_short > ma_long
        downtrend = ma_short < ma_long
        
        # === CHECK EXITS FIRST (if in position) ===
        if current_position_type == "LONG":
            # LONG EXIT conditions
            if downtrend:
                return "SELL", "LONG exit: Trend reversal (Short MA < Long MA)"
            
            momentum_weak = (prev_rsi > 50) and (rsi < 50)
            if momentum_weak:
                return "SELL", f"LONG exit: Momentum weakening (RSI: {prev_rsi:.1f}→{rsi:.1f}, crossed 50)"
            
            support_broken = current_close < ma_long
            if support_broken:
                return "SELL", f"LONG exit: Support broken (₹{current_close:.2f} < MA: ₹{ma_long:.2f})"
        
        elif current_position_type == "SHORT":
            # SHORT EXIT conditions
            if uptrend:
                return "COVER", "SHORT exit: Trend reversal (Short MA > Long MA)"
            
            momentum_recovering = (prev_rsi < rsi_short_exit) and (rsi >= rsi_short_exit)
            if momentum_recovering:
                return "COVER", f"SHORT exit: Momentum recovering (RSI: {prev_rsi:.1f}→{rsi:.1f}, crossed {rsi_short_exit})"
            
            resistance_broken = current_close > ma_long
            if resistance_broken:
                return "COVER", f"SHORT exit: Resistance broken (₹{current_close:.2f} > MA: ₹{ma_long:.2f})"
        
        # === CHECK ENTRIES (if not in position) ===
        if current_position_type is None:
            # LONG ENTRY: Uptrend + RSI breakout above threshold
            rsi_long_breakout = (prev_rsi < rsi_long_entry) and (rsi >= rsi_long_entry)
            if uptrend and rsi_long_breakout:
                return "BUY", f"LONG entry: Momentum breakout (RSI: {prev_rsi:.1f}→{rsi:.1f}, crossing {rsi_long_entry})"
            
            # SHORT ENTRY: Downtrend + RSI breakdown below threshold
            rsi_short_breakdown = (prev_rsi > rsi_short_entry) and (rsi < rsi_short_entry)
            if downtrend and rsi_short_breakdown:
                return "SHORT", f"SHORT entry: Momentum breakdown (RSI: {prev_rsi:.1f}→{rsi:.1f}, crossing {rsi_short_entry})"
        
        # === HOLD ===
        if current_position_type:
            return "HOLD", f"Holding {current_position_type} position"
        elif uptrend:
            return "HOLD", "Uptrend but no entry signal"
        elif downtrend:
            return "HOLD", "Downtrend but no entry signal"
        else:
            return "HOLD", "Neutral, waiting for setup"
    
    def _process_stock(self, stock: str) -> None:
        """
        Process a single stock: fetch data, calculate indicators, generate signal.
        
        Args:
            stock: Stock symbol
        """
        print(f"\nProcessing {stock}...")
        print("-" * 60)
        
        try:
            # Fetch historical data
            df = self._fetch_historical_data(stock)
            
            if len(df) < self.config['strategy']['indicators']['ma_long'] + 1:
                print(f"  ✗ Insufficient data ({len(df)} days)")
                return
            
            # Calculate indicators
            ma_short_period = self.config['strategy']['indicators']['ma_short']
            ma_long_period = self.config['strategy']['indicators']['ma_long']
            rsi_period = self.config['strategy']['indicators']['rsi_period']
            
            df['ma_short'] = self._calculate_sma(df, ma_short_period)
            df['ma_long'] = self._calculate_sma(df, ma_long_period)
            df['rsi'] = self._calculate_rsi(df, rsi_period)
            
            # Get latest values
            latest = df.iloc[-1]
            previous = df.iloc[-2]
            
            ma_short = latest['ma_short']
            ma_long = latest['ma_long']
            rsi = latest['rsi']
            prev_rsi = previous['rsi']
            current_close = latest['close']
            
            # Check for NaN values
            if pd.isna(ma_short) or pd.isna(ma_long) or pd.isna(rsi) or pd.isna(prev_rsi):
                print(f"  ✗ Insufficient data for indicators")
                return
            
            # Display current values
            print(f"  Latest Close: ₹{current_close:.2f}")
            print(f"  MA({ma_short_period}): {ma_short:.2f} | MA({ma_long_period}): {ma_long:.2f}")
            print(f"  RSI({rsi_period}): {rsi:.2f} (prev: {prev_rsi:.2f})")
            
            # Check position status
            in_position = self.positions.get(stock, {}).get('in_position', False)
            position_type = self.positions.get(stock, {}).get('position_type', None)
            
            if in_position and position_type:
                entry_price = self.positions[stock]['entry_price']
                
                if position_type == "LONG":
                    pnl = current_close - entry_price
                elif position_type == "SHORT":
                    pnl = entry_price - current_close  # Profit when price falls
                else:
                    pnl = 0
                
                pnl_pct = (pnl / entry_price) * 100
                print(f"  Position: {position_type} @ ₹{entry_price:.2f} | P&L: ₹{pnl:.2f} ({pnl_pct:+.2f}%)")
            else:
                print(f"  Position: NONE")
                position_type = None
            
            # Generate signal
            signal, reason = self._generate_signal(
                ma_short, ma_long, rsi, prev_rsi, current_close, position_type
            )
            
            print(f"  Signal: {signal} ({reason})")
            
            # Execute or simulate order
            self._execute_signal(stock, signal, current_close)
            
        except Exception as e:
            print(f"  ✗ Error processing {stock}: {e}")
    
    def _execute_signal(self, stock: str, signal: str, current_price: float) -> None:
        """
        Execute trading signal based on mode (trial/live) with position tracking.
        
        Signals:
        - BUY: Open LONG position
        - SELL: Close LONG position
        - SHORT: Open SHORT position
        - COVER: Close SHORT position
        - HOLD: No action
        
        Args:
            stock: Stock symbol
            signal: Trading signal (BUY/SELL/SHORT/COVER/HOLD)
            current_price: Current closing price
        """
        # Check current position status
        in_position = self.positions.get(stock, {}).get('in_position', False)
        position_type = self.positions.get(stock, {}).get('position_type', None)
        
        # Position tracking logic
        if signal == "BUY":
            if in_position:
                print(f"  → Already in {position_type} position, skipping BUY signal")
                return
        elif signal == "SELL":
            if not in_position or position_type != "LONG":
                print(f"  → No LONG position to exit, skipping SELL signal")
                return
        elif signal == "SHORT":
            if in_position:
                print(f"  → Already in {position_type} position, skipping SHORT signal")
                return
        elif signal == "COVER":
            if not in_position or position_type != "SHORT":
                print(f"  → No SHORT position to cover, skipping COVER signal")
                return
        elif signal == "HOLD":
            print(f"  → No action taken")
            return
        
        mode = self.config['strategy']['mode']
        quantity = self.config['strategy']['trading']['quantity']
        exchange = self.config['strategy']['trading']['exchange']
        product = self.config['strategy']['trading']['product']
        
        if mode == "trial":
            # Trial mode - just print what would happen and update positions
            print(f"  [TRIAL MODE] Would place: {signal} {stock} qty={quantity}")
            print(f"               Exchange: {exchange}, Product: {product}")
            
            # Update position tracking in trial mode
            if signal == "BUY":
                self.positions[stock] = {
                    'in_position': True,
                    'position_type': 'LONG',
                    'entry_price': current_price
                }
                print(f"               Entry Price: ₹{current_price:.2f}")
                
            elif signal == "SELL":
                entry_price = self.positions[stock]['entry_price']
                pnl = current_price - entry_price
                pnl_pct = (pnl / entry_price) * 100
                print(f"               Exit Price: ₹{current_price:.2f}")
                print(f"               P&L: ₹{pnl:.2f} ({pnl_pct:+.2f}%)")
                self.positions[stock] = {
                    'in_position': False,
                    'position_type': None,
                    'entry_price': 0.0
                }
                
            elif signal == "SHORT":
                self.positions[stock] = {
                    'in_position': True,
                    'position_type': 'SHORT',
                    'entry_price': current_price
                }
                print(f"               Entry Price: ₹{current_price:.2f}")
                
            elif signal == "COVER":
                entry_price = self.positions[stock]['entry_price']
                pnl = entry_price - current_price  # Profit when price falls
                pnl_pct = (pnl / entry_price) * 100
                print(f"               Cover Price: ₹{current_price:.2f}")
                print(f"               P&L: ₹{pnl:.2f} ({pnl_pct:+.2f}%)")
                self.positions[stock] = {
                    'in_position': False,
                    'position_type': None,
                    'entry_price': 0.0
                }
        
        elif mode == "live":
            # Live mode - execute actual order
            print(f"  [LIVE MODE] Placing order: {signal} {stock} qty={quantity}")
            
            try:
                # Execute order based on signal
                if signal == "BUY":
                    # Open LONG position
                    response = self.trader.buy(
                        stock=stock,
                        quantity=quantity,
                        exchange=exchange,
                        product=product
                    )
                elif signal == "SELL":
                    # Close LONG position
                    response = self.trader.sell(
                        stock=stock,
                        quantity=quantity,
                        exchange=exchange,
                        product=product
                    )
                elif signal == "SHORT":
                    # Open SHORT position (sell first)
                    response = self.trader.sell(
                        stock=stock,
                        quantity=quantity,
                        exchange=exchange,
                        product=product
                    )
                elif signal == "COVER":
                    # Close SHORT position (buy to cover)
                    response = self.trader.buy(
                        stock=stock,
                        quantity=quantity,
                        exchange=exchange,
                        product=product
                    )
                
                # Check response
                if response.get('Success'):
                    order_id = response['Success'].get('order_id', 'N/A')
                    print(f"  ✓ Order placed successfully (ID: {order_id})")
                    
                    # Update position tracking
                    if signal == "BUY":
                        self.positions[stock] = {
                            'in_position': True,
                            'position_type': 'LONG',
                            'entry_price': current_price
                        }
                    elif signal == "SELL":
                        entry_price = self.positions[stock]['entry_price']
                        pnl = current_price - entry_price
                        pnl_pct = (pnl / entry_price) * 100
                        print(f"  💰 P&L: ₹{pnl:.2f} ({pnl_pct:+.2f}%)")
                        self.positions[stock] = {
                            'in_position': False,
                            'position_type': None,
                            'entry_price': 0.0
                        }
                    elif signal == "SHORT":
                        self.positions[stock] = {
                            'in_position': True,
                            'position_type': 'SHORT',
                            'entry_price': current_price
                        }
                    elif signal == "COVER":
                        entry_price = self.positions[stock]['entry_price']
                        pnl = entry_price - current_price  # Profit when price falls
                        pnl_pct = (pnl / entry_price) * 100
                        print(f"  💰 P&L: ₹{pnl:.2f} ({pnl_pct:+.2f}%)")
                        self.positions[stock] = {
                            'in_position': False,
                            'position_type': None,
                            'entry_price': 0.0
                        }
                else:
                    print(f"  ✗ Order failed: {response}")
                    
            except Exception as e:
                print(f"  ✗ Error placing order: {e}")
        
        else:
            print(f"  ✗ Invalid mode: {mode} (use 'trial' or 'live')")
    
    def run(self) -> None:
        """Run the trading strategy for all configured stocks."""
        print("=" * 60)
        print("  MA + RSI Momentum Strategy (Long & Short)")
        print("=" * 60)
        
        mode = self.config['strategy']['mode'].upper()
        stocks = self.config['strategy']['stocks']
        rsi_long = self.config['strategy']['indicators']['rsi_long_entry']
        rsi_short_entry = self.config['strategy']['indicators']['rsi_short_entry']
        rsi_short_exit = self.config['strategy']['indicators']['rsi_short_exit']
        
        print(f"\nMode: {mode}")
        if mode == "TRIAL":
            print("(No real orders will be placed - position tracking simulated)")
        else:
            print("⚠️  LIVE MODE - Real orders will be executed!")
        
        print(f"Stocks: {', '.join(stocks)}")
        print(f"Strategy: Momentum Breakout/Breakdown (Long & Short)")
        print(f"  LONG Entry: Uptrend + RSI crossing {rsi_long}")
        print(f"  LONG Exit: Trend reversal OR RSI < 50 OR Price < Long MA")
        print(f"  SHORT Entry: Downtrend + RSI crossing {rsi_short_entry}")
        print(f"  SHORT Exit: Trend reversal OR RSI > {rsi_short_exit} OR Price > Long MA")
        print(f"Indicators: MA({self.config['strategy']['indicators']['ma_short']}/"
              f"{self.config['strategy']['indicators']['ma_long']}), "
              f"RSI({self.config['strategy']['indicators']['rsi_period']})")
        
        # Initialize trader
        self._initialize_trader()
        
        # Process each stock
        for stock in stocks:
            self._process_stock(stock)
        
        print("\n" + "=" * 60)
        print("  Strategy Run Complete")
        print("=" * 60)
        
        # Summary of positions
        long_positions = [stock for stock, pos in self.positions.items() 
                         if pos.get('in_position', False) and pos.get('position_type') == 'LONG']
        short_positions = [stock for stock, pos in self.positions.items() 
                          if pos.get('in_position', False) and pos.get('position_type') == 'SHORT']
        
        print(f"\n📊 Position Summary:")
        if long_positions:
            print(f"  LONG: {', '.join(long_positions)}")
        if short_positions:
            print(f"  SHORT: {', '.join(short_positions)}")
        if not long_positions and not short_positions:
            print(f"  No active positions")
        
        print(f"\nData cached in: {self.cache_dir.absolute()}")
        print("Tip: Edit strategy_config.yaml to customize parameters")


def main():
    """Main entry point."""
    try:
        runner = MAStrategyRunner()
        runner.run()
        
    except KeyboardInterrupt:
        print("\n\nStrategy run interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

