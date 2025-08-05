"""
Centralized logging configuration for PixelFlow Studio.

This module provides a unified logging system that replaces all print() calls
with proper structured logging using loguru.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


class LoggingConfig:
    """Configuration for centralized logging system."""
    
    # Log levels
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    # Log formats
    CONSOLE_FORMAT = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    FILE_FORMAT = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    # File settings
    LOG_DIR = Path("logs")
    LOG_FILE = LOG_DIR / "pixelflow_studio.log"
    MAX_FILE_SIZE = "10 MB"
    RETENTION_DAYS = 30
    
    @classmethod
    def setup_logging(cls, level: str = INFO, enable_console: bool = True) -> None:
        """
        Setup centralized logging system.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_console: Whether to enable console output
        """
        # Create logs directory if it doesn't exist
        cls.LOG_DIR.mkdir(exist_ok=True)
        
        # Remove default handler
        logger.remove()
        
        # Add file handler
        logger.add(
            cls.LOG_FILE,
            format=cls.FILE_FORMAT,
            level=level,
            rotation=cls.MAX_FILE_SIZE,
            retention=f"{cls.RETENTION_DAYS} days",
            compression="zip",
            backtrace=True,
            diagnose=True
        )
        
        # Add console handler if enabled
        if enable_console:
            logger.add(
                lambda msg: print(msg, end=""),
                format=cls.CONSOLE_FORMAT,
                level=level,
                colorize=True,
                backtrace=True,
                diagnose=True
            )
        
        logger.info("Logging system initialized")
    
    @classmethod
    def get_logger(cls, name: str) -> "logger":
        """
        Get a logger instance for a specific module.
        
        Args:
            name: Module name (usually __name__)
            
        Returns:
            Logger instance
        """
        return logger.bind(name=name)


# Global logger instance
app_logger = LoggingConfig.get_logger("pixelflow_studio")


def setup_logging(level: str = LoggingConfig.INFO, enable_console: bool = True) -> None:
    """Convenience function to setup logging."""
    LoggingConfig.setup_logging(level, enable_console)


def get_logger(name: str) -> "logger":
    """Convenience function to get a logger."""
    return LoggingConfig.get_logger(name) 