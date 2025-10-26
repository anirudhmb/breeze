# Troubleshooting MA+RSI Strategy

## Error: "No data returned from API"

### Quick Checklist (Do these in order):

#### ✅ Step 1: Login First (Most Common Fix)
```bash
python scripts/login.py
```
- Required **DAILY** (session expires after 24 hours)
- If you see "Session expired" - this is the fix

#### ✅ Step 2: Test Connection
```bash
python scripts/test_connection.py
```
- Confirms API is working
- Verifies credentials are correct

#### ✅ Step 3: Try Different Stocks

Edit `strategy_config.yaml`:
```yaml
stocks:
  - SBIN      # Try this first (usually works)
  - INFY      # Backup option
  - TCS       # Another reliable one
```

**Common mistakes:**
- ❌ `RELIANCE` → might need different symbol
- ❌ Wrong capitalization
- ❌ Stock not available on NSE

#### ✅ Step 4: Reduce Date Range

Edit `strategy_config.yaml`:
```yaml
data:
  days_to_fetch: 10    # Change from 30 to 10
```

**Why:** Shorter date range = more reliable data

#### ✅ Step 5: Try Different Exchange

Edit `strategy_config.yaml`:
```yaml
trading:
  exchange: BSE    # Change from NSE to BSE
```

**Why:** Some stocks only trade on specific exchanges

---

## Understanding the Error Messages

### "Session expired"
**Fix:** Run `python scripts/login.py`

### "API returned empty data for [STOCK]"
**Causes:**
1. Wrong stock symbol
2. Stock not on that exchange
3. No trading data for date range (weekends/holidays)

**Fix:** Try different stock or exchange

### "Failed to initialize BreezeTrader"
**Causes:**
1. Missing `config.yaml` or `.env` file
2. Wrong credentials

**Fix:**
```bash
# Create config.yaml from example
cp config.yaml.example config.yaml

# Edit with your credentials
nano config.yaml
```

---

## Step-by-Step Debugging Process

### 1. Verify Setup
```bash
# Check if venv is activated
which python
# Should show: /Users/.../breeze/venv/bin/python

# Check if dependencies installed
pip list | grep pandas
pip list | grep numpy
```

### 2. Check Configuration Files

**File: `config.yaml`** (must exist)
```yaml
credentials:
  api_key: "YOUR_ACTUAL_API_KEY"  # Not the example text!
  secret_key: "YOUR_ACTUAL_SECRET"
  user_id: "YOUR_USER_ID"
```

**File: `strategy_config.yaml`**
```yaml
strategy:
  mode: trial
  stocks:
    - SBIN     # Start with one reliable stock
```

### 3. Test Individual Components

**Test 1: Connection**
```python
from breeze_client import BreezeTrader
trader = BreezeTrader()  # Should not error
```

**Test 2: Historical Data**
```python
from breeze_client import BreezeTrader
from datetime import datetime, timedelta

trader = BreezeTrader()

to_date = datetime.now()
from_date = to_date - timedelta(days=10)

data = trader.get_historical_data(
    stock="SBIN",
    interval="1day",
    from_date=from_date.strftime("%Y-%m-%d"),
    to_date=to_date.strftime("%Y-%m-%d"),
    exchange_code="NSE"
)

print(f"Got {len(data)} data points")
```

### 4. Run with Verbose Output

The updated strategy now shows:
```
Processing RELIANCE...
  Fetching data from Breeze API...
  Parameters: stock=RELIANCE, exchange=NSE, interval=1day
  Date range: 2025-09-26 to 2025-10-26
  ✗ API returned empty data for RELIANCE
  💡 Try:
     1. Different stock symbol
     2. Different exchange (BSE instead of NSE)
     3. Shorter date range (10 days)
     4. Run 'python scripts/login.py' if session expired
```

---

## Stock Symbol Reference

### Commonly Working Symbols (NSE):
- `SBIN` - State Bank of India
- `INFY` - Infosys
- `TCS` - Tata Consultancy Services
- `HDFCBANK` - HDFC Bank
- `ICICIBANK` - ICICI Bank
- `RELIANCE` - Reliance Industries
- `WIPRO` - Wipro
- `AXISBANK` - Axis Bank

### How to Find Correct Symbol:
1. Go to ICICI Direct trading platform
2. Search for the stock
3. Note the exact symbol shown
4. Use that in `strategy_config.yaml`

---

## Still Having Issues?

### Check These:

1. **Session Token Exists?**
   ```bash
   ls -la .session_token
   # Should show file modified today
   ```

2. **Config File Valid?**
   ```bash
   cat config.yaml | grep api_key
   # Should show your actual key, not ${BREEZE_API_KEY}
   ```

3. **Python Environment?**
   ```bash
   python --version
   # Should be Python 3.8+
   
   which python
   # Should point to venv
   ```

4. **Market Open?**
   - Indian markets: Mon-Fri, 9:15 AM - 3:30 PM IST
   - No data on holidays/weekends
   - Try fetching data from last week

---

## Quick Test Command

Try this minimal test:
```bash
python -c "
from breeze_client import BreezeTrader
from datetime import datetime, timedelta

trader = BreezeTrader()
to_date = datetime.now()
from_date = to_date - timedelta(days=5)

stocks = ['SBIN', 'INFY', 'TCS']
for stock in stocks:
    try:
        data = trader.get_historical_data(
            stock=stock,
            interval='1day',
            from_date=from_date.strftime('%Y-%m-%d'),
            to_date=to_date.strftime('%Y-%m-%d'),
            exchange_code='NSE'
        )
        print(f'{stock}: {len(data)} days')
    except Exception as e:
        print(f'{stock}: ERROR - {e}')
"
```

This will quickly tell you which stocks are working.

---

## Contact Support

If none of this works:
1. Check ICICI Direct API documentation
2. Verify your API subscription is active
3. Contact ICICI Direct support

---

**Last Updated:** 2025-10-26

