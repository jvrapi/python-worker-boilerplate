"""Logging infrastructure module."""

from .structlog_logger import StructLogLogger

logger = StructLogLogger()

__all__ = ["logger", "StructLogLogger"]
