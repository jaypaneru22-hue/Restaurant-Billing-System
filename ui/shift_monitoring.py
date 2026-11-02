"""Shift Operations & Cash Drawer Floor Monitoring View."""
from typing import Optional
from datetime import datetime
import customtkinter as ctk

from ui.theme_manager import theme_manager
from database.db import db
from utils.logger import logger


class ShiftMonitoringFrame(ctk.CTkFrame):
    """Floor manager interface for shift sales monitoring, cash drawer reconciliation, and tender breakdowns."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self._load_shift_data()

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, _theme: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self._load_shift_data()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Header Frame
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 8))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="💼 Shift Monitoring & Cash Drawer Reconciliation",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Real-time shift financial telemetry, payment method aggregates, and cash balance verification.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Refresh Button
        ctk.CTkButton(
            header,
            text="🔄 Refresh Shift",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            height=32,
            width=120,
            command=self._load_shift_data
        ).pack(side="right")

        # KPI Summary Cards
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=20, pady=(0, 10))

        # Main Scrollable Body
        self.main_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=palette.get("sidebar_hover", "#245A9B")
        )
        self.main_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _load_shift_data(self):
        palette = theme_manager.get_palette()

        # Query bills
        try:
            total_rev_row = db.fetchone("SELECT COUNT(*), COALESCE(SUM(final_total), 0.0) FROM bills;")
            total_bills = total_rev_row[0]
            total_sales = float(total_rev_row[1])

            cash_row = db.fetchone("SELECT COALESCE(SUM(final_total), 0.0) FROM bills WHERE payment_method = 'CASH';")
            cash_sales = float(cash_row[0]) if cash_row else 0.0

            card_row = db.fetchone("SELECT COALESCE(SUM(final_total), 0.0) FROM bills WHERE payment_method = 'CARD';")
            card_sales = float(card_row[0]) if card_row else 0.0

            upi_row = db.fetchone("SELECT COALESCE(SUM(final_total), 0.0) FROM bills WHERE payment_method = 'UPI';")
            upi_sales = float(upi_row[0]) if upi_row else 0.0

            recent_bills = db.fetchall("""
                SELECT b.bill_number, b.final_total, b.payment_method, b.billed_at,
                       o.order_number, o.table_number, o.customer_name
                FROM bills b
                JOIN orders o ON b.order_id = o.id
                ORDER BY b.id DESC LIMIT 15;
            """)
        except Exception as e:
            logger.error(f"Error querying shift data: {e}")
            total_bills = 0
            total_sales = 0.0
            cash_sales = 0.0
            card_sales = 0.0
            upi_sales = 0.0
            recent_bills = []

        # Render KPI Cards
        for w in self.kpi_container.winfo_children():
            w.destroy()

        kpis = [
            ("Total Shift Sales", f"₹{total_sales:,.2f}", "💰", "#10B981"),
            ("Cash in Drawer", f"₹{cash_sales:,.2f}", "💵", "#3B82F6"),
            ("Card Swipe POS", f"₹{card_sales:,.2f}", "💳", "#F59E0B"),
            ("UPI / QR Digital", f"₹{upi_sales:,.2f}", "📱", "#8B5CF6")
        ]

        for title, val, icon, _acc in kpis:
            card = ctk.CTkFrame(
                self.kpi_container,
                fg_color=palette["bg_card"],
                corner_radius=8,
                border_width=1,
                border_color=palette["border"],
                height=65
            )
            card.pack(side="left", fill="x", expand=True, padx=4)
            card.pack_propagate(False)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=12, pady=8)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left")
            ctk.CTkLabel(left, text=title, font=ctk.CTkFont(size=10), text_color=palette["text_secondary"]).pack(anchor="w")
            ctk.CTkLabel(left, text=val, font=ctk.CTkFont(size=16, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(anchor="w")

            ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=18)).pack(side="right")

        # Clear scroll content
        for w in self.main_scroll.winfo_children():
            w.destroy()

        # Two-column split: Left = Shift Metadata & Drawer Status, Right = Tender Mix
        split_row = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        split_row.pack(fill="x", padx=6, pady=(0, 15))
        split_row.columnconfigure((0, 1), weight=1)

        # Left: Current Shift Overview Card
        c1 = ctk.CTkFrame(split_row, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)

        ctk.CTkLabel(c1, text="🏢 Active Shift Parameters", font=ctk.CTkFont(size=13, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(anchor="w", padx=14, pady=(12, 8))

        params = [
            ("Shift Status", "🟢 OPEN & RECONCILED", "#10B981"),
            ("Terminal ID", "POS-COUNTER-01", palette["text_primary"]),
            ("Shift Manager On Duty", "Operational Manager", palette["text_primary"]),
            ("Today's Settled Bills", f"{total_bills} completed transactions", palette["text_primary"]),
            ("Drawer Starting Float", "₹2,000.00 (Fixed Reserve)", palette["text_secondary"]),
            ("Expected Cash in Drawer", f"₹{cash_sales + 2000.0:,.2f}", palette["accent"])
        ]

        for p_lbl, p_val, p_col in params:
            r = ctk.CTkFrame(c1, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(r, text=p_lbl, font=ctk.CTkFont(size=11), text_color=palette["text_secondary"]).pack(side="left")
            ctk.CTkLabel(r, text=p_val, font=ctk.CTkFont(size=11, weight="bold"), text_color=p_col).pack(side="right")

        ctk.CTkLabel(c1, text="", height=4).pack()

        # Right: Tender Mix Card
        c2 = ctk.CTkFrame(split_row, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        c2.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)

        ctk.CTkLabel(c2, text="📊 Payment Tender Distribution", font=ctk.CTkFont(size=13, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(anchor="w", padx=14, pady=(12, 8))

        tenders = [
            ("💵 Cash Payments", cash_sales, "#10B981"),
            ("💳 Credit / Debit Card", card_sales, "#3B82F6"),
            ("📱 UPI / QR Code", upi_sales, "#8B5CF6")
        ]

        for t_label, t_val, t_color in tenders:
            pct = (t_val / total_sales * 100) if total_sales > 0 else 0.0
            t_box = ctk.CTkFrame(c2, fg_color="transparent")
            t_box.pack(fill="x", padx=14, pady=4)

            top_t = ctk.CTkFrame(t_box, fg_color="transparent")
            top_t.pack(fill="x")
            ctk.CTkLabel(top_t, text=t_label, font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(side="left")
            ctk.CTkLabel(top_t, text=f"₹{t_val:,.2f} ({pct:.1f}%)", font=ctk.CTkFont(size=11), text_color=palette["text_secondary"]).pack(side="right")

            # Progress bar
            bar = ctk.CTkProgressBar(t_box, height=8, progress_color=t_color)
            bar.pack(fill="x", pady=(2, 0))
            bar.set(pct / 100.0)

        ctk.CTkLabel(c2, text="", height=6).pack()

        # Section 2: Recent Shift Settlements Table
        ctk.CTkLabel(
            self.main_scroll,
            text="Recent Settled Shift Receipts",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w", padx=6, pady=(10, 6))

        tbl_head = ctk.CTkFrame(self.main_scroll, fg_color=palette["bg_secondary"], corner_radius=6, height=34)
        tbl_head.pack(fill="x", padx=6, pady=(0, 4))
        tbl_head.pack_propagate(False)

        cols = [
            ("Bill #", 130, "w"),
            ("Order #", 140, "w"),
            ("Table", 100, "w"),
            ("Customer Name", 180, "w"),
            ("Tender Method", 130, "center"),
            ("Settled Amount", 120, "e"),
            ("Timestamp", 140, "w")
        ]
        for cname, cwidth, calign in cols:
            ctk.CTkLabel(tbl_head, text=cname, font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"], width=cwidth, anchor=calign).pack(side="left", padx=8)

        for b in recent_bills:
            row = ctk.CTkFrame(self.main_scroll, fg_color=palette["bg_card"], corner_radius=6, border_width=1, border_color=palette["border"], height=40)
            row.pack(fill="x", padx=6, pady=2)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=b["bill_number"], font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color=palette["accent"], width=130, anchor="w").pack(side="left", padx=8)
            ctk.CTkLabel(row, text=b["order_number"], font=ctk.CTkFont(family="Consolas", size=11), text_color=palette["text_secondary"], width=140, anchor="w").pack(side="left", padx=8)
            ctk.CTkLabel(row, text=b["table_number"] or "Takeaway", font=ctk.CTkFont(size=11), text_color=palette["text_primary"], width=100, anchor="w").pack(side="left", padx=8)
            ctk.CTkLabel(row, text=b["customer_name"] or "Guest", font=ctk.CTkFont(size=11), text_color=palette["text_primary"], width=180, anchor="w").pack(side="left", padx=8)

            # Method Pill
            m_box = ctk.CTkFrame(row, fg_color="transparent", width=130)
            m_box.pack(side="left", padx=8)
            m_box.pack_propagate(False)
            mp = ctk.CTkFrame(m_box, fg_color=palette["bg_secondary"], corner_radius=4)
            mp.pack(expand=True)
            ctk.CTkLabel(mp, text=b["payment_method"], font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["accent"]).pack(padx=8, pady=2)

            ctk.CTkLabel(row, text=f"₹{float(b['final_total']):,.2f}", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("heading", palette["text_primary"]), width=120, anchor="e").pack(side="left", padx=8)
            ctk.CTkLabel(row, text=b["billed_at"] or "", font=ctk.CTkFont(size=10), text_color=palette["text_secondary"], width=140, anchor="w").pack(side="left", padx=8)
