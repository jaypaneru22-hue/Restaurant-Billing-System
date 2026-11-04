"""Verification script mounting GUI frames for Cashier Billing Queue."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import customtkinter as ctk
from services.auth_service import auth_service
from services.order_service import order_service
from ui.cashier_billing_queue import CashierBillingQueueFrame
from ui.dashboard import DashboardFrame
from ui.orders import OrderHistoryFrame
from ui.main_window import MainWindow

app = ctk.CTk()
app.withdraw()

# 1. Authenticate as Cashier
ok, msg, user = auth_service.login("cashier1", "Cashier@123")
assert ok is True
assert user.role == "CASHIER"
print("[OK] Authenticated as Cashier (@cashier1).")

# 2. Mount CashierBillingQueueFrame
queue_frame = CashierBillingQueueFrame(
    app,
    on_generate_bill=lambda oid: print(f"Generate bill requested for order #{oid}"),
    on_view_receipt=lambda oid: print(f"View receipt requested for order #{oid}")
)
queue_frame.pack(fill="both", expand=True)
app.update_idletasks()

# Verify KPI labels
assert queue_frame.card_total_unbilled.cget("text") == "1"
assert queue_frame.card_served.cget("text") == "1"
print("[OK] CashierBillingQueueFrame mounted: Total Unbilled=1, Served=1.")

# Verify children inside scroll_orders
order_cards = queue_frame.scroll_orders.winfo_children()
assert len(order_cards) >= 1
print(f"[OK] Found {len(order_cards)} order card(s) in queue frame.")
queue_frame.destroy()

# 3. Mount Cashier DashboardFrame
dash = DashboardFrame(app, navigate_fn=lambda v: print(f"Navigate to {v}"), role="CASHIER")
dash.pack(fill="both", expand=True)
app.update_idletasks()
dash.refresh_data()
app.update_idletasks()
assert dash.lbl_c_pending.cget("text") == "1"
print("[OK] Cashier DashboardFrame mounted: Pending Orders KPI=1.")
dash.destroy()

# 4. Mount OrderHistoryFrame
hist = OrderHistoryFrame(
    app,
    on_open_bill=lambda oid: print(f"Open bill for #{oid}"),
    on_view_receipt=lambda oid: print(f"View receipt for #{oid}")
)
hist.pack(fill="both", expand=True)
app.update_idletasks()
hist.refresh_history()
app.update_idletasks()
hist_children = hist.scroll_orders.winfo_children()
assert len(hist_children) >= 1
print(f"[OK] OrderHistoryFrame mounted: {len(hist_children)} order(s) listed.")
hist.destroy()

# 5. Mount full MainWindow for Cashier
mw = MainWindow(app, on_logout=lambda: None)
mw.pack(fill="both", expand=True)
app.update_idletasks()

# Navigate to pending_billing
mw.navigate_to("pending_billing")
app.update_idletasks()
assert mw.current_view_name == "pending_billing"
assert isinstance(mw.current_view, CashierBillingQueueFrame)
print("[OK] MainWindow navigated to 'pending_billing' successfully.")

mw.destroy()
app.destroy()
print("\n[ALL GUI CHECKS PASSED] Cashier Billing Queue integration is fully operational.")
