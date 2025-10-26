"""
Breeze Trading Client - Main Client Class

A trader-friendly wrapper around the official breeze-connect SDK.
Simple by default, advanced when needed, nothing hidden.
"""

import logging
from typing import Any, Dict, List, Optional, Callable

from breeze_connect import BreezeConnect

from .config_manager import ConfigManager
from .session_manager import SessionManager
from .exceptions import (
    BreezeTraderError,
    SessionExpiredError,
    AuthenticationError,
    translate_sdk_error,
)
from .utils import (
    resolve_parameter_aliases,
    merge_dicts,
    setup_logging,
)


class BreezeTrader:
    """
    Main trading client for ICICI Direct Breeze API.
    
    Provides three levels of complexity:
    
    1. Simple: trader.buy("RELIANCE", 10)
    2. Advanced: trader.buy("RELIANCE", 10, price=2450, order_type="limit")
    3. Expert: trader.breeze.place_order(...)  # Direct SDK access
    
    Features:
    - Automatic configuration management
    - Automatic session management
    - User-friendly error messages
    - Parameter aliases for ease of use
    - Full access to SDK functionality
    
    Example:
        >>> trader = BreezeTrader()
        >>> trader.buy("RELIANCE", 10)
        >>> trader.get_portfolio()
    """
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialize BreezeTrader client.
        
        Args:
            config_path: Path to configuration file (default: config.yaml)
            
        Raises:
            ConfigurationError: If configuration is invalid
            SessionExpiredError: If session token is expired
            AuthenticationError: If authentication fails
        """
        # Load configuration
        self._config_manager = ConfigManager(config_path)
        self._session_manager = SessionManager()
        
        # Setup logging
        log_config = self._config_manager.get('logging', {})
        self._logger = setup_logging(
            level=log_config.get('level', 'INFO'),
            log_file=log_config.get('log_file') if log_config.get('log_to_file') else None,
            log_format=log_config.get('format'),
            date_format=log_config.get('date_format'),
        )
        
        # Initialize SDK
        self._breeze_sdk: Optional[BreezeConnect] = None
        self._initialize_sdk()
        
        self._logger.info("BreezeTrader initialized successfully")
    
    def _initialize_sdk(self) -> None:
        """
        Initialize and authenticate with Breeze SDK.
        
        Raises:
            SessionExpiredError: If session token is expired or not found
            AuthenticationError: If authentication fails
        """
        # Get credentials
        credentials = self._config_manager.get_credentials()
        api_key = credentials['api_key']
        secret_key = credentials['secret_key']
        
        if not api_key or not secret_key:
            raise AuthenticationError(
                "API key and secret key are required.\n"
                "Please configure them in config.yaml or .env file."
            )
        
        # Check session validity
        if not self._session_manager.is_valid():
            raise SessionExpiredError()
        
        # Warn if session expiring soon
        warning = self._session_manager.warn_if_expiring_soon(
            self._config_manager.get('session.warn_before_expiry_minutes', 60)
        )
        if warning:
            self._logger.warning(warning)
        
        # Get session token
        try:
            session_token = self._session_manager.get_session_token()
        except Exception as e:
            raise SessionExpiredError(str(e))
        
        # Initialize SDK
        try:
            self._breeze_sdk = BreezeConnect(api_key=api_key)
            
            # Generate session
            response = self._breeze_sdk.generate_session(
                api_secret=secret_key,
                session_token=session_token
            )
            
            # Check if session generation was successful
            if response and isinstance(response, dict):
                if response.get('Status') != 200 and response.get('Error'):
                    raise AuthenticationError(f"Session generation failed: {response.get('Error')}")
            
            self._logger.info("SDK session generated successfully")
            
        except Exception as e:
            self._logger.error(f"SDK initialization failed: {e}")
            raise translate_sdk_error(e)
    
    # ==================== ORDER MANAGEMENT ====================
    
    def buy(self, stock: str, quantity: int, **kwargs) -> Dict[str, Any]:
        """
        Place a BUY order.
        
        Simple:
            >>> trader.buy("RELIANCE", 10)
        
        Advanced:
            >>> trader.buy("RELIANCE", 10,
            ...           order_type="limit",
            ...           price=2450.50,
            ...           validity="IOC",
            ...           disclosed_quantity=5)
        
        Args:
            stock: Stock symbol (e.g., "RELIANCE", "TCS", "INFY")
            quantity: Number of shares to buy
            **kwargs: Additional parameters (see below)
        
        Keyword Args:
            exchange_code (str): Exchange (NSE, BSE, NFO, etc.)
            product (str): Product type (cash, margin, futures, options, etc.)
            order_type (str): Order type (market, limit, stop_loss, etc.)
            price (float): Limit price (required for limit orders)
            validity (str): Order validity (day, IOC, etc.)
            stoploss (float): Stop loss price
            disclosed_quantity (int): Disclosed quantity for iceberg orders
            expiry_date (str): Expiry date for F&O (ISO 8601 format)
            right (str): Option type (call, put, others)
            strike_price (float): Strike price for options
            user_remark (str): Custom remark
            
        Returns:
            dict: Order response containing order_id and status
            
        Raises:
            OrderValidationError: If parameters are invalid
            SessionExpiredError: If session has expired
            InsufficientFundsError: If insufficient funds
            BreezeTraderError: For other errors
        """
        return self.place_order(stock, "buy", quantity, **kwargs)
    
    def sell(self, stock: str, quantity: int, **kwargs) -> Dict[str, Any]:
        """
        Place a SELL order.
        
        Simple:
            >>> trader.sell("RELIANCE", 10)
        
        Advanced:
            >>> trader.sell("RELIANCE", 10,
            ...            order_type="limit",
            ...            price=2500.00,
            ...            validity="day")
        
        Args:
            stock: Stock symbol
            quantity: Number of shares to sell
            **kwargs: Additional parameters (same as buy())
            
        Returns:
            dict: Order response containing order_id and status
            
        Raises:
            Same exceptions as buy()
        """
        return self.place_order(stock, "sell", quantity, **kwargs)
    
    def place_order(
        self,
        stock: str,
        action: str,
        quantity: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generic order placement method with full control.
        
        Args:
            stock: Stock symbol
            action: Order action ("buy" or "sell")
            quantity: Number of shares
            **kwargs: All SDK order parameters
            
        Returns:
            dict: Order response
            
        Raises:
            BreezeTraderError: If order placement fails
        """
        # Check session validity
        self._check_session()
        
        # Resolve parameter aliases
        kwargs = resolve_parameter_aliases(kwargs)
        
        # Build parameters with three-layer resolution
        # Layer 1: Hard defaults
        defaults = {
            'order_type': 'market',
            'price': '0',
            'validity': 'day',
            'stoploss': '',
            'disclosed_quantity': '0',
            'expiry_date': '',
            'right': '',
            'strike_price': '',
            'user_remark': '',
            'order_type_fresh': '',
            'order_rate_fresh': '',
        }
        
        # Layer 2: Config defaults
        config_defaults = {
            'exchange_code': self._config_manager.get('trading.default_exchange', 'NSE'),
            'product': self._config_manager.get('trading.default_product', 'cash'),
        }
        
        # Layer 3: User provided (via kwargs)
        # Merge all layers
        params = merge_dicts(defaults, config_defaults, kwargs)
        
        # Convert types to strings as required by SDK
        params['quantity'] = str(quantity)
        params['price'] = str(params.get('price', 0))
        params['stoploss'] = str(params.get('stoploss', ''))
        params['disclosed_quantity'] = str(params.get('disclosed_quantity', 0))
        params['strike_price'] = str(params.get('strike_price', ''))
        
        # Order confirmation if enabled
        if self._config_manager.get('trading.confirm_orders', False):
            if not self._confirm_order(stock, action, quantity, params):
                self._logger.info("Order cancelled by user")
                return {'Status': 'cancelled', 'Message': 'Order cancelled by user'}
        
        # Place order via SDK
        try:
            self._logger.info(
                f"Placing {action.upper()} order: {stock} x {quantity} @ "
                f"{params['order_type']} {params['price']}"
            )
            
            response = self._breeze_sdk.place_order(
                stock_code=stock,
                exchange_code=params['exchange_code'],
                product=params['product'],
                action=action,
                order_type=params['order_type'],
                stoploss=params['stoploss'],
                quantity=params['quantity'],
                price=params['price'],
                validity=params['validity'],
                disclosed_quantity=params['disclosed_quantity'],
                expiry_date=params['expiry_date'],
                right=params['right'],
                strike_price=params['strike_price'],
                user_remark=params.get('user_remark', ''),
                order_type_fresh=params.get('order_type_fresh', ''),
                order_rate_fresh=params.get('order_rate_fresh', ''),
            )
            
            # Log successful order
            if response and response.get('Success'):
                order_id = response['Success'].get('order_id', 'N/A')
                self._logger.info(f"Order placed successfully: {order_id}")
                
                # Show confirmation if enabled
                if self._config_manager.get('notifications.show_order_confirmations', True):
                    print(f"✓ Order placed: {order_id}")
            
            return response
            
        except Exception as e:
            self._logger.error(f"Order placement failed: {e}")
            raise translate_sdk_error(e)
    
    def modify_order(
        self,
        order_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Modify an existing order.
        
        Simple:
            >>> trader.modify_order("ORDER123", quantity=20)
        
        Advanced:
            >>> trader.modify_order("ORDER123",
            ...                    quantity=20,
            ...                    price=2460.00,
            ...                    order_type="limit")
        
        Args:
            order_id: Order ID to modify
            **kwargs: Parameters to modify
            
        Keyword Args:
            exchange_code (str): Exchange code
            quantity (int): New quantity
            price (float): New price
            order_type (str): New order type
            validity (str): New validity
            disclosed_quantity (int): New disclosed quantity
            stoploss (float): New stop loss
            
        Returns:
            dict: Modification response
            
        Raises:
            OrderNotFoundError: If order not found
            BreezeTraderError: If modification fails
        """
        self._check_session()
        
        # Resolve aliases
        kwargs = resolve_parameter_aliases(kwargs)
        
        # Get exchange code (required for modification)
        exchange_code = kwargs.get(
            'exchange_code',
            self._config_manager.get('trading.default_exchange', 'NSE')
        )
        
        # Convert numeric values to strings
        if 'quantity' in kwargs:
            kwargs['quantity'] = str(kwargs['quantity'])
        if 'price' in kwargs:
            kwargs['price'] = str(kwargs['price'])
        if 'disclosed_quantity' in kwargs:
            kwargs['disclosed_quantity'] = str(kwargs['disclosed_quantity'])
        if 'stoploss' in kwargs:
            kwargs['stoploss'] = str(kwargs['stoploss'])
        
        try:
            self._logger.info(f"Modifying order: {order_id}")
            
            response = self._breeze_sdk.modify_order(
                order_id=order_id,
                exchange_code=exchange_code,
                order_type=kwargs.get('order_type', ''),
                stoploss=kwargs.get('stoploss', ''),
                quantity=kwargs.get('quantity', ''),
                price=kwargs.get('price', ''),
                validity=kwargs.get('validity', ''),
                disclosed_quantity=kwargs.get('disclosed_quantity', ''),
                expiry_date=kwargs.get('expiry_date', ''),
                right=kwargs.get('right', ''),
                strike_price=kwargs.get('strike_price', ''),
            )
            
            self._logger.info(f"Order modified successfully: {order_id}")
            return response
            
        except Exception as e:
            self._logger.error(f"Order modification failed: {e}")
            raise translate_sdk_error(e)
    
    def cancel_order(
        self,
        order_id: str,
        exchange_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            exchange_code: Exchange code (optional, uses default if not provided)
            
        Returns:
            dict: Cancellation response
            
        Raises:
            OrderNotFoundError: If order not found
            BreezeTraderError: If cancellation fails
        """
        self._check_session()
        
        if exchange_code is None:
            exchange_code = self._config_manager.get('trading.default_exchange', 'NSE')
        
        try:
            self._logger.info(f"Cancelling order: {order_id}")
            
            response = self._breeze_sdk.cancel_order(
                order_id=order_id,
                exchange_code=exchange_code
            )
            
            self._logger.info(f"Order cancelled successfully: {order_id}")
            
            if self._config_manager.get('notifications.show_order_confirmations', True):
                print(f"✓ Order cancelled: {order_id}")
            
            return response
            
        except Exception as e:
            self._logger.error(f"Order cancellation failed: {e}")
            raise translate_sdk_error(e)
    
    def get_order(
        self,
        order_id: str,
        exchange_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get details of a specific order.
        
        Args:
            order_id: Order ID
            exchange_code: Exchange code (optional)
            
        Returns:
            dict: Order details
            
        Raises:
            OrderNotFoundError: If order not found
        """
        self._check_session()
        
        if exchange_code is None:
            exchange_code = self._config_manager.get('trading.default_exchange', 'NSE')
        
        try:
            response = self._breeze_sdk.get_order_detail(
                exchange_code=exchange_code,
                order_id=order_id
            )
            return response
            
        except Exception as e:
            raise translate_sdk_error(e)
    
    def get_orders(
        self,
        exchange_code: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of orders.
        
        Args:
            exchange_code: Exchange code (optional, gets all if not provided)
            from_date: Start date in YYYY-MM-DD format (optional)
            to_date: End date in YYYY-MM-DD format (optional)
            
        Returns:
            list: List of orders
        """
        self._check_session()
        
        if exchange_code is None:
            exchange_code = self._config_manager.get('trading.default_exchange', 'NSE')
        
        try:
            response = self._breeze_sdk.get_order_list(
                exchange_code=exchange_code,
                from_date=from_date or '',
                to_date=to_date or ''
            )
            
            # Extract order list from response
            if response and response.get('Success'):
                return response['Success']
            
            return []
            
        except Exception as e:
            raise translate_sdk_error(e)
    
    # ==================== PORTFOLIO & POSITIONS ====================
    
    def get_portfolio(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Get portfolio holdings.
        
        Simple:
            >>> portfolio = trader.get_portfolio()
        
        Advanced:
            >>> portfolio = trader.get_portfolio(
            ...     exchange_code="NSE",
            ...     from_date="2025-01-01",
            ...     to_date="2025-10-25"
            ... )
        
        Args:
            **kwargs: Optional filtering parameters
            
        Keyword Args:
            exchange_code (str): Exchange code
            from_date (str): Start date (YYYY-MM-DD)
            to_date (str): End date (YYYY-MM-DD)
            stock_code (str): Specific stock code
            portfolio_type (str): Portfolio type
            
        Returns:
            list: List of portfolio holdings
        """
        self._check_session()
        
        exchange_code = kwargs.get(
            'exchange_code',
            self._config_manager.get('trading.default_exchange', 'NSE')
        )
        
        try:
            response = self._breeze_sdk.get_portfolio_holdings(
                exchange_code=exchange_code,
                from_date=kwargs.get('from_date', ''),
                to_date=kwargs.get('to_date', ''),
                stock_code=kwargs.get('stock_code', ''),
                portfolio_type=kwargs.get('portfolio_type', '')
            )
            
            if response and response.get('Success'):
                return response['Success']
            
            return []
            
        except Exception as e:
            raise translate_sdk_error(e)
    
    def get_positions(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Get open positions.
        
        Args:
            **kwargs: Optional parameters
            
        Keyword Args:
            exchange_code (str): Exchange code
            product_type (str): Product type
            
        Returns:
            list: List of open positions
        """
        self._check_session()
        
        exchange_code = kwargs.get(
            'exchange_code',
            self._config_manager.get('trading.default_exchange', 'NSE')
        )
        
        try:
            response = self._breeze_sdk.get_portfolio_positions(
                exchange_code=exchange_code,
                product_type=kwargs.get('product_type', '')
            )
            
            if response and response.get('Success'):
                return response['Success']
            
            return []
            
        except Exception as e:
            raise translate_sdk_error(e)
    
    def square_off(self, **kwargs) -> Dict[str, Any]:
        """
        Square off a position.
        
        Args:
            **kwargs: Square off parameters (all SDK parameters supported)
            
        Keyword Args:
            exchange_code (str): Exchange code
            product (str): Product type
            stock_code (str): Stock symbol
            quantity (int): Quantity to square off
            price (float): Price
            action (str): Action (buy/sell)
            order_type (str): Order type
            validity (str): Validity
            stoploss (float): Stop loss
            disclosed_quantity (int): Disclosed quantity
            expiry_date (str): Expiry date for F&O
            right (str): Option type
            strike_price (float): Strike price
            
        Returns:
            dict: Square off response
        """
        self._check_session()
        
        # Resolve aliases
        kwargs = resolve_parameter_aliases(kwargs)
        
        # Get exchange code
        exchange_code = kwargs.get(
            'exchange_code',
            self._config_manager.get('trading.default_exchange', 'NSE')
        )
        
        try:
            response = self._breeze_sdk.square_off(
                source_flag="N",
                exchange_code=exchange_code,
                product=kwargs.get('product', ''),
                stock_code=kwargs.get('stock_code', ''),
                quantity=kwargs.get('quantity', ''),
                price=kwargs.get('price', ''),
                action=kwargs.get('action', ''),
                order_type=kwargs.get('order_type', ''),
                validity=kwargs.get('validity', 'day'),
                stoploss=kwargs.get('stoploss', ''),
                disclosed_quantity=kwargs.get('disclosed_quantity', ''),
                protection_percentage=kwargs.get('protection_percentage', ''),
                settlement_id=kwargs.get('settlement_id', ''),
                margin_amount=kwargs.get('margin_amount', ''),
                open_quantity=kwargs.get('open_quantity', ''),
                cover_quantity=kwargs.get('cover_quantity', ''),
                product_type=kwargs.get('product_type', 'futures'),
                expiry_date=kwargs.get('expiry_date', ''),
                right=kwargs.get('right', ''),
                strike_price=kwargs.get('strike_price', ''),
                modify_flag=kwargs.get('modify_flag', 'N'),
                order_id=kwargs.get('order_id', ''),
                trading_symbol=kwargs.get('trading_symbol', ''),
            )
            
            return response
            
        except Exception as e:
            raise translate_sdk_error(e)
    
    # ==================== MARKET DATA ====================
    
    def get_quote(
        self,
        stock: str,
        exchange: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get real-time quote for a stock.
        
        Simple:
            >>> quote = trader.get_quote("RELIANCE")
        
        Advanced:
            >>> quote = trader.get_quote("NIFTY",
            ...                         exchange="NFO",
            ...                         product_type="futures",
            ...                         expiry_date="2025-10-31")
        
        Args:
            stock: Stock symbol
            exchange: Exchange code (optional)
            **kwargs: Additional parameters
            
        Keyword Args:
            product_type (str): Product type
            expiry_date (str): Expiry date for F&O
            right (str): Option type (call/put)
            strike_price (float): Strike price
            
        Returns:
            dict: Real-time quote data
        """
        self._check_session()
        
        if exchange is None:
            exchange = self._config_manager.get('trading.default_exchange', 'NSE')
        
        try:
            response = self._breeze_sdk.get_quotes(
                stock_code=stock,
                exchange_code=exchange,
                expiry_date=kwargs.get('expiry_date', ''),
                product_type=kwargs.get('product_type', ''),
                right=kwargs.get('right', ''),
                strike_price=kwargs.get('strike_price', ''),
            )
            
            return response
            
        except Exception as e:
            raise translate_sdk_error(e)
    
    def get_historical_data(
        self,
        stock: str,
        interval: str = "1day",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Get historical market data.
        
        Simple:
            >>> data = trader.get_historical_data("NIFTY",
            ...                                   from_date="2024-01-01",
            ...                                   to_date="2024-12-31")
        
        Advanced:
            >>> data = trader.get_historical_data("NIFTY",
            ...                                   interval="5minute",
            ...                                   exchange_code="NFO",
            ...                                   product_type="futures",
            ...                                   from_date="2025-10-01",
            ...                                   to_date="2025-10-25")
        
        Args:
            stock: Stock symbol
            interval: Data interval (1minute, 5minute, 30minute, 1day, etc.)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            **kwargs: Additional parameters
            
        Keyword Args:
            exchange_code (str): Exchange code
            product_type (str): Product type
            expiry_date (str): Expiry date for F&O
            right (str): Option type
            strike_price (float): Strike price
            
        Returns:
            list: Historical OHLCV data
        """
        self._check_session()
        
        exchange_code = kwargs.get(
            'exchange_code',
            self._config_manager.get('trading.default_exchange', 'NSE')
        )
        
        # Format dates if provided
        if from_date:
            from_date = from_date + "T07:00:00.000Z"
        if to_date:
            to_date = to_date + "T07:00:00.000Z"
        
        try:
            response = self._breeze_sdk.get_historical_data_v2(
                interval=interval,
                from_date=from_date or '',
                to_date=to_date or '',
                stock_code=stock,
                exchange_code=exchange_code,
                product_type=kwargs.get('product_type', ''),
                expiry_date=kwargs.get('expiry_date', ''),
                right=kwargs.get('right', ''),
                strike_price=kwargs.get('strike_price', ''),
            )
            
            if response and response.get('Success'):
                return response['Success']
            
            return []
            
        except Exception as e:
            raise translate_sdk_error(e)
    
    def get_option_chain(self, **kwargs) -> Dict[str, Any]:
        """
        Get option chain data.
        
        Args:
            **kwargs: Option chain parameters
            
        Keyword Args:
            stock_code (str): Stock symbol
            exchange_code (str): Exchange code
            product_type (str): Product type
            expiry_date (str): Expiry date
            
        Returns:
            dict: Option chain data
        """
        self._check_session()
        
        exchange_code = kwargs.get(
            'exchange_code',
            self._config_manager.get('trading.default_exchange', 'NFO')
        )
        
        try:
            response = self._breeze_sdk.get_option_chain_quotes(
                stock_code=kwargs.get('stock_code', ''),
                exchange_code=exchange_code,
                expiry_date=kwargs.get('expiry_date', ''),
                product_type=kwargs.get('product_type', ''),
                right=kwargs.get('right', ''),
                strike_price=kwargs.get('strike_price', ''),
            )
            
            return response
            
        except Exception as e:
            raise translate_sdk_error(e)
    
    # ==================== FUNDS & MARGIN ====================
    
    def get_funds(self, **kwargs) -> Dict[str, Any]:
        """
        Get fund details.
        
        Args:
            **kwargs: Optional parameters
            
        Keyword Args:
            exchange_code (str): Exchange code
            
        Returns:
            dict: Fund details including available margin
        """
        self._check_session()
        
        exchange_code = kwargs.get(
            'exchange_code',
            self._config_manager.get('trading.default_exchange', 'NSE')
        )
        
        try:
            response = self._breeze_sdk.get_funds(
                exchange_code=exchange_code
            )
            
            return response
            
        except Exception as e:
            raise translate_sdk_error(e)
    
    def get_margin(self, **kwargs) -> Dict[str, Any]:
        """
        Get margin details.
        
        Args:
            **kwargs: Optional parameters
            
        Keyword Args:
            exchange_code (str): Exchange code
            
        Returns:
            dict: Margin details
        """
        self._check_session()
        
        exchange_code = kwargs.get(
            'exchange_code',
            self._config_manager.get('trading.default_exchange', 'NSE')
        )
        
        try:
            response = self._breeze_sdk.get_margin(
                exchange_code=exchange_code
            )
            
            return response
            
        except Exception as e:
            raise translate_sdk_error(e)
    
    # ==================== ACCOUNT INFO ====================
    
    def get_customer_details(self) -> Dict[str, Any]:
        """
        Get customer account details.
        
        Returns:
            dict: Customer details including account info, segments, etc.
        """
        # Note: Customer details doesn't require session check
        # as it's used during initial setup
        
        try:
            response = self._breeze_sdk.get_customer_details(
                api_session=self._session_manager.get_session_token()
            )
            
            return response
            
        except Exception as e:
            raise translate_sdk_error(e)
    
    # ==================== GTT ORDERS ====================
    
    def place_gtt(self, stock: str, **kwargs) -> Dict[str, Any]:
        """
        Place GTT (Good Till Triggered) order.
        
        Simple GTT:
            >>> trader.place_gtt("TATAMOTORS",
            ...                 quantity=50,
            ...                 trigger_price=800,
            ...                 limit_price=805,
            ...                 action="buy")
        
        Advanced OCO GTT:
            >>> trader.place_gtt("TATAMOTORS",
            ...                 quantity=50,
            ...                 gtt_type="cover_oco",
            ...                 order_details=[
            ...                     {
            ...                         'gtt_leg_type': 'target',
            ...                         'action': 'sell',
            ...                         'limit_price': '75',
            ...                         'trigger_price': '72'
            ...                     },
            ...                     {
            ...                         'gtt_leg_type': 'stoploss',
            ...                         'action': 'sell',
            ...                         'limit_price': '18',
            ...                         'trigger_price': '22'
            ...                     }
            ...                 ])
        
        Args:
            stock: Stock symbol
            **kwargs: GTT parameters
            
        Keyword Args:
            exchange_code (str): Exchange code
            product (str): Product type
            action (str): buy/sell
            quantity (int/str): Quantity
            gtt_type (str): "single" or "cover_oco"
            trigger_price (str): Trigger price (for single GTT)
            limit_price (str): Limit price (for single GTT)
            order_details (list): List of order legs (for OCO GTT)
            expiry_date (str): Expiry date for F&O
            right (str): Option type
            strike_price (str): Strike price
            
        Returns:
            dict: GTT order response with gtt_order_id
        """
        self._check_session()
        
        # Resolve aliases
        kwargs = resolve_parameter_aliases(kwargs)
        
        exchange_code = kwargs.get(
            'exchange_code',
            self._config_manager.get('trading.default_exchange', 'NSE')
        )
        
        try:
            # Build GTT order parameters
            gtt_params = {
                'stock_code': stock,
                'exchange_code': exchange_code,
                'product': kwargs.get('product', 'cash'),
                'action': kwargs.get('action', 'buy'),
                'quantity': str(kwargs.get('quantity', '')),
                'gtt_type': kwargs.get('gtt_type', 'single'),
                'expiry_date': kwargs.get('expiry_date', ''),
                'right': kwargs.get('right', ''),
                'strike_price': str(kwargs.get('strike_price', '')),
            }
            
            # Handle simple single GTT vs OCO GTT
            if kwargs.get('gtt_type') == 'cover_oco' or 'order_details' in kwargs:
                gtt_params['order_details'] = kwargs.get('order_details', [])
            else:
                # Simple GTT - single trigger
                gtt_params['trigger_price'] = str(kwargs.get('trigger_price', ''))
                gtt_params['limit_price'] = str(kwargs.get('limit_price', ''))
                gtt_params['order_type'] = kwargs.get('order_type', 'limit')
            
            response = self._breeze_sdk.place_gtt_order(**gtt_params)
            
            if response and response.get('Success'):
                gtt_order_id = response['Success'].get('gtt_order_id', 'N/A')
                self._logger.info(f"GTT order placed successfully: {gtt_order_id}")
                
                if self._config_manager.get('notifications.show_order_confirmations', True):
                    print(f"✓ GTT order placed: {gtt_order_id}")
            
            return response
            
        except Exception as e:
            self._logger.error(f"GTT order placement failed: {e}")
            raise translate_sdk_error(e)
    
    def get_gtt_orders(self, **kwargs) -> Dict[str, Any]:
        """
        Get GTT order book.
        
        Args:
            **kwargs: Optional parameters
            
        Keyword Args:
            exchange_code (str): Exchange code
            
        Returns:
            dict: GTT order book
        """
        self._check_session()
        
        exchange_code = kwargs.get(
            'exchange_code',
            self._config_manager.get('trading.default_exchange', 'NSE')
        )
        
        try:
            response = self._breeze_sdk.get_gtt_order_list(
                exchange_code=exchange_code
            )
            
            return response
            
        except Exception as e:
            raise translate_sdk_error(e)
    
    def modify_gtt(self, gtt_order_id: str, **kwargs) -> Dict[str, Any]:
        """
        Modify a GTT order.
        
        Args:
            gtt_order_id: GTT order ID to modify
            **kwargs: Parameters to modify
            
        Keyword Args:
            exchange_code (str): Exchange code
            gtt_type (str): GTT type
            order_details (list): Order details for OCO
            
        Returns:
            dict: Modification response
        """
        self._check_session()
        
        exchange_code = kwargs.get(
            'exchange_code',
            self._config_manager.get('trading.default_exchange', 'NSE')
        )
        
        try:
            response = self._breeze_sdk.modify_gtt_order(
                gtt_order_id=gtt_order_id,
                exchange_code=exchange_code,
                gtt_type=kwargs.get('gtt_type', 'single'),
                order_details=kwargs.get('order_details', [])
            )
            
            self._logger.info(f"GTT order modified successfully: {gtt_order_id}")
            return response
            
        except Exception as e:
            self._logger.error(f"GTT order modification failed: {e}")
            raise translate_sdk_error(e)
    
    def cancel_gtt(self, gtt_order_id: str, exchange_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel a GTT order.
        
        Args:
            gtt_order_id: GTT order ID to cancel
            exchange_code: Exchange code (optional)
            
        Returns:
            dict: Cancellation response
        """
        self._check_session()
        
        if exchange_code is None:
            exchange_code = self._config_manager.get('trading.default_exchange', 'NSE')
        
        try:
            self._logger.info(f"Cancelling GTT order: {gtt_order_id}")
            
            response = self._breeze_sdk.cancel_gtt_order(
                gtt_order_id=gtt_order_id,
                exchange_code=exchange_code
            )
            
            self._logger.info(f"GTT order cancelled successfully: {gtt_order_id}")
            
            if self._config_manager.get('notifications.show_order_confirmations', True):
                print(f"✓ GTT order cancelled: {gtt_order_id}")
            
            return response
            
        except Exception as e:
            self._logger.error(f"GTT order cancellation failed: {e}")
            raise translate_sdk_error(e)
    
    # ==================== LIVE DATA STREAMING ====================
    
    def subscribe_feeds(
        self,
        stocks: List[str],
        on_tick: Callable,
        **kwargs
    ) -> None:
        """
        Subscribe to live market data feeds (WebSocket).
        
        Simple:
            >>> def my_callback(tick_data):
            ...     print(f"{tick_data['stock']}: ₹{tick_data['ltp']}")
            >>> 
            >>> trader.subscribe_feeds(
            ...     stocks=["RELIANCE", "TCS"],
            ...     on_tick=my_callback
            ... )
        
        Advanced:
            >>> trader.subscribe_feeds(
            ...     stocks=["RELIANCE", "TCS", "INFY"],
            ...     on_tick=my_tick_handler,
            ...     interval="1second",
            ...     exchange_code="NSE"
            ... )
        
        Args:
            stocks: List of stock symbols to subscribe
            on_tick: Callback function called for each tick
            **kwargs: Additional parameters
            
        Keyword Args:
            interval (str): Update interval ("1second", "1minute")
            exchange_code (str): Exchange code
            
        Note:
            This is a blocking call. Run in a separate thread if needed.
            The callback function receives tick data as a dictionary.
        """
        self._check_session()
        
        exchange_code = kwargs.get(
            'exchange_code',
            self._config_manager.get('trading.default_exchange', 'NSE')
        )
        
        interval = kwargs.get('interval', '1second')
        
        try:
            self._logger.info(f"Subscribing to feeds for {len(stocks)} stocks")
            
            # Subscribe to live feeds
            self._breeze_sdk.subscribe_feeds(
                stock_token=stocks,
                exchange_code=exchange_code,
                interval=interval,
                on_ticks=on_tick
            )
            
        except Exception as e:
            self._logger.error(f"Feed subscription failed: {e}")
            raise translate_sdk_error(e)
    
    def subscribe_order_updates(self, on_update: Callable) -> None:
        """
        Subscribe to order update notifications (WebSocket).
        
        Args:
            on_update: Callback function called on order updates
            
        Example:
            >>> def handle_update(order_data):
            ...     print(f"Order {order_data['order_id']}: {order_data['status']}")
            >>> 
            >>> trader.subscribe_order_updates(on_update=handle_update)
        
        Note:
            This is a blocking call. Run in a separate thread if needed.
        """
        self._check_session()
        
        try:
            self._logger.info("Subscribing to order notifications")
            
            # Subscribe to order notifications
            self._breeze_sdk.subscribe_order_notification(
                on_update=on_update
            )
            
        except Exception as e:
            self._logger.error(f"Order notification subscription failed: {e}")
            raise translate_sdk_error(e)
    
    def ws_connect(self) -> None:
        """
        Establish WebSocket connection for live streaming.
        
        Call this before subscribing to feeds.
        """
        try:
            self._breeze_sdk.ws_connect()
            self._logger.info("WebSocket connected")
        except Exception as e:
            self._logger.error(f"WebSocket connection failed: {e}")
            raise translate_sdk_error(e)
    
    def ws_disconnect(self) -> None:
        """
        Disconnect WebSocket connection.
        """
        try:
            self._breeze_sdk.ws_disconnect()
            self._logger.info("WebSocket disconnected")
        except Exception as e:
            self._logger.error(f"WebSocket disconnection failed: {e}")
    
    # ==================== UTILITY METHODS ====================
    
    def _check_session(self) -> None:
        """
        Check if session is still valid.
        
        Raises:
            SessionExpiredError: If session has expired
        """
        if not self._session_manager.is_valid():
            raise SessionExpiredError()
        
        # Check if session needs refresh warning
        if self._config_manager.get('notifications.alert_on_session_expiry', True):
            warning = self._session_manager.warn_if_expiring_soon(
                self._config_manager.get('session.warn_before_expiry_minutes', 60)
            )
            if warning:
                print(warning)
    
    def _confirm_order(
        self,
        stock: str,
        action: str,
        quantity: int,
        params: Dict[str, Any]
    ) -> bool:
        """
        Ask user to confirm order placement.
        
        Args:
            stock: Stock symbol
            action: buy or sell
            quantity: Quantity
            params: Order parameters
            
        Returns:
            bool: True if confirmed, False if cancelled
        """
        order_type = params.get('order_type', 'market')
        price = params.get('price', '0')
        
        print(f"\n{'='*50}")
        print(f"  {action.upper()} Order Confirmation")
        print(f"{'='*50}")
        print(f"  Stock: {stock}")
        print(f"  Quantity: {quantity}")
        print(f"  Order Type: {order_type}")
        if order_type != 'market':
            print(f"  Price: ₹{price}")
        print(f"  Exchange: {params.get('exchange_code')}")
        print(f"  Product: {params.get('product')}")
        print(f"{'='*50}")
        
        response = input("Confirm order? (y/n): ").strip().lower()
        return response in ['y', 'yes']
    
    def is_session_valid(self) -> bool:
        """
        Check if current session is valid.
        
        Returns:
            bool: True if session is valid
        """
        return self._session_manager.is_valid()
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get session information.
        
        Returns:
            dict: Session info including expiry time and remaining time
        """
        return {
            'is_valid': self._session_manager.is_valid(),
            'expiry_time': self._session_manager.get_expiry_time(),
            'time_until_expiry_seconds': self._session_manager.time_until_expiry(),
        }
    
    @property
    def breeze(self) -> BreezeConnect:
        """
        Direct access to Breeze SDK for advanced usage.
        
        Returns:
            BreezeConnect: The underlying SDK instance
            
        Example:
            >>> trader.breeze.place_order(...)
            >>> trader.breeze.get_margin_calculator(...)
        """
        return self._breeze_sdk
    
    @property
    def config(self) -> Dict[str, Any]:
        """
        Access to configuration.
        
        Returns:
            dict: Configuration dictionary
        """
        return self._config_manager.config
    
    def __repr__(self) -> str:
        """String representation of BreezeTrader."""
        session_status = "valid" if self.is_session_valid() else "expired"
        return f"BreezeTrader(session={session_status})"

