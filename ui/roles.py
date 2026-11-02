"""Roles & Permissions (RBAC) Governance view with interactive permissions matrix."""
from typing import Dict, List, Optional
import customtkinter as ctk

from database.db import DatabaseManager, db
from ui.theme_manager import theme_manager

DEFAULT_PERMISSIONS = {
    "ADMIN": {
        "pos_create_order": True, "pos_apply_discount": True, "pos_cancel_order": True, "pos_settle_bill": True, "pos_reprint_receipt": True,
        "menu_view_catalog": True, "menu_toggle_86": True, "menu_edit_pricing": True, "menu_manage_categories": True,
        "reports_view_shift": True, "reports_view_analytics": True, "reports_export_csv": True,
        "staff_create_account": True, "staff_edit_account": True, "staff_reset_password": True, "audit_view_logs": True,
        "system_edit_profile": True, "system_edit_taxes": True, "db_backup_restore": True, "system_diagnostics": True
    },
    "MANAGER": {
        "pos_create_order": True, "pos_apply_discount": True, "pos_cancel_order": True, "pos_settle_bill": True, "pos_reprint_receipt": True,
        "menu_view_catalog": True, "menu_toggle_86": True, "menu_edit_pricing": False, "menu_manage_categories": False,
        "reports_view_shift": True, "reports_view_analytics": True, "reports_export_csv": False,
        "staff_create_account": False, "staff_edit_account": False, "staff_reset_password": False, "audit_view_logs": False,
        "system_edit_profile": False, "system_edit_taxes": False, "db_backup_restore": False, "system_diagnostics": False
    },
    "CASHIER": {
        "pos_create_order": True, "pos_apply_discount": False, "pos_cancel_order": False, "pos_settle_bill": True, "pos_reprint_receipt": True,
        "menu_view_catalog": True, "menu_toggle_86": False, "menu_edit_pricing": False, "menu_manage_categories": False,
        "reports_view_shift": True, "reports_view_analytics": False, "reports_export_csv": False,
        "staff_create_account": False, "staff_edit_account": False, "staff_reset_password": False, "audit_view_logs": False,
        "system_edit_profile": False, "system_edit_taxes": False, "db_backup_restore": False, "system_diagnostics": False
    }
}

PERMISSION_METADATA = [
    ("Point of Sale & Counter Billing", [
        ("pos_create_order", "Take Counter Orders", "Take table and takeaway orders and add items to cart"),
        ("pos_apply_discount", "Apply Bill Discounts", "Enter discretionary customer discounts and promo rates"),
        ("pos_cancel_order", "Void / Cancel Orders", "Cancel pending orders in table queue before billing"),
        ("pos_settle_bill", "Settle Payments", "Process Cash, Card, and UPI payments to finalize bills"),
        ("pos_reprint_receipt", "Reprint Receipts", "View and reprint customer tax receipts from history")
    ]),
    ("Menu & Inventory Availability", [
        ("menu_view_catalog", "View Menu Catalog", "Inspect dish names, categories, and standard pricing"),
        ("menu_toggle_86", "Toggle Food Stock (86 List)", "Mark items out-of-stock or in-stock instantly"),
        ("menu_edit_pricing", "Edit Dish Prices", "Create new dishes, delete items, or modify selling prices"),
        ("menu_manage_categories", "Manage Menu Categories", "Create, edit, or reorder restaurant menu categories")
    ]),
    ("Financial Analytics & Reporting", [
        ("reports_view_shift", "View Shift Summaries", "Review counter closeout tickets and shift sales volume"),
        ("reports_view_analytics", "View Sales Velocity Charts", "Inspect 7-day revenue velocity and trends"),
        ("reports_export_csv", "Export Financial CSV Data", "Export historical orders, bills, and tax reports to CSV")
    ]),
    ("Staff Management & Security", [
        ("staff_create_account", "Register Staff Accounts", "Create new login credentials for staff members"),
        ("staff_edit_account", "Edit Staff Roles & Details", "Update employee names, roles, and active status"),
        ("staff_reset_password", "Reset Staff Passwords", "Set new passwords for cashier and manager accounts"),
        ("audit_view_logs", "Inspect Audit Trail", "Review security events, login attempts, and voids")
    ]),
    ("System Settings & Maintenance", [
        ("system_edit_profile", "Restaurant Legal Profile", "Modify business name, address, GSTIN, and receipt footer"),
        ("system_edit_taxes", "Configure Tax & Rates", "Configure CGST, SGST, and service charge rates"),
        ("db_backup_restore", "Database Backup & Restore", "Trigger snapshot backups and restore database copies"),
        ("system_diagnostics", "System Diagnostics", "Run database integrity checks and inspect diagnostic logs")
    ])
]


class RolesPermissionsFrame(ctk.CTkFrame):
    """Real Roles & Permissions (RBAC) Governance view with interactive matrix."""

    def __init__(self, master, db_manager: DatabaseManager = db, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db_manager
        self.selected_role = "CASHIER"
        self.permission_switches: Dict[str, ctk.CTkSwitch] = {}

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self._load_permissions()

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self._load_permissions()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        # Header Bar
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 12))

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left")

        ctk.CTkLabel(
            title_col,
            text="🛡️ Roles & Permissions Governance (RBAC Matrix)",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="Role-based access control • Configure operational privileges per staff persona",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        # Top Actions
        act_box = ctk.CTkFrame(header, fg_color="transparent")
        act_box.pack(side="right")

        ctk.CTkButton(
            act_box,
            text="🔄 Reset Defaults",
            width=120,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_card"],
            hover_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            command=self._reset_defaults
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            act_box,
            text="💾 Save Matrix",
            width=115,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._save_permissions
        ).pack(side="left", padx=4)

        # Role Selector Segmented Bar
        role_bar = ctk.CTkFrame(self.scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        role_bar.pack(fill="x", padx=24, pady=(0, 14))

        r_inner = ctk.CTkFrame(role_bar, fg_color="transparent")
        r_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(r_inner, text="Select Role to Inspect / Configure:", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"]).pack(side="left", padx=(0, 14))

        self.role_seg = ctk.CTkSegmentedButton(
            r_inner,
            values=["CASHIER", "MANAGER", "ADMIN"],
            height=34,
            font=ctk.CTkFont(size=11, weight="bold"),
            selected_color=palette["accent"],
            selected_hover_color=palette["accent_hover"],
            command=self._on_role_switched
        )
        self.role_seg.set("CASHIER")
        self.role_seg.pack(side="left")

        # Status toast
        self.lbl_status = ctk.CTkLabel(r_inner, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["success"])
        self.lbl_status.pack(side="right", padx=10)

        # Permission Categories Grid
        self.matrix_box = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.matrix_box.pack(fill="both", expand=True, padx=24, pady=(0, 20))

    def _on_role_switched(self, role: str):
        self.selected_role = role
        self._load_permissions()

    def _load_permissions(self):
        palette = theme_manager.get_palette()

        # Load existing overrides from DB or use defaults
        rows = self.db.fetchall("SELECT permission_key, is_granted FROM roles_permissions WHERE role = ?;", (self.selected_role,))
        db_perms = {r["permission_key"]: bool(r["is_granted"]) for r in rows}

        defaults = DEFAULT_PERMISSIONS.get(self.selected_role, {})
        current_perms = {**defaults, **db_perms}

        for w in self.matrix_box.winfo_children():
            w.destroy()
        self.permission_switches.clear()

        # Build category cards
        for cat_name, perms in PERMISSION_METADATA:
            card = ctk.CTkFrame(self.matrix_box, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
            card.pack(fill="x", pady=(0, 12))

            c_head = ctk.CTkFrame(card, fg_color=palette["bg_secondary"], corner_radius=6, height=32)
            c_head.pack(fill="x", padx=10, pady=(10, 8))

            ctk.CTkLabel(c_head, text=f"📂 {cat_name.upper()}", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(side="left", padx=12, pady=6)

            for key, name, desc in perms:
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=16, pady=4)

                t_col = ctk.CTkFrame(row, fg_color="transparent")
                t_col.pack(side="left")

                ctk.CTkLabel(t_col, text=name, font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(anchor="w")
                ctk.CTkLabel(t_col, text=desc, font=ctk.CTkFont(size=9), text_color=palette["text_secondary"]).pack(anchor="w")

                switch = ctk.CTkSwitch(row, text="", width=40)
                switch.pack(side="right")
                if current_perms.get(key, False):
                    switch.select()
                else:
                    switch.deselect()

                # If configuring Admin, keep switches active as full privilege
                if self.selected_role == "ADMIN":
                    switch.select()
                    switch.configure(state="disabled")

                self.permission_switches[key] = switch

    def _save_permissions(self):
        palette = theme_manager.get_palette()
        if self.selected_role == "ADMIN":
            self.lbl_status.configure(text="✓ Admin permissions are permanently enabled.", text_color=palette["accent"])
            return

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            for key, switch in self.permission_switches.items():
                is_granted = 1 if switch.get() else 0
                cursor.execute(
                    """INSERT INTO roles_permissions (role, module, permission_key, is_granted)
                       VALUES (?, 'CORE', ?, ?)
                       ON CONFLICT(role, module, permission_key)
                       DO UPDATE SET is_granted = excluded.is_granted;""",
                    (self.selected_role, key, is_granted)
                )

        self.lbl_status.configure(text=f"✓ {self.selected_role} permissions saved successfully to database.", text_color=palette["success"])

    def _reset_defaults(self):
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM roles_permissions WHERE role = ?;", (self.selected_role,))
        self._load_permissions()
        self.lbl_status.configure(text="✓ Reset to default configuration.", text_color=theme_manager.get_palette()["accent"])
