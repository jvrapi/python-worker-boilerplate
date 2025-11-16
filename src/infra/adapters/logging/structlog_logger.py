"""Structured logging configuration using structlog."""

import inspect
import logging
import sys
from typing import Optional

import structlog
from structlog.processors import CallsiteParameter, CallsiteParameterAdder

from core.ports.logger import Logger
from infra.config import Settings, get_settings


class StructLogLogger(Logger):
    """StructLog implementation of Logger interface."""

    def __init__(
        self,
        name: Optional[str] = None,
        settings: Settings = get_settings(),
    ):
        self._configure_logging(level=settings.log_level, json_logs=settings.json_logs)
        self._logger = structlog.get_logger(name) if name else structlog.get_logger()

    def _event_first_processor(
        self, logger, method_name: str, event_dict: dict
    ) -> dict:
        """
        Custom processor that ensures 'event' is always the first field.

        This processor reorders the event_dict to put 'event' first,
        then maintains the original order of other fields.
        """
        if "event" in event_dict:
            new_dict = {"event": event_dict["event"]}
            for key, value in event_dict.items():
                if key != "event":
                    new_dict[key] = value
            return new_dict
        return event_dict

    def _add_fq_module(self, logger, method_name: str, event_dict: dict) -> dict:
        """
        Add fully qualified module path (module) from the callsite.

        Ignora frames do wrapper e de structlog/logging para pegar o chamador real.
        """
        ignores = [
            "app.infra.adapters.logging.structlog_logger",
            "infra.adapters.logging.structlog_logger",
            "structlog",
            "logging",
        ]
        try:
            for frame_info in inspect.stack():
                mod = frame_info.frame.f_globals.get("__name__")
                if not mod:
                    continue
                if any(mod == ig or mod.startswith(ig + ".") for ig in ignores):
                    continue
                event_dict.setdefault("module", mod)
                break
        except Exception:
            pass
        return event_dict

    def _configure_logging(self, level: str = "INFO", json_logs: bool = True) -> None:
        """
        Configure structured logging with structlog.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            json_logs: Whether to output logs in JSON format
        """
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, level.upper()),
        )

        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            CallsiteParameterAdder(
                parameters=[
                    CallsiteParameter.LINENO,
                ],
                additional_ignores=[
                    "app.adapters.logging.structlog_logger",
                    "adapters.logging.structlog_logger",
                ],
            ),
            self._add_fq_module,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            self._event_first_processor,
        ]

        if json_logs:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._logger.error(message, **kwargs)
