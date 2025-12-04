"""
Logger - Structured logging for IPI-Shield.
"""

import logging
import sys


class IPIShieldLogger:
    """Custom logger with structured output."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.loggers = {}
        self._initialized = True

        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

    def get_logger(self, name: str) -> logging.Logger:
        if name not in self.loggers:
            logger = logging.getLogger(f"ipi-shield.{name}")
            self.loggers[name] = logger
        return self.loggers[name]


_logger_instance = IPIShieldLogger()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return _logger_instance.get_logger(name)
