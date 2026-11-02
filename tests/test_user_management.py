"""Unit and integration tests for Staff User Management, Password Reset, and Status Toggles."""
import pytest
from database.db import DatabaseManager
from database.migrations import initialize_database
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from utils.security import hash_password, verify_password


@pytest.fixture
def user_test_fixture(tmp_path):
    db_file = tmp_path / "user_test.db"
    db_mgr = DatabaseManager(db_file)
    initialize_database(db_mgr)
    u_repo = UserRepository(db_mgr)
    auth_svc = AuthService(u_repo)
    return {"db": db_mgr, "repo": u_repo, "auth": auth_svc}


def test_list_all_users_includes_status(user_test_fixture):
    repo = user_test_fixture["repo"]
    users = repo.list_all()
    assert len(users) >= 2
    for u in users:
        assert hasattr(u, "is_active")
        assert u.is_active is True


def test_create_new_staff_member(user_test_fixture):
    repo = user_test_fixture["repo"]
    pwd_hash = hash_password("StaffPass@123")
    new_user = repo.create(
        username="vikram1",
        password_hash=pwd_hash,
        full_name="Vikram Singh",
        role="CASHIER",
        is_active=True
    )
    assert new_user is not None
    assert new_user.username == "vikram1"
    assert new_user.role == "CASHIER"
    assert new_user.is_active is True

    # Check persistence
    fetched = repo.get_by_username("vikram1")
    assert fetched is not None
    assert fetched.full_name == "Vikram Singh"


def test_deactivate_and_activate_staff(user_test_fixture):
    repo = user_test_fixture["repo"]
    auth = user_test_fixture["auth"]

    # Create active user
    pwd_hash = hash_password("Cashier@123")
    u = repo.create("cashier_test", pwd_hash, "Test Cashier", "CASHIER", is_active=True)

    # Login succeeds when active
    ok, msg, session_user = auth.login("cashier_test", "Cashier@123")
    assert ok is True

    # Deactivate user
    ok_toggle = repo.toggle_status(u.id, False)
    assert ok_toggle is True

    # Login fails when deactivated
    auth.logout()
    ok_login, err_msg, _ = auth.login("cashier_test", "Cashier@123")
    assert ok_login is False
    assert "deactivated" in err_msg.lower()

    # Reactivate user
    repo.toggle_status(u.id, True)
    ok_relogin, _, _ = auth.login("cashier_test", "Cashier@123")
    assert ok_relogin is True


def test_admin_password_reset(user_test_fixture):
    repo = user_test_fixture["repo"]
    auth = user_test_fixture["auth"]

    pwd_hash = hash_password("OldPassword@123")
    u = repo.create("reset_test", pwd_hash, "Reset User", "CASHIER", is_active=True)

    # Reset password
    new_hash = hash_password("NewPassword@999")
    ok_reset = repo.reset_password(u.id, new_hash)
    assert ok_reset is True

    # Old password fails, new password succeeds
    ok_old, _, _ = auth.login("reset_test", "OldPassword@123")
    assert ok_old is False
    ok_new, _, _ = auth.login("reset_test", "NewPassword@999")
    assert ok_new is True


def test_cannot_delete_last_admin(user_test_fixture):
    repo = user_test_fixture["repo"]
    admin = repo.get_by_username("admin")
    assert admin is not None

    with pytest.raises(ValueError) as excinfo:
        repo.delete(admin.id)
    assert "only administrative account" in str(excinfo.value)
