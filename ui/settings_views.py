"""Restaurant Profile and Billing & Tax Configuration views."""
from typing import Optional
from decimal import Decimal
import customtkinter as ctk

from database.db import DatabaseManager, db
from ui.theme_manager import theme_manager
from config.settings import CURRENCY_SYMBOL


class RestaurantSettingsFrame(ctk.CTkFrame):
    """Real Restaurant Profile & Legal Identity management screen."""

    def __init__(self, master, db_manager: DatabaseManager = db, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db_manager

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self.load_data()

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        # Header
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 12))

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left")

        ctk.CTkLabel(
            title_col,
            text="🏢 Restaurant Profile & Legal Identity",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="Configure official restaurant business details, GSTIN tax registration and receipt branding",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        act_box = ctk.CTkFrame(header, fg_color="transparent")
        act_box.pack(side="right")

        ctk.CTkButton(
            act_box,
            text="💾 Save Profile",
            width=120,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self.save_data
        ).pack(side="left", padx=4)

        # Status toast
        self.lbl_status = ctk.CTkLabel(self.scroll, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["success"])
        self.lbl_status.pack(anchor="w", padx=24, pady=(0, 10))

        # Card 1: Business Identity
        c1 = ctk.CTkFrame(self.scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        c1.pack(fill="x", padx=24, pady=(0, 14))

        ctk.CTkLabel(c1, text="1. Business Identity & Branding", font=ctk.CTkFont(size=13, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(anchor="w", padx=16, pady=(12, 10))

        g1 = ctk.CTkFrame(c1, fg_color="transparent")
        g1.pack(fill="x", padx=16, pady=(0, 14))
        g1.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(g1, text="Restaurant Legal Name *", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 2))
        self.entry_name = ctk.CTkEntry(g1, height=34, font=ctk.CTkFont(size=12))
        self.entry_name.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 10))

        ctk.CTkLabel(g1, text="Brand Tagline / Slogan", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=0, column=1, sticky="w", padx=(8, 0), pady=(0, 2))
        self.entry_tagline = ctk.CTkEntry(g1, height=34, font=ctk.CTkFont(size=12))
        self.entry_tagline.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(0, 10))

        # Card 2: Contact Details & Location
        c2 = ctk.CTkFrame(self.scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        c2.pack(fill="x", padx=24, pady=(0, 14))

        ctk.CTkLabel(c2, text="2. Contact Details & Premises Location", font=ctk.CTkFont(size=13, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(anchor="w", padx=16, pady=(12, 10))

        g2 = ctk.CTkFrame(c2, fg_color="transparent")
        g2.pack(fill="x", padx=16, pady=(0, 14))
        g2.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(g2, text="Full Address (Printed on Invoices) *", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))
        self.entry_address = ctk.CTkEntry(g2, height=34, font=ctk.CTkFont(size=12))
        self.entry_address.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(g2, text="Telephone / Contact Number *", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 2))
        self.entry_phone = ctk.CTkEntry(g2, height=34, font=ctk.CTkFont(size=12))
        self.entry_phone.grid(row=3, column=0, sticky="ew", padx=(0, 8), pady=(0, 10))

        ctk.CTkLabel(g2, text="Official Email Address", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(0, 2))
        self.entry_email = ctk.CTkEntry(g2, height=34, font=ctk.CTkFont(size=12))
        self.entry_email.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(0, 10))

        # Card 3: Legal & Regulatory
        c3 = ctk.CTkFrame(self.scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        c3.pack(fill="x", padx=24, pady=(0, 14))

        ctk.CTkLabel(c3, text="3. Legal & Regulatory Registrations", font=ctk.CTkFont(size=13, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(anchor="w", padx=16, pady=(12, 10))

        g3 = ctk.CTkFrame(c3, fg_color="transparent")
        g3.pack(fill="x", padx=16, pady=(0, 14))
        g3.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(g3, text="GSTIN Registration Number *", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 2))
        self.entry_gstin = ctk.CTkEntry(g3, height=34, font=ctk.CTkFont(size=12))
        self.entry_gstin.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 10))

        ctk.CTkLabel(g3, text="FSSAI Food License Number", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=0, column=1, sticky="w", padx=(8, 0), pady=(0, 2))
        self.entry_fssai = ctk.CTkEntry(g3, height=34, font=ctk.CTkFont(size=12))
        self.entry_fssai.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(0, 10))

        # Card 4: Receipt Template
        c4 = ctk.CTkFrame(self.scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        c4.pack(fill="x", padx=24, pady=(0, 20))

        ctk.CTkLabel(c4, text="4. Customer Receipt Customization", font=ctk.CTkFont(size=13, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(anchor="w", padx=16, pady=(12, 10))

        g4 = ctk.CTkFrame(c4, fg_color="transparent")
        g4.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(g4, text="Receipt Header Greeting Text", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).pack(anchor="w", pady=(0, 2))
        self.entry_rec_header = ctk.CTkEntry(g4, height=34, font=ctk.CTkFont(size=12))
        self.entry_rec_header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(g4, text="Receipt Footer Policy / Note", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).pack(anchor="w", pady=(0, 2))
        self.entry_rec_footer = ctk.CTkEntry(g4, height=34, font=ctk.CTkFont(size=12))
        self.entry_rec_footer.pack(fill="x", pady=(0, 6))

    def load_data(self):
        row = self.db.fetchone("SELECT * FROM restaurant_profile WHERE id = 1;")
        if row:
            self.entry_name.delete(0, "end"); self.entry_name.insert(0, row["restaurant_name"] or "")
            self.entry_tagline.delete(0, "end"); self.entry_tagline.insert(0, row["tagline"] or "")
            self.entry_address.delete(0, "end"); self.entry_address.insert(0, row["address"] or "")
            self.entry_phone.delete(0, "end"); self.entry_phone.insert(0, row["phone"] or "")
            self.entry_email.delete(0, "end"); self.entry_email.insert(0, row["email"] or "")
            self.entry_gstin.delete(0, "end"); self.entry_gstin.insert(0, row["gstin"] or "")
            self.entry_fssai.delete(0, "end"); self.entry_fssai.insert(0, row["fssai_license"] or "")
            self.entry_rec_header.delete(0, "end"); self.entry_rec_header.insert(0, row["receipt_header"] or "")
            self.entry_rec_footer.delete(0, "end"); self.entry_rec_footer.insert(0, row["receipt_footer"] or "")

    def save_data(self):
        palette = theme_manager.get_palette()
        with self.db.transaction() as conn:
            conn.execute(
                """UPDATE restaurant_profile
                   SET restaurant_name = ?, tagline = ?, address = ?, phone = ?, email = ?,
                       gstin = ?, fssai_license = ?, receipt_header = ?, receipt_footer = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = 1;""",
                (
                    self.entry_name.get().strip(), self.entry_tagline.get().strip(),
                    self.entry_address.get().strip(), self.entry_phone.get().strip(),
                    self.entry_email.get().strip(), self.entry_gstin.get().strip(),
                    self.entry_fssai.get().strip(), self.entry_rec_header.get().strip(),
                    self.entry_rec_footer.get().strip()
                )
            )
            conn.execute(
                """INSERT INTO audit_logs (username, action, module, details)
                   VALUES ('Admin', 'UPDATE_PROFILE', 'RESTAURANT', ?);""",
                (f"Updated profile for {self.entry_name.get().strip()}",)
            )
        self.lbl_status.configure(text="✓ Restaurant Profile saved successfully.", text_color=palette["success"])


class BillingTaxSettingsFrame(ctk.CTkFrame):
    """Real Billing, Tax & Payment Gateway Configuration screen."""

    def __init__(self, master, db_manager: DatabaseManager = db, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db_manager

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self.load_data()

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        # Header
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 12))

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left")

        ctk.CTkLabel(
            title_col,
            text="💳 Billing, Tax & Payment Configuration",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="Configure GST tax slabs (CGST/SGST), service charge toggle, discount caps and active payment channels",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        act_box = ctk.CTkFrame(header, fg_color="transparent")
        act_box.pack(side="right")

        ctk.CTkButton(
            act_box,
            text="💾 Save Rules",
            width=120,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self.save_data
        ).pack(side="left", padx=4)

        self.lbl_status = ctk.CTkLabel(self.scroll, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["success"])
        self.lbl_status.pack(anchor="w", padx=24, pady=(0, 10))

        # Card 1: GST Tax Rates
        c1 = ctk.CTkFrame(self.scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        c1.pack(fill="x", padx=24, pady=(0, 14))

        ctk.CTkLabel(c1, text="1. Goods & Services Tax (GST) Slabs", font=ctk.CTkFont(size=13, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(anchor="w", padx=16, pady=(12, 10))

        g1 = ctk.CTkFrame(c1, fg_color="transparent")
        g1.pack(fill="x", padx=16, pady=(0, 14))
        g1.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(g1, text="CGST Rate (%) *", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 2))
        self.entry_cgst = ctk.CTkEntry(g1, height=34, font=ctk.CTkFont(size=12))
        self.entry_cgst.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(0, 6))

        ctk.CTkLabel(g1, text="SGST Rate (%) *", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=0, column=1, sticky="w", padx=6, pady=(0, 2))
        self.entry_sgst = ctk.CTkEntry(g1, height=34, font=ctk.CTkFont(size=12))
        self.entry_sgst.grid(row=1, column=1, sticky="ew", padx=6, pady=(0, 6))

        ctk.CTkLabel(g1, text="Total GST Rate (%)", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=0, column=2, sticky="w", padx=(6, 0), pady=(0, 2))
        self.lbl_total_gst = ctk.CTkLabel(g1, text="5.0%", font=ctk.CTkFont(size=14, weight="bold"), text_color=palette["accent"])
        self.lbl_total_gst.grid(row=1, column=2, sticky="w", padx=(6, 0), pady=(0, 6))

        # Card 2: Service Charge & Discount Caps
        c2 = ctk.CTkFrame(self.scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        c2.pack(fill="x", padx=24, pady=(0, 14))

        ctk.CTkLabel(c2, text="2. Service Charges & Discount Governance", font=ctk.CTkFont(size=13, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(anchor="w", padx=16, pady=(12, 10))

        g2 = ctk.CTkFrame(c2, fg_color="transparent")
        g2.pack(fill="x", padx=16, pady=(0, 14))
        g2.grid_columnconfigure((0, 1), weight=1)

        self.switch_service_charge = ctk.CTkSwitch(g2, text="Enable Service Charge on Dine-In", font=ctk.CTkFont(size=11, weight="bold"))
        self.switch_service_charge.grid(row=0, column=0, sticky="w", pady=(0, 6))

        ctk.CTkLabel(g2, text="Service Charge Rate (%)", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=1, column=0, sticky="w", pady=(0, 2))
        self.entry_sc_rate = ctk.CTkEntry(g2, height=34, font=ctk.CTkFont(size=12), width=160)
        self.entry_sc_rate.grid(row=2, column=0, sticky="w", pady=(0, 10))

        self.switch_discounts = ctk.CTkSwitch(g2, text="Allow Cashier Discretionary Discounts", font=ctk.CTkFont(size=11, weight="bold"))
        self.switch_discounts.grid(row=0, column=1, sticky="w", pady=(0, 6))

        ctk.CTkLabel(g2, text="Maximum Allowable Discount (%) Cap", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=1, column=1, sticky="w", pady=(0, 2))
        self.entry_max_disc = ctk.CTkEntry(g2, height=34, font=ctk.CTkFont(size=12), width=160)
        self.entry_max_disc.grid(row=2, column=1, sticky="w", pady=(0, 10))

        # Card 3: Financial Rounding & Payment Channels
        c3 = ctk.CTkFrame(self.scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        c3.pack(fill="x", padx=24, pady=(0, 20))

        ctk.CTkLabel(c3, text="3. Payment Channels & Invoice Rounding", font=ctk.CTkFont(size=13, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(anchor="w", padx=16, pady=(12, 10))

        g3 = ctk.CTkFrame(c3, fg_color="transparent")
        g3.pack(fill="x", padx=16, pady=(0, 14))

        self.switch_round_off = ctk.CTkSwitch(g3, text="Round Final Invoice Amount to Nearest Whole Rupee", font=ctk.CTkFont(size=11, weight="bold"))
        self.switch_round_off.pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(g3, text="Active Payment Acceptance Channels at POS Terminals:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).pack(anchor="w", pady=(0, 6))

        ch_box = ctk.CTkFrame(g3, fg_color="transparent")
        ch_box.pack(fill="x")

        self.chk_cash = ctk.CTkCheckBox(ch_box, text="Cash Payment", font=ctk.CTkFont(size=11))
        self.chk_cash.select(); self.chk_cash.pack(side="left", padx=(0, 16))

        self.chk_card = ctk.CTkCheckBox(ch_box, text="Credit / Debit Card", font=ctk.CTkFont(size=11))
        self.chk_card.select(); self.chk_card.pack(side="left", padx=(0, 16))

        self.chk_upi = ctk.CTkCheckBox(ch_box, text="UPI / QR Code", font=ctk.CTkFont(size=11))
        self.chk_upi.select(); self.chk_upi.pack(side="left")

    def load_data(self):
        row = self.db.fetchone("SELECT * FROM billing_config WHERE id = 1;")
        if row:
            self.entry_cgst.delete(0, "end"); self.entry_cgst.insert(0, str(row["cgst_rate"]))
            self.entry_sgst.delete(0, "end"); self.entry_sgst.insert(0, str(row["sgst_rate"]))
            self.entry_sc_rate.delete(0, "end"); self.entry_sc_rate.insert(0, str(row["service_charge_rate"]))
            self.entry_max_disc.delete(0, "end"); self.entry_max_disc.insert(0, str(row["max_discount_percent"]))

            if row["enable_service_charge"]: self.switch_service_charge.select()
            else: self.switch_service_charge.deselect()

            if row["enable_discounts"]: self.switch_discounts.select()
            else: self.switch_discounts.deselect()

            if row["round_off_total"]: self.switch_round_off.select()
            else: self.switch_round_off.deselect()

            try:
                tot = float(row["cgst_rate"]) + float(row["sgst_rate"])
                self.lbl_total_gst.configure(text=f"{tot:.1f}%")
            except Exception:
                pass

    def save_data(self):
        palette = theme_manager.get_palette()
        try:
            cgst = Decimal(self.entry_cgst.get().strip() or "2.5")
            sgst = Decimal(self.entry_sgst.get().strip() or "2.5")
            sc = Decimal(self.entry_sc_rate.get().strip() or "0.0")
            max_disc = Decimal(self.entry_max_disc.get().strip() or "25.0")
        except Exception:
            self.lbl_status.configure(text="Please enter valid numerical rates.", text_color=palette["danger"])
            return

        with self.db.transaction() as conn:
            conn.execute(
                """UPDATE billing_config
                   SET cgst_rate = ?, sgst_rate = ?, service_charge_rate = ?,
                       enable_service_charge = ?, enable_discounts = ?,
                       max_discount_percent = ?, round_off_total = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = 1;""",
                (
                    str(cgst), str(sgst), str(sc),
                    1 if self.switch_service_charge.get() else 0,
                    1 if self.switch_discounts.get() else 0,
                    str(max_disc),
                    1 if self.switch_round_off.get() else 0
                )
            )
            conn.execute(
                """INSERT INTO audit_logs (username, action, module, details)
                   VALUES ('Admin', 'UPDATE_BILLING_TAX', 'BILLING', ?);""",
                (f"Updated GST: CGST={cgst}%, SGST={sgst}%, Total={(cgst + sgst)}%, MaxDisc={max_disc}%",)
            )

        self.lbl_total_gst.configure(text=f"{(cgst + sgst):.1f}%")
        self.lbl_status.configure(text="✓ Billing & Tax Configuration saved successfully.", text_color=palette["success"])
