"""
Centralized Loguru configuration for the Voice AI Assistant.

Features
--------
- Colored console logging
- Rotating log files
- Separate error log
- Compression
- Retention policy
- Thread-safe logging
"""

from pathlib import Path
import sys

from loguru import logger


# ==========================================================
# Log Directory
# ==========================================================

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


# ==========================================================
# Remove Default Logger
# ==========================================================

logger.remove()


# ==========================================================
# Console Logger
# ==========================================================

logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    backtrace=True,
    diagnose=True,
    enqueue=True,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
)


# ==========================================================
# Application Log
# ==========================================================

logger.add(
    LOG_DIR / "app.log",
    level="DEBUG",
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    enqueue=True,
    backtrace=True,
    diagnose=True,
    encoding="utf-8",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{module}:{function}:{line} | "
        "{message}"
    ),
)


# ==========================================================
# Error Log
# ==========================================================

logger.add(
    LOG_DIR / "error.log",
    level="ERROR",
    rotation="5 MB",
    retention="30 days",
    compression="zip",
    enqueue=True,
    backtrace=True,
    diagnose=True,
    encoding="utf-8",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{module}:{function}:{line} | "
        "{message}"
    ),
)


# ==========================================================
# Export Logger
# ==========================================================

__all__ = ["logger"]