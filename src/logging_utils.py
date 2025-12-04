from __future__ import annotations

import logging
import sys
from typing import Optional


class _MaxLevelFilter(logging.Filter):
    def __init__(self, max_level: int):
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self.max_level


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger("valid_builder")
    logger.handlers.clear()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.propagate = False

    info_handler = logging.StreamHandler(sys.stdout)
    info_handler.setLevel(logging.DEBUG)
    info_handler.addFilter(_MaxLevelFilter(logging.INFO))
    logger.addHandler(info_handler)

    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.WARNING)
    logger.addHandler(error_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    return logger


class SummaryHandler(logging.Handler):
    """Track warning and error counts for a run without emitting output."""

    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.warning_count = 0
        self.error_count = 0

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - trivial
        if record.levelno >= logging.ERROR:
            self.error_count += 1
        elif record.levelno >= logging.WARNING:
            self.warning_count += 1


def attach_summary_handler(logger: logging.Logger) -> SummaryHandler:
    """Attach a summary counter handler to the provided logger."""

    handler = SummaryHandler()
    logger.addHandler(handler)
    return handler


def log_final_summary(
    logger: logging.Logger,
    summary_handler: SummaryHandler | None,
    *,
    rule_count: int | None,
    success: bool,
) -> None:
    """Log a final summary line with counts and overall status."""

    warnings = summary_handler.warning_count if summary_handler else 0
    errors = summary_handler.error_count if summary_handler else 0

    if success:
        count_text = f"Completed successfully. Extracted {rule_count or 0} rules."
        warning_text = f"{warnings} warning(s)." if warnings else "No warnings."
        logger.info("%s %s", count_text, warning_text)
    else:
        logger.error("Failed with %d error(s). See messages above.", errors or 1)
