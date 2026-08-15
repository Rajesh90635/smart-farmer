"""
Structured logging setup.

Hard rule (Step 12 of the spec): this configuration must never be given
passwords, JWT tokens, API keys, personal sensitive data, full image bytes,
or payment credentials to log. Loggers throughout the app log *identifiers*
(ids, correlation ids, status codes), never raw payloads containing the
above. Code review should treat a raw-payload log line as a bug, not a
style choice.
"""
import logging
import sys
from logging import Logger

_LOG_FORMAT = (
    "%(asctime)s level=%(levelname)s logger=%(name)s "
    "correlation_id=%(correlation_id)s message=%(message)s"
)


class _CorrelationIdFilter(logging.Filter):
    """Ensures every log record has a correlation_id field, defaulting to
    '-' when one hasn't been bound (e.g. outside a request context)."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "-"
        return True


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    handler.addFilter(_CorrelationIdFilter())

    root.handlers.clear()
    root.addHandler(handler)


def get_logger(name: str) -> Logger:
    return logging.getLogger(name)
