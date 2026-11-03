"""Tests for Account Status, Last Session tracking, and database persistence."""
import pytest
from datetime import datetime
from decimal import Decimal

from database.db import DatabaseManager
from database.migrations import initialize_database
from models.user import User
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from services.dashboard_service import DashboardService


@pytest.fixture
def auth_fixture(tmp_path):
    db_file = tmp_path / "login_tracking_test.db"
    db_manager = DatabaseManager(db_file)
    initialize_database(db_manager)
    repo = UserRepository(db_manager)
    auth_svc = AuthService(repo)
    dash_svc = DashboardService(db_manager)
    return auth_svc, repo, dash_svc, db_manager


def test_initial_state_never_logged_in(auth_fixture):
    """Initial seeded accounts must have last_login as None and show 'Never logged in'."""
    _, repo, _, _ = auth_fixture
    users = repo.list_all()
    assert len(users) >= 5

    for u in users:
        assert u.is_active is True
        assert u.last_login is None
        assert u.format_last_login() == "Never logged in"


def test_account_status_separate_from_login_activity(auth_fixture):
    """Account Status (is_active) must be independent of Last Session."""
    auth_svc, repo, dash_svc, _ = auth_fixture
    
    # 1. User is active but has never logged in
    admin = repo.get_by_username("admin")
    assert admin.is_active is True
    assert admin.last_login is None

    # 2. Deactivating a user changes is_active but preserves last_login
    repo.toggle_status(admin.id, False)
    admin_deactivated = repo.get_by_id(admin.id)
    assert admin_deactivated.is_active is False
    assert admin_deactivated.last_login is None

    # 3. Deactivated account cannot login and last_login is not updated
    ok, msg, user = auth_svc.login("admin", "Admin@123")
    assert ok is False
    assert "Account deactivated" in msg
    assert user is None

    # Check database persistence
    refreshed = repo.get_by_id(admin.id)
    assert refreshed.is_active is False
    assert refreshed.last_login is None


def test_failed_login_does_not_update_last_session(auth_fixture):
    """Failed login attempts (wrong password or invalid user) must not update last_login."""
    auth_svc, repo, _, _ = auth_fixture

    # Test with wrong password
    ok, msg, user = auth_svc.login("cashier1", "WrongPassword!999")
    assert ok is False
    assert user is None

    cashier = repo.get_by_username("cashier1")
    assert cashier.last_login is None
    assert cashier.format_last_login() == "Never logged in"

    # Test with non-existent user
    ok, msg, user = auth_svc.login("ghost_user", "AnyPassword123")
    assert ok is False


def test_all_five_roles_login_tracking(auth_fixture):
    """Verify login tracking updates database for ADMIN, MANAGER, CASHIER, CHEF, and CUSTOMER."""
    auth_svc, repo, _, _ = auth_fixture

    role_credentials = [
        ("admin", "Admin@123", "ADMIN"),
        ("manager1", "Manager@123", "MANAGER"),
        ("cashier1", "Cashier@123", "CASHIER"),
        ("chef1", "Chef@123", "CHEF"),
        ("customer1", "Customer@123", "CUSTOMER"),
    ]

    for username, password, expected_role in role_credentials:
        # Before login: last_login is None
        pre_user = repo.get_by_username(username)
        assert pre_user is not None, f"Seeded user {username} not found"
        assert pre_user.last_login is None

        # Perform login
        before_time = datetime.now()
        ok, msg, user = auth_svc.login(username, password)
        assert ok is True, f"Login failed for {username}: {msg}"
        assert user.role == expected_role
        assert user.last_login is not None

        # Verify database persistence via fresh query
        post_user = repo.get_by_username(username)
        assert post_user.last_login is not None
        assert post_user.last_login == user.last_login

        # Verify parsed timestamp
        login_dt = datetime.strptime(post_user.last_login, "%Y-%m-%d %H:%M:%S")
        assert login_dt.year == before_time.year
        assert login_dt.month == before_time.month
        assert login_dt.day == before_time.day

        # Verify human-readable formatted timestamp
        formatted = post_user.format_last_login()
        assert formatted != "Never logged in"
        assert login_dt.strftime("%d %b %Y") in formatted


def test_customer_registration_tracks_initial_session(auth_fixture):
    """Newly registered customer must automatically record their initial login session."""
    auth_svc, repo, _, _ = auth_fixture

    ok, msg, customer = auth_svc.register_customer(
        username="new_foodie",
        password="SecretPassword123",
        full_name="Pooja Sharma"
    )
    assert ok is True
    assert customer is not None
    assert customer.role == "CUSTOMER"
    assert customer.last_login is not None

    # Verify persistence in database
    db_cust = repo.get_by_username("new_foodie")
    assert db_cust.last_login is not None
    assert db_cust.last_login == customer.last_login
    assert "Never logged in" != db_cust.format_last_login()


def test_dashboard_metrics_active_users_reflection(auth_fixture):
    """Admin Dashboard active users KPI must accurately reflect active vs deactivated accounts."""
    auth_svc, repo, dash_svc, _ = auth_fixture

    metrics = dash_svc.get_admin_metrics()
    total_initial = metrics["total_staff"]
    active_initial = metrics["active_users"]
    assert total_initial == active_initial
    assert active_initial >= 5

    # Deactivate one user (e.g. cashier1)
    cashier = repo.get_by_username("cashier1")
    repo.toggle_status(cashier.id, False)

    # Refresh metrics
    refreshed_metrics = dash_svc.get_admin_metrics()
    assert refreshed_metrics["total_staff"] == total_initial
    assert refreshed_metrics["active_users"] == active_initial - 1


def test_consecutive_logins_update_to_latest_timestamp(auth_fixture):
    """Subsequent logins must update the last_login to the newest session timestamp."""
    auth_svc, repo, _, _ = auth_fixture

    # First login
    auth_svc.login("admin", "Admin@123")
    first_login = repo.get_by_username("admin").last_login

    # Explicitly set an earlier timestamp on DB to simulate time progression
    repo.update_last_login(repo.get_by_username("admin").id, "2026-01-01 10:00:00")
    old_login = repo.get_by_username("admin").last_login
    assert old_login == "2026-01-01 10:00:00"

    # Second login
    auth_svc.login("admin", "Admin@123")
    second_login = repo.get_by_username("admin").last_login
    assert second_login != old_login
    assert second_login.startswith(datetime.now().strftime("%Y-%m-%d"))
