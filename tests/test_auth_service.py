"""Unit tests for AuthService and user sessions."""
import pytest
from database.db import DatabaseManager
from database.migrations import initialize_database
from repositories.user_repository import UserRepository
from services.auth_service import AuthService


@pytest.fixture
def auth_fixture(tmp_path):
    db_file = tmp_path / "auth_test.db"
    db_manager = DatabaseManager(db_file)
    initialize_database(db_manager)
    repo = UserRepository(db_manager)
    service = AuthService(repo)
    return service, repo


def test_auth_login_success_admin(auth_fixture):
    service, _ = auth_fixture
    ok, msg, user = service.login("admin", "Admin@123")
    assert ok is True
    assert msg == "Login successful."
    assert user is not None
    assert user.username == "admin"
    assert service.is_authenticated() is True
    assert service.is_admin() is True
    assert service.current_user.id == user.id


def test_auth_login_success_cashier(auth_fixture):
    service, _ = auth_fixture
    ok, msg, user = service.login("cashier1", "Cashier@123")
    assert ok is True
    assert user.role == "CASHIER"
    assert service.is_admin() is False


def test_auth_login_wrong_password(auth_fixture):
    service, _ = auth_fixture
    ok, msg, user = service.login("admin", "WrongPass123")
    assert ok is False
    assert "Invalid username or password" in msg
    assert user is None
    assert service.is_authenticated() is False


def test_auth_login_non_existent_user(auth_fixture):
    service, _ = auth_fixture
    ok, msg, user = service.login("unknown_user", "AnyPass123")
    assert ok is False
    assert "Invalid username or password" in msg
    assert service.is_authenticated() is False


def test_auth_logout(auth_fixture):
    service, _ = auth_fixture
    service.login("admin", "Admin@123")
    assert service.is_authenticated() is True

    service.logout()
    assert service.is_authenticated() is False
    assert service.current_user is None
