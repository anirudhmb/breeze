# Troubleshooting Guide
## Breeze Trading Client

Common issues and their solutions.

---

## Configuration Issues

### ❌ Config file not found

**Error:**
```
ConfigurationError: Config file not found: config.yaml
Please copy config.yaml.example to config.yaml
```

**Solution:**
```bash
cp config.yaml.example config.yaml
# Then edit config.yaml with your credentials
```

---

### ❌ Environment variable not set

**Error:**
```
ConfigurationError: Environment variable 'BREEZE_API_KEY' is not set.
Please set it in your .env file or environment.
```

**Solutions:**

**Option 1: Create .env file**
```bash
cp .env.example .env
# Edit .env and add your keys
```

**Option 2: Set directly in config.yaml**
```yaml
credentials:
  api_key: "your_actual_api_key"  # Instead of ${BREEZE_API_KEY}
  secret_key: "your_actual_secret_key"
```

**Option 3: Set in shell**
```bash
export BREEZE_API_KEY="your_api_key"
export BREEZE_SECRET_KEY="your_secret_key"
```

---

### ❌ Invalid YAML syntax

**Error:**
```
ConfigurationError: Invalid YAML in config file
```

**Solution:**
- Check for proper indentation (use spaces, not tabs)
- Ensure quotes are matched
- Validate YAML syntax online: [YAML Lint](https://www.yamllint.com/)

---

## Session Issues

### ❌ Session not found

**Error:**
```
SessionNotFoundError: No active session found!
Please run: python scripts/login.py
```

**Solution:**
```bash
python scripts/login.py
# Follow the prompts to generate a session token
```

---

### ❌ Session expired

**Error:**
```
SessionExpiredError: Session expired!
Please run: python scripts/login.py
Session tokens are valid for 24 hours or until midnight.
```

**Solution:**
Run the login script to get a new session token:
```bash
python scripts/login.py
```

**Note:** Sessions expire at midnight or after 24 hours, whichever comes first.

---

### ❌ Corrupted session file

**Error:**
```
SessionNotFoundError: (session file exists but invalid)
```

**Solution:**
```bash
# Delete the corrupted session file
rm .session_token

# Generate new session
python scripts/login.py
```

---

## Authentication Issues

### ❌ Authentication failed

**Error:**
```
AuthenticationError: Authentication failed! Please check:
  1. API key and secret key are correct
  2. Session token is valid
  3. Your Breeze API account is active
```

**Solutions:**

1. **Verify credentials:**
   - Check API key in config.yaml
   - Check secret key in config.yaml
   - Ensure no extra spaces or quotes

2. **Regenerate session:**
   ```bash
   python scripts/login.py
   ```

3. **Check API account:**
   - Log into [ICICI Direct API Portal](https://api.icicidirect.com/)
   - Verify your app is active
   - Check if API keys are still valid

---

### ❌ Invalid API key

**Error:**
```
AuthenticationError: Invalid credentials
```

**Solution:**
- Regenerate API keys from ICICI Direct portal
- Update config.yaml with new keys
- Run login script again

---

## Order Placement Issues

### ❌ Insufficient funds

**Error:**
```
InsufficientFundsError: Insufficient funds for this order.
```

**Solutions:**
1. Check available funds:
   ```python
   funds = trader.get_funds()
   print(funds)
   ```

2. Reduce order quantity
3. Add funds to your account

---

### ❌ Market closed

**Error:**
```
MarketClosedError: Market is closed.
Trading hours: Equity: 9:15 AM - 3:30 PM (Mon-Fri)
```

**Solution:**
- Wait until market opens
- Check market holidays
- Verify correct exchange (NSE vs BSE)

---

### ❌ Invalid stock code

**Error:**
```
InvalidStockCodeError: Invalid stock code: 'XYZ'
```

**Solutions:**
1. Verify stock symbol is correct
2. Check if stock is listed on selected exchange
3. Use correct format (e.g., "RELIANCE" not "reliance")

---

### ❌ Order validation error

**Error:**
```
OrderValidationError: Invalid quantity
```

**Solutions:**
1. Check quantity is positive integer
2. For F&O, use correct lot size
3. Verify minimum order requirements

---

## Network Issues

### ❌ Connection timeout

**Error:**
```
NetworkError: Network error! Please check:
  1. Your internet connection
  2. ICICI Direct API status
  3. Firewall/proxy settings
```

**Solutions:**

1. **Check internet:**
   ```bash
   ping api.icicidirect.com
   ```

2. **Check API status:**
   - Visit [ICICI Direct API Portal](https://api.icicidirect.com/)
   - Check if API is operational

3. **Firewall/Proxy:**
   - Allow connections to `api.icicidirect.com`
   - Configure proxy if needed

---

### ❌ WebSocket connection failed

**Error:**
```
WebSocketError: WebSocket connection failed
```

**Solutions:**

1. **Check session validity:**
   ```bash
   python scripts/session_status.py
   ```

2. **Reconnect:**
   ```python
   trader.ws_disconnect()
   trader.ws_connect()
   ```

3. **Check WebSocket settings** in config.yaml:
   ```yaml
   websocket:
     auto_reconnect: true
     max_reconnect_attempts: 5
   ```

---

## Rate Limiting Issues

### ❌ Rate limit exceeded

**Error:**
```
RateLimitError: API rate limit exceeded!
Limits: 100 calls/minute, 5000 calls/day
Please wait a moment before trying again.
```

**Solutions:**

1. **Wait before retrying:**
   ```python
   import time
   time.sleep(60)  # Wait 1 minute
   ```

2. **Reduce API call frequency**

3. **Enable rate limiting** in config:
   ```yaml
   advanced:
     rate_limit_enabled: true
   ```

---

## Import Issues

### ❌ Module not found

**Error:**
```
ModuleNotFoundError: No module named 'breeze_client'
```

**Solutions:**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Check Python path:**
   ```python
   import sys
   sys.path.insert(0, '/path/to/breeze')
   ```

3. **Install package:**
   ```bash
   pip install -e .
   ```

---

### ❌ breeze-connect not found

**Error:**
```
ModuleNotFoundError: No module named 'breeze_connect'
```

**Solution:**
```bash
pip install breeze-connect
```

---

## Data Issues

### ❌ No data returned

**Problem:** API call succeeds but returns empty list

**Solutions:**

1. **Check parameters:**
   ```python
   # Ensure dates are correct
   data = trader.get_historical_data(
       "NIFTY",
       from_date="2024-10-01",  # Valid date
       to_date="2024-10-25"
   )
   ```

2. **Verify stock code and exchange**

3. **Check if data exists for that period**

---

### ❌ Invalid date format

**Error:**
```
ValueError: Invalid date format
```

**Solution:**
Use correct format (YYYY-MM-DD):
```python
trader.get_historical_data(
    "NIFTY",
    from_date="2024-10-01",  # ✅ Correct
    to_date="2024-10-25"
)

# Not:
# from_date="01-10-2024"  # ❌ Wrong
# from_date="Oct 1, 2024"  # ❌ Wrong
```

---

## Performance Issues

### ❌ Slow API calls

**Problem:** API calls taking too long

**Solutions:**

1. **Check network speed**

2. **Use appropriate intervals** for historical data:
   ```python
   # For intraday, use minutes
   data = trader.get_historical_data("NIFTY", interval="5minute")
   
   # For long periods, use daily
   data = trader.get_historical_data("NIFTY", interval="1day")
   ```

3. **Limit data range:**
   ```python
   # Don't fetch years of minute data
   data = trader.get_historical_data(
       "NIFTY",
       interval="1minute",
       from_date="2024-10-25",  # Just today
       to_date="2024-10-25"
   )
   ```

---

## Logging Issues

### Enable Debug Logging

To get more detailed error information:

**In config.yaml:**
```yaml
logging:
  level: "DEBUG"
  log_to_file: true
  log_file: "breeze_trader.log"
```

**In code:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

trader = BreezeTrader()
```

**View logs:**
```bash
tail -f breeze_trader.log
```

---

## Platform-Specific Issues

### Windows

**Path issues:**
```python
# Use raw strings or forward slashes
config_path = r"C:\Users\You\breeze\config.yaml"
# or
config_path = "C:/Users/You/breeze/config.yaml"
```

**Permission issues:**
- Run terminal as Administrator if needed

### macOS/Linux

**Permission denied:**
```bash
chmod +x scripts/login.py
chmod 600 .session_token
```

---

## Still Having Issues?

### Debugging Steps

1. **Enable debug mode:**
   ```yaml
   advanced:
     debug_mode: true
   ```

2. **Check logs:**
   ```bash
   cat breeze_trader.log
   ```

3. **Test connection:**
   ```bash
   python scripts/test_connection.py
   ```

4. **Verify SDK directly:**
   ```python
   from breeze_connect import BreezeConnect
   breeze = BreezeConnect(api_key="your_key")
   # Test if SDK works
   ```

### Get Help

1. Check [ICICI Direct Documentation](https://api.icicidirect.com/breezeapi/documents/)
2. Review [Setup Guide](SETUP_GUIDE.md)
3. Check [API Reference](API_REFERENCE.md)
4. Review [Examples](EXAMPLES.md)

---

## Common Questions

**Q: How often do I need to login?**
A: Once per day. Sessions expire at midnight or after 24 hours.

**Q: Can I automate the login?**
A: No. Manual login is required by ICICI for regulatory compliance.

**Q: What if I forget to login before market opens?**
A: Just run `python scripts/login.py` anytime. Takes 10 seconds.

**Q: Can I use multiple sessions?**
A: Only one session per API key is active at a time.

**Q: Why did my session expire early?**
A: Sessions expire at midnight UTC or after 24 hours, whichever comes first.

---

**Need more help?** Review the documentation or check ICICI Direct support.

