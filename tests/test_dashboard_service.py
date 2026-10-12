"""Unit tests for DashboardService metrics calculations (Feature 1: Interactive Dashboard)."""
import pytest
from decimal import Decimal
from database.db import DatabaseManager
from database.migrations import initialize_database
from repositories.order_repository import OrderRepository
from repositories.menu_repository import MenuRepository
from repositories.billing_repository import BillingRepository
from services.order_service import OrderService
from services.billing_service import BillingService
from services.dashboard_service import DashboardService


@pytest.fixture
def dashboard_fixture(tmp_path):
    db_file = tmp_path / "dashboard_test.db"
    db_manager = DatabaseManager(db_file)
    initialize_database(db_manager)
    o_repo = OrderRepository(db_manager)
    m_repo = MenuRepository(db_manager)
    b_repo = BillingRepository(db_manager)
    o_svc = OrderService(o_repo, m_repo)
    b_svc = BillingService(b_repo, o_repo)
    d_svc = DashboardService(db_manager)
    return d_svc, o_svc, b_svc, m_repo


def test_dashboard_metrics_empty_data(dashboard_fixture):
    d_svc, _, _, _ = dashboard_fixture
    metrics = d_svc.get_dashboard_metrics()
    assert metrics["today_sales"] == Decimal("0.00")
    assert metrics["completed_orders_count"] == 0
    assert metrics["pending_orders_count"] == 0
    assert metrics["average_order_value"] == Decimal("0.00")
    assert len(metrics["recent_orders"]) == 0
    assert len(metrics["popular_items"]) == 0
    assert metrics["active_menu_items_count"] > 0


def test_dashboard_metrics_with_active_data(dashboard_fixture):
    d_svc, o_svc, b_svc, m_repo = dashboard_fixture
    items = m_repo.list_all(available_only=True)
    item1 = items[0]  # Masala Chai
    item2 = items[1]  # Cold Coffee

    # Order 1: Finalized
    _, _, ord1 = o_svc.create_order(1, "T-01", "Customer 1", [(item1.id, 2)])
    _, _, bill1 = b_svc.finalize_bill(ord1.id, "CASH")

    # Order 2: Finalized
    _, _, ord2 = o_svc.create_order(1, "T-02", "Customer 2", [(item1.id, 1), (item2.id, 2)])
    _, _, bill2 = b_svc.finalize_bill(ord2.id, "UPI")

    # Order 3: Pending
    _, _, ord3 = o_svc.create_order(1, "T-03", "Customer 3", [(item2.id, 1)])

    metrics = d_svc.get_dashboard_metrics()
    assert metrics["completed_orders_count"] == 2
    assert metrics["pending_orders_count"] == 1
    expected_sales = bill1.final_total + bill2.final_total
    assert metrics["today_sales"] == expected_sales
    assert metrics["average_order_value"] == (expected_sales / Decimal("2")).quantize(Decimal("0.01"))
    assert len(metrics["recent_orders"]) == 3
    assert len(metrics["popular_items"]) >= 1
    # Check top item sold
    top_item = metrics["popular_items"][0]
    assert top_item["quantity_sold"] >= 2
