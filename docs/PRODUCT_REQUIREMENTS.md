# Product Requirements Document (PRD)
## Breeze Trading Client

**Version:** 1.0  
**Date:** October 25, 2025  
**Status:** Approved

---

## 1. Executive Summary

### 1.1 Overview
A Python trading client that wraps the official ICICI Direct `breeze-connect` SDK, designed for traders who want to automate their strategies without worrying about technical complexities like OAuth2 token management, API authentication, and parameter handling.

### 1.2 Target User
- **Primary:** Individual traders with minimal coding experience
- **Use Case:** Automated trading strategy execution
- **Pain Points:** 
  - Complex authentication flows
  - Technical SDK documentation
  - Verbose API parameters
  - Session token management

### 1.3 Success Criteria
- ✅ Trader can set up in < 10 minutes
- ✅ Daily workflow takes < 30 seconds
- ✅ Simple trades require 1 line of code
- ✅ All SDK features remain accessible
- ✅ Account-safe (fully compliant with ICICI ToS)

---

## 2. Core Requirements

### 2.1 Functional Requirements

#### FR-1: Progressive Complexity Design
**Priority:** P0 (Critical)

The system MUST support three levels of usage:

```python
# LEVEL 1: Simple (Default)
trader.buy("RELIANCE", 10)

# LEVEL 2: Advanced (All SDK parameters via kwargs)
trader.buy("RELIANCE", 10, order_type="limit", price=2450, validity="IOC")

# LEVEL 3: Expert (Direct SDK access)
trader.breeze.place_order(...)
```

**Acceptance Criteria:**
- Simple methods work with minimal parameters
- All SDK parameters accessible via kwargs
- Direct SDK instance exposed as `trader.breeze`
- No SDK functionality hidden or removed

#### FR-2: Configuration Management
**Priority:** P0 (Critical)

**Requirements:**
- Single YAML config file for all settings
- Automatic loading on initialization
- Support for defaults (exchange, product type, etc.)
- Secure credential storage (.env support)

**Acceptance Criteria:**
- User edits one config file for setup
- No hardcoded credentials in code
- Config validation on load
- Clear error messages for invalid config

#### FR-3: Session Token Management
**Priority:** P0 (Critical)

**Requirements:**
- Automatic session token save/load
- Session validity checking
- Clear expiration warnings
- Manual daily login workflow (regulatory requirement)

**Acceptance Criteria:**
- Session token persists across script runs
- Expires at midnight or 24 hours
- User warned 1 hour before expiry
- Clear error message when expired

#### FR-4: Order Management
**Priority:** P0 (Critical)

**Requirements:**
- Buy/Sell methods for equity
- Limit, market, stop-loss orders
- Order modification and cancellation
- Order history and tracking

**Acceptance Criteria:**
- All SDK order types supported
- Return values include order IDs
- Error handling with plain English messages

#### FR-5: Portfolio & Position Management
**Priority:** P1 (High)

**Requirements:**
- View current holdings
- View open positions
- Square-off positions
- P&L calculation

**Acceptance Criteria:**
- Data returned in clean, readable format
- All SDK portfolio methods accessible

#### FR-6: Market Data
**Priority:** P1 (High)

**Requirements:**
- Real-time quotes
- Historical data (up to 10 years)
- Multiple timeframes (1min, 5min, 1day, etc.)

**Acceptance Criteria:**
- All SDK market data methods accessible
- Simple parameter names
- Data in standard format (easy for pandas)

#### FR-7: Advanced Trading Features
**Priority:** P2 (Medium)

**Requirements:**
- GTT (Good Till Triggered) orders
- Options trading (call/put)
- Futures trading
- Option chain data

**Acceptance Criteria:**
- All advanced SDK features accessible
- Examples provided for complex scenarios

#### FR-8: Live Data Streaming
**Priority:** P2 (Medium)

**Requirements:**
- WebSocket connection management
- Real-time tick data
- Order update notifications
- OHLCV candle streaming

**Acceptance Criteria:**
- SDK WebSocket methods accessible
- Callback-based interface
- Connection error handling

### 2.2 Non-Functional Requirements

#### NFR-1: Security
**Priority:** P0 (Critical)

- No credentials in code
- Session tokens stored securely
- .env file for secrets
- .gitignore for sensitive files

#### NFR-2: Usability
**Priority:** P0 (Critical)

- < 10 minute setup time
- < 30 second daily workflow
- Clear error messages in plain English
- Comprehensive examples

#### NFR-3: Compliance
**Priority:** P0 (Critical)

- Fully compliant with ICICI ToS
- Manual daily login (no automation)
- No terms of service violations

#### NFR-4: Maintainability
**Priority:** P1 (High)

- Well-documented code
- Type hints throughout
- Comprehensive docstrings
- Clean architecture

#### NFR-5: Extensibility
**Priority:** P1 (High)

- Easy to add new methods
- Future SDK updates work immediately
- Plugin architecture for custom strategies

---

## 3. User Stories

### US-1: First Time Setup
**As a** trader with no coding experience  
**I want to** configure the client with my API keys  
**So that** I can start trading without understanding technical details

**Acceptance Criteria:**
- Edit one config file
- Run one setup command
- Clear success/error messages

### US-2: Daily Trading Workflow
**As a** trader  
**I want to** start trading each day with minimal effort  
**So that** I can focus on strategy, not technical setup

**Acceptance Criteria:**
- Run login script (< 30 seconds)
- Scripts work all day without interruption
- Clear expiry warnings

### US-3: Simple Order Placement
**As a** beginner trader  
**I want to** place buy/sell orders with simple commands  
**So that** I can automate basic strategies

**Acceptance Criteria:**
- One-line order placement
- Smart defaults applied
- Clear confirmation messages

### US-4: Advanced Order Control
**As an** experienced trader  
**I want to** access all order parameters  
**So that** I can implement complex strategies

**Acceptance Criteria:**
- All SDK parameters accessible
- Optional parameter documentation
- Examples for advanced scenarios

### US-5: Portfolio Monitoring
**As a** trader  
**I want to** view my holdings and positions easily  
**So that** I can track my portfolio programmatically

**Acceptance Criteria:**
- Simple method calls
- Clean data format
- P&L calculations included

### US-6: Strategy Backtesting
**As a** trader developing strategies  
**I want to** access historical market data  
**So that** I can backtest before live trading

**Acceptance Criteria:**
- Multi-year data access
- Multiple timeframes
- Format compatible with pandas

---

## 4. Out of Scope (v1.0)

The following are explicitly OUT OF SCOPE for v1.0:

- ❌ Automated session token generation (violates ToS)
- ❌ Graphical user interface (CLI/API only)
- ❌ Paper trading simulation (may be added later)
- ❌ Built-in strategy backtesting engine
- ❌ Portfolio optimization algorithms
- ❌ Risk management system
- ❌ Multi-broker support (ICICI only)
- ❌ Mobile app

---

## 5. Technical Constraints

### 5.1 Dependencies
- Python 3.8+
- Official `breeze-connect` SDK
- YAML for config
- Standard library where possible

### 5.2 API Limitations
- 100 API calls per minute (ICICI limit)
- 5000 API calls per day (ICICI limit)
- Session valid 24 hours or until midnight
- Manual login required daily (regulatory)

### 5.3 Platform Support
- macOS ✅
- Linux ✅
- Windows ✅

---

## 6. Design Principles

### 6.1 Progressive Disclosure
- Simple by default
- Complexity available on demand
- Never hide functionality

### 6.2 Convention over Configuration
- Smart defaults for 80% use cases
- Override anything when needed
- Config-driven behavior

### 6.3 Fail-Safe Defaults
- Market orders require explicit confirmation
- Conservative default order types
- Warn before destructive operations

### 6.4 Explicit Better Than Implicit
- Clear method names
- Obvious parameter names
- No magic behavior

### 6.5 DRY (Don't Repeat Yourself)
- Wrapper eliminates boilerplate
- Reusable config
- Helper utilities

---

## 7. Success Metrics

### 7.1 User Experience Metrics
- **Setup Time:** < 10 minutes (target: 5 minutes)
- **Daily Workflow:** < 30 seconds (target: 10 seconds)
- **Lines of Code:** < 5 for simple order (target: 1)

### 7.2 Technical Metrics
- **Test Coverage:** > 80%
- **Documentation Coverage:** 100% of public methods
- **SDK Feature Parity:** 100% (all features accessible)

### 7.3 Compliance Metrics
- **ToS Violations:** 0
- **Security Issues:** 0
- **Failed Authentications:** < 1%

---

## 8. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| SDK API changes | High | Medium | Version pinning, update monitoring |
| Session token automation detection | Critical | Low | Enforce manual login |
| User credential exposure | Critical | Medium | Secure storage, .gitignore |
| API rate limits hit | Medium | Medium | Rate limiting, warnings |
| Documentation outdated | Low | High | Sync with SDK updates |

---

## 9. Assumptions

1. User has ICICI Direct Breeze API account
2. User has basic terminal/command line familiarity
3. User has Python 3.8+ installed
4. User can manually login to ICICI portal daily
5. User's trading strategies are in Python

---

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-10-25 | Use official SDK as base | Avoid reimplementing API, stay updated |
| 2025-10-25 | Manual daily login | Comply with ICICI ToS and regulations |
| 2025-10-25 | Progressive complexity design | Support beginners and experts |
| 2025-10-25 | YAML config file | Human-readable, easy to edit |
| 2025-10-25 | Expose SDK directly | Never lock users in |

---

## 11. Approval

**Approved By:** User (Trader)  
**Date:** October 25, 2025  
**Next Steps:** Create Technical Design Document

---

## Appendix A: Key Terminology

| Term | Definition |
|------|------------|
| **SDK** | Software Development Kit - Official breeze-connect library |
| **Wrapper** | Our custom client layer on top of SDK |
| **Session Token** | Authentication token valid for 24 hours |
| **GTT** | Good Till Triggered - Advanced order type |
| **Progressive Complexity** | Simple by default, advanced when needed |
| **ToS** | Terms of Service |

---

## Appendix B: Reference Links

- [Breeze API Documentation](https://api.icicidirect.com/breezeapi/documents/index.html)
- [breeze-connect SDK on PyPI](https://pypi.org/project/breeze-connect/)
- [ICICI Direct FAQ](https://www.icicidirect.com/faqs/)

