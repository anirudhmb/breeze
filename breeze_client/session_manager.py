"""
Breeze Trading Client - Session Manager

Handles session token persistence and validation.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from .exceptions import SessionExpiredError, SessionNotFoundError


class SessionManager:
    """
    Manages session token persistence and validation.
    
    Features:
    - Save session token with expiry time
    - Load session token from file
    - Validate session token is not expired
    - Calculate time until expiry
    - Secure file permissions (read/write for owner only)
    
    Session File Format:
        <session_token>|<expiry_timestamp_iso8601>
        
    Example:
        58593|2025-10-26T00:00:00Z
    """
    
    SESSION_FILE = '.session_token'
    
    def __init__(self, session_file: str = SESSION_FILE):
        """
        Initialize SessionManager.
        
        Args:
            session_file: Path to session token file (default: .session_token)
        """
        self.session_file = Path(session_file)
        self._session_token: Optional[str] = None
        self._expiry: Optional[datetime] = None
        
        # Load existing session if available
        if self.session_file.exists():
            try:
                self._load_session()
            except (SessionExpiredError, SessionNotFoundError):
                # Silently ignore if session is expired or invalid
                pass
    
    def save_session(self, session_token: str, expiry: Optional[datetime] = None) -> None:
        """
        Save session token to file with expiry time.
        
        Args:
            session_token: Session token from API
            expiry: Expiry datetime (defaults to midnight today UTC)
            
        Note:
            ICICI Breeze session tokens expire at midnight or after 24 hours,
            whichever comes first.
        """
        if expiry is None:
            # Default: midnight today UTC
            now = datetime.now(timezone.utc)
            expiry = datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=timezone.utc)
        
        # Ensure expiry has timezone info
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        
        # Save to file
        content = f"{session_token}|{expiry.isoformat()}\n"
        
        try:
            # Write to file
            self.session_file.write_text(content)
            
            # Set secure file permissions (owner read/write only)
            # 0o600 = -rw------- (owner can read/write, others have no access)
            os.chmod(self.session_file, 0o600)
            
            # Update in-memory cache
            self._session_token = session_token
            self._expiry = expiry
            
        except Exception as e:
            raise IOError(f"Failed to save session token: {e}")
    
    def _load_session(self) -> None:
        """
        Load session token from file.
        
        Raises:
            SessionNotFoundError: If session file doesn't exist
            SessionExpiredError: If session has expired
        """
        if not self.session_file.exists():
            raise SessionNotFoundError()
        
        try:
            content = self.session_file.read_text().strip()
            
            if '|' not in content:
                # Old format or corrupted file
                self.clear_session()
                raise SessionNotFoundError()
            
            token, expiry_str = content.split('|', 1)
            expiry = datetime.fromisoformat(expiry_str)
            
            # Ensure timezone awareness
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            
            # Check if expired
            now = datetime.now(timezone.utc)
            if now >= expiry:
                self.clear_session()
                raise SessionExpiredError(
                    f"Session expired at {expiry.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                    "Please run: python scripts/login.py"
                )
            
            # Update in-memory cache
            self._session_token = token
            self._expiry = expiry
            
        except (ValueError, OSError) as e:
            # Corrupted session file
            self.clear_session()
            raise SessionNotFoundError()
    
    def load_session(self) -> Tuple[str, datetime]:
        """
        Load and return session token and expiry.
        
        Returns:
            Tuple of (session_token, expiry_datetime)
            
        Raises:
            SessionNotFoundError: If no session file exists
            SessionExpiredError: If session has expired
        """
        self._load_session()
        return self._session_token, self._expiry
    
    def get_session_token(self) -> str:
        """
        Get current session token.
        
        Returns:
            Session token string
            
        Raises:
            SessionNotFoundError: If no session exists
            SessionExpiredError: If session has expired
        """
        if self._session_token is None:
            self._load_session()
        
        # Double-check not expired
        if not self.is_valid():
            raise SessionExpiredError()
        
        return self._session_token
    
    def is_valid(self) -> bool:
        """
        Check if current session is valid (exists and not expired).
        
        Returns:
            True if session is valid, False otherwise
        """
        if self._session_token is None or self._expiry is None:
            if not self.session_file.exists():
                return False
            try:
                self._load_session()
            except (SessionExpiredError, SessionNotFoundError):
                return False
        
        # Check expiry
        now = datetime.now(timezone.utc)
        return now < self._expiry
    
    def time_until_expiry(self) -> Optional[float]:
        """
        Get time remaining until session expires.
        
        Returns:
            Seconds until expiry, or None if no valid session
        """
        if not self.is_valid():
            return None
        
        now = datetime.now(timezone.utc)
        remaining = (self._expiry - now).total_seconds()
        return max(0, remaining)
    
    def get_expiry_time(self) -> Optional[datetime]:
        """
        Get session expiry time.
        
        Returns:
            Expiry datetime or None if no session
        """
        if self._expiry is None and self.session_file.exists():
            try:
                self._load_session()
            except (SessionExpiredError, SessionNotFoundError):
                return None
        
        return self._expiry
    
    def clear_session(self) -> None:
        """
        Delete session file and clear cached session.
        """
        if self.session_file.exists():
            self.session_file.unlink()
        
        self._session_token = None
        self._expiry = None
    
    def warn_if_expiring_soon(self, warning_minutes: int = 60) -> Optional[str]:
        """
        Check if session is expiring soon and return warning message.
        
        Args:
            warning_minutes: Warn if expiring within this many minutes
            
        Returns:
            Warning message if expiring soon, None otherwise
        """
        remaining_seconds = self.time_until_expiry()
        
        if remaining_seconds is None:
            return None
        
        remaining_minutes = remaining_seconds / 60
        
        if remaining_minutes < warning_minutes:
            hours = int(remaining_minutes // 60)
            minutes = int(remaining_minutes % 60)
            
            time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            
            return (
                f"⚠️  Session expires in {time_str}\n"
                f"Run 'python scripts/login.py' to refresh your session."
            )
        
        return None
    
    def __repr__(self) -> str:
        """String representation of SessionManager."""
        if self.is_valid():
            remaining = self.time_until_expiry()
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            return f"SessionManager(valid=True, expires_in={hours}h {minutes}m)"
        else:
            return "SessionManager(valid=False)"

