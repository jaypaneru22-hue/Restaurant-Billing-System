"""Capture visual evidence of Waiter Dashboard and Manager Waiter Management."""
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import time
import customtkinter as ctk
from PIL import ImageGrab
from ui.waiter_dashboard import WaiterDashboardFrame
from ui.table_management import TableManagementFrame
from ui.manager_active_orders import ManagerActiveOrdersFrame
from ui.theme_manager import theme_manager
from models.user import User
from config.settings import ROLE_WAITER, ROLE_MANAGER
from database.db import db

OUTPUT_DIR = r"C:\Users\jaypa\.gemini\antigravity\brain\8c320227-f5be-45fb-9cd9-48cc564ae2f6"


def ensure_demo_data():
    """Ensures at least one READY and one PICKED_UP order exist for visual demonstration."""
    with db.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM orders WHERE status = 'READY' LIMIT 1;")
        ready_row = cursor.fetchone()
        if not ready_row:
            cursor.execute(
                """INSERT INTO orders (order_number, user_id, table_number, customer_name, status, special_instructions, waiter_id)
                   VALUES ('ORD-DEMO-0101', 1, 'T-1', 'Priya Sharma (VIP)', 'READY', 'Extra chili oil on the side', 14);"""
            )
            ord_id = cursor.lastrowid
            cursor.execute(
                """INSERT INTO order_items (order_id, menu_item_id, item_name, unit_price, quantity, line_total)
                   VALUES (?, 1, 'Margherita Pizza', 299.00, 2, 598.00);""",
                (ord_id,)
            )

        cursor.execute("SELECT id FROM orders WHERE status = 'PICKED_UP' LIMIT 1;")
        picked_row = cursor.fetchone()
        if not picked_row:
            cursor.execute(
                """INSERT INTO orders (order_number, user_id, table_number, customer_name, status, special_instructions, waiter_id, picked_up_at)
                   VALUES ('ORD-DEMO-0102', 1, 'T-3', 'Vikram Malhotra', 'PICKED_UP', 'Serve with fresh mint leaves', 14, CURRENT_TIMESTAMP);"""
            )
            ord_id2 = cursor.lastrowid
            cursor.execute(
                """INSERT INTO order_items (order_id, menu_item_id, item_name, unit_price, quantity, line_total)
                   VALUES (?, 2, 'Paneer Tikka Platter', 349.00, 1, 349.00);""",
                (ord_id2,)
            )

        # Assign T-1 and T-3 to waiter 14
        cursor.execute("UPDATE restaurant_tables SET waiter_id = 14 WHERE table_number IN ('T-1', 'T-3');")

        # Ensure demo service requests
        cursor.execute("SELECT id FROM service_requests WHERE status = 'PENDING' LIMIT 1;")
        if not cursor.fetchone():
            cursor.execute(
                """INSERT INTO service_requests (table_number, order_id, customer_id, customer_name, request_type, notes, status, assigned_waiter_id)
                   VALUES ('T-1', NULL, 1, 'Priya Sharma (VIP)', 'Water', 'Chilled water with lime slice', 'PENDING', 14);"""
            )
            cursor.execute(
                """INSERT INTO service_requests (table_number, order_id, customer_id, customer_name, request_type, notes, status, assigned_waiter_id)
                   VALUES ('T-3', NULL, 1, 'Vikram Malhotra', 'Extra Cutlery', '2 dessert spoons and extra napkins', 'IN_PROGRESS', 14);"""
            )


def capture_waiter_dashboard(theme_name: str, filename: str, initial_filter: str = "ALL"):
    theme_manager.apply_theme(theme_name)
    ctk.set_appearance_mode("dark" if theme_name == "dark" else "light")

    root = ctk.CTk()
    root.geometry("1180x780+80+60")
    root.title(f"RestoPro Floor Waiter Terminal — {theme_name.capitalize()}")

    frame = WaiterDashboardFrame(root, waiter_id=14, initial_filter=initial_filter)
    frame.pack(fill="both", expand=True)

    root.update_idletasks()
    root.update()
    time.sleep(0.5)

    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()

    filepath = os.path.join(OUTPUT_DIR, filename)
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img.save(filepath)
    print(f"Captured: {filepath}")

    try:
        if hasattr(frame, "_auto_refresh_id") and frame._auto_refresh_id:
            root.after_cancel(frame._auto_refresh_id)
        root.destroy()
    except Exception:
        pass


def capture_manager_tables(filename: str):
    theme_manager.apply_theme("dark")
    ctk.set_appearance_mode("dark")

    root = ctk.CTk()
    root.geometry("1180x780+80+60")
    root.title("RestoPro Table Management — Waiter Allocation")

    frame = TableManagementFrame(root)
    frame.pack(fill="both", expand=True)

    root.update_idletasks()
    root.update()
    time.sleep(0.5)

    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()

    filepath = os.path.join(OUTPUT_DIR, filename)
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img.save(filepath)
    print(f"Captured: {filepath}")

    try:
        root.destroy()
    except Exception:
        pass


def capture_manager_active_orders(filename: str):
    theme_manager.apply_theme("dark")
    ctk.set_appearance_mode("dark")

    root = ctk.CTk()
    root.geometry("1180x780+80+60")
    root.title("RestoPro Manager Active Orders — Waiter Dispatch")

    frame = ManagerActiveOrdersFrame(root)
    frame.pack(fill="both", expand=True)

    root.update_idletasks()
    root.update()
    time.sleep(0.5)

    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()

    filepath = os.path.join(OUTPUT_DIR, filename)
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img.save(filepath)
    print(f"Captured: {filepath}")

    try:
        root.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    ensure_demo_data()
    capture_waiter_dashboard("dark", "waiter_dashboard_dark.png", initial_filter="ALL")
    capture_waiter_dashboard("light", "waiter_dashboard_light.png", initial_filter="ALL")
    capture_waiter_dashboard("dark", "waiter_service_requests_dark.png", initial_filter="REQUESTS")
    capture_waiter_dashboard("dark", "waiter_assigned_tables_dark.png", initial_filter="TABLES")
    capture_manager_tables("manager_table_waiters_dark.png")
    capture_manager_active_orders("manager_active_orders_waiters_dark.png")
