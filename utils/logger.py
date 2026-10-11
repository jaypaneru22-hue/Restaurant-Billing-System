"""Application logging configuration with security sanitization."""
import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config.settings import LOGS_DIR

_SENSITIVE_PATTERNS = [
    re.compile(r"password['\"]?\s*[:=]\s*['\"]?([^'\",\s]+)", re.IGNORECASE),
    re.compile(r"secret['\"]?\s*[:=]\s*['\"]?([^'\",\s]+)", re.IGNORECASE),
    re.compile(r"token['\"]?\s*[:=]\s*['\"]?([^'\",\s]+)", re.IGNORECASE),
]


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive details like passwords from application log streams."""
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern in _SENSITIVE_PATTERNS:
                msg = pattern.sub("password=***REDACTED***", msg)
            record.msg = msg
        return True


def setup_logger(name: str = "TQM_App", log_filename: str = "app.log") -> logging.Logger:
    """Configures and returns a thread-safe rotating file and console logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Rotating file handler (max 2 MB per file, keep 3 backups)
    log_file = LOGS_DIR / log_filename
    file_handler = RotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(console_handler)

    return logger


# Global root logger instance
logger = setup_logger()
