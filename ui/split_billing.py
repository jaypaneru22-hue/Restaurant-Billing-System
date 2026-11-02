"""Split Billing Dialog for Equal and Custom Dining Party Settlement (Phase F)."""
from typing import Optional, Callable, List, Dict
from decimal import Decimal
import customtkinter as ctk

from ui.theme_manager import theme_manager
from database.db import db
from models.bill import Bill
from models.order import Order
from utils.window_utils import center_dialog


class SplitBillingDialog(ctk.CTkToplevel):
    """Modern modal dialog allowing dining guests to divide a tax invoice equally or with custom amounts."""

    def __init__(self, master, bill: Bill, order: Order, on_settled: Optional[Callable] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.bill = bill
        self.order = order
        self.on_settled = on_settled
        self.split_mode = "EQUAL"  # EQUAL or CUSTOM
        self.split_shares: List[Decimal] = []

        self.title(f"Split Bill — #{self.bill.bill_number}")
        self.resizable(False, False)
        center_dialog(self, master, target_width=500, target_height=480, min_width=460, min_height=440)
        self.grab_set()

        self._build_ui()
        self._calculate_equal_split()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Header
        ctk.CTkLabel(
            self,
            text=f"💳 Split Bill #{self.bill.bill_number}",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(padx=20, pady=(15, 2), anchor="w")

        ctk.CTkLabel(
            self,
            text=f"Total Amount Payable: ₹{self.bill.final_total:,.2f}  •  Table: {self.order.table_number}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=palette["accent"]
        ).pack(padx=20, pady=(0, 10), anchor="w")

        # Split Mode Segmented Switch
        mode_box = ctk.CTkFrame(self, fg_color="transparent")
        mode_box.pack(fill="x", padx=20, pady=(0, 10))

        self.seg_mode = ctk.CTkSegmentedButton(
            mode_box,
            values=["Equal Party Split", "Custom Guest Amounts"],
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_mode_change
        )
        self.seg_mode.set("Equal Party Split")
        self.seg_mode.pack(fill="x")

        # Container Frame
        self.content_frame = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Bottom Bar
        bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=20, pady=(0, 15))

        self.lbl_status = ctk.CTkLabel(bottom_bar, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["danger"])
        self.lbl_status.pack(side="left")

        ctk.CTkButton(
            bottom_bar,
            text="Close",
            width=90,
            height=32,
            fg_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

        self.btn_confirm = ctk.CTkButton(
            bottom_bar,
            text="✓ Confirm Split Payments",
            width=180,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._handle_confirm_split
        )
        self.btn_confirm.pack(side="right")

    def _on_mode_change(self, val: str):
        if val == "Equal Party Split":
            self.split_mode = "EQUAL"
            self._render_equal_split()
        else:
            self.split_mode = "CUSTOM"
            self._render_custom_split()

    def _render_equal_split(self):
        palette = theme_manager.get_palette()
        for w in self.content_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.content_frame,
            text="Divide total equally among dining party:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", padx=16, pady=(12, 6))

        # Number of guests selector
        r = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        r.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(r, text="Number of Diners:", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"]).pack(side="left")

        self.spin_guests = ctk.CTkOptionMenu(
            r,
            values=["2 Diners", "3 Diners", "4 Diners", "5 Diners", "6 Diners"],
            width=120,
            height=30,
            command=lambda *_: self._calculate_equal_split()
        )
        self.spin_guests.set("2 Diners")
        self.spin_guests.pack(side="left", padx=10)

        # Result box
        self.result_box = ctk.CTkFrame(self.content_frame, fg_color=palette["bg_secondary"], corner_radius=8)
        self.result_box.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self._calculate_equal_split()

    def _calculate_equal_split(self):
        palette = theme_manager.get_palette()
        guests_str = getattr(self, "spin_guests", None)
        guests_count = int(guests_str.get().split()[0]) if guests_str else 2

        total = Decimal(str(self.bill.final_total))
        base_share = (total / Decimal(guests_count)).quantize(Decimal("0.01"))
        remainder = total - (base_share * guests_count)

        self.split_shares = [base_share] * guests_count
        # Reconcile penny remainder onto the first guest so sum(shares) == total exactly
        if remainder != Decimal("0.00"):
            self.split_shares[0] += remainder

        assert sum(self.split_shares) == total, "Split amounts must sum exactly to bill total"

        if hasattr(self, "result_box"):
            for w in self.result_box.winfo_children():
                w.destroy()

            ctk.CTkLabel(
                self.result_box,
                text=f"Total Divided Exactly: ₹{total:,.2f} across {guests_count} Guests",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=palette["text_secondary"]
            ).pack(anchor="w", padx=12, pady=(10, 6))

            for idx, share in enumerate(self.split_shares):
                row = ctk.CTkFrame(self.result_box, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=2)
                ctk.CTkLabel(row, text=f"Guest #{idx + 1} Share:", font=ctk.CTkFont(size=11), text_color=palette["text_primary"]).pack(side="left")
                ctk.CTkLabel(row, text=f"₹{share:,.2f}", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["success"]).pack(side="right")

    def _render_custom_split(self):
        palette = theme_manager.get_palette()
        for w in self.content_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.content_frame,
            text="Enter custom amount for 2 dining guests:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", padx=16, pady=(12, 6))

        total = Decimal(str(self.bill.final_total))

        # Guest 1 Input
        g1_row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        g1_row.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(g1_row, text="Guest 1 Amount (₹):", width=140, anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(side="left")
        self.entry_g1 = ctk.CTkEntry(g1_row, height=30)
        half = (total / Decimal("2")).quantize(Decimal("0.01"))
        self.entry_g1.insert(0, str(half))
        self.entry_g1.pack(side="left", fill="x", expand=True)
        self.entry_g1.bind("<KeyRelease>", lambda e: self._on_custom_input_change())

        # Guest 2 Input
        g2_row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        g2_row.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(g2_row, text="Guest 2 Amount (₹):", width=140, anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(side="left")
        self.entry_g2 = ctk.CTkEntry(g2_row, height=30)
        self.entry_g2.insert(0, str(total - half))
        self.entry_g2.pack(side="left", fill="x", expand=True)
        self.entry_g2.bind("<KeyRelease>", lambda e: self._on_custom_input_change())

        self.lbl_custom_diff = ctk.CTkLabel(self.content_frame, text="Sum matches bill total exactly (Balanced)", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["success"])
        self.lbl_custom_diff.pack(padx=16, pady=(8, 12))

    def _on_custom_input_change(self):
        palette = theme_manager.get_palette()
        try:
            v1 = Decimal(self.entry_g1.get().strip() or "0")
            v2 = Decimal(self.entry_g2.get().strip() or "0")
            tot = Decimal(str(self.bill.final_total))
            diff = (v1 + v2) - tot

            if abs(diff) < Decimal("0.01"):
                self.lbl_custom_diff.configure(text="✓ Sum matches bill total exactly (Balanced)", text_color=palette["success"])
                self.btn_confirm.configure(state="normal")
            elif diff > Decimal("0"):
                self.lbl_custom_diff.configure(text=f"⚠️ Overpayment by ₹{diff:,.2f}", text_color=palette["danger"])
                self.btn_confirm.configure(state="disabled")
            else:
                self.lbl_custom_diff.configure(text=f"⚠️ Underpayment by ₹{abs(diff):,.2f}", text_color=palette["danger"])
                self.btn_confirm.configure(state="disabled")
        except Exception:
            self.lbl_custom_diff.configure(text="Invalid numerical amount", text_color=palette["danger"])
            self.btn_confirm.configure(state="disabled")

    def _handle_confirm_split(self):
        palette = theme_manager.get_palette()
        try:
            db.execute(
                """INSERT INTO audit_logs (username, action, module, details)
                   VALUES ('Cashier', 'SPLIT_BILL_SETTLED', 'BILLING', ?);""",
                (f"Settled Split Bill #{self.bill.bill_number} (Total ₹{self.bill.final_total}) into {len(self.split_shares)} shares",)
            )
            self.lbl_status.configure(text="✓ Split billing settled successfully.", text_color=palette["success"])
            if self.on_settled:
                self.on_settled()
            self.after(500, self.destroy)
        except Exception as e:
            self.lbl_status.configure(text=f"Error: {e}")
