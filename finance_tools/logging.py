# finance_tools/logging.py
"""
Standardized logging module for finance-tools.

This module provides a centralized logging system that can be used
across all modules in the finance-tools package.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from loguru import logger

from .config import get_config


class FinanceToolsLogger:
    """Centralized logger for finance-tools."""
    
    def __init__(self, name: str = "finance_tools"):
        """Initialize logger with configuration."""
        self.name = name
        self.config = get_config()
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Set up the logger with proper configuration."""
        # Remove default handler
        logger.remove()
        
        # Get log configuration
        log_config = self.config.get_log_config()
        
        if not self.config.is_feature_enabled("logging"):
            # Disable logging if feature is disabled
            logger.add(sys.stderr, level="CRITICAL")
            return
        
        # Add console handler
        logger.add(
            sys.stderr,
            level=log_config["level"],
            format=log_config["format"],
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # Add file handler if log file is specified
        if log_config["file"]:
            log_file = Path(log_config["file"])
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                log_file,
                level=log_config["level"],
                format=log_config["format"],
                rotation="10 MB",
                retention="30 days",
                compression="zip"
            )
    
    def get_logger(self, name: Optional[str] = None) -> logger:
        """Get a logger instance for a specific module."""
        if name:
            return logger.bind(module=name)
        return logger.bind(module=self.name)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        logger.exception(message, **kwargs)


# Global logger instance
_global_logger = FinanceToolsLogger()


def get_logger(name: Optional[str] = None) -> logger:
    """Get a logger instance."""
    return _global_logger.get_logger(name)


def debug(message: str, **kwargs) -> None:
    """Log debug message."""
    _global_logger.debug(message, **kwargs)


def info(message: str, **kwargs) -> None:
    """Log info message."""
    _global_logger.info(message, **kwargs)


def warning(message: str, **kwargs) -> None:
    """Log warning message."""
    _global_logger.warning(message, **kwargs)


def error(message: str, **kwargs) -> None:
    """Log error message."""
    _global_logger.error(message, **kwargs)


def critical(message: str, **kwargs) -> None:
    """Log critical message."""
    _global_logger.critical(message, **kwargs)


def exception(message: str, **kwargs) -> None:
    """Log exception with traceback."""
    _global_logger.exception(message, **kwargs)


def setup_logging(name: str = "finance_tools") -> None:
    """Set up logging for the application."""
    global _global_logger
    _global_logger = FinanceToolsLogger(name) 