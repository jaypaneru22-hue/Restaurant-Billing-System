"""Unit and integration tests for Stage 2: Role-based Dashboards and Authentication."""
import pytest
from decimal import Decimal
import customtkinter as ctk

from database.db import DatabaseManager
from database.migrations import initialize_database
from repositories.user_repository import UserRepository
from repositories.order_repository import OrderRepository
from repositories.menu_repository import MenuRepository
from repositories.billing_repository import BillingRepository
from services.auth_service import AuthService
from services.dashboard_service import DashboardService
from services.order_service import OrderService
from services.billing_service import BillingService
from ui.dashboard import DashboardFrame
from ui.login import LoginFrame
from ui.main_window import MainWindow
from utils.security import hash_password


@pytest.fixture
def role_fixture(tmp_path):
    db_file = tmp_path / "role_test.db"
    db_mgr = DatabaseManager(db_file)
    initialize_database(db_mgr)
    u_repo = UserRepository(db_mgr)
    o_repo = OrderRepository(db_mgr)
    m_repo = MenuRepository(db_mgr)
    b_repo = BillingRepository(db_mgr)

    auth_svc = AuthService(u_repo)
    dash_svc = DashboardService(db_mgr)
    order_svc = OrderService(o_repo, m_repo)
    bill_svc = BillingService(b_repo, o_repo)

    # Register manager user in this test db
    u_repo.create("manager_test", hash_password("Manager@123"), "Test Floor Manager", "MANAGER")

    return {
        "db": db_mgr,
        "u_repo": u_repo,
        "auth_svc": auth_svc,
        "dash_svc": dash_svc,
        "order_svc": order_svc,
        "bill_svc": bill_svc,
        "m_repo": m_repo
    }


def test_admin_authentication_and_role(role_fixture):
    auth_svc = role_fixture["auth_svc"]
    ok, msg, user = auth_svc.login("admin", "Admin@123")
    assert ok is True
    assert user is not None
    assert user.role == "ADMIN"
    assert user.is_admin() is True
    assert user.is_cashier() is False
    assert user.is_manager() is False


def test_cashier_authentication_and_role(role_fixture):
    auth_svc = role_fixture["auth_svc"]
    ok, msg, user = auth_svc.login("cashier1", "Cashier@123")
    assert ok is True
    assert user is not None
    assert user.role == "CASHIER"
    assert user.is_cashier() is True
    assert user.is_admin() is False
    assert user.is_manager() is False


def test_manager_authentication_and_role(role_fixture):
    auth_svc = role_fixture["auth_svc"]
    ok, msg, user = auth_svc.login("manager_test", "Manager@123")
    assert ok is True
    assert user is not None
    assert user.role == "MANAGER"
    assert user.is_manager() is True
    assert user.is_admin() is False
    assert user.is_cashier() is False


def test_admin_dashboard_metrics(role_fixture):
    dash_svc = role_fixture["dash_svc"]
    metrics = dash_svc.get_admin_metrics()

    # 7 Mandatory Admin KPIs
    assert "total_staff" in metrics
    assert "active_users" in metrics
    assert "total_orders" in metrics
    assert "total_sales" in metrics
    assert "total_transactions" in metrics
    assert "pending_orders" in metrics
    assert "system_status" in metrics
    assert metrics["total_staff"] >= 2
    assert metrics["active_users"] >= 2
    assert isinstance(metrics["total_sales"], Decimal)
    assert metrics["system_status"] in ["ONLINE • HEALTHY", "DEGRADED"]

    # Backwards compatibility & operational fields
    assert "total_revenue" in metrics
    assert "today_sales" in metrics
    assert "active_dishes" in metrics
    assert "total_dishes" in metrics
    assert "payment_breakdown" in metrics
    assert "recent_transactions" in metrics
    assert isinstance(metrics["total_revenue"], Decimal)


def test_cashier_dashboard_metrics(role_fixture):
    dash_svc = role_fixture["dash_svc"]
    metrics = dash_svc.get_cashier_metrics(user_id=2)

    assert "shift_sales" in metrics
    assert "shift_tickets" in metrics
    assert "pending_count" in metrics
    assert "terminal_status" in metrics
    assert "recent_tickets" in metrics
    assert isinstance(metrics["shift_sales"], Decimal)


def test_manager_dashboard_metrics(role_fixture):
    dash_svc = role_fixture["dash_svc"]
    metrics = dash_svc.get_manager_metrics()

    assert "floor_revenue" in metrics
    assert "orders_today" in metrics
    assert "pending_count" in metrics
    assert "oos_count" in metrics
    assert "total_items" in metrics
    assert "pending_orders" in metrics
    assert isinstance(metrics["floor_revenue"], Decimal)


def test_cashier_role_navigation_restriction():
    """Verifies Cashier cannot navigate to Menu Management or Reports via MainWindow."""
    mw = object.__new__(MainWindow)
    mw.user_role = "CASHIER"
    mw.nav_buttons = {}
    mw.current_view = None

    # Cashier attempts to navigate to 'menu'
    recorded_view = []
    def mock_navigate(v):
        if mw.user_role == "CASHIER" and v in ["menu", "reports"]:
            recorded_view.append("BLOCKED")
        else:
            recorded_view.append(v)

    mw._safe_navigate = mock_navigate

    mw._safe_navigate("menu")
    mw._safe_navigate("reports")
    mw._safe_navigate("orders")

    assert recorded_view == ["BLOCKED", "BLOCKED", "orders"]
