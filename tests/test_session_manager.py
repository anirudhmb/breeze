"""
Tests for SessionManager
"""

import os
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from breeze_client.session_manager import SessionManager
from breeze_client.exceptions import SessionExpiredError, SessionNotFoundError


@pytest.fixture
def temp_session_file(tmp_path, monkeypatch):
    """Create a temporary session file for testing."""
    session_file = tmp_path / ".test_session"
    monkeypatch.chdir(tmp_path)
    return session_file


def test_save_and_load_session(temp_session_file):
    """Test saving and loading session."""
    manager = SessionManager(str(temp_session_file))
    
    token = "test_token_123"
    expiry = datetime.now(timezone.utc) + timedelta(hours=12)
    
    manager.save_session(token, expiry)
    
    loaded_token, loaded_expiry = manager.load_session()
    assert loaded_token == token
    assert loaded_expiry.replace(microsecond=0) == expiry.replace(microsecond=0)


def test_save_session_without_expiry(temp_session_file):
    """Test saving session without specifying expiry."""
    manager = SessionManager(str(temp_session_file))
    
    token = "test_token_456"
    manager.save_session(token)
    
    loaded_token, loaded_expiry = manager.load_session()
    assert loaded_token == token
    assert loaded_expiry is not None


def test_get_session_token(temp_session_file):
    """Test getting current session token."""
    manager = SessionManager(str(temp_session_file))
    
    token = "test_token_789"
    expiry = datetime.now(timezone.utc) + timedelta(hours=6)
    manager.save_session(token, expiry)
    
    assert manager.get_session_token() == token


def test_is_valid_with_valid_session(temp_session_file):
    """Test is_valid returns True for valid session."""
    manager = SessionManager(str(temp_session_file))
    
    token = "valid_token"
    expiry = datetime.now(timezone.utc) + timedelta(hours=3)
    manager.save_session(token, expiry)
    
    assert manager.is_valid() is True


def test_is_valid_with_expired_session(temp_session_file):
    """Test is_valid returns False for expired session."""
    manager = SessionManager(str(temp_session_file))
    
    token = "expired_token"
    expiry = datetime.now(timezone.utc) - timedelta(hours=1)
    manager.save_session(token, expiry)
    
    assert manager.is_valid() is False


def test_is_valid_no_session(temp_session_file):
    """Test is_valid returns False when no session exists."""
    manager = SessionManager(str(temp_session_file))
    assert manager.is_valid() is False


def test_load_session_not_found(temp_session_file):
    """Test error when session file doesn't exist."""
    manager = SessionManager(str(temp_session_file))
    
    with pytest.raises(SessionNotFoundError):
        manager.load_session()


def test_load_expired_session(temp_session_file):
    """Test error when loading expired session."""
    manager = SessionManager(str(temp_session_file))
    
    token = "expired_token"
    expiry = datetime.now(timezone.utc) - timedelta(hours=2)
    manager.save_session(token, expiry)
    
    # Create new manager to force reload
    manager2 = SessionManager(str(temp_session_file))
    
    with pytest.raises(SessionExpiredError):
        manager2.load_session()


def test_time_until_expiry(temp_session_file):
    """Test calculating time until expiry."""
    manager = SessionManager(str(temp_session_file))
    
    token = "test_token"
    expiry = datetime.now(timezone.utc) + timedelta(hours=2)
    manager.save_session(token, expiry)
    
    remaining = manager.time_until_expiry()
    assert remaining is not None
    assert 7000 < remaining < 7300  # ~2 hours in seconds (with some tolerance)


def test_time_until_expiry_no_session(temp_session_file):
    """Test time_until_expiry returns None when no session."""
    manager = SessionManager(str(temp_session_file))
    assert manager.time_until_expiry() is None


def test_get_expiry_time(temp_session_file):
    """Test getting expiry time."""
    manager = SessionManager(str(temp_session_file))
    
    token = "test_token"
    expiry = datetime.now(timezone.utc) + timedelta(hours=5)
    manager.save_session(token, expiry)
    
    retrieved_expiry = manager.get_expiry_time()
    assert retrieved_expiry is not None
    assert retrieved_expiry.replace(microsecond=0) == expiry.replace(microsecond=0)


def test_clear_session(temp_session_file):
    """Test clearing session."""
    manager = SessionManager(str(temp_session_file))
    
    token = "test_token"
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    manager.save_session(token, expiry)
    
    assert manager.is_valid() is True
    
    manager.clear_session()
    
    assert manager.is_valid() is False
    assert not temp_session_file.exists()


def test_warn_if_expiring_soon(temp_session_file):
    """Test warning when session is expiring soon."""
    manager = SessionManager(str(temp_session_file))
    
    token = "test_token"
    expiry = datetime.now(timezone.utc) + timedelta(minutes=30)
    manager.save_session(token, expiry)
    
    warning = manager.warn_if_expiring_soon(warning_minutes=60)
    assert warning is not None
    assert "expires in" in warning.lower()


def test_no_warning_when_not_expiring_soon(temp_session_file):
    """Test no warning when session not expiring soon."""
    manager = SessionManager(str(temp_session_file))
    
    token = "test_token"
    expiry = datetime.now(timezone.utc) + timedelta(hours=10)
    manager.save_session(token, expiry)
    
    warning = manager.warn_if_expiring_soon(warning_minutes=60)
    assert warning is None


def test_file_permissions(temp_session_file):
    """Test that session file has secure permissions."""
    manager = SessionManager(str(temp_session_file))
    
    token = "test_token"
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    manager.save_session(token, expiry)
    
    # Check file permissions (owner read/write only = 0o600)
    stat_info = os.stat(temp_session_file)
    permissions = stat_info.st_mode & 0o777
    assert permissions == 0o600


def test_corrupted_session_file(temp_session_file):
    """Test handling of corrupted session file."""
    # Create corrupted session file
    temp_session_file.write_text("corrupted data without separator")
    
    manager = SessionManager(str(temp_session_file))
    
    with pytest.raises(SessionNotFoundError):
        manager.load_session()


def test_repr(temp_session_file):
    """Test string representation."""
    manager = SessionManager(str(temp_session_file))
    
    # No session
    repr_str = repr(manager)
    assert "SessionManager" in repr_str
    assert "valid=False" in repr_str
    
    # With valid session
    token = "test_token"
    expiry = datetime.now(timezone.utc) + timedelta(hours=2)
    manager.save_session(token, expiry)
    
    repr_str = repr(manager)
    assert "SessionManager" in repr_str
    assert "valid=True" in repr_str
    assert "expires_in" in repr_str


def test_auto_load_on_init(temp_session_file):
    """Test that session is auto-loaded on initialization if exists."""
    # Save a session
    manager1 = SessionManager(str(temp_session_file))
    token = "auto_load_token"
    expiry = datetime.now(timezone.utc) + timedelta(hours=4)
    manager1.save_session(token, expiry)
    
    # Create new manager - should auto-load
    manager2 = SessionManager(str(temp_session_file))
    assert manager2.is_valid() is True
    assert manager2.get_session_token() == token

