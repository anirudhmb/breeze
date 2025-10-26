#!/usr/bin/env python3
"""
Breeze Trading Client - Daily Login Helper

This script helps you generate and save your daily session token.
Session tokens are valid for 24 hours or until midnight, whichever comes first.
"""

import sys
import os
import webbrowser
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from breeze_client.config_manager import ConfigManager
from breeze_client.session_manager import SessionManager
from breeze_client.exceptions import ConfigurationError


def main():
    """Main function to handle daily login."""
    print("=" * 60)
    print("  Breeze Trading Client - Daily Login")
    print("=" * 60)
    print()
    
    # Load configuration
    try:
        config = ConfigManager()
        credentials = config.get_credentials()
        api_key = credentials['api_key']
        
        if not api_key:
            print("❌ Error: API key not configured!")
            print()
            print("Please configure your API key in config.yaml or .env file")
            print("Example:")
            print("  BREEZE_API_KEY=your_api_key_here")
            print()
            return 1
            
    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e}")
        print()
        print("Please ensure config.yaml exists and is properly configured.")
        print("See config.yaml.example for reference.")
        print()
        return 1
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return 1
    
    # Build login URL
    login_url = f"https://api.icicidirect.com/apiuser/login?api_key={urllib.parse.quote_plus(api_key)}"
    
    print("📋 Step 1: Open ICICI Direct Login")
    print("-" * 60)
    print()
    print("Opening your browser to ICICI Direct login page...")
    print()
    print("If the browser doesn't open automatically, visit:")
    print(f"  {login_url}")
    print()
    
    # Open browser
    try:
        webbrowser.open(login_url)
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print(f"Please manually visit: {login_url}")
    
    print()
    print("📋 Step 2: Login and Copy Session Token")
    print("-" * 60)
    print()
    print("After logging in with your ICICI Direct credentials:")
    print("  1. You will be redirected to your configured redirect URL")
    print("  2. Look at the address bar in your browser")
    print("  3. Find the 'apisession' parameter in the URL")
    print()
    print("Example URL:")
    print("  https://yourapp.com/callback?apisession=123456")
    print("                                            ^^^^^^")
    print("                                   Copy this token")
    print()
    
    # Get session token from user
    while True:
        try:
            session_token = input("Enter the session token: ").strip()
            
            if not session_token:
                print("❌ Session token cannot be empty. Please try again.")
                continue
            
            # Basic validation
            if len(session_token) < 4:
                print("❌ Session token seems too short. Please check and try again.")
                retry = input("Continue anyway? (y/n): ").strip().lower()
                if retry not in ['y', 'yes']:
                    continue
            
            break
            
        except KeyboardInterrupt:
            print()
            print("❌ Login cancelled by user.")
            return 1
    
    # Calculate expiry (midnight today UTC)
    now = datetime.now(timezone.utc)
    expiry = datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=timezone.utc)
    
    # Save session token
    try:
        session_manager = SessionManager()
        session_manager.save_session(session_token, expiry)
        
        print()
        print("=" * 60)
        print("✅ Session token saved successfully!")
        print("=" * 60)
        print()
        print(f"📅 Valid until: {expiry.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Calculate remaining time
        remaining_seconds = (expiry - now).total_seconds()
        remaining_hours = int(remaining_seconds // 3600)
        remaining_minutes = int((remaining_seconds % 3600) // 60)
        
        print(f"⏱️  Time remaining: {remaining_hours}h {remaining_minutes}m")
        print()
        print("🎯 You're ready to trade!")
        print()
        print("Next steps:")
        print("  • Run your trading scripts")
        print("  • Test connection: python scripts/test_connection.py")
        print("  • Check status: python scripts/session_status.py")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print(f"❌ Error saving session token: {e}")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

