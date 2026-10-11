"""Security utilities for password hashing and credential verification."""
import hashlib
import hmac
import os
import re

ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """Hashes a plaintext password using PBKDF2-HMAC-SHA256 with a random 16-byte salt."""
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string.")
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{salt.hex()}${key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a plaintext password against a stored salt$hash string using constant-time comparison."""
    if not password or not stored_hash or "$" not in stored_hash:
        return False
    try:
        salt_hex, key_hex = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        computed_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
        return hmac.compare_digest(computed_key, expected_key)
    except Exception:
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validates password strength: minimum 6 characters, at least 1 letter and 1 digit."""
    if not password or len(password.strip()) < 6:
        return False, "Password must be at least 6 characters long."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one alphabetical letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one numeric digit."
    return True, "Password is valid."
