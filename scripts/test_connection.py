#!/usr/bin/env python3
"""
Breeze Trading Client - Connection Test

Test your setup and verify connection to ICICI Direct Breeze API.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from breeze_client import BreezeTrader
from breeze_client.exceptions import (
    ConfigurationError,
    SessionExpiredError,
    SessionNotFoundError,
    AuthenticationError,
    BreezeTraderError,
)


def test_configuration():
    """Test configuration."""
    print("📋 Testing Configuration...")
    try:
        from breeze_client.config_manager import ConfigManager
        config = ConfigManager()
        credentials = config.get_credentials()
        
        # Check API key
        if not credentials['api_key']:
            print("   ❌ API key not configured")
            return False
        print("   ✅ API key configured")
        
        # Check secret key
        if not credentials['secret_key']:
            print("   ❌ Secret key not configured")
            return False
        print("   ✅ Secret key configured")
        
        # Check default settings
        default_exchange = config.get('trading.default_exchange')
        print(f"   ✅ Default exchange: {default_exchange}")
        
        return True
        
    except ConfigurationError as e:
        print(f"   ❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_session():
    """Test session token."""
    print()
    print("📋 Testing Session...")
    try:
        from breeze_client.session_manager import SessionManager
        session_manager = SessionManager()
        
        if not session_manager.is_valid():
            print("   ❌ No valid session found")
            print("   ℹ️  Run 'python scripts/login.py' to generate a session")
            return False
        
        expiry = session_manager.get_expiry_time()
        remaining = session_manager.time_until_expiry()
        
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        
        print("   ✅ Session token valid")
        print(f"   ℹ️  Expires in: {hours}h {minutes}m")
        
        return True
        
    except SessionNotFoundError:
        print("   ❌ Session not found")
        print("   ℹ️  Run 'python scripts/login.py' to generate a session")
        return False
    except SessionExpiredError:
        print("   ❌ Session expired")
        print("   ℹ️  Run 'python scripts/login.py' to refresh your session")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_connection():
    """Test API connection."""
    print()
    print("📋 Testing API Connection...")
    try:
        trader = BreezeTrader()
        print("   ✅ BreezeTrader initialized successfully")
        
        # Test getting customer details
        print()
        print("📋 Testing API Call (Customer Details)...")
        try:
            response = trader.get_customer_details()
            
            if response and response.get('Success'):
                customer_data = response['Success']
                print("   ✅ API call successful")
                print()
                print("   Account Information:")
                print(f"   • User ID: {customer_data.get('idirect_userid', 'N/A')}")
                print(f"   • User Name: {customer_data.get('idirect_user_name', 'N/A')}")
                print()
                print("   Segments Allowed:")
                segments = customer_data.get('segments_allowed', {})
                print(f"   • Trading: {'Yes' if segments.get('Trading') == 'Y' else 'No'}")
                print(f"   • Equity: {'Yes' if segments.get('Equity') == 'Y' else 'No'}")
                print(f"   • Derivatives: {'Yes' if segments.get('Derivatives') == 'Y' else 'No'}")
                print(f"   • Currency: {'Yes' if segments.get('Currency') == 'Y' else 'No'}")
                print()
                print("   Exchange Status:")
                exg_status = customer_data.get('exg_status', {})
                print(f"   • NSE: {'Open' if exg_status.get('NSE') == 'Y' else 'Closed'}")
                print(f"   • BSE: {'Open' if exg_status.get('BSE') == 'Y' else 'Closed'}")
                print(f"   • F&O: {'Open' if exg_status.get('FNO') == 'Y' else 'Closed'}")
                
                return True
            else:
                print(f"   ❌ API call failed: {response}")
                return False
                
        except Exception as e:
            print(f"   ❌ API call failed: {e}")
            return False
        
    except SessionExpiredError as e:
        print(f"   ❌ Session expired: {e}")
        print("   ℹ️  Run 'python scripts/login.py' to refresh your session")
        return False
    except SessionNotFoundError as e:
        print(f"   ❌ Session not found: {e}")
        print("   ℹ️  Run 'python scripts/login.py' to generate a session")
        return False
    except AuthenticationError as e:
        print(f"   ❌ Authentication failed: {e}")
        print("   ℹ️  Check your API key and secret key in config.yaml")
        return False
    except ConfigurationError as e:
        print(f"   ❌ Configuration error: {e}")
        return False
    except BreezeTraderError as e:
        print(f"   ❌ Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to test connection."""
    print("=" * 60)
    print("  Breeze Trading Client - Connection Test")
    print("=" * 60)
    print()
    
    # Run tests
    config_ok = test_configuration()
    session_ok = test_session()
    
    if not config_ok or not session_ok:
        print()
        print("=" * 60)
        print("❌ Setup Incomplete")
        print("=" * 60)
        print()
        print("Please complete the setup steps above before testing connection.")
        print()
        return 1
    
    connection_ok = test_connection()
    
    print()
    print("=" * 60)
    if connection_ok:
        print("✅ All Tests Passed!")
        print("=" * 60)
        print()
        print("🎯 Your setup is complete and working!")
        print()
        print("Next steps:")
        print("  • Start trading: from breeze_client import BreezeTrader")
        print("  • View examples: scripts/examples/")
        print("  • Read docs: docs/")
        print()
        return 0
    else:
        print("❌ Some Tests Failed")
        print("=" * 60)
        print()
        print("Please fix the issues above and try again.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

