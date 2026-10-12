"""Unit tests for ReportService analytics queries and Matplotlib figures (Feature 2: Visual Reports)."""
import pytest
from matplotlib.figure import Figure
from database.db import DatabaseManager
from database.migrations import initialize_database
from repositories.order_repository import OrderRepository
from repositories.menu_repository import MenuRepository
from repositories.billing_repository import BillingRepository
from services.order_service import OrderService
from services.billing_service import BillingService
from services.report_service import ReportService


@pytest.fixture
def report_fixture(tmp_path):
    db_file = tmp_path / "report_test.db"
    db_manager = DatabaseManager(db_file)
    initialize_database(db_manager)
    o_repo = OrderRepository(db_manager)
    m_repo = MenuRepository(db_manager)
    b_repo = BillingRepository(db_manager)
    o_svc = OrderService(o_repo, m_repo)
    b_svc = BillingService(b_repo, o_repo)
    r_svc = ReportService(db_manager)
    return r_svc, o_svc, b_svc, m_repo


def test_sales_trend_query_structure(report_fixture):
    r_svc, _, _, _ = report_fixture
    trend = r_svc.get_sales_trend(days=7)
    assert len(trend) == 7
    for day in trend:
        assert "date" in day
        assert "label" in day
        assert "total_sales" in day
        assert "order_count" in day


def test_report_charts_empty_database(report_fixture):
    r_svc, _, _, _ = report_fixture
    fig_sales = r_svc.plot_daily_sales("dark")
    assert isinstance(fig_sales, Figure)

    fig_items = r_svc.plot_top_items("dark")
    assert isinstance(fig_items, Figure)

    fig_status = r_svc.plot_order_status("light")
    assert isinstance(fig_status, Figure)

    fig_pay = r_svc.plot_payment_methods("light")
    assert isinstance(fig_pay, Figure)


def test_report_charts_with_transactions(report_fixture):
    r_svc, o_svc, b_svc, m_repo = report_fixture
    items = m_repo.list_all(available_only=True)

    # Place orders with various payment methods
    _, _, ord1 = o_svc.create_order(1, "T-1", "A", [(items[0].id, 2)])
    b_svc.finalize_bill(ord1.id, "CASH")

    _, _, ord2 = o_svc.create_order(1, "T-2", "B", [(items[1].id, 3)])
    b_svc.finalize_bill(ord2.id, "UPI")

    _, _, ord3 = o_svc.create_order(1, "T-3", "C", [(items[0].id, 1)])
    o_svc.cancel_order(ord3.id)

    # Verify distributions
    status_dist = r_svc.get_order_status_distribution()
    assert status_dist["COMPLETED"] == 2
    assert status_dist["CANCELLED"] == 1

    pay_dist = r_svc.get_payment_method_distribution()
    assert pay_dist["CASH"] == 1
    assert pay_dist["UPI"] == 1
    assert pay_dist["CARD"] == 0

    top_items = r_svc.get_top_selling_items()
    assert len(top_items) >= 2

    # Verify chart renderers with live data
    fig1 = r_svc.plot_daily_sales("dark")
    fig2 = r_svc.plot_top_items("dark")
    fig3 = r_svc.plot_order_status("dark")
    fig4 = r_svc.plot_payment_methods("light")

    assert all(isinstance(f, Figure) for f in [fig1, fig2, fig3, fig4])
