"""
Logging utilities for AutoTrade AI system
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme
from config import DirectoryConfig, settings


# Custom theme for rich console
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green bold",
    "trade": "magenta bold",
    "ai": "blue bold",
})

console = Console(theme=custom_theme)


class AutoTradeLogger:
    """Custom logger for AutoTrade system"""

    def __init__(self, name: str = "AutoTrade", log_to_file: bool = True):
        self.name = name
        self.logger = logging.getLogger(name)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Set log level
        if settings:
            log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
        else:
            log_level = logging.INFO

        self.logger.setLevel(log_level)

        # Rich console handler
        console_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            show_time=True,
            show_path=False,
        )
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter("%(message)s", datefmt="[%X]")
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler
        if log_to_file:
            DirectoryConfig.create_directories()
            log_file = DirectoryConfig.LOGS_DIR / f"autotrade_{datetime.now().strftime('%Y%m%d')}.log"

            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)

    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)

    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)

    def success(self, message: str):
        """Log success message (custom)"""
        console.print(f"[success]OK[/success] {message}")
        self.logger.info(f"SUCCESS: {message}")

    def trade(self, message: str):
        """Log trading action"""
        console.print(f"[trade]TRADE:[/trade] {message}")
        self.logger.info(f"TRADE: {message}")

    def ai_decision(self, message: str):
        """Log AI decision"""
        console.print(f"[ai]AI:[/ai] {message}")
        self.logger.info(f"AI: {message}")

    def separator(self):
        """Print separator line"""
        console.print("-" * 80)


# Global logger instance
logger = AutoTradeLogger()


# Convenience functions
def log_info(message: str):
    logger.info(message)


def log_warning(message: str):
    logger.warning(message)


def log_error(message: str):
    logger.error(message)


def log_success(message: str):
    logger.success(message)


def log_trade(message: str):
    logger.trade(message)


def log_ai(message: str):
    logger.ai_decision(message)


def log_separator():
    logger.separator()


__all__ = [
    "AutoTradeLogger",
    "logger",
    "console",
    "log_info",
    "log_warning",
    "log_error",
    "log_success",
    "log_trade",
    "log_ai",
    "log_separator",
]
