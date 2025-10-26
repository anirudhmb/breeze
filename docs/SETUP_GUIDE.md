# Setup Guide
## Breeze Trading Client

Complete guide to setting up and configuring your Breeze Trading Client.

---

## Prerequisites

- Python 3.8 or higher
- ICICI Direct Breeze API account
- API Key and Secret Key from ICICI Direct

---

## Step 1: Installation

### Clone or Download

```bash
# Navigate to your projects directory
cd /path/to/your/projects

# Clone the repository (if using git)
git clone <repository-url> breeze
cd breeze
```

### Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# For development (optional)
pip install -r requirements-dev.txt
```

---

## Step 2: Configuration

### Create Configuration File

```bash
# Copy the example config
cp config.yaml.example config.yaml
```

### Edit Configuration

Open `config.yaml` in your favorite text editor and update:

```yaml
credentials:
  api_key: "YOUR_API_KEY_HERE"
  secret_key: "YOUR_SECRET_KEY_HERE"
  user_id: "YOUR_USER_ID"

trading:
  default_exchange: "NSE"        # or BSE, NFO, etc.
  default_product: "cash"         # or margin, futures, options
  confirm_orders: false           # Set true for confirmation prompts
```

### Alternative: Environment Variables (Recommended)

For better security, use environment variables:

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env file
BREEZE_API_KEY=your_api_key_here
BREEZE_SECRET_KEY=your_secret_key_here
BREEZE_USER_ID=your_user_id_here
```

Then in `config.yaml`:

```yaml
credentials:
  api_key: "${BREEZE_API_KEY}"
  secret_key: "${BREEZE_SECRET_KEY}"
  user_id: "${BREEZE_USER_ID}"
```

---

## Step 3: Daily Login (Required)

**Important:** You must login once per day to generate a session token.

### Run Login Script

```bash
python scripts/login.py
```

### Follow the Steps

1. Script opens your browser to ICICI Direct login page
2. Login with your ICICI Direct credentials
3. After login, you'll be redirected to your configured URL
4. Copy the `apisession` value from the URL
5. Paste it into the terminal when prompted

Example URL after login:
```
https://yourapp.com/callback?apisession=123456
                                        ^^^^^^
                                 Copy this token
```

### Verify Session

```bash
python scripts/session_status.py
```

You should see:
```
✅ Session Status: VALID
   Expires at: 2025-10-26 00:00:00 UTC
   Time remaining: 8h 30m
```

---

## Step 4: Test Connection

```bash
python scripts/test_connection.py
```

This will verify:
- ✅ Configuration is correct
- ✅ Session token is valid
- ✅ API connection works
- ✅ Account details are accessible

---

## Step 5: Start Trading!

### In Python Scripts

```python
from breeze_client import BreezeTrader

# Initialize trader
trader = BreezeTrader()

# Place your first order
trader.buy("RELIANCE", 10)

# View your portfolio
portfolio = trader.get_portfolio()
print(portfolio)
```

### Run Example Scripts

```bash
# Simple order example
python scripts/examples/simple_order.py

# View portfolio
python scripts/examples/view_portfolio.py

# Market data
python scripts/examples/market_data.py
```

---

## Configuration Options

### Complete config.yaml Reference

```yaml
# API Credentials
credentials:
  api_key: "${BREEZE_API_KEY}"
  secret_key: "${BREEZE_SECRET_KEY}"
  user_id: "${BREEZE_USER_ID}"

# Trading Defaults
trading:
  default_exchange: "NSE"           # NSE, BSE, NFO, MCX, NDX
  default_product: "cash"            # cash, margin, futures, options
  confirm_orders: false              # Prompt before placing orders
  paper_trading: false               # Not implemented in v1.0

# Session Management
session:
  auto_save: true                    # Auto-save session tokens
  check_validity: true               # Check before each API call
  warn_before_expiry_minutes: 60     # Warn when expiring soon

# Notifications & Alerts
notifications:
  show_order_confirmations: true     # Show order confirmations
  alert_on_session_expiry: true      # Alert when session expiring
  log_trades: true                   # Log trades to CSV
  trade_log_pattern: "trades_{date}.csv"

# Advanced Settings
advanced:
  rate_limit_enabled: true           # Enable rate limit protection
  max_retries: 3                     # API retry attempts
  timeout_seconds: 30                # API timeout
  debug_mode: false                  # Enable debug logging
  validate_parameters: true          # Validate before sending to API

# Logging
logging:
  level: "INFO"                      # DEBUG, INFO, WARNING, ERROR
  log_to_file: true
  log_file: "breeze_trader.log"
  format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  date_format: "%Y-%m-%d %H:%M:%S"

# WebSocket Settings
websocket:
  auto_reconnect: true
  max_reconnect_attempts: 5
  reconnect_delay: 5
```

---

## Daily Workflow

### Morning Routine (30 seconds)

```bash
# 1. Generate today's session token
python scripts/login.py

# 2. Verify connection (optional)
python scripts/test_connection.py

# 3. Run your trading strategies
python my_strategy.py
```

### During the Day

Your scripts run automatically with the active session.

### Session Expired?

If you see "Session expired" error:

```bash
# Simply re-run login
python scripts/login.py
```

---

## Troubleshooting

### Common Issues

**1. Config file not found**
```
❌ Configuration Error: Config file not found
```
**Solution:** Copy `config.yaml.example` to `config.yaml`

**2. Environment variable not set**
```
❌ Configuration Error: Environment variable 'BREEZE_API_KEY' is not set
```
**Solution:** Create `.env` file or set the value directly in `config.yaml`

**3. Session expired**
```
❌ Session expired! Please run: python scripts/login.py
```
**Solution:** Run the login script to get a new session token

**4. Authentication failed**
```
❌ Authentication failed! Please check your credentials
```
**Solution:** Verify API key and secret key in config.yaml

For more troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## Security Best Practices

### 1. Protect Your Credentials

- ✅ Use `.env` file for credentials (not committed to git)
- ✅ Add `.env` to `.gitignore` (already done)
- ✅ Never commit config.yaml with real credentials
- ✅ Use environment variables in production

### 2. Session Token Security

- Session tokens are automatically stored in `.session_token`
- File permissions are set to 0600 (owner read/write only)
- Token is never logged or printed
- Automatically cleared when expired

### 3. Code Security

- Never share your API keys publicly
- Don't commit `.session_token` to git (already in .gitignore)
- Keep your repository private if it contains strategies

---

## Getting API Credentials

### Register for Breeze API

1. Visit [ICICI Direct Breeze API Portal](https://api.icicidirect.com/)
2. Register your application
3. Provide:
   - App Name
   - Redirect URL (can be any URL you control)
4. Generate AppKey (API Key) and secret_key
5. Save these securely

### Redirect URL

Can be any URL you have access to:
- Your website: `https://yourwebsite.com/callback`
- Localhost: `http://localhost:8000/callback`
- Any valid URL where you can see the redirected parameters

---

## Next Steps

- [API Reference](API_REFERENCE.md) - Complete method documentation
- [Examples](EXAMPLES.md) - Code examples for all features
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

---

## Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review [API Reference](API_REFERENCE.md)
3. Check [Examples](EXAMPLES.md)
4. Review [ICICI Direct Documentation](https://api.icicidirect.com/breezeapi/documents/)

---

**Ready to trade!** 🚀

