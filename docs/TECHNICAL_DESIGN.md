# Technical Design Document
## Breeze Trading Client

**Version:** 1.0  
**Date:** October 25, 2025  
**Status:** Approved

---

## 1. Architecture Overview

### 1.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER'S TRADING SCRIPTS                   │
│                    (my_strategy.py)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ import BreezeTrader
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   BREEZE TRADER CLIENT                      │
│                   (breeze_client package)                   │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Config     │  │   Session    │  │    Error     │     │
│  │   Manager    │  │   Manager    │  │   Handler    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │         BreezeTrader (Main Client)               │     │
│  │  - Trading Methods (buy, sell, etc.)             │     │
│  │  - Portfolio Methods (get_portfolio, etc.)       │     │
│  │  - Market Data Methods (get_quote, etc.)         │     │
│  │  - Advanced Methods (GTT, streaming, etc.)       │     │
│  │  - Direct SDK Access (trader.breeze)             │     │
│  └──────────────────────────────────────────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ calls methods
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              OFFICIAL BREEZE-CONNECT SDK                    │
│              (pip install breeze-connect)                   │
│                                                             │
│  - BreezeConnect class                                      │
│  - generate_session()                                       │
│  - place_order()                                            │
│  - get_portfolio_holdings()                                 │
│  - WebSocket connections                                    │
│  - Checksum calculation                                     │
│  - All API interactions                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS/WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ICICI DIRECT BREEZE API                        │
│              https://api.icicidirect.com                    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Component Diagram

```
breeze_client/
├── __init__.py              # Package exports
├── client.py                # BreezeTrader main class
├── config_manager.py        # YAML config handling
├── session_manager.py       # Session token persistence
├── exceptions.py            # Custom exceptions
├── validators.py            # Input validation
└── utils.py                 # Utility functions
```

---

## 2. Core Components

### 2.1 BreezeTrader Class

**Responsibility:** Main client interface providing all trading functionality

**Key Design Decisions:**
- Wraps official SDK, doesn't reimplement
- Exposes SDK instance for direct access
- Progressive complexity through kwargs
- Stateful (holds config and session)

**Class Structure:**

```python
class BreezeTrader:
    """
    Main trading client wrapping breeze-connect SDK
    
    Usage Levels:
    1. Simple: trader.buy("RELIANCE", 10)
    2. Advanced: trader.buy("RELIANCE", 10, price=2450, validity="IOC")
    3. Expert: trader.breeze.place_order(...)
    """
    
    def __init__(self, config_path='config.yaml'):
        """
        Initialize client with config and session
        
        Args:
            config_path: Path to config.yaml file
        """
        self._config_manager = ConfigManager(config_path)
        self._session_manager = SessionManager()
        self._breeze_sdk = None
        self._initialize_sdk()
    
    # ===== SDK Initialization =====
    def _initialize_sdk(self):
        """Initialize and authenticate SDK"""
        
    # ===== ORDER MANAGEMENT =====
    def buy(self, stock, quantity, **kwargs):
        """Place BUY order with progressive complexity"""
        
    def sell(self, stock, quantity, **kwargs):
        """Place SELL order with progressive complexity"""
        
    def place_order(self, stock, action, quantity, **kwargs):
        """Generic order placement"""
        
    def modify_order(self, order_id, **kwargs):
        """Modify existing order"""
        
    def cancel_order(self, order_id, exchange_code=None):
        """Cancel order"""
        
    def get_order(self, order_id, exchange_code=None):
        """Get order details"""
        
    def get_orders(self, exchange_code=None, from_date=None, to_date=None):
        """Get order list"""
        
    # ===== PORTFOLIO & POSITIONS =====
    def get_portfolio(self, **kwargs):
        """Get portfolio holdings"""
        
    def get_positions(self, **kwargs):
        """Get open positions"""
        
    def square_off(self, **kwargs):
        """Square off position"""
        
    # ===== MARKET DATA =====
    def get_quote(self, stock, exchange=None, **kwargs):
        """Get real-time quote"""
        
    def get_historical_data(self, stock, interval="1day", **kwargs):
        """Get historical data"""
        
    def get_option_chain(self, **kwargs):
        """Get option chain data"""
        
    # ===== ADVANCED FEATURES =====
    def place_gtt(self, stock, **kwargs):
        """Place GTT order"""
        
    def get_gtt_orders(self, **kwargs):
        """Get GTT order book"""
        
    def modify_gtt(self, gtt_order_id, **kwargs):
        """Modify GTT order"""
        
    def cancel_gtt(self, gtt_order_id, exchange_code):
        """Cancel GTT order"""
        
    # ===== LIVE STREAMING =====
    def subscribe_feeds(self, stocks, on_tick, **kwargs):
        """Subscribe to live market data"""
        
    def subscribe_order_updates(self, on_update):
        """Subscribe to order notifications"""
        
    # ===== FUNDS & MARGIN =====
    def get_funds(self, **kwargs):
        """Get fund details"""
        
    def get_margin(self, **kwargs):
        """Get margin details"""
        
    # ===== UTILITY =====
    def get_customer_details(self):
        """Get customer account details"""
        
    def is_session_valid(self):
        """Check if current session is valid"""
        
    @property
    def breeze(self):
        """Direct SDK access for advanced users"""
        return self._breeze_sdk
    
    @property
    def config(self):
        """Access to configuration"""
        return self._config_manager.config
```

### 2.2 ConfigManager Class

**Responsibility:** Load, validate, and provide access to configuration

**Design:**

```python
class ConfigManager:
    """
    Manages configuration from YAML file
    Supports environment variable overrides
    """
    
    def __init__(self, config_path='config.yaml'):
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """Load config from YAML with env var overrides"""
        
    def _validate_config(self):
        """Validate required fields exist"""
        
    def get(self, key, default=None):
        """Get config value with dot notation"""
        # e.g., get('trading.default_exchange')
    
    def get_credentials(self):
        """Get API credentials securely"""
        # Load from .env if available, else from config
```

**Config Schema:**

```yaml
# config.yaml
credentials:
  api_key: "${BREEZE_API_KEY}"       # Can use env vars
  secret_key: "${BREEZE_SECRET_KEY}" # or direct values
  user_id: "XY123456"

trading:
  default_exchange: "NSE"
  default_product: "cash"
  confirm_orders: false
  paper_trading: false

session:
  auto_save: true
  check_validity: true
  warn_before_expiry_minutes: 60

notifications:
  show_order_confirmations: true
  alert_on_session_expiry: true
  log_trades: true

advanced:
  rate_limit_enabled: true
  max_retries: 3
  timeout_seconds: 30
```

### 2.3 SessionManager Class

**Responsibility:** Persist and validate session tokens

**Design:**

```python
class SessionManager:
    """
    Manages session token persistence and validation
    """
    
    SESSION_FILE = '.session_token'
    
    def save_session(self, session_token, expiry=None):
        """Save session token to file"""
        # Format: token|expiry_timestamp
        
    def load_session(self):
        """Load session token from file"""
        # Returns: (token, expiry) tuple
        
    def is_valid(self):
        """Check if current session is still valid"""
        # Check expiry time
        
    def time_until_expiry(self):
        """Get remaining session time"""
        # Returns timedelta
        
    def clear_session(self):
        """Delete session file"""
```

**Session File Format:**

```
# .session_token (auto-generated)
<session_token>|<expiry_timestamp>

# Example:
58593|2025-10-26T00:00:00Z
```

### 2.4 Exception Handling

**Design Philosophy:**
- SDK exceptions are caught and wrapped
- User-friendly error messages
- Technical details available in debug mode

**Custom Exceptions:**

```python
# exceptions.py

class BreezeTraderError(Exception):
    """Base exception for all wrapper errors"""
    pass

class ConfigurationError(BreezeTraderError):
    """Config file issues"""
    pass

class SessionExpiredError(BreezeTraderError):
    """Session token expired"""
    def __str__(self):
        return "Session expired! Run: python scripts/login.py"

class OrderValidationError(BreezeTraderError):
    """Order parameter validation failed"""
    pass

class InsufficientFundsError(BreezeTraderError):
    """Not enough funds for order"""
    pass

class MarketClosedError(BreezeTraderError):
    """Market is closed"""
    pass

class RateLimitError(BreezeTraderError):
    """API rate limit exceeded"""
    pass
```

**Error Translation Layer:**

```python
def _handle_sdk_error(self, sdk_error):
    """
    Translate SDK errors to user-friendly messages
    
    SDK: {"Error": "Insufficient funds"}
    User: "❌ Insufficient funds for this order. Available: ₹50,000"
    """
```

---

## 3. Progressive Complexity Implementation

### 3.1 Parameter Handling Strategy

**Three-Layer Parameter Resolution:**

```python
def buy(self, stock, quantity, **kwargs):
    """
    Layer 1: Hard defaults (from code)
    Layer 2: Config defaults (from config.yaml)
    Layer 3: User provided (from kwargs)
    
    Later layers override earlier ones
    """
    
    # Layer 1: Hard defaults
    defaults = {
        'order_type': 'market',
        'price': '0',
        'validity': 'day',
        'stoploss': '',
        'disclosed_quantity': '0',
        'expiry_date': '',
        'right': '',
        'strike_price': ''
    }
    
    # Layer 2: Config defaults
    config_defaults = {
        'exchange_code': self.config['trading']['default_exchange'],
        'product': self.config['trading']['default_product']
    }
    
    # Layer 3: User provided
    # Merge: defaults < config_defaults < kwargs
    params = {**defaults, **config_defaults, **kwargs}
    
    # Call SDK
    return self.breeze.place_order(
        stock_code=stock,
        action="buy",
        quantity=str(quantity),
        **params
    )
```

### 3.2 Parameter Aliases

**Support trader-friendly parameter names:**

```python
PARAMETER_ALIASES = {
    'type': 'order_type',
    'exchange': 'exchange_code',
    'qty': 'quantity',
    'product_type': 'product',
    'stop_loss': 'stoploss',
    'sl': 'stoploss',
    'disclosed_qty': 'disclosed_quantity'
}

def _resolve_aliases(self, kwargs):
    """Convert aliases to SDK parameter names"""
    resolved = {}
    for key, value in kwargs.items():
        resolved_key = PARAMETER_ALIASES.get(key, key)
        resolved[resolved_key] = value
    return resolved
```

### 3.3 SDK Method Mapping

**Direct passthrough to SDK:**

```python
# All SDK methods accessible via trader.breeze
trader.breeze.place_order(...)
trader.breeze.get_portfolio_holdings(...)
trader.breeze.subscribe_feeds(...)

# Future SDK additions work immediately
trader.breeze.any_new_sdk_method(...)
```

---

## 4. Data Flow

### 4.1 Initialization Flow

```
┌──────────────────────┐
│ BreezeTrader()       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Load config.yaml     │
│ (ConfigManager)      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Load .env secrets    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Load session token   │
│ (SessionManager)     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Validate session     │
│ - Check expiry       │
│ - Warn if expiring   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Initialize SDK       │
│ BreezeConnect()      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ generate_session()   │
│ (SDK method)         │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Ready for trading!   │
└──────────────────────┘
```

### 4.2 Order Placement Flow

```
┌──────────────────────────────┐
│ trader.buy("RELIANCE", 10)   │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Check session validity       │
│ (SessionManager)             │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Resolve parameters           │
│ - Apply defaults             │
│ - Resolve aliases            │
│ - Merge kwargs               │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Validate parameters          │
│ (optional, if enabled)       │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Confirm order                │
│ (if enabled in config)       │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Call SDK place_order()       │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Handle response              │
│ - Success: return order ID   │
│ - Error: translate & raise   │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Log transaction              │
│ (if enabled)                 │
└──────────────────────────────┘
```

### 4.3 Daily Login Flow

```
┌──────────────────────────────┐
│ python scripts/login.py      │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Load API key from config     │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Build login URL              │
│ api.icicidirect.com/apiuser/ │
│ login?api_key=XXX            │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Open URL in browser          │
│ (webbrowser.open())          │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ User logs in manually        │
│ (Compliant with ToS)         │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Prompt for session token     │
│ OR auto-detect from clipboard│
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Validate token format        │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Calculate expiry             │
│ (midnight or +24 hours)      │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Save to .session_token       │
│ (SessionManager)             │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Confirm success              │
│ "✓ Ready to trade!"          │
└──────────────────────────────┘
```

---

## 5. File Structure

```
breeze/
├── .gitignore                     # Ignore sensitive files
├── .env.example                   # Example environment variables
├── config.yaml.example            # Example configuration
├── requirements.txt               # Python dependencies
├── setup.py                       # Package installation
├── README.md                      # User documentation
├── PRODUCT_REQUIREMENTS.md        # This PRD
├── TECHNICAL_DESIGN.md            # This document
├── ROADMAP.md                     # Development roadmap
│
├── breeze_client/                 # Main package
│   ├── __init__.py               # Package exports
│   ├── client.py                 # BreezeTrader class
│   ├── config_manager.py         # Config handling
│   ├── session_manager.py        # Session persistence
│   ├── exceptions.py             # Custom exceptions
│   ├── validators.py             # Input validation
│   └── utils.py                  # Utility functions
│
├── scripts/                       # Helper scripts
│   ├── login.py                  # Daily login helper
│   ├── test_connection.py        # Verify setup
│   ├── session_status.py         # Check session
│   └── examples/                 # Example strategies
│       ├── simple_order.py
│       ├── view_portfolio.py
│       ├── gtt_order.py
│       ├── options_trading.py
│       ├── live_streaming.py
│       └── backtesting_data.py
│
├── tests/                         # Unit tests
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_config_manager.py
│   ├── test_session_manager.py
│   └── test_integration.py
│
└── docs/                          # Additional documentation
    ├── API_REFERENCE.md          # Complete API docs
    ├── SETUP_GUIDE.md            # Setup instructions
    ├── EXAMPLES.md               # Code examples
    └── TROUBLESHOOTING.md        # Common issues
```

---

## 6. Security Considerations

### 6.1 Credential Storage

**Three-tier security:**

```
Priority 1: Environment variables (.env file)
Priority 2: Config file (config.yaml)
Priority 3: Runtime prompt (fallback)
```

**Implementation:**

```python
def get_credentials():
    # Try .env first
    api_key = os.getenv('BREEZE_API_KEY')
    if api_key:
        return api_key
    
    # Try config.yaml
    if '${' in config['credentials']['api_key']:
        # Env var reference but not found
        raise ConfigurationError("Environment variable not set")
    
    return config['credentials']['api_key']
```

### 6.2 .gitignore

```gitignore
# Sensitive files
.env
config.yaml
.session_token

# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp

# Logs
*.log
trades_*.csv
```

### 6.3 Session Token Security

- Stored in `.session_token` (ignored by git)
- File permissions: 0600 (owner read/write only)
- Auto-cleared on expiry
- Never logged or printed

---

## 7. Testing Strategy

### 7.1 Unit Tests

```python
# tests/test_config_manager.py
def test_load_config_valid()
def test_load_config_missing()
def test_env_var_override()

# tests/test_session_manager.py
def test_save_and_load_session()
def test_session_expiry_check()
def test_session_validation()

# tests/test_client.py
def test_buy_simple()
def test_buy_with_all_params()
def test_direct_sdk_access()
def test_parameter_aliases()
```

### 7.2 Integration Tests

```python
# tests/test_integration.py
def test_full_initialization_flow()
def test_order_placement_e2e()
def test_session_expiry_handling()
```

### 7.3 Mock Strategy

- Mock SDK responses for unit tests
- Use test credentials for integration tests
- Paper trading mode for live testing

---

## 8. Performance Considerations

### 8.1 Rate Limiting

**ICICI Limits:**
- 100 calls/minute
- 5000 calls/day

**Implementation:**

```python
class RateLimiter:
    def __init__(self, calls_per_minute=90):  # 10 buffer
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    def check_limit(self):
        # Remove calls older than 1 minute
        # Check if limit exceeded
        # Raise RateLimitError if needed
```

### 8.2 Connection Pooling

- SDK handles connection pooling
- WebSocket connections reused
- No additional pooling needed

### 8.3 Caching

**Session Token:**
- Cached in memory after load
- File read only once per initialization

**Config:**
- Loaded once at initialization
- No dynamic reloading (restart required)

---

## 9. Logging Strategy

### 9.1 Log Levels

```python
# DEBUG: All API calls, parameters
# INFO: Orders placed, session events
# WARNING: Session expiring, rate limits
# ERROR: Failed orders, exceptions
# CRITICAL: Authentication failures
```

### 9.2 Log Format

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('breeze_trader.log'),
        logging.StreamHandler()
    ]
)
```

### 9.3 Trade Log

```csv
# trades_2025-10-25.csv
timestamp,action,stock,quantity,price,order_type,order_id,status
2025-10-25 09:30:15,buy,RELIANCE,10,2450.50,limit,ORDER123,success
```

---

## 10. Future Extensibility

### 10.1 Plugin Architecture

```python
# Future: Custom strategy plugins
class StrategyPlugin:
    def on_tick(self, tick_data):
        pass
    
    def on_order_update(self, order):
        pass

trader.register_plugin(MyStrategy())
```

### 10.2 Multiple Broker Support

```python
# Future: Abstract broker interface
class BrokerInterface:
    def buy(self, stock, quantity, **kwargs):
        raise NotImplementedError

class BreezeTrader(BrokerInterface):
    # Implementation

class ZerodhaTrader(BrokerInterface):
    # Future implementation
```

### 10.3 Event System

```python
# Future: Event-driven architecture
trader.on('order_placed', callback)
trader.on('position_closed', callback)
trader.on('session_expiring', callback)
```

---

## 11. Dependencies

### 11.1 Required

```txt
breeze-connect>=1.0.0
pyyaml>=6.0
python-dotenv>=1.0.0
```

### 11.2 Optional

```txt
pandas>=2.0.0          # For data analysis
pyotp>=2.8.0           # For TOTP (if needed)
```

### 11.3 Development

```txt
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
```

---

## 12. Implementation Phases

See `ROADMAP.md` for detailed development plan.

**High-Level Phases:**
1. Project setup & structure
2. Core client & config management
3. Basic trading methods
4. Advanced features
5. Helper scripts
6. Documentation & examples
7. Testing & validation

---

## 13. Open Questions

*To be resolved during implementation:*

1. ~~Should we support multiple session tokens (multi-account)?~~ → No, v1.0 single account only
2. ~~Paper trading simulation needed?~~ → Maybe v2.0
3. ~~Built-in backtesting engine?~~ → No, user provides data to their backtester
4. ~~GUI or CLI only?~~ → CLI/API only for v1.0

---

## 14. Approval

**Approved By:** User (Trader)  
**Date:** October 25, 2025  
**Next Steps:** Create Development Roadmap

---

## Appendix: Code Style Guide

### Naming Conventions

```python
# Classes: PascalCase
class BreezeTrader:

# Functions/methods: snake_case
def place_order():

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3

# Private methods: _leading_underscore
def _validate_config():
```

### Type Hints

```python
def buy(self, stock: str, quantity: int, **kwargs) -> dict:
    """Type hints for all public methods"""
```

### Docstrings

```python
def buy(self, stock: str, quantity: int, **kwargs) -> dict:
    """
    Place a BUY order
    
    Args:
        stock: Stock symbol (e.g., "RELIANCE")
        quantity: Number of shares to buy
        **kwargs: Additional SDK parameters
            order_type: 'market' or 'limit' (default: 'market')
            price: Limit price (required if order_type='limit')
            ...
    
    Returns:
        dict: Order response with order_id
        
    Raises:
        SessionExpiredError: If session token expired
        OrderValidationError: If parameters invalid
        
    Examples:
        Simple:
            >>> trader.buy("RELIANCE", 10)
        
        Advanced:
            >>> trader.buy("RELIANCE", 10, 
            ...           order_type="limit",
            ...           price=2450.50)
    """
```

