"""Verification script for Cashier Pending Billing queue and Order #1 retrieval."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from services.order_service import order_service
from services.dashboard_service import dashboard_service

orders = order_service.get_pending_billing_orders()
print(f"Found {len(orders)} order(s) in Cashier Pending Billing queue:")
for o in orders:
    print(f"  • Order ID       : {o['id']}")
    print(f"  • Order Number   : {o['order_number']}")
    print(f"  • Customer       : {o['customer_name']}")
    print(f"  • Table          : {o['table_number']}")
    print(f"  • Kitchen Status : {o['kitchen_status']}")
    print(f"  • Serving Status : {o['serving_status']}")
    print(f"  • Billing Status : {o['billing_status']}")
    print(f"  • Payment Status : {o['payment_status']}")
    print(f"  • Total Amount   : ₹{o['total_amount']}")
    print(f"  • Items Summary  : {o['items_summary']}")
    print(f"  • Floor Server   : {o['waiter_name']}")

c_metrics = dashboard_service.get_cashier_metrics()
print("\nCashier Dashboard Telemetry:")
print(f"  • Shift Sales    : ₹{c_metrics['shift_sales']}")
print(f"  • Pending Orders : {c_metrics['pending_count']}")
print(f"  • Recent Tickets : {len(c_metrics['recent_tickets'])}")

assert len(orders) == 1, f"Expected 1 unbilled order, found {len(orders)}"
assert orders[0]["id"] == 1, f"Expected Order ID 1, got {orders[0]['id']}"
assert orders[0]["serving_status"] == "SERVED", f"Expected SERVED, got {orders[0]['serving_status']}"
assert orders[0]["billing_status"] == "NOT_GENERATED", f"Expected NOT_GENERATED, got {orders[0]['billing_status']}"
assert c_metrics["pending_count"] == 1, f"Expected pending_count 1, got {c_metrics['pending_count']}"
print("\n[SUCCESS] Cashier Pending Billing queue and dashboard telemetry fully verified.")
