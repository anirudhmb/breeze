"""
Tests for ConfigManager
"""

import os
import pytest
from pathlib import Path
from breeze_client.config_manager import ConfigManager
from breeze_client.exceptions import ConfigurationError


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_content = """
credentials:
  api_key: "test_api_key"
  secret_key: "test_secret_key"
  user_id: "TEST123"

trading:
  default_exchange: "NSE"
  default_product: "cash"
  confirm_orders: false

session:
  auto_save: true
  check_validity: true

notifications:
  show_order_confirmations: true

advanced:
  rate_limit_enabled: true
  max_retries: 3
"""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def temp_env_file(tmp_path, monkeypatch):
    """Create a temporary .env file and set environment variables."""
    env_content = """
BREEZE_API_KEY=env_api_key
BREEZE_SECRET_KEY=env_secret_key
"""
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    
    # Change to temp directory
    monkeypatch.chdir(tmp_path)
    
    return env_file


@pytest.fixture
def config_with_env_vars(tmp_path):
    """Create config file that references environment variables."""
    config_content = """
credentials:
  api_key: "${BREEZE_API_KEY}"
  secret_key: "${BREEZE_SECRET_KEY}"
  user_id: "TEST123"

trading:
  default_exchange: "NSE"
  default_product: "cash"
"""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(config_content)
    return config_file


def test_load_config_success(temp_config_file):
    """Test successful config loading."""
    config = ConfigManager(str(temp_config_file))
    assert config.get('credentials.api_key') == 'test_api_key'
    assert config.get('trading.default_exchange') == 'NSE'


def test_load_config_file_not_found():
    """Test error when config file doesn't exist."""
    with pytest.raises(ConfigurationError) as exc_info:
        ConfigManager('nonexistent_config.yaml')
    assert "not found" in str(exc_info.value)


def test_config_get_with_dot_notation(temp_config_file):
    """Test getting config values with dot notation."""
    config = ConfigManager(str(temp_config_file))
    assert config.get('credentials.api_key') == 'test_api_key'
    assert config.get('credentials.secret_key') == 'test_secret_key'
    assert config.get('trading.default_exchange') == 'NSE'


def test_config_get_with_default(temp_config_file):
    """Test getting config with default value."""
    config = ConfigManager(str(temp_config_file))
    assert config.get('nonexistent.key', 'default') == 'default'
    assert config.get('trading.nonexistent', 'FOO') == 'FOO'


def test_config_get_credentials(temp_config_file):
    """Test getting credentials."""
    config = ConfigManager(str(temp_config_file))
    creds = config.get_credentials()
    assert creds['api_key'] == 'test_api_key'
    assert creds['secret_key'] == 'test_secret_key'
    assert creds['user_id'] == 'TEST123'


def test_config_dict_access(temp_config_file):
    """Test dictionary-style access to config."""
    config = ConfigManager(str(temp_config_file))
    assert config['credentials']['api_key'] == 'test_api_key'
    assert config['trading']['default_exchange'] == 'NSE'


def test_config_dict_access_invalid_key(temp_config_file):
    """Test dictionary access with invalid key."""
    config = ConfigManager(str(temp_config_file))
    with pytest.raises(KeyError):
        _ = config['nonexistent_key']


def test_env_var_substitution(config_with_env_vars, monkeypatch):
    """Test environment variable substitution."""
    # Set environment variables
    monkeypatch.setenv('BREEZE_API_KEY', 'env_api_key_value')
    monkeypatch.setenv('BREEZE_SECRET_KEY', 'env_secret_key_value')
    
    config = ConfigManager(str(config_with_env_vars))
    assert config.get('credentials.api_key') == 'env_api_key_value'
    assert config.get('credentials.secret_key') == 'env_secret_key_value'


def test_env_var_not_set(config_with_env_vars, monkeypatch):
    """Test error when environment variable is not set."""
    # Unset the env var
    monkeypatch.delenv('BREEZE_API_KEY', raising=False)
    
    with pytest.raises(ConfigurationError) as exc_info:
        ConfigManager(str(config_with_env_vars))
    assert "BREEZE_API_KEY" in str(exc_info.value)
    assert "not set" in str(exc_info.value)


def test_validate_required_fields(tmp_path):
    """Test validation of required fields."""
    # Missing required field
    config_content = """
credentials:
  api_key: "test_key"
  # secret_key missing

trading:
  default_exchange: "NSE"
  default_product: "cash"
"""
    config_file = tmp_path / "invalid_config.yaml"
    config_file.write_text(config_content)
    
    with pytest.raises(ConfigurationError) as exc_info:
        ConfigManager(str(config_file))
    assert "required" in str(exc_info.value).lower()


def test_config_property(temp_config_file):
    """Test accessing full config via property."""
    config_manager = ConfigManager(str(temp_config_file))
    full_config = config_manager.config
    assert isinstance(full_config, dict)
    assert 'credentials' in full_config
    assert 'trading' in full_config


def test_invalid_yaml(tmp_path):
    """Test error with invalid YAML syntax."""
    config_content = """
credentials:
  api_key: "test"
  invalid yaml: [unclosed bracket
"""
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text(config_content)
    
    with pytest.raises(ConfigurationError) as exc_info:
        ConfigManager(str(config_file))
    assert "Invalid YAML" in str(exc_info.value)


def test_repr(temp_config_file):
    """Test string representation."""
    config = ConfigManager(str(temp_config_file))
    repr_str = repr(config)
    assert "ConfigManager" in repr_str
    assert str(temp_config_file) in repr_str

