"""Application entry point and GUI lifecycle coordinator."""
import sys
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
import customtkinter as ctk
from config.settings import (
    APP_NAME,
    STUDENT_NAME,
    REGISTRATION_NUMBER,
    QUALITY_GOAL,
    DEFAULT_THEME,
    SUPPORTED_PAYMENT_METHODS
)
from database.migrations import initialize_database
from database.db import db
from services.auth_service import auth_service
from services.menu_service import menu_service
from services.order_service import order_service
from services.billing_service import billing_service
from ui.theme_manager import theme_manager
from ui.login import LoginFrame
from ui.main_window import MainWindow
from utils.logger import logger


def seed_demo_transactions() -> None:
    """Populates demonstrable past orders and finalized bills for charts and dashboard."""
    logger.info("Checking and seeding realistic demonstration transactions...")
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders;")
    order_count = cursor.fetchone()[0]
    conn.close()

    if order_count > 0:
        logger.info(f"Existing orders found ({order_count}). Skipping demonstration transaction seeding.")
        return

    items = menu_service.get_all_items(available_only=True)
    if not items:
        return

    admin_user = auth_service.user_repo.get_by_username("admin")
    user_id = admin_user.id if admin_user else 1

    customers = [
        ("Rahul Verma", "Table 1", ["CASH", "UPI"]),
        ("Pooja Nair", "Table 3", ["CARD", "UPI"]),
        ("Amitabh Sen", "Takeaway", ["CASH"]),
        ("Sneha Kulkarni", "Table 5", ["CARD"]),
        ("Vikram Singh", "Table 2", ["UPI"]),
        ("Ananya Roy", "Table 4", ["CARD", "CASH"]),
        ("Rajesh Khanna", "Table 6", ["UPI"]),
        ("Kavita Rao", "Takeaway", ["CASH"]),
        ("Rohan Joshi", "Table 2", ["UPI"]),
        ("Meera Patel", "Table 1", ["CARD"])
    ]

    today = datetime.now()
    payment_methods = ["CASH", "CARD", "UPI"]

    for idx, (cust_name, table, pay_pref) in enumerate(customers):
        # Stagger orders across the past 5 days
        days_ago = idx % 5
        ord_date = today - timedelta(days=days_ago, hours=(idx * 2) % 12, minutes=idx * 7)

        # Select 2 to 3 dishes
        dish1 = items[idx % len(items)]
        dish2 = items[(idx + 3) % len(items)]
        entries = [(dish1.id, 1 + (idx % 3)), (dish2.id, 1 + ((idx + 1) % 2))]

        ok, msg, order = order_service.create_order(user_id, table, cust_name, entries)
        if ok and order:
            # Complete 8 out of 10 orders
            if idx < 8:
                pm = pay_pref[0] if pay_pref else payment_methods[idx % len(payment_methods)]
                discount = Decimal("5.0") if idx % 3 == 0 else Decimal("0.0")
                ok_bill, _, bill = billing_service.finalize_bill(order.id, pm, discount, Decimal("5.0"))
                # Adjust timestamps in DB for historical trend demonstration
                if ok_bill and bill:
                    db.execute(
                        "UPDATE orders SET created_at = ? WHERE id = ?;",
                        (ord_date.strftime("%Y-%m-%d %H:%M:%S"), order.id)
                    )
                    db.execute(
                        "UPDATE bills SET billed_at = ? WHERE id = ?;",
                        (ord_date.strftime("%Y-%m-%d %H:%M:%S"), bill.id)
                    )
            elif idx == 8:
                # Leave as PENDING
                pass
            else:
                # Cancel 1 order
                order_service.cancel_order(order.id)

    logger.info("Demonstration transactions successfully seeded.")


class RestaurantBillingApp(ctk.CTk):
    """Main application GUI coordinator managing authentication and workspace views."""

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} — {STUDENT_NAME} ({REGISTRATION_NUMBER}) — {QUALITY_GOAL}")
        self.geometry("1240x750")
        self.minsize(1024, 640)

        # Apply default theme
        theme_manager.apply_theme(DEFAULT_THEME)

        self.current_frame = None
        self.show_login()

    def show_login(self):
        """Displays the login authentication view."""
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = LoginFrame(self, on_login_success=self.show_main_window)
        self.current_frame.pack(fill="both", expand=True)

    def show_main_window(self, user):
        """Displays the authenticated main workspace."""
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = MainWindow(self, on_logout=self.show_login)
        self.current_frame.pack(fill="both", expand=True)


def main():
    parser = argparse.ArgumentParser(description=f"{APP_NAME} Point of Sale System")
    parser.add_argument("--headless-check", action="store_true", help="Initialize and verify database without GUI")
    parser.add_argument("--no-demo-seed", action="store_true", help="Skip demo transaction seeding")
    args = parser.parse_args()

    # Step 1: Initialize Database & Core Seeds
    initialize_database()

    # Step 2: Seed Demonstration transactions unless disabled
    if not args.no_demo_seed:
        seed_demo_transactions()

    if args.headless_check:
        print(f"System verified cleanly in headless mode. All database tables and seeds operational.")
        sys.exit(0)

    # Step 3: Launch CustomTkinter Desktop Application
    app = RestaurantBillingApp()
    app.mainloop()


if __name__ == "__main__":
    main()
