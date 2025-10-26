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
import csv
import logging
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
        self.log_dir = Path('logs')
        self.run_timestamp = datetime.now()
        
        # Position tracking: {stock: {'in_position': bool, 'position_type': 'LONG'/'SHORT', 'entry_price': float}}
        self.positions = {}
        self.position_history = []  # Track all position changes
        
        # Create directories
        if self.config['strategy']['data']['cache_enabled']:
            self.cache_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self._setup_logging()
    
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
    
    def _setup_logging(self) -> None:
        """Setup logging to both file and console."""
        date_str = self.run_timestamp.strftime('%Y-%m-%d')
        
        # Full debug log file
        log_file = self.log_dir / f"full_{date_str}.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
        # Signal CSV logger (clean log)
        self.signal_log_file = self.log_dir / f"signals_{date_str}.csv"
        self._init_signal_log()
    
    def _init_signal_log(self) -> None:
        """Initialize signal CSV log file with headers if it doesn't exist."""
        if not self.signal_log_file.exists():
            with open(self.signal_log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'stock', 'signal', 'position_type', 'price', 'quantity',
                    'ma_short', 'ma_long', 'rsi_prev', 'rsi_curr', 'reason', 'mode'
                ])
    
    def _log_signal(self, stock: str, signal: str, position_type: str, price: float,
                   ma_short: float, ma_long: float, rsi_prev: float, rsi_curr: float,
                   reason: str) -> None:
        """Log signal to CSV file."""
        # Only log actual signals (not HOLD)
        if signal == "HOLD":
            return
        
        quantity = self.config['strategy']['trading']['quantity']
        mode = self.config['strategy']['mode'].upper()
        
        with open(self.signal_log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                self.run_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                stock, signal, position_type, f"{price:.2f}", quantity,
                f"{ma_short:.2f}", f"{ma_long:.2f}", f"{rsi_prev:.2f}", f"{rsi_curr:.2f}",
                reason, mode
            ])
        
        self.logger.info(f"✓ Signal logged to {self.signal_log_file.name}")
    
    def _initialize_trader(self) -> None:
        """Initialize BreezeTrader client."""
        try:
            self.trader = BreezeTrader()
            self.logger.info("✓ Connected to Breeze API")
        except Exception as e:
            self.logger.error(f"✗ Failed to connect to Breeze API: {e}")
            raise
    
    def _get_cache_filepath(self, stock: str) -> Path:
        """Get cache file path for a stock."""
        return self.cache_dir / f"{stock}_historical.csv"
    
    def _load_cached_data(self, stock: str) -> Optional[pd.DataFrame]:
        """
        Load cached historical data if available.
        
        Note: Cache is kept forever (no expiration) for historical analysis.
        
        Args:
            stock: Stock symbol
            
        Returns:
            DataFrame with ALL historical data or None if cache doesn't exist
        """
        if not self.config['strategy']['data']['cache_enabled']:
            return None
        
        cache_file = self._get_cache_filepath(stock)
        
        if not cache_file.exists():
            return None
        
        try:
            df = pd.read_csv(cache_file, parse_dates=['datetime'])
            
            if df.empty:
                return None
            
            last_date = pd.to_datetime(df['datetime'].max())
            self.logger.info(f"  Cache loaded: {len(df)} rows, latest: {last_date}")
            
            return df
            
        except Exception as e:
            self.logger.warning(f"  Could not load cache: {e}")
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
        Fetch historical data with incremental updates.
        
        Strategy:
        - If cache exists: Fetch only new data since last update
        - If no cache: Fetch initial 60 days
        - Keep ALL data in cache (no trimming)
        - Use only last 30 days for indicator calculation
        
        Args:
            stock: Stock symbol
            
        Returns:
            DataFrame with ALL historical OHLCV data
        """
        interval = self.config['strategy']['data']['interval']
        exchange = self.config['strategy']['trading']['exchange']
        
        # Try to load existing cache
        cached_df = self._load_cached_data(stock)
        
        if cached_df is not None:
            # Cache exists - do incremental update
            last_datetime = cached_df['datetime'].max()
            self.logger.info(f"  Fetching new data since {last_datetime}...")
            
            # Fetch only recent data (last few candles)
            to_date = datetime.now()
            from_date = last_datetime
            
            try:
                new_data = self.trader.get_historical_data(
                    stock=stock,
                    interval=interval,
                    from_date=from_date.strftime("%Y-%m-%d"),
                    to_date=to_date.strftime("%Y-%m-%d"),
                    exchange_code=exchange
                )
                
                if new_data and len(new_data) > 0:
                    # Convert and append new data
                    new_df = pd.DataFrame(new_data)
                    new_df['datetime'] = pd.to_datetime(new_df['datetime'])
                    
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        if col in new_df.columns:
                            new_df[col] = pd.to_numeric(new_df[col], errors='coerce')
                    
                    # Append to cache (avoiding duplicates)
                    combined_df = pd.concat([cached_df, new_df], ignore_index=True)
                    combined_df = combined_df.drop_duplicates(subset=['datetime'], keep='last')
                    combined_df = combined_df.sort_values('datetime').reset_index(drop=True)
                    
                    # Save updated cache
                    self._save_to_cache(stock, combined_df)
                    
                    self.logger.info(f"  ✓ Added {len(new_df)} new candles. Total: {len(combined_df)} rows")
                    return combined_df
                else:
                    self.logger.info(f"  No new data available. Using cache ({len(cached_df)} rows)")
                    return cached_df
                    
            except Exception as e:
                self.logger.warning(f"  Could not fetch new data: {e}")
                self.logger.info(f"  Using existing cache ({len(cached_df)} rows)")
                return cached_df
        
        else:
            # No cache - fetch initial data
            days = self.config['strategy']['data']['days_to_fetch']
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days + 10)
            
            self.logger.info(f"  No cache. Fetching initial {days} days...")
            self.logger.info(f"  Parameters: stock={stock}, exchange={exchange}, interval={interval}")
            self.logger.info(f"  Date range: {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}")
            
            try:
                data = self.trader.get_historical_data(
                    stock=stock,
                    interval=interval,
                    from_date=from_date.strftime("%Y-%m-%d"),
                    to_date=to_date.strftime("%Y-%m-%d"),
                    exchange_code=exchange
                )
                
                if not data or len(data) == 0:
                    self.logger.error(f"  ✗ API returned empty data for {stock}")
                    self.logger.info(f"  💡 Try: Different stock symbol, exchange, or check session")
                    raise ValueError(f"No data returned from API for {stock}")
                
                # Convert to DataFrame
                df = pd.DataFrame(data)
                df['datetime'] = pd.to_datetime(df['datetime'])
                
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                df = df.sort_values('datetime').reset_index(drop=True)
                
                # Save initial cache
                self._save_to_cache(stock, df)
                
                self.logger.info(f"  ✓ Fetched {len(df)} rows (initial cache created)")
                return df
                
            except ValueError:
                raise
            except Exception as e:
                self.logger.error(f"  ✗ API Error: {type(e).__name__}: {e}")
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
        
        Strategy: Keep ALL data in cache, calculate on last 30 days only
        
        Args:
            stock: Stock symbol
        """
        self.logger.info(f"\nProcessing {stock}...")
        self.logger.info("-" * 60)
        
        try:
            # Fetch ALL historical data (incremental)
            df_all = self._fetch_historical_data(stock)
            
            # Use only LAST 30 days for indicator calculation
            days_to_use = 30
            ma_long_period = self.config['strategy']['indicators']['ma_long']
            
            # Calculate how many rows we need (30 days, accounting for minute data)
            if '5minute' in self.config['strategy']['data']['interval']:
                # For 5min data: ~78 candles per day (6.5 trading hours * 12 candles/hour)
                rows_needed = days_to_use * 78
            elif '1minute' in self.config['strategy']['data']['interval']:
                rows_needed = days_to_use * 390  # 390 minutes per trading day
            else:
                # For daily data
                rows_needed = days_to_use
            
            # Take last N rows
            if len(df_all) > rows_needed:
                df = df_all.tail(rows_needed).copy()
                self.logger.info(f"  Using last {len(df)} rows ({days_to_use} days) from {len(df_all)} total")
            else:
                df = df_all.copy()
                self.logger.info(f"  Using all {len(df)} rows available")
            
            # Check sufficient data
            if len(df) < ma_long_period + 1:
                self.logger.warning(f"  ✗ Insufficient data for indicators ({len(df)} rows)")
                return
            
            # Calculate indicators on recent data
            ma_short_period = self.config['strategy']['indicators']['ma_short']
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
                self.logger.warning(f"  ✗ Insufficient data for indicators (NaN values)")
                return
            
            # Display current values
            self.logger.info(f"  Latest Close: ₹{current_close:.2f}")
            self.logger.info(f"  MA({ma_short_period}): {ma_short:.2f} | MA({ma_long_period}): {ma_long:.2f}")
            self.logger.info(f"  RSI({rsi_period}): {rsi:.2f} (prev: {prev_rsi:.2f})")
            
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
                self.logger.info(f"  Position: {position_type} @ ₹{entry_price:.2f} | P&L: ₹{pnl:.2f} ({pnl_pct:+.2f}%)")
            else:
                self.logger.info(f"  Position: NONE")
                position_type = None
            
            # Generate signal
            signal, reason = self._generate_signal(
                ma_short, ma_long, rsi, prev_rsi, current_close, position_type
            )
            
            self.logger.info(f"  Signal: {signal} ({reason})")
            
            # Log signal to CSV (only if not HOLD)
            if signal != "HOLD":
                # Determine position type for log (what position type WILL be after this signal)
                if signal == "BUY":
                    log_position_type = "LONG"
                elif signal == "SHORT":
                    log_position_type = "SHORT"
                elif signal in ["SELL", "COVER"]:
                    log_position_type = "NONE"
                else:
                    log_position_type = position_type or "NONE"
                
                self._log_signal(stock, signal, log_position_type, current_close,
                                ma_short, ma_long, prev_rsi, rsi, reason)
            
            # Execute or simulate order
            self._execute_signal(stock, signal, current_close)
            
        except Exception as e:
            self.logger.error(f"  ✗ Error processing {stock}: {e}")
    
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
                    'entry_price': current_price,
                    'entry_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
                    'entry_price': current_price,
                    'entry_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
                            'entry_price': current_price,
                            'entry_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
                            'entry_price': current_price,
                            'entry_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
    
    def _save_positions_file(self) -> None:
        """Save current positions to positions.txt for status display."""
        positions_file = self.log_dir / 'positions.txt'
        
        with open(positions_file, 'w') as f:
            f.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("ACTIVE POSITIONS:\n")
            f.write("=" * 60 + "\n\n")
            
            active_count = 0
            long_count = 0
            short_count = 0
            
            for stock, pos in self.positions.items():
                if pos.get('in_position', False):
                    position_type = pos.get('position_type')
                    entry_price = pos.get('entry_price', 0)
                    
                    f.write(f"{stock}:\n")
                    f.write(f"  Type: {position_type}\n")
                    f.write(f"  Entry Price: ₹{entry_price:.2f}\n")
                    f.write(f"  Entry Time: {pos.get('entry_time', 'N/A')}\n")
                    f.write("\n")
                    
                    active_count += 1
                    if position_type == "LONG":
                        long_count += 1
                    elif position_type == "SHORT":
                        short_count += 1
            
            if active_count == 0:
                f.write("No active positions\n\n")
            
            f.write("=" * 60 + "\n")
            f.write(f"Total Active: {active_count} position(s)\n")
            f.write(f"  LONG: {long_count}\n")
            f.write(f"  SHORT: {short_count}\n")
    
    def _save_last_run_file(self, success: bool, stocks_processed: int, signals: int, errors: int) -> None:
        """Save last run info to last_run.txt for status display."""
        last_run_file = self.log_dir / 'last_run.txt'
        
        end_time = datetime.now()
        duration = (end_time - self.run_timestamp).total_seconds()
        
        with open(last_run_file, 'w') as f:
            f.write(f"Last Run: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Status: {'SUCCESS' if success else 'FAILED'}\n")
            f.write(f"Stocks Processed: {stocks_processed}\n")
            f.write(f"Signals Generated: {signals}\n")
            if errors > 0:
                f.write(f"Errors: {errors}\n")
            f.write(f"Execution Time: {duration:.1f} seconds\n")
            
            # Count active positions
            active_positions = sum(1 for p in self.positions.values() if p.get('in_position', False))
            f.write(f"Active Positions: {active_positions}\n")
    
    def run(self) -> None:
        """Run the trading strategy for all configured stocks."""
        self.logger.info("=" * 60)
        self.logger.info("  MA + RSI Momentum Strategy (Long & Short)")
        self.logger.info("=" * 60)
        
        mode = self.config['strategy']['mode'].upper()
        stocks = self.config['strategy']['stocks']
        rsi_long = self.config['strategy']['indicators']['rsi_long_entry']
        rsi_short_entry = self.config['strategy']['indicators']['rsi_short_entry']
        rsi_short_exit = self.config['strategy']['indicators']['rsi_short_exit']
        
        self.logger.info(f"\nMode: {mode}")
        if mode == "TRIAL":
            self.logger.info("(No real orders will be placed - position tracking simulated)")
        else:
            self.logger.info("⚠️  LIVE MODE - Real orders will be executed!")
        
        self.logger.info(f"Stocks: {', '.join(stocks)}")
        self.logger.info(f"Strategy: Momentum Breakout/Breakdown (Long & Short)")
        self.logger.info(f"  LONG Entry: Uptrend + RSI crossing {rsi_long}")
        self.logger.info(f"  LONG Exit: Trend reversal OR RSI < 50 OR Price < Long MA")
        self.logger.info(f"  SHORT Entry: Downtrend + RSI crossing {rsi_short_entry}")
        self.logger.info(f"  SHORT Exit: Trend reversal OR RSI > {rsi_short_exit} OR Price > Long MA")
        self.logger.info(f"Indicators: MA({self.config['strategy']['indicators']['ma_short']}/"
              f"{self.config['strategy']['indicators']['ma_long']}), "
              f"RSI({self.config['strategy']['indicators']['rsi_period']})")
        
        # Track stats
        stocks_processed = 0
        signals_generated = 0
        errors = 0
        
        try:
            # Initialize trader
            self._initialize_trader()
            
            # Process each stock
            for stock in stocks:
                try:
                    self._process_stock(stock)
                    stocks_processed += 1
                except Exception as e:
                    self.logger.error(f"Error processing {stock}: {e}")
                    errors += 1
            
            success = True
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            success = False
            errors += 1
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("  Strategy Run Complete")
        self.logger.info("=" * 60)
        
        # Summary of positions
        long_positions = [stock for stock, pos in self.positions.items() 
                         if pos.get('in_position', False) and pos.get('position_type') == 'LONG']
        short_positions = [stock for stock, pos in self.positions.items() 
                          if pos.get('in_position', False) and pos.get('position_type') == 'SHORT']
        
        self.logger.info(f"\n📊 Position Summary:")
        if long_positions:
            self.logger.info(f"  LONG: {', '.join(long_positions)}")
        if short_positions:
            self.logger.info(f"  SHORT: {', '.join(short_positions)}")
        if not long_positions and not short_positions:
            self.logger.info(f"  No active positions")
        
        self.logger.info(f"\nLogs directory: {self.log_dir.absolute()}")
        self.logger.info(f"Data cached in: {self.cache_dir.absolute()}")
        
        # Save status files
        self._save_positions_file()
        self._save_last_run_file(success, stocks_processed, signals_generated, errors)
        
        self.logger.info("Status files updated: positions.txt, last_run.txt")


def main():
    """Main entry point."""
    # Check for RUNNING flag file
    flag_file = Path('breeze_RUNNING.flag')
    
    if not flag_file.exists():
        print("=" * 60)
        print("  Strategy is STOPPED")
        print("=" * 60)
        print("\nThe strategy is currently disabled.")
        print("Flag file 'breeze_RUNNING.flag' not found.")
        print("\nTo start the strategy:")
        print("  Double-click: START_Strategy.bat")
        print()
        sys.exit(0)
    
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

