"""Unit tests for logging utilities and sensitive data redaction."""
import logging
from utils.logger import setup_logger, SensitiveDataFilter


def test_logger_initialization():
    log = setup_logger("test_logger", "test_app.log")
    assert log is not None
    assert isinstance(log, logging.Logger)


def test_sensitive_data_filter_redacts_password():
    flt = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="User login attempt with password='secretPassword123' failed",
        args=(),
        exc_info=None
    )
    flt.filter(record)
    assert "secretPassword123" not in record.msg
    assert "***REDACTED***" in record.msg
