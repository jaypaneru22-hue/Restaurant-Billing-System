"""Customer Dining Portal, Online Ordering & Real-Time Order Tracking (Phase D)."""
from typing import Optional, Callable, Dict, List
from decimal import Decimal
import customtkinter as ctk

from ui.theme_manager import theme_manager
from database.db import db
from services.auth_service import auth_service
from services.menu_service import menu_service
from services.order_service import order_service
from utils.logger import logger


class CustomerPortalFrame(ctk.CTkFrame):
    """Customer Dining Portal with real-time order tracking and isolated account history."""

    def __init__(
        self,
        master,
        navigate_fn: Optional[Callable[[str], None]] = None,
        on_browse_menu: Optional[Callable] = None,
        on_give_feedback: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.navigate = navigate_fn or (lambda route: on_browse_menu() if (route == "orders" and on_browse_menu) else (on_give_feedback() if (route == "feedback" and on_give_feedback) else None))
        self.user = auth_service.current_user

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self._load_customer_data()

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, _theme: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self._load_customer_data()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # -------------------------------------------------------------
        # TOP BANNER
        # -------------------------------------------------------------
        banner = ctk.CTkFrame(self, fg_color=palette["accent_light"], corner_radius=10, border_width=1, border_color=palette["border"])
        banner.pack(fill="x", padx=20, pady=(15, 12))

        b_left = ctk.CTkFrame(banner, fg_color="transparent")
        b_left.pack(side="left", padx=16, pady=12)

        user_name = self.user.full_name if self.user else "Valued Guest"
        ctk.CTkLabel(
            b_left,
            text=f"🍽️ Welcome to TQM Dining, {user_name}!",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=palette["accent"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            b_left,
            text="Explore our gourmet multi-cuisine catalog, place orders, and track your kitchen preparation live.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        b_right = ctk.CTkFrame(banner, fg_color="transparent")
        b_right.pack(side="right", padx=16)

        ctk.CTkButton(
            b_right,
            text="📖 Browse Food Menu",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            height=36,
            width=160,
            command=lambda: self.navigate("orders")
        ).pack(side="right")

        # -------------------------------------------------------------
        # ACTIVE ORDER TRACKING CARD (Q08 VOC-06)
        # -------------------------------------------------------------
        self.track_container = ctk.CTkFrame(self, fg_color="transparent")
        self.track_container.pack(fill="x", padx=20, pady=(0, 12))

        # -------------------------------------------------------------
        # MY ORDER HISTORY & FEEDBACK SECTION
        # -------------------------------------------------------------
        history_card = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        history_card.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        h_head = ctk.CTkFrame(history_card, fg_color="transparent")
        h_head.pack(fill="x", padx=16, pady=(12, 8))

        ctk.CTkLabel(
            h_head,
            text="📜 My Dining Orders & Invoices",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(side="left")

        ctk.CTkButton(
            h_head,
            text="⭐ Give Dining Feedback",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_secondary"],
            hover_color=palette["border"],
            text_color=palette["accent"],
            height=28,
            width=160,
            command=lambda: self.navigate("feedback")
        ).pack(side="right")

        # Scrollable order table
        self.history_scroll = ctk.CTkScrollableFrame(
            history_card,
            fg_color="transparent",
            scrollbar_button_color=palette.get("sidebar_hover", "#292938")
        )
        self.history_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _load_customer_data(self):
        palette = theme_manager.get_palette()
        user_id = self.user.id if self.user else 1

        # 1. Fetch most recent active order for this customer
        active_order = db.fetchone(
            """SELECT o.id, o.order_number, o.table_number, o.status, o.created_at
               FROM orders o
               WHERE o.user_id = ? AND o.status IN ('PENDING', 'ACCEPTED', 'PREPARING', 'READY')
               ORDER BY o.id DESC LIMIT 1;""",
            (user_id,)
        )

        for w in self.track_container.winfo_children():
            w.destroy()

        if active_order:
            t_card = ctk.CTkFrame(self.track_container, fg_color=palette["bg_card"], corner_radius=10, border_width=2, border_color=palette["accent"])
            t_card.pack(fill="x")

            t_head = ctk.CTkFrame(t_card, fg_color="transparent")
            t_head.pack(fill="x", padx=16, pady=(10, 6))

            ctk.CTkLabel(
                t_head,
                text=f"⚡ Live Order Tracker — #{active_order['order_number']} ({active_order['table_number']})",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=palette.get("heading", palette["text_primary"])
            ).pack(side="left")

            st_colors = {
                "PENDING": ("#DBEAFE", "#1D4ED8", "Placed & Waiting Confirmation"),
                "ACCEPTED": ("#EDE9FE", "#6D28D9", "Order Accepted by Kitchen"),
                "PREPARING": ("#FEF3C7", "#B45309", "Chef Cooking in Kitchen"),
                "READY": ("#DCFCE7", "#15803D", "Food Ready at Counter / Table")
            }
            s_bg, s_fg, s_desc = st_colors.get(active_order["status"], ("#F1F5F9", "#475569", active_order["status"]))

            pill = ctk.CTkFrame(t_head, fg_color=s_bg, corner_radius=6)
            pill.pack(side="right")
            ctk.CTkLabel(pill, text=active_order["status"], font=ctk.CTkFont(size=10, weight="bold"), text_color=s_fg).pack(padx=8, pady=2)

            # Timeline Steps Bar
            timeline = ctk.CTkFrame(t_card, fg_color=palette["bg_secondary"], corner_radius=6)
            timeline.pack(fill="x", padx=16, pady=(0, 10))

            steps = ["Placed", "Accepted", "Preparing", "Ready", "Served"]
            active_step_map = {"PENDING": 0, "ACCEPTED": 1, "PREPARING": 2, "READY": 3, "COMPLETED": 4}
            current_step_idx = active_step_map.get(active_order["status"], 0)

            t_row = ctk.CTkFrame(timeline, fg_color="transparent")
            t_row.pack(fill="x", padx=12, pady=6)
            t_row.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

            for s_idx, s_name in enumerate(steps):
                col = ctk.CTkFrame(t_row, fg_color="transparent")
                col.grid(row=0, column=s_idx, sticky="nsew")

                is_done = s_idx <= current_step_idx
                is_curr = s_idx == current_step_idx
                mark = "●" if is_done else "○"
                col_color = palette["accent"] if is_curr else (palette["success"] if is_done else palette["text_secondary"])

                ctk.CTkLabel(col, text=f"{mark} {s_name}", font=ctk.CTkFont(size=10, weight="bold" if is_curr else "normal"), text_color=col_color).pack(anchor="center")

        # 2. Load historical orders strictly isolated to this customer
        for w in self.history_scroll.winfo_children():
            w.destroy()

        try:
            orders = db.fetchall(
                """SELECT o.id, o.order_number, o.table_number, o.status, o.created_at,
                          b.bill_number, b.final_total, b.payment_method
                   FROM orders o
                   LEFT JOIN bills b ON o.id = b.order_id
                   WHERE o.user_id = ?
                   ORDER BY o.id DESC LIMIT 15;""",
                (user_id,)
            )
        except Exception as e:
            logger.error(f"Error fetching customer orders: {e}")
            orders = []

        if not orders:
            ctk.CTkLabel(
                self.history_scroll,
                text="You have not placed any dining orders yet. Click 'Browse Food Menu' above to get started!",
                font=ctk.CTkFont(size=11),
                text_color=palette["text_secondary"]
            ).pack(pady=30)
            return

        for o in orders:
            row = ctk.CTkFrame(self.history_scroll, fg_color=palette["bg_secondary"], corner_radius=6)
            row.pack(fill="x", pady=3)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", padx=12, pady=8)

            ctk.CTkLabel(
                left,
                text=f"Order #{o['order_number']}  •  {o['table_number']}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=palette["text_primary"]
            ).pack(anchor="w")

            status_text = f"Status: {o['status']}  |  Placed: {o['created_at']}"
            if o["bill_number"]:
                status_text += f"  |  Invoice: #{o['bill_number']} ({o['payment_method']})"
            ctk.CTkLabel(left, text=status_text, font=ctk.CTkFont(size=10), text_color=palette["text_secondary"]).pack(anchor="w")

            right = ctk.CTkFrame(row, fg_color="transparent")
            right.pack(side="right", padx=12)

            if o["final_total"]:
                ctk.CTkLabel(
                    right,
                    text=f"₹{float(o['final_total']):,.2f}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=palette["success"]
                ).pack(side="right")
            else:
                ctk.CTkLabel(
                    right,
                    text="Pending Bill",
                    font=ctk.CTkFont(size=11, slant="italic"),
                    text_color=palette["warning"]
                ).pack(side="right")
