"""Main application window, dynamic role-based navigation, and global keyboard shortcuts."""
from typing import Callable, Optional
import customtkinter as ctk

from ui.theme_manager import theme_manager
from ui.dashboard import DashboardFrame
from ui.orders import NewOrderFrame, OrderHistoryFrame
from ui.menu import MenuFrame
from ui.billing import BillingDialog, ReceiptDialog
from ui.reports import ReportsFrame
from ui.profile import ProfileFrame
from ui.users import UserManagementFrame
from ui.roles import RolesPermissionsFrame
from ui.settings_views import RestaurantSettingsFrame, BillingTaxSettingsFrame
from ui.audit import SecurityAuditFrame
from ui.maintenance import DatabaseBackupFrame, SystemHealthFrame
from services.auth_service import AuthService, auth_service
from services.billing_service import BillingService, billing_service
from services.order_service import OrderService, order_service
from utils.window_utils import center_dialog


class ShortcutsHelpDialog(ctk.CTkToplevel):
    """Modal displaying all supported cashier keyboard accelerators."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Keyboard Shortcuts Reference")
        self.resizable(False, False)
        center_dialog(self, master, target_width=480, target_height=420, min_width=440, min_height=380)
        self.grab_set()

        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        ctk.CTkLabel(
            self,
            text="⌨️ Keyboard Accelerators",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(padx=25, pady=(20, 10), anchor="w")

        box = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        box.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        shortcuts = [
            ("Alt + D  /  Ctrl + D", "Navigate to Dashboard"),
            ("Alt + N  /  Ctrl + N", "Navigate to New POS Order (Billing)"),
            ("Alt + M  /  Ctrl + M", "Navigate to Menu Catalog Management"),
            ("Alt + O  /  Ctrl + O", "Navigate to Orders History & Billing"),
            ("Alt + R  /  Ctrl + R", "Navigate to Sales Reports & Analytics"),
            ("Alt + P  /  Ctrl + P", "Navigate to User Profile"),
            ("Alt + S  /  Ctrl + S", "Navigate to System Settings"),
            ("Alt + T", "Toggle Theme Mode (Light / Dark)"),
            ("Escape", "Dismiss active modal dialog / receipt")
        ]

        for key, desc in shortcuts:
            row = ctk.CTkFrame(box, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(row, text=key, font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color=palette["accent"]).pack(side="left")
            ctk.CTkLabel(row, text=desc, font=ctk.CTkFont(size=11), text_color=palette["text_secondary"]).pack(side="right")

        btn = ctk.CTkButton(
            self,
            text="Got It (Esc)",
            width=110,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self.destroy
        )
        btn.pack(padx=25, pady=(0, 20), anchor="e")

        self.bind("<Escape>", lambda e: self.destroy())


class MainWindow(ctk.CTkFrame):
    """Main application shell containing Blue Navigation Sidebar, Header, and Dynamic Workspace."""

    def __init__(self, master, on_logout: Callable, auth_svc: AuthService = auth_service, **kwargs):
        super().__init__(master, **kwargs)
        self.on_logout = on_logout
        self.auth_svc = auth_svc
        self.user = self.auth_svc.current_user
        self.user_role = self.user.role.upper() if self.user else "ADMIN"
        self.current_view_name = "dashboard"
        self.current_view = None

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self._bind_keyboard_shortcuts()
        self.navigate_to("dashboard")

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self.header_frame.configure(fg_color=palette.get("header_bg", palette["bg_card"]), border_color=palette.get("header_border", palette["border"]))
            self.sidebar_frame.configure(fg_color=palette.get("sidebar_bg", "#173B70"), border_color=palette.get("sidebar_border", palette["border"]))
            self.status_bar.configure(fg_color=palette["bg_secondary"], border_color=palette["border"])
            self.theme_btn.configure(
                text="🌙 Dark Mode" if theme_name == "light" else "☀️ Light Mode",
                fg_color=palette.get("accent_light", palette["bg_secondary"]),
                text_color=palette["accent"]
            )
            self._update_nav_button_styles()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # =====================================================================
        # TOP HEADER BAR
        # =====================================================================
        self.header_frame = ctk.CTkFrame(
            self,
            height=56,
            fg_color=palette.get("header_bg", palette["bg_card"]),
            corner_radius=0,
            border_width=1,
            border_color=palette.get("header_border", palette["border"])
        )
        self.header_frame.pack(fill="x", side="top")

        # Brand / App Title
        brand_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        brand_box.pack(side="left", padx=20)
        ctk.CTkLabel(
            brand_box,
            text="🍽️ RESTAURANT MANAGEMENT PLATFORM",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette.get("header_text", palette.get("heading", palette["text_primary"]))
        ).pack(side="left")

        # Right Header Controls
        hdr_right = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        hdr_right.pack(side="right", padx=15)

        # Shortcuts Info Button
        btn_sc = ctk.CTkButton(
            hdr_right,
            text="⌨️ Shortcuts",
            width=92,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette.get("accent_light", palette["bg_secondary"]),
            text_color=palette["accent"],
            hover_color=palette["border"],
            command=self._open_shortcuts_help
        )
        btn_sc.pack(side="left", padx=4)

        # Theme Toggle Button
        self.theme_btn = ctk.CTkButton(
            hdr_right,
            text="🌙 Dark Mode" if theme_manager.current_theme == "light" else "☀️ Light Mode",
            width=105,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette.get("accent_light", palette["bg_secondary"]),
            text_color=palette["accent"],
            hover_color=palette["border"],
            command=self._handle_theme_toggle
        )
        self.theme_btn.pack(side="left", padx=4)

        # Active User Role Pill
        role_colors = {
            "ADMIN": ("#EEF2FF", "#4F46E5"),
            "CASHIER": ("#ECFDF5", "#059669"),
            "MANAGER": ("#FFFBEB", "#D97706")
        }
        bg_col, txt_col = role_colors.get(self.user_role, ("#F1F5F9", "#334155"))
        role_pill = ctk.CTkFrame(hdr_right, fg_color=bg_col, corner_radius=6)
        role_pill.pack(side="left", padx=(8, 4))
        ctk.CTkLabel(
            role_pill,
            text=f"● {self.user_role}",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=txt_col
        ).pack(padx=8, pady=3)

        # Logout Button
        logout_btn = ctk.CTkButton(
            hdr_right,
            text="🚪 Sign Out",
            width=85,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["danger"],
            hover_color="#B91C1C",
            text_color="#FFFFFF",
            command=self._handle_logout
        )
        logout_btn.pack(side="left", padx=(4, 0))

        # =====================================================================
        # BOTTOM STATUS BAR (COMMERCIAL TERMINAL METADATA)
        # =====================================================================
        self.status_bar = ctk.CTkFrame(
            self,
            height=26,
            fg_color=palette["bg_secondary"],
            corner_radius=0,
            border_width=1,
            border_color=palette["border"]
        )
        self.status_bar.pack(fill="x", side="bottom")

        terminal_id = "ADMIN-01" if self.user_role == "ADMIN" else "COUNTER-01"
        status_text = f"Restaurant Management Platform  |  Terminal: {terminal_id}  |  System Status: Operational  |  Database: Online (Connected)"
        ctk.CTkLabel(
            self.status_bar,
            text=status_text,
            font=ctk.CTkFont(size=10),
            text_color=palette["text_secondary"]
        ).pack(side="left", padx=18)

        # =====================================================================
        # CENTER WORKSPACE (DEEP NAVY SIDEBAR + WORKSPACE)
        # =====================================================================
        workspace = ctk.CTkFrame(self, fg_color=palette["bg_primary"])
        workspace.pack(fill="both", expand=True)

        # Left Navigation Sidebar
        self.sidebar_frame = ctk.CTkFrame(
            workspace,
            width=230,
            fg_color=palette.get("sidebar_bg", "#173B70"),
            corner_radius=0,
            border_width=1,
            border_color=palette.get("sidebar_border", palette["border"])
        )
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        # Sidebar Header Branding — Distinct by Role
        side_head = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        side_head.pack(fill="x", padx=16, pady=(18, 10))

        if self.user_role == "CASHIER":
            head_title = "BILLING TERMINAL"
            head_sub = "Counter Point-of-Sale"
        elif self.user_role == "MANAGER":
            head_title = "FLOOR OPERATIONS"
            head_sub = "Shift & Catalog Management"
        else:
            head_title = "RESTAURANT ADMIN"
            head_sub = "Executive Management"

        ctk.CTkLabel(
            side_head,
            text=head_title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=palette.get("sidebar_text", "#FFFFFF")
        ).pack(anchor="w")

        ctk.CTkLabel(
            side_head,
            text=head_sub,
            font=ctk.CTkFont(size=10),
            text_color=palette.get("sidebar_text_muted", "#BFDBFE")
        ).pack(anchor="w", pady=(1, 0))

        # Divider
        div = ctk.CTkFrame(self.sidebar_frame, height=1, fg_color=palette.get("sidebar_secondary", "#245A9B"))
        div.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkLabel(
            self.sidebar_frame,
            text="NAVIGATION",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=palette.get("sidebar_text_muted", "#BFDBFE")
        ).pack(anchor="w", padx=16, pady=(0, 4))

        # -------------------------------------------------------------
        # Role-Specific Sidebar Navigation Items
        # -------------------------------------------------------------
        self.nav_buttons = {}
        if self.user_role == "CASHIER":
            nav_items = [
                ("dashboard", "⚡ Shift Overview", "Alt+D"),
                ("orders", "🛒 Counter Billing", "Alt+N"),
                ("orders_history", "🧾 Today's Receipts", "Alt+O"),
                ("profile", "👤 My Profile", "Alt+P"),
                ("settings", "⚙️ Terminal Settings", "Alt+S"),
            ]
        elif self.user_role == "MANAGER":
            nav_items = [
                ("dashboard", "📋 Operations Floor", "Alt+D"),
                ("orders", "🛒 Counter Billing", "Alt+N"),
                ("menu", "📋 Menu & 86 Catalog", "Alt+M"),
                ("orders_history", "📜 Order Monitoring", "Alt+O"),
                ("reports", "📈 Shift Sales Reports", "Alt+R"),
                ("profile", "👤 My Profile", "Alt+P"),
            ]
        else:
            # ADMIN — Complete Enterprise Navigation Suite
            nav_items = [
                ("dashboard", "📊 Executive Overview", "Alt+D"),
                ("users", "👥 Staff Management", "Alt+U"),
                ("roles", "🛡️ Roles & Permissions", "Alt+K"),
                ("restaurant", "🏢 Restaurant Profile", "Alt+B"),
                ("billing_cfg", "💳 Billing & Tax Rules", "Alt+T"),
                ("security_audit", "📜 Security & Audit Logs", "Alt+A"),
                ("database", "💾 Database & Backups", "Alt+X"),
                ("system_health", "🩺 System Health Monitor", "Alt+H"),
                ("orders", "🛒 Point of Sale (POS)", "Alt+N"),
                ("menu", "🍽️ Menu Catalog", "Alt+M"),
                ("orders_history", "🧾 Order Audit History", "Alt+O"),
                ("reports", "📈 Reports & Analytics", "Alt+R"),
                ("settings", "⚙️ System Configuration", "Alt+S"),
            ]

        # Navigation buttons container inside sidebar (Scrollable for comprehensive Admin suite)
        nav_container = ctk.CTkScrollableFrame(
            self.sidebar_frame,
            fg_color="transparent",
            scrollbar_button_color=palette.get("sidebar_hover", "#245A9B"),
            scrollbar_button_hover_color=palette.get("sidebar_active", "#2563EB")
        )
        nav_container.pack(fill="both", expand=True, padx=2, pady=(0, 4))

        for code, label, key_hint in nav_items:
            btn = ctk.CTkButton(
                nav_container,
                text=f"{label}  ({key_hint})",
                anchor="w",
                height=38,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="transparent",
                text_color=palette.get("sidebar_text", "#FFFFFF"),
                hover_color=palette.get("sidebar_hover", "#245A9B"),
                command=lambda c=code: self.navigate_to(c)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[code] = btn

        # Persistent Staff Info Card at Bottom of Sidebar
        user_card = ctk.CTkFrame(self.sidebar_frame, fg_color=palette.get("sidebar_secondary", "#245A9B"), corner_radius=8)
        user_card.pack(fill="x", side="bottom", padx=10, pady=12)

        ctk.CTkLabel(
            user_card,
            text=self.user.full_name if self.user else "Staff User",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w", padx=10, pady=(8, 1))

        ctk.CTkLabel(
            user_card,
            text=f"Role: {self.user_role}",
            font=ctk.CTkFont(size=9),
            text_color=palette.get("sidebar_text_muted", "#BFDBFE")
        ).pack(anchor="w", padx=10, pady=(0, 8))

        # Content Area Container (Clean White: #FFFFFF)
        self.content_container = ctk.CTkFrame(workspace, fg_color=palette["bg_primary"])
        self.content_container.pack(side="right", fill="both", expand=True)

    def _can_trigger_shortcut(self) -> bool:
        """Poka-Yoke guard: Prevents shortcut keys from interfering while user is editing input fields."""
        try:
            focused = self.winfo_toplevel().focus_get()
            if focused is not None:
                w_class = focused.winfo_class().lower()
                if any(k in w_class for k in ["entry", "text"]):
                    return False
        except Exception:
            pass
        return True

    def _safe_navigate(self, view_name: str):
        if self._can_trigger_shortcut():
            # Role permission check before navigating
            if self.user_role == "CASHIER" and view_name in ["menu", "reports"]:
                return
            if self.user_role == "MANAGER" and view_name in ["settings"]:
                return
            self.navigate_to(view_name)

    def _safe_theme_toggle(self):
        if self._can_trigger_shortcut():
            self._handle_theme_toggle()

    def _bind_keyboard_shortcuts(self):
        root = self.winfo_toplevel()

        root.bind("<Alt-d>", lambda e: self._safe_navigate("dashboard"))
        root.bind("<Alt-D>", lambda e: self._safe_navigate("dashboard"))
        root.bind("<Control-d>", lambda e: self._safe_navigate("dashboard"))

        root.bind("<Alt-n>", lambda e: self._safe_navigate("orders"))
        root.bind("<Alt-N>", lambda e: self._safe_navigate("orders"))
        root.bind("<Control-n>", lambda e: self._safe_navigate("orders"))

        root.bind("<Alt-m>", lambda e: self._safe_navigate("menu"))
        root.bind("<Alt-M>", lambda e: self._safe_navigate("menu"))
        root.bind("<Control-m>", lambda e: self._safe_navigate("menu"))

        root.bind("<Alt-o>", lambda e: self._safe_navigate("orders_history"))
        root.bind("<Alt-O>", lambda e: self._safe_navigate("orders_history"))
        root.bind("<Control-o>", lambda e: self._safe_navigate("orders_history"))

        root.bind("<Alt-r>", lambda e: self._safe_navigate("reports"))
        root.bind("<Alt-R>", lambda e: self._safe_navigate("reports"))
        root.bind("<Control-r>", lambda e: self._safe_navigate("reports"))

        root.bind("<Alt-p>", lambda e: self._safe_navigate("profile"))
        root.bind("<Alt-P>", lambda e: self._safe_navigate("profile"))
        root.bind("<Control-p>", lambda e: self._safe_navigate("profile"))

        root.bind("<Alt-s>", lambda e: self._safe_navigate("settings"))
        root.bind("<Alt-S>", lambda e: self._safe_navigate("settings"))
        root.bind("<Control-s>", lambda e: self._safe_navigate("settings"))

        root.bind("<Alt-t>", lambda e: self._safe_theme_toggle())
        root.bind("<Alt-T>", lambda e: self._safe_theme_toggle())

    def _open_shortcuts_help(self):
        ShortcutsHelpDialog(self)

    def _handle_theme_toggle(self):
        user_id = self.auth_svc.current_user.id if self.auth_svc.current_user else None
        theme_manager.toggle_theme(user_id=user_id)

    def _handle_logout(self):
        self.auth_svc.logout()
        self.on_logout()

    def _update_nav_button_styles(self):
        palette = theme_manager.get_palette()
        for code, btn in self.nav_buttons.items():
            if code == self.current_view_name:
                btn.configure(
                    fg_color=palette.get("sidebar_active", "#2563EB"),
                    text_color="#FFFFFF"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=palette.get("sidebar_text", "#FFFFFF"),
                    hover_color=palette.get("sidebar_hover", "#245A9B")
                )

    def navigate_to(self, view_name: str):
        """Switches active view and updates navigation highlights with strict role guards."""
        # Enforce role-based view permissions
        if self.user_role == "CASHIER" and view_name in ["menu", "reports"]:
            view_name = "dashboard"
        elif self.user_role == "MANAGER" and view_name in ["settings"]:
            view_name = "dashboard"

        self.current_view_name = view_name
        self._update_nav_button_styles()

        # Destroy old view cleanly
        if self.current_view:
            self.current_view.destroy()

        # Instantiate new view with role context
        if view_name == "dashboard":
            self.current_view = DashboardFrame(
                self.content_container,
                navigate_fn=self.navigate_to,
                role=self.user_role
            )
        elif view_name == "orders":
            self.current_view = NewOrderFrame(self.content_container, on_proceed_to_bill=self.open_billing_modal)
        elif view_name == "menu":
            self.current_view = MenuFrame(self.content_container)
        elif view_name == "orders_history":
            self.current_view = OrderHistoryFrame(
                self.content_container,
                on_open_bill=self.open_billing_modal,
                on_view_receipt=self.open_receipt_modal
            )
        elif view_name == "reports":
            self.current_view = ReportsFrame(self.content_container)
        elif view_name == "profile":
            self.current_view = ProfileFrame(self.content_container, initial_tab="profile")
        elif view_name == "settings":
            self.current_view = ProfileFrame(self.content_container, initial_tab="settings")
        elif view_name == "users":
            self.current_view = UserManagementFrame(self.content_container)
        elif view_name == "roles":
            self.current_view = RolesPermissionsFrame(self.content_container)
        elif view_name == "restaurant":
            self.current_view = RestaurantSettingsFrame(self.content_container)
        elif view_name == "billing_cfg":
            self.current_view = BillingTaxSettingsFrame(self.content_container)
        elif view_name == "security_audit":
            self.current_view = SecurityAuditFrame(self.content_container)
        elif view_name == "database":
            self.current_view = DatabaseBackupFrame(self.content_container)
        elif view_name == "system_health":
            self.current_view = SystemHealthFrame(self.content_container)

        if self.current_view:
            self.current_view.pack(fill="both", expand=True)

    def open_billing_modal(self, order_id: int):
        BillingDialog(
            self,
            order_id=order_id,
            on_bill_completed=lambda oid: self.navigate_to("orders_history")
        )

    def open_receipt_modal(self, order_id: int):
        order = order_service.get_order(order_id)
        bill = billing_service.get_bill_for_order(order_id)
        if order and bill:
            receipt_text = billing_service.format_receipt_text(bill, order)
            ReceiptDialog(self, receipt_text=receipt_text)
