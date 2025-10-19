# finance_tools/config.py
"""
Centralized configuration management for finance-tools.

This module provides a single source of truth for all configuration
settings, reading from environment variables and providing defaults.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class Config:
    """Centralized configuration class for finance-tools."""
    
    def __init__(self):
        """Initialize configuration with environment variables."""
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            # API Keys
            "YAHOO_FINANCE_API_KEY": os.getenv("YAHOO_FINANCE_API_KEY"),
            "NEWS_API_KEY": os.getenv("NEWS_API_KEY"),
            "ALPHA_VANTAGE_API_KEY": os.getenv("ALPHA_VANTAGE_API_KEY"),
            
            # Logging
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "LOG_FILE": os.getenv("LOG_FILE", "finance_tools.log"),
            "LOG_FORMAT": os.getenv("LOG_FORMAT", "{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {message}"),
            
            # Data storage
            "DATA_CACHE_DIR": os.getenv("DATA_CACHE_DIR", "./cache"),
            "DATA_EXPIRY_HOURS": int(os.getenv("DATA_EXPIRY_HOURS", "24")),
            "DATA_FORMAT": os.getenv("DATA_FORMAT", "csv"),

            # Database
            "DATABASE_TYPE": os.getenv("DATABASE_TYPE", "sqlite"),
            "DATABASE_NAME": os.getenv("DATABASE_NAME", "test_finance_tools.db"),
            "DATABASE_HOST": os.getenv("DATABASE_HOST", "localhost"),
            "DATABASE_PORT": os.getenv("DATABASE_PORT", "5432"),
            "DATABASE_USER": os.getenv("DATABASE_USER", "postgres"),
            "DATABASE_PASSWORD": os.getenv("DATABASE_PASSWORD", ""),
            "DATABASE_ECHO": os.getenv("DATABASE_ECHO", "false").lower() == "true",
            
            # Network settings
            "REQUEST_TIMEOUT": int(os.getenv("REQUEST_TIMEOUT", "30")),
            "MAX_RETRIES": int(os.getenv("MAX_RETRIES", "3")),
            "RETRY_DELAY": int(os.getenv("RETRY_DELAY", "1")),
            
            # Rate limiting
            "RATE_LIMIT_REQUESTS": int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            "RATE_LIMIT_PERIOD": int(os.getenv("RATE_LIMIT_PERIOD", "60")),
            
            # Default settings
            "DEFAULT_PERIOD": os.getenv("DEFAULT_PERIOD", "1y"),
            "DEFAULT_INTERVAL": os.getenv("DEFAULT_INTERVAL", "1d"),
            "DEFAULT_CURRENCY": os.getenv("DEFAULT_CURRENCY", "USD"),
            
            # Feature flags
            "ENABLE_CACHING": os.getenv("ENABLE_CACHING", "true").lower() == "true",
            "ENABLE_LOGGING": os.getenv("ENABLE_LOGGING", "true").lower() == "true",
            "ENABLE_METRICS": os.getenv("ENABLE_METRICS", "true").lower() == "true",
            "ENABLE_DEBUG": os.getenv("ENABLE_DEBUG", "false").lower() == "true",
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service."""
        key_map = {
            "yahoo": "YAHOO_FINANCE_API_KEY",
            "news": "NEWS_API_KEY",
            "alpha_vantage": "ALPHA_VANTAGE_API_KEY",
        }
        return self.get(key_map.get(service.lower()))
    
    def get_cache_dir(self) -> Path:
        """Get cache directory path."""
        cache_dir = Path(self.get("DATA_CACHE_DIR"))
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def get_log_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            "level": self.get("LOG_LEVEL"),
            "file": self.get("LOG_FILE"),
            "format": self.get("LOG_FORMAT"),
            "enabled": self.get("ENABLE_LOGGING"),
        }

    def get_database_url(self) -> str:
        """Build and return a SQLAlchemy database URL from config values.

        Supports:
        - sqlite (default): uses a file path in the current working directory unless an absolute path is provided
        - postgres: builds a standard postgresql URL
        """
        db_type = (self.get("DATABASE_TYPE") or "sqlite").lower()
        if db_type == "sqlite":
            db_name = self.get("DATABASE_NAME") or "test_finance_tools.db"





            if db_name in {":memory:", "memory"}:
                return "sqlite+pysqlite:///:memory:"
            # If absolute path provided, use as-is; else place in project root
            db_path = Path(db_name)
            if not db_path.is_absolute():
                db_path = Path.cwd() / db_path
            return f"sqlite:///{db_path.as_posix()}"

        if db_type in {"postgres", "postgresql"}:
            user = self.get("DATABASE_USER") or "postgres"
            password = self.get("DATABASE_PASSWORD") or ""
            host = self.get("DATABASE_HOST") or "localhost"
            port = self.get("DATABASE_PORT") or "5432"
            name = self.get("DATABASE_NAME") or "finance_tools"
            auth = f"{user}:{password}@" if password else f"{user}@"
            return f"postgresql+psycopg2://{auth}{host}:{port}/{name}"

        # Fallback to treating it as a full URL string if provided
        return str(self.get("DATABASE_TYPE"))
    
    def get_network_config(self) -> Dict[str, Any]:
        """Get network configuration."""
        return {
            "timeout": self.get("REQUEST_TIMEOUT"),
            "max_retries": self.get("MAX_RETRIES"),
            "retry_delay": self.get("RETRY_DELAY"),
        }
    
    def get_rate_limit_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration."""
        return {
            "requests": self.get("RATE_LIMIT_REQUESTS"),
            "period": self.get("RATE_LIMIT_PERIOD"),
        }
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        feature_map = {
            "caching": "ENABLE_CACHING",
            "logging": "ENABLE_LOGGING",
            "metrics": "ENABLE_METRICS",
            "debug": "ENABLE_DEBUG",
        }
        return self.get(feature_map.get(feature.lower(), ""), False)
    
    def reload(self) -> None:
        """Reload configuration from environment variables."""
        self._config = self._load_config()


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def reload_config() -> None:
    """Reload the global configuration."""
    config.reload() 