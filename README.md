# Breeze Trading Client

A Python wrapper for ICICI Direct's Breeze API, designed for traders who want to automate their strategies without dealing with technical complexities.

---

## 🎯 What This Is

A simple, trader-friendly Python client that:
- ✅ Makes trading automation **easy** for non-technical users
- ✅ Handles authentication and session management automatically
- ✅ Provides simple methods for common trades (`buy`, `sell`, etc.)
- ✅ Gives full access to advanced features when you need them
- ✅ Is fully compliant with ICICI Direct's Terms of Service

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd breeze

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy example files
cp config.yaml.example config.yaml
cp .env.example .env

# Edit config.yaml with your API credentials
# Edit .env with your API keys (recommended for security)
```

### Daily Workflow

```bash
# Step 1: Login once per day (takes 10 seconds)
python scripts/login.py

# Step 2: Run your trading strategies all day
python my_strategy.py
```

---

## 📝 Simple Example

```python
from breeze_client import BreezeTrader

# Initialize (reads config automatically)
trader = BreezeTrader()

# Simple buy order
trader.buy("RELIANCE", 10)

# Advanced buy order with all parameters
trader.buy("RELIANCE", 10, 
          order_type="limit", 
          price=2450.50,
          validity="IOC")

# View portfolio
portfolio = trader.get_portfolio()
for holding in portfolio:
    print(f"{holding['stock']}: {holding['quantity']} shares")

# Get live quote
quote = trader.get_quote("INFY")
print(f"Current Price: ₹{quote['last_price']}")
```

---

## 📚 Documentation

**For detailed documentation, see:**
- [Setup Guide](docs/SETUP_GUIDE.md) - Installation and configuration
- [API Reference](docs/API_REFERENCE.md) - Complete method documentation
- [Examples](docs/EXAMPLES.md) - Code examples for all features
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

**Planning Documents:**
- [Product Requirements](docs/PRODUCT_REQUIREMENTS.md) - What we're building and why
- [Technical Design](docs/TECHNICAL_DESIGN.md) - How it's built
- [Development Roadmap](docs/ROADMAP.md) - Development phases

---

## 🎨 Features

### Three Levels of Complexity

**Level 1: Simple (For Beginners)**
```python
trader.buy("RELIANCE", 10)
```

**Level 2: Advanced (When You Need More Control)**
```python
trader.buy("RELIANCE", 10, price=2450, order_type="limit", validity="IOC")
```

**Level 3: Expert (Direct SDK Access)**
```python
trader.breeze.place_order(...)  # Full SDK power, nothing hidden
```

### What You Can Do

- ✅ **Order Management:** Buy, sell, modify, cancel orders
- ✅ **Portfolio:** View holdings, positions, P&L
- ✅ **Market Data:** Real-time quotes, historical data (10 years)
- ✅ **Advanced Orders:** GTT (Good Till Triggered), stop-loss
- ✅ **Options & Futures:** Full derivatives trading support
- ✅ **Live Streaming:** WebSocket feeds for real-time data
- ✅ **Everything Else:** Full access to all Breeze API features

---

## 🔐 Security

- Credentials stored in `.env` file (never committed to git)
- Session tokens encrypted and auto-managed
- Compliant with ICICI Direct security requirements
- Manual login required daily (regulatory requirement)

---

## 🛠️ Project Status

**Current Status:** 🚧 In Development

See [ROADMAP.md](ROADMAP.md) for detailed development plan.

**Completed:**
- ✅ Product requirements defined
- ✅ Technical design completed
- ✅ Development roadmap created

**Next Steps:**
- ⏳ Core client implementation
- ⏳ Helper scripts
- ⏳ Documentation
- ⏳ Testing

---

## 📦 Requirements

- Python 3.8 or higher
- ICICI Direct Breeze API account
- Internet connection
- Terminal/command line access

---

## 🤝 Contributing

This project is currently in initial development. Contributions welcome after v1.0 release.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

[Add license information]

---

## ⚠️ Disclaimer

This is an unofficial client for ICICI Direct's Breeze API. Use at your own risk. Always test with small amounts before deploying live trading strategies.

Trading in securities markets involves risk. Past performance is not indicative of future results.

---

## 🔗 Links

- [Breeze API Documentation](https://api.icicidirect.com/breezeapi/documents/index.html)
- [Official breeze-connect SDK](https://pypi.org/project/breeze-connect/)
- [ICICI Direct Website](https://www.icicidirect.com/)

---

## 📞 Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
2. Review [API Reference](docs/API_REFERENCE.md)
3. Check [Examples](docs/EXAMPLES.md)
4. [Create an issue](../../issues) (after repository is public)

---

## 🎯 Design Philosophy

**Three Core Principles:**

1. **Progressive Complexity** - Simple by default, advanced when needed
2. **Transparency** - Never hide SDK functionality, always accessible
3. **Safety First** - Fully compliant with ICICI ToS and regulations

**For Traders, By Understanding Traders:**
- Minimal technical knowledge required
- 10-second daily setup
- Focus on strategy, not implementation
- Clean, readable code

---

## 🏗️ Architecture

```
Your Scripts → BreezeTrader (Wrapper) → breeze-connect (SDK) → ICICI API
```

**Simple layer on top of official SDK:**
- Easier configuration management
- Automatic session handling
- Trader-friendly method names
- Full SDK access when needed

---

**Built with ❤️ for traders who want to automate**

Ready to get started? See [Setup Guide](docs/SETUP_GUIDE.md) →

