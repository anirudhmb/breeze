#!/usr/bin/env python3
"""
Breeze Trading Client - Session Status Checker

Check the status of your current session token.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from breeze_client.session_manager import SessionManager
from breeze_client.config_manager import ConfigManager
from breeze_client.exceptions import SessionExpiredError, SessionNotFoundError, ConfigurationError


def format_time_remaining(seconds):
    """Format remaining time in human-readable format."""
    if seconds <= 0:
        return "Expired"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def main():
    """Main function to check session status."""
    print("=" * 60)
    print("  Breeze Trading Client - Session Status")
    print("=" * 60)
    print()
    
    # Check configuration
    try:
        config = ConfigManager()
        credentials = config.get_credentials()
        api_key = credentials['api_key']
        
        print("✅ Configuration:")
        print(f"   API Key: {'*' * (len(api_key) - 4)}{api_key[-4:] if api_key else 'Not set'}")
        print(f"   Secret Key: {'*' * 8} (configured)" if credentials['secret_key'] else "   Secret Key: Not set")
        print()
        
    except ConfigurationError as e:
        print(f"❌ Configuration Error:")
        print(f"   {e}")
        print()
        return 1
    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
        print()
        return 1
    
    # Check session status
    session_manager = SessionManager()
    
    try:
        is_valid = session_manager.is_valid()
        
        if is_valid:
            print("✅ Session Status: VALID")
            print()
            
            # Get expiry information
            expiry_time = session_manager.get_expiry_time()
            remaining_seconds = session_manager.time_until_expiry()
            
            if expiry_time:
                print(f"   Expires at: {expiry_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                print(f"   Time remaining: {format_time_remaining(remaining_seconds)}")
                print()
                
                # Warn if expiring soon
                if remaining_seconds < 3600:  # Less than 1 hour
                    print("⚠️  WARNING: Session expires in less than 1 hour!")
                    print("   Run 'python scripts/login.py' to refresh your session.")
                    print()
            
            print("🎯 You're ready to trade!")
            print()
            
        else:
            print("❌ Session Status: INVALID or EXPIRED")
            print()
            print("📋 Action Required:")
            print("   Run 'python scripts/login.py' to generate a new session.")
            print()
            return 1
            
    except SessionNotFoundError:
        print("❌ Session Status: NOT FOUND")
        print()
        print("📋 First Time Setup:")
        print("   Run 'python scripts/login.py' to generate your session token.")
        print("   You'll need to do this once per day.")
        print()
        return 1
        
    except SessionExpiredError:
        print("❌ Session Status: EXPIRED")
        print()
        print("📋 Action Required:")
        print("   Run 'python scripts/login.py' to generate a new session.")
        print("   Sessions expire at midnight or after 24 hours.")
        print()
        return 1
        
    except Exception as e:
        print(f"❌ Error checking session status: {e}")
        print()
        return 1
    
    # Additional system info
    print("=" * 60)
    print("  System Information")
    print("=" * 60)
    print()
    print(f"   Current Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"   Config File: config.yaml")
    print(f"   Session File: .session_token")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

