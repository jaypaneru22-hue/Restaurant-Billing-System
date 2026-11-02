"""Cashier Shift Summary & Register Closeout View."""
from typing import Optional
from datetime import datetime
import customtkinter as ctk

from ui.theme_manager import theme_manager
from database.db import db
from utils.window_utils import center_dialog
from utils.logger import logger


class ShiftCloseoutModal(ctk.CTkToplevel):
    """Modal displaying formatted thermal-style shift closeout report."""

    def __init__(self, master, report_text: str, **kwargs):
        super().__init__(master, **kwargs)
        self.title("End of Shift Closeout Report")
        self.resizable(False, False)
        center_dialog(self, master, target_width=440, target_height=520, min_width=420, min_height=480)
        self.grab_set()

        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        ctk.CTkLabel(
            self,
            text="🧾 Shift Closeout Slip",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(padx=20, pady=(15, 6), anchor="w")

        txt_frame = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
        txt_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.textbox = ctk.CTkTextbox(txt_frame, font=ctk.CTkFont(family="Consolas", size=11), border_width=0)
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.insert("1.0", report_text)
        self.textbox.configure(state="disabled")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_row,
            text="Close (Esc)",
            width=100,
            height=32,
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self.destroy
        ).pack(side="right")
        self.bind("<Escape>", lambda e: self.destroy())


class ShiftSummaryFrame(ctk.CTkFrame):
    """Cashier interface for shift closeout, denomination reconciliation, and drawer balance verification."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.denominations = {500: 0, 200: 0, 100: 0, 50: 0, 20: 0, 10: 0}
        self.denom_vars = {}

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
            text="💼 Cashier Shift Summary & Drawer Closeout",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Verify cash drawer intake, enter physical note counts, and generate final shift closeout receipts.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

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
            self.total_bills = total_rev_row[0]
            self.total_sales = float(total_rev_row[1])

            cash_row = db.fetchone("SELECT COALESCE(SUM(final_total), 0.0) FROM bills WHERE payment_method = 'CASH';")
            self.cash_sales = float(cash_row[0]) if cash_row else 0.0

            card_row = db.fetchone("SELECT COALESCE(SUM(final_total), 0.0) FROM bills WHERE payment_method = 'CARD';")
            self.card_sales = float(card_row[0]) if card_row else 0.0

            upi_row = db.fetchone("SELECT COALESCE(SUM(final_total), 0.0) FROM bills WHERE payment_method = 'UPI';")
            self.upi_sales = float(upi_row[0]) if upi_row else 0.0
        except Exception as e:
            logger.error(f"Error querying shift data: {e}")
            self.total_bills = 0
            self.total_sales = 0.0
            self.cash_sales = 0.0
            self.card_sales = 0.0
            self.upi_sales = 0.0

        self.starting_float = 2000.00
        self.expected_cash = self.starting_float + self.cash_sales

        # Render KPI Cards
        for w in self.kpi_container.winfo_children():
            w.destroy()

        kpis = [
            ("Shift Sales Total", f"₹{self.total_sales:,.2f}", "💰", "#10B981"),
            ("Expected Cash Drawer", f"₹{self.expected_cash:,.2f}", "💵", "#3B82F6"),
            ("Card Swipe Volume", f"₹{self.card_sales:,.2f}", "💳", "#F59E0B"),
            ("UPI / QR Volume", f"₹{self.upi_sales:,.2f}", "📱", "#8B5CF6")
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

        # Two-column layout: Left = Denomination Tally, Right = Closeout Summary & Finalize
        split_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        split_frame.pack(fill="x", padx=6, pady=4)
        split_frame.columnconfigure((0, 1), weight=1)

        # Left Column: Cash Drawer Note Counter
        c1 = ctk.CTkFrame(split_frame, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)

        ctk.CTkLabel(c1, text="💵 Cash Drawer Denomination Tally", font=ctk.CTkFont(size=13, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(anchor="w", padx=14, pady=(12, 6))
        ctk.CTkLabel(c1, text="Count physical notes in the cash drawer at shift end:", font=ctk.CTkFont(size=10), text_color=palette["text_secondary"]).pack(anchor="w", padx=14, pady=(0, 10))

        # Denomination inputs
        self.denom_vars = {}
        for denom in [500, 200, 100, 50, 20, 10]:
            r = ctk.CTkFrame(c1, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=3)

            ctk.CTkLabel(r, text=f"₹{denom} Notes:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"], width=90, anchor="w").pack(side="left")

            var = ctk.StringVar(value="0")
            var.trace_add("write", lambda *_: self._recalculate_drawer_tally())
            self.denom_vars[denom] = var

            entry = ctk.CTkEntry(r, textvariable=var, width=70, height=28, border_color=palette["border"], justify="center")
            entry.pack(side="left", padx=8)

            sub_lbl = ctk.CTkLabel(r, text="= ₹0.00", font=ctk.CTkFont(size=11), text_color=palette["text_secondary"], width=100, anchor="e")
            sub_lbl.pack(side="right")
            self.denom_vars[f"sub_{denom}"] = sub_lbl

        ctk.CTkLabel(c1, text="", height=8).pack()

        # Right Column: Shift Reconciliation & Actions
        c2 = ctk.CTkFrame(split_frame, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        c2.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)

        ctk.CTkLabel(c2, text="⚖️ Shift Reconciliation & Balancing", font=ctk.CTkFont(size=13, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(anchor="w", padx=14, pady=(12, 6))

        # Reconciliation Rows
        recon_box = ctk.CTkFrame(c2, fg_color=palette["bg_secondary"], corner_radius=8)
        recon_box.pack(fill="x", padx=14, pady=(4, 10))

        def make_row(lbl, val_str, color=palette["text_primary"], bold=False):
            rf = ctk.CTkFrame(recon_box, fg_color="transparent")
            rf.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(rf, text=lbl, font=ctk.CTkFont(size=11), text_color=palette["text_secondary"]).pack(side="left")
            val_lbl = ctk.CTkLabel(rf, text=val_str, font=ctk.CTkFont(size=11, weight="bold" if bold else "normal"), text_color=color)
            val_lbl.pack(side="right")
            return val_lbl

        make_row("Starting Cash Reserve (Float)", f"₹{self.starting_float:,.2f}")
        make_row("Shift Cash Sales Intake", f"+ ₹{self.cash_sales:,.2f}")
        make_row("Non-Cash Sales (Card + UPI)", f"₹{self.card_sales + self.upi_sales:,.2f}")

        div = ctk.CTkFrame(recon_box, height=1, fg_color=palette["border"])
        div.pack(fill="x", padx=12, pady=4)

        make_row("Total Expected Cash in Drawer", f"₹{self.expected_cash:,.2f}", color=palette["accent"], bold=True)
        self.counted_lbl = make_row("Physical Counted Cash", "₹0.00", color=palette.get("heading", palette["text_primary"]), bold=True)
        self.variance_lbl = make_row("Cash Variance (Discrepancy)", f"- ₹{self.expected_cash:,.2f} (SHORT)", color="#EF4444", bold=True)

        # Action Buttons
        btn_box = ctk.CTkFrame(c2, fg_color="transparent")
        btn_box.pack(fill="x", padx=14, pady=(10, 14))

        ctk.CTkButton(
            btn_box,
            text="🧾 View Shift Closeout Slip",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=34,
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._generate_closeout_slip
        ).pack(fill="x", pady=(0, 8))

        self.btn_finalize = ctk.CTkButton(
            btn_box,
            text="🔒 Finalize & Close Active Shift",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=34,
            fg_color="#10B981",
            hover_color="#059669",
            command=self._finalize_shift
        )
        self.btn_finalize.pack(fill="x")

        self.lbl_close_status = ctk.CTkLabel(btn_box, text="", font=ctk.CTkFont(size=11, weight="bold"))
        self.lbl_close_status.pack(pady=(4, 0))

        self._recalculate_drawer_tally()

    def _recalculate_drawer_tally(self):
        palette = theme_manager.get_palette()
        total_counted = 0.0

        for denom in [500, 200, 100, 50, 20, 10]:
            var = self.denom_vars.get(denom)
            sub_lbl = self.denom_vars.get(f"sub_{denom}")
            if var and sub_lbl:
                val_txt = var.get().strip()
                count = int(val_txt) if val_txt.isdigit() else 0
                subtotal = count * denom
                total_counted += subtotal
                sub_lbl.configure(text=f"= ₹{subtotal:,.2f}")

        self.counted_cash = total_counted
        variance = self.counted_cash - self.expected_cash

        if hasattr(self, "counted_lbl"):
            self.counted_lbl.configure(text=f"₹{self.counted_cash:,.2f}")

        if hasattr(self, "variance_lbl"):
            if abs(variance) < 0.01:
                self.variance_lbl.configure(text="₹0.00 (EXACT MATCH / BALANCED)", text_color="#10B981")
            elif variance > 0:
                self.variance_lbl.configure(text=f"+ ₹{variance:,.2f} (DRAWER OVER)", text_color="#3B82F6")
            else:
                self.variance_lbl.configure(text=f"- ₹{abs(variance):,.2f} (DRAWER SHORT)", text_color="#EF4444")

    def _generate_closeout_slip(self):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        variance = getattr(self, "counted_cash", 0.0) - self.expected_cash
        var_text = "BALANCED (0.00)" if abs(variance) < 0.01 else (f"OVER (+₹{variance:.2f})" if variance > 0 else f"SHORT (-₹{abs(variance):.2f})")

        report = f"""========================================
     RESTAURANT MANAGEMENT PLATFORM
     DAILY CASHIER SHIFT CLOSEOUT SLIP
========================================
Terminal ID       : POS-COUNTER-01
Timestamp         : {now_str}
Total Bills       : {self.total_bills} completed

----------------------------------------
SHIFT FINANCIAL TELEMETRY
----------------------------------------
Gross Sales       : ₹{self.total_sales:>12,.2f}
Cash Intake       : ₹{self.cash_sales:>12,.2f}
Card Intake       : ₹{self.card_sales:>12,.2f}
UPI / QR Intake   : ₹{self.upi_sales:>12,.2f}

----------------------------------------
CASH DRAWER RECONCILIATION
----------------------------------------
Starting Float    : ₹{self.starting_float:>12,.2f}
Expected Cash     : ₹{self.expected_cash:>12,.2f}
Physical Counted  : ₹{getattr(self, 'counted_cash', 0.0):>12,.2f}
Cash Variance     : {var_text:>15}

----------------------------------------
STATUS: RECONCILED & AUDITED
Operator Signature: ____________________
========================================
"""
        ShiftCloseoutModal(self, report_text=report)

    def _finalize_shift(self):
        if getattr(self, "_is_shift_closed", False):
            return
        palette = theme_manager.get_palette()
        variance = getattr(self, "counted_cash", 0.0) - self.expected_cash
        try:
            db.execute(
                """INSERT INTO audit_logs (username, action, module, details)
                   VALUES ('Cashier', 'CLOSE_SHIFT', 'SHIFT_RECONCILIATION', ?);""",
                (f"Finalized shift: Sales ₹{self.total_sales:.2f}, Counted Cash ₹{getattr(self, 'counted_cash', 0.0):.2f}, Variance ₹{variance:.2f}",)
            )
            self._is_shift_closed = True
            if hasattr(self, "btn_finalize"):
                self.btn_finalize.configure(state="disabled", text="✓ Shift Closed & Audited")
            if hasattr(self, "lbl_close_status"):
                self.lbl_close_status.configure(text="✓ Shift successfully closed and audited in SQLite.", text_color=palette["success"])
            self._generate_closeout_slip()
        except Exception as e:
            logger.error(f"Error finalizing shift: {e}")
