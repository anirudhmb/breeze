#!/usr/bin/env python3
"""
MA + RSI Momentum Breakout Strategy

A config-driven momentum trading strategy that:
- Buys when RSI crosses into overbought zone during uptrends (momentum acceleration)
- Exits when trend reverses, momentum weakens, or support breaks
- Tracks positions to prevent duplicate entries/exits

Entry Logic (LONG):
  - Short MA > Long MA (uptrend)
  - Previous RSI < threshold (e.g., 70)
  - Current RSI >= threshold (momentum breakout)

Exit Logic (LONG):
  - Short MA < Long MA (trend reversal) OR
  - Previous RSI > 50 AND Current RSI < 50 (momentum weakening) OR
  - Current Close < Long MA (support broken)

Features:
- Trial/Live mode toggle (safe testing)
- Position tracking (prevents duplicate buys/sells)
- Historical data caching (CSV)
- Multi-stock support
- P&L tracking
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
        
        # Position tracking: {stock: {'in_position': bool, 'entry_price': float}}
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
            
            data = self.trader.get_historical_data(
                stock=stock,
                interval=interval,
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d"),
                exchange_code=exchange
            )
            
            if not data or len(data) == 0:
                raise ValueError("No data returned from API")
            
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
            
        except Exception as e:
            raise Exception(f"Failed to fetch historical data: {e}")
    
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
        current_close: float
    ) -> Tuple[str, str]:
        """
        Generate trading signal based on momentum breakout strategy.
        
        LONG ENTRY:
        - Short MA > Long MA (uptrend)
        - Previous RSI < overbought threshold
        - Current RSI >= overbought threshold (momentum accelerating)
        
        LONG EXIT (any one triggers):
        - Short MA < Long MA (trend reversal)
        - Previous RSI > 50 AND Current RSI < 50 (momentum weakening)
        - Current Close < Long MA (support broken)
        
        Args:
            ma_short: Current short MA
            ma_long: Current long MA
            rsi: Current RSI
            prev_rsi: Previous RSI
            current_close: Current closing price
            
        Returns:
            Tuple of (signal, reason) where signal is BUY/SELL/HOLD
        """
        rsi_overbought = self.config['strategy']['indicators']['rsi_overbought']
        
        # === LONG ENTRY LOGIC ===
        # BUY when: Uptrend + RSI just crossed into overbought (momentum breakout)
        uptrend = ma_short > ma_long
        rsi_breakout = (prev_rsi < rsi_overbought) and (rsi >= rsi_overbought)
        
        if uptrend and rsi_breakout:
            return "BUY", f"Momentum breakout (RSI: {prev_rsi:.1f}→{rsi:.1f}, crossing {rsi_overbought})"
        
        # === LONG EXIT LOGIC ===
        # Exit 1: Trend reversal (bearish crossover)
        trend_reversal = ma_short < ma_long
        if trend_reversal:
            return "SELL", "Trend reversal (Short MA < Long MA)"
        
        # Exit 2: Momentum weakening (RSI crosses below 50)
        momentum_weak = (prev_rsi > 50) and (rsi < 50)
        if momentum_weak:
            return "SELL", f"Momentum weakening (RSI: {prev_rsi:.1f}→{rsi:.1f}, crossed below 50)"
        
        # Exit 3: Support broken (price below long MA)
        support_broken = current_close < ma_long
        if support_broken:
            return "SELL", f"Support broken (Price: ₹{current_close:.2f} < MA: ₹{ma_long:.2f})"
        
        # === HOLD ===
        if uptrend:
            return "HOLD", "Uptrend but no entry/exit signal"
        else:
            return "HOLD", "Downtrend, waiting for setup"
    
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
            if in_position:
                entry_price = self.positions[stock]['entry_price']
                pnl = current_close - entry_price
                pnl_pct = (pnl / entry_price) * 100
                print(f"  Position: LONG @ ₹{entry_price:.2f} | P&L: ₹{pnl:.2f} ({pnl_pct:+.2f}%)")
            else:
                print(f"  Position: NONE")
            
            # Generate signal
            signal, reason = self._generate_signal(
                ma_short, ma_long, rsi, prev_rsi, current_close
            )
            
            print(f"  Signal: {signal} ({reason})")
            
            # Execute or simulate order
            self._execute_signal(stock, signal, current_close)
            
        except Exception as e:
            print(f"  ✗ Error processing {stock}: {e}")
    
    def _execute_signal(self, stock: str, signal: str, current_price: float) -> None:
        """
        Execute trading signal based on mode (trial/live) with position tracking.
        
        Args:
            stock: Stock symbol
            signal: Trading signal (BUY/SELL/HOLD)
            current_price: Current closing price
        """
        # Check current position status
        in_position = self.positions.get(stock, {}).get('in_position', False)
        
        # Position tracking logic
        if signal == "BUY":
            if in_position:
                print(f"  → Already in position, skipping BUY signal")
                return
        elif signal == "SELL":
            if not in_position:
                print(f"  → No position to exit, skipping SELL signal")
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
                    'entry_price': 0.0
                }
        
        elif mode == "live":
            # Live mode - execute actual order
            print(f"  [LIVE MODE] Placing order: {signal} {stock} qty={quantity}")
            
            try:
                if signal == "BUY":
                    response = self.trader.buy(
                        stock=stock,
                        quantity=quantity,
                        exchange=exchange,
                        product=product
                    )
                elif signal == "SELL":
                    response = self.trader.sell(
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
                            'entry_price': current_price
                        }
                    elif signal == "SELL":
                        entry_price = self.positions[stock]['entry_price']
                        pnl = current_price - entry_price
                        pnl_pct = (pnl / entry_price) * 100
                        print(f"  💰 P&L: ₹{pnl:.2f} ({pnl_pct:+.2f}%)")
                        self.positions[stock] = {
                            'in_position': False,
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
        print("  MA + RSI Momentum Breakout Strategy")
        print("=" * 60)
        
        mode = self.config['strategy']['mode'].upper()
        stocks = self.config['strategy']['stocks']
        rsi_threshold = self.config['strategy']['indicators']['rsi_overbought']
        
        print(f"\nMode: {mode}")
        if mode == "TRIAL":
            print("(No real orders will be placed - position tracking simulated)")
        else:
            print("⚠️  LIVE MODE - Real orders will be executed!")
        
        print(f"Stocks: {', '.join(stocks)}")
        print(f"Strategy: Momentum Breakout")
        print(f"  - Entry: Uptrend + RSI crossing {rsi_threshold}")
        print(f"  - Exit: Trend reversal OR RSI < 50 OR Price < Long MA")
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
        active_positions = [stock for stock, pos in self.positions.items() if pos.get('in_position', False)]
        if active_positions:
            print(f"\n📊 Active Positions: {', '.join(active_positions)}")
        else:
            print(f"\n📊 No active positions")
        
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

