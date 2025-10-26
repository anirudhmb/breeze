"""
Breeze Trading Client - Configuration Manager

Handles loading and validating configuration from YAML files and environment variables.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

from .exceptions import ConfigurationError


class ConfigManager:
    """
    Manages configuration from YAML file with environment variable overrides.
    
    Features:
    - Load config from YAML file
    - Support environment variable substitution (${VAR_NAME})
    - Validate required fields
    - Provide easy access to config values with dot notation
    
    Usage:
        config = ConfigManager('config.yaml')
        api_key = config.get('credentials.api_key')
        exchange = config.get('trading.default_exchange', 'NSE')
    """
    
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialize ConfigManager and load configuration.
        
        Args:
            config_path: Path to config.yaml file
            
        Raises:
            ConfigurationError: If config file not found or invalid
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        
        # Load environment variables from .env file if it exists
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)
        
        # Load configuration
        self._load_config()
        self._validate_config()
    
    def _load_config(self) -> None:
        """
        Load configuration from YAML file.
        
        Raises:
            ConfigurationError: If config file not found or invalid YAML
        """
        if not self.config_path.exists():
            raise ConfigurationError(
                f"Config file not found: {self.config_path}\n"
                f"Please copy config.yaml.example to config.yaml and update it with your credentials."
            )
        
        try:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML in config file: {self.config_path}\n{str(e)}",
                e
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to read config file: {self.config_path}\n{str(e)}",
                e
            )
        
        # Resolve environment variables in config values
        self._config = self._resolve_env_vars(self._config)
    
    def _resolve_env_vars(self, obj: Any) -> Any:
        """
        Recursively resolve environment variables in config values.
        
        Supports ${VAR_NAME} syntax.
        
        Args:
            obj: Config value (dict, list, str, etc.)
            
        Returns:
            Resolved value with env vars substituted
        """
        if isinstance(obj, dict):
            return {k: self._resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._substitute_env_var(obj)
        else:
            return obj
    
    def _substitute_env_var(self, value: str) -> str:
        """
        Substitute environment variables in a string.
        
        Args:
            value: String that may contain ${VAR_NAME}
            
        Returns:
            String with env vars substituted
            
        Raises:
            ConfigurationError: If referenced env var is not set
        """
        def replacer(match):
            var_name = match.group(1)
            env_value = os.getenv(var_name)
            
            if env_value is None:
                raise ConfigurationError(
                    f"Environment variable '${{{var_name}}}' is not set.\n"
                    f"Please set it in your .env file or environment.\n"
                    f"Example: {var_name}=your_value_here"
                )
            
            return env_value
        
        return self.ENV_VAR_PATTERN.sub(replacer, value)
    
    def _validate_config(self) -> None:
        """
        Validate that required configuration fields are present.
        
        Raises:
            ConfigurationError: If required fields are missing
        """
        required_fields = [
            ('credentials', 'api_key'),
            ('credentials', 'secret_key'),
            ('trading', 'default_exchange'),
            ('trading', 'default_product'),
        ]
        
        missing_fields = []
        
        for *path, key in required_fields:
            current = self._config
            field_path = '.'.join(path + [key])
            
            # Navigate to the nested field
            for part in path:
                if not isinstance(current, dict) or part not in current:
                    missing_fields.append(field_path)
                    break
                current = current[part]
            else:
                # Check final key
                if not isinstance(current, dict) or key not in current or not current[key]:
                    missing_fields.append(field_path)
        
        if missing_fields:
            raise ConfigurationError(
                f"Missing required configuration fields:\n" +
                "\n".join(f"  - {field}" for field in missing_fields) +
                f"\n\nPlease update your {self.config_path} file."
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'credentials.api_key')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Examples:
            >>> config.get('credentials.api_key')
            'your_api_key'
            >>> config.get('trading.default_exchange')
            'NSE'
            >>> config.get('nonexistent.key', 'default_value')
            'default_value'
        """
        keys = key.split('.')
        current = self._config
        
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return default
            current = current[k]
        
        return current
    
    def get_credentials(self) -> Dict[str, str]:
        """
        Get API credentials.
        
        Returns:
            dict: API credentials with keys 'api_key', 'secret_key', 'user_id'
            
        Raises:
            ConfigurationError: If credentials are missing
        """
        credentials = self.get('credentials', {})
        
        return {
            'api_key': credentials.get('api_key', ''),
            'secret_key': credentials.get('secret_key', ''),
            'user_id': credentials.get('user_id', ''),
        }
    
    @property
    def config(self) -> Dict[str, Any]:
        """
        Get the complete configuration dictionary.
        
        Returns:
            Complete config as dict
        """
        return self._config
    
    def __getitem__(self, key: str) -> Any:
        """
        Allow dict-style access to config.
        
        Args:
            key: Top-level config key
            
        Returns:
            Config value
            
        Raises:
            KeyError: If key not found
        """
        if key not in self._config:
            raise KeyError(f"Config key not found: {key}")
        return self._config[key]
    
    def __repr__(self) -> str:
        """String representation of ConfigManager."""
        return f"ConfigManager(config_path='{self.config_path}')"

