"""Unit tests for PBKDF2 password hashing and verification."""
import pytest
from utils.security import hash_password, verify_password, validate_password_strength


def test_hash_password_generates_salt_and_hash():
    pw = "SecretPass123"
    hashed = hash_password(pw)
    assert "$" in hashed
    parts = hashed.split("$")
    assert len(parts) == 2
    assert len(parts[0]) == 32  # 16 bytes in hex = 32 chars
    assert len(parts[1]) == 64  # SHA256 in hex = 64 chars


def test_verify_password_success():
    pw = "Admin@123"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True


def test_verify_password_wrong_password_fails():
    pw = "Admin@123"
    hashed = hash_password(pw)
    assert verify_password("WrongPassword!", hashed) is False


def test_verify_password_tampered_hash_fails():
    pw = "Admin@123"
    assert verify_password(pw, "invalid_hash_string") is False
    assert verify_password(pw, "") is False
    assert verify_password("", "some$hash") is False


def test_validate_password_strength():
    ok, _ = validate_password_strength("validPass1")
    assert ok is True

    short_ok, short_msg = validate_password_strength("short")
    assert short_ok is False
    assert "at least 6" in short_msg

    no_digit_ok, _ = validate_password_strength("NoDigitsHere")
    assert no_digit_ok is False

    no_letter_ok, _ = validate_password_strength("12345678")
    assert no_letter_ok is False
