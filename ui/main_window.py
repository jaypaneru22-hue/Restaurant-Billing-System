"""Main application window, navigation sidebar, and global keyboard shortcuts (Q08-F3 & Q08-F4)."""
import customtkinter as ctk
from typing import Callable, Optional
from ui.theme_manager import theme_manager
from ui.dashboard import DashboardFrame
from ui.orders import NewOrderFrame, OrderHistoryFrame
from ui.menu import MenuFrame
from ui.billing import BillingDialog, ReceiptDialog
from ui.reports import ReportsFrame
from ui.profile import ProfileFrame
from services.auth_service import AuthService, auth_service
from services.billing_service import BillingService, billing_service
from services.order_service import OrderService, order_service
from config.settings import (
    APP_NAME,
    ACADEMIC_SUBJECT,
    REGISTRATION_NUMBER,
    QUALITY_GOAL,
    ACADEMIC_SESSION
)


class ShortcutsHelpDialog(ctk.CTkToplevel):
    """Modal displaying all supported cashier keyboard accelerators (Q08-F4)."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Keyboard Accelerators (Q08-F4)")
        self.geometry("450x380")
        self.resizable(False, False)
        self.grab_set()

        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        ctk.CTkLabel(
            self,
            text="⌨️ Keyboard Accelerators",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(padx=25, pady=(20, 10), anchor="w")

        box = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        box.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        shortcuts = [
            ("Alt + D  /  Ctrl + D", "Navigate to Interactive Dashboard"),
            ("Alt + N  /  Ctrl + N", "Navigate to New Order (Point-of-Sale)"),
            ("Alt + M  /  Ctrl + M", "Navigate to Menu Catalog Management"),
            ("Alt + O  /  Ctrl + O", "Navigate to Orders History & Billing"),
            ("Alt + R  /  Ctrl + R", "Navigate to Visual Reports & Analytics"),
            ("Alt + P  /  Ctrl + P", "Navigate to User Profile & Settings"),
            ("Alt + T", "Toggle Theme Mode (Dark / Light)"),
            ("Escape", "Dismiss active modal dialog / receipt")
        ]

        for key, desc in shortcuts:
            row = ctk.CTkFrame(box, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=6)
            ctk.CTkLabel(row, text=key, font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color=palette["accent"]).pack(side="left")
            ctk.CTkLabel(row, text=desc, font=ctk.CTkFont(size=11), text_color=palette["text_secondary"]).pack(side="right")

        btn = ctk.CTkButton(
            self,
            text="Got It (Esc)",
            width=100,
            height=34,
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self.destroy
        )
        btn.pack(padx=25, pady=(0, 20), anchor="e")

        self.bind("<Escape>", lambda e: self.destroy())


class MainWindow(ctk.CTkFrame):
    """Main application shell containing sidebar navigation, header, and dynamic content."""

    def __init__(self, master, on_logout: Callable, auth_svc: AuthService = auth_service, **kwargs):
        super().__init__(master, **kwargs)
        self.on_logout = on_logout
        self.auth_svc = auth_svc
        self.current_view_name = "dashboard"
        self.current_view = None

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self._bind_keyboard_shortcuts()
        self.navigate_to("dashboard")

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self.header_frame.configure(fg_color=palette["bg_secondary"], border_color=palette["border"])
            self.sidebar_frame.configure(fg_color=palette["bg_secondary"], border_color=palette["border"])
            self.status_bar.configure(fg_color=palette["bg_secondary"], border_color=palette["border"])
            self.theme_btn.configure(text="🌙 Dark Mode" if theme_name == "dark" else "☀️ Light Mode")

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Top Header Bar
        self.header_frame = ctk.CTkFrame(self, height=54, fg_color=palette["bg_secondary"], corner_radius=0, border_width=1, border_color=palette["border"])
        self.header_frame.pack(fill="x", side="top")

        # Brand / App Title
        brand_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        brand_box.pack(side="left", padx=20)
        ctk.CTkLabel(
            brand_box,
            text=f"🍽️ {APP_NAME}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(side="left")

        # Right Header Controls
        hdr_right = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        hdr_right.pack(side="right", padx=15)

        # Shortcuts Info Button
        btn_sc = ctk.CTkButton(
            hdr_right,
            text="⌨️ Shortcuts",
            width=90,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=palette["text_primary"],
            hover_color=palette["bg_card"],
            command=self._open_shortcuts_help
        )
        btn_sc.pack(side="left", padx=4)

        # Theme Toggle Button (Q08-F3)
        self.theme_btn = ctk.CTkButton(
            hdr_right,
            text="🌙 Dark Mode" if theme_manager.current_theme == "dark" else "☀️ Light Mode",
            width=100,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_card"],
            text_color=palette["text_primary"],
            hover_color=palette["border"],
            command=self._handle_theme_toggle
        )
        self.theme_btn.pack(side="left", padx=4)

        # Active User Identity Pill
        user = self.auth_svc.current_user
        user_name = user.full_name if user else "Guest Cashier"
        user_role = user.role if user else "CASHIER"
        user_pill = ctk.CTkLabel(
            hdr_right,
            text=f"👤 {user_name} ({user_role})",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=palette["accent"]
        )
        user_pill.pack(side="left", padx=10)

        # Logout Button
        logout_btn = ctk.CTkButton(
            hdr_right,
            text="🚪 Logout",
            width=75,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color=palette["danger"],
            hover_color="#b91c1c",
            command=self._handle_logout
        )
        logout_btn.pack(side="left", padx=4)

        # Bottom Academic Status Bar
        self.status_bar = ctk.CTkFrame(self, height=28, fg_color=palette["bg_secondary"], corner_radius=0, border_width=1, border_color=palette["border"])
        self.status_bar.pack(fill="x", side="bottom")

        status_text = f"{ACADEMIC_SUBJECT}  |  Reg No: {REGISTRATION_NUMBER}  |  Quality Goal: {QUALITY_GOAL}  |  Session: {ACADEMIC_SESSION}"
        ctk.CTkLabel(
            self.status_bar,
            text=status_text,
            font=ctk.CTkFont(size=10),
            text_color=palette["text_secondary"]
        ).pack(side="left", padx=20)

        # Center Workspace (Sidebar + Content)
        workspace = ctk.CTkFrame(self, fg_color="transparent")
        workspace.pack(fill="both", expand=True)

        # Left Navigation Sidebar
        self.sidebar_frame = ctk.CTkFrame(workspace, width=200, fg_color=palette["bg_secondary"], corner_radius=0, border_width=1, border_color=palette["border"])
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        # Sidebar navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊 Dashboard", "Alt+D"),
            ("orders", "➕ New Order", "Alt+N"),
            ("menu", "📋 Menu Catalog", "Alt+M"),
            ("orders_history", "📜 Orders History", "Alt+O"),
            ("reports", "📈 Visual Reports", "Alt+R"),
            ("profile", "👤 User Profile", "Alt+P"),
        ]

        ctk.CTkLabel(self.sidebar_frame, text="MAIN NAVIGATION", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"]).pack(anchor="w", padx=15, pady=(15, 6))

        for code, label, key_hint in nav_items:
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=f"{label}  ({key_hint})",
                anchor="w",
                height=38,
                font=ctk.CTkFont(size=12),
                fg_color="transparent",
                text_color=palette["text_primary"],
                hover_color=palette["bg_card"],
                command=lambda c=code: self.navigate_to(c)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[code] = btn

        # Content Area Container
        self.content_container = ctk.CTkFrame(workspace, fg_color="transparent")
        self.content_container.pack(side="right", fill="both", expand=True)

    def _bind_keyboard_shortcuts(self):
        """Binds root window keyboard accelerators (Q08-F4)."""
        root = self.winfo_toplevel()
        root.bind("<Alt-d>", lambda e: self.navigate_to("dashboard"))
        root.bind("<Alt-D>", lambda e: self.navigate_to("dashboard"))
        root.bind("<Control-d>", lambda e: self.navigate_to("dashboard"))

        root.bind("<Alt-n>", lambda e: self.navigate_to("orders"))
        root.bind("<Alt-N>", lambda e: self.navigate_to("orders"))
        root.bind("<Control-n>", lambda e: self.navigate_to("orders"))

        root.bind("<Alt-m>", lambda e: self.navigate_to("menu"))
        root.bind("<Alt-M>", lambda e: self.navigate_to("menu"))
        root.bind("<Control-m>", lambda e: self.navigate_to("menu"))

        root.bind("<Alt-o>", lambda e: self.navigate_to("orders_history"))
        root.bind("<Alt-O>", lambda e: self.navigate_to("orders_history"))
        root.bind("<Control-o>", lambda e: self.navigate_to("orders_history"))

        root.bind("<Alt-r>", lambda e: self.navigate_to("reports"))
        root.bind("<Alt-R>", lambda e: self.navigate_to("reports"))
        root.bind("<Control-r>", lambda e: self.navigate_to("reports"))

        root.bind("<Alt-p>", lambda e: self.navigate_to("profile"))
        root.bind("<Alt-P>", lambda e: self.navigate_to("profile"))
        root.bind("<Control-p>", lambda e: self.navigate_to("profile"))

        root.bind("<Alt-t>", lambda e: self._handle_theme_toggle())
        root.bind("<Alt-T>", lambda e: self._handle_theme_toggle())

    def _open_shortcuts_help(self):
        ShortcutsHelpDialog(self)

    def _handle_theme_toggle(self):
        user_id = self.auth_svc.current_user.id if self.auth_svc.current_user else None
        theme_manager.toggle_theme(user_id=user_id)

    def _handle_logout(self):
        self.auth_svc.logout()
        self.on_logout()

    def navigate_to(self, view_name: str):
        """Switches active view and updates navigation highlights."""
        self.current_view_name = view_name
        palette = theme_manager.get_palette()

        # Update button states
        for code, btn in self.nav_buttons.items():
            if code == view_name:
                btn.configure(fg_color=palette["accent"], text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color=palette["text_primary"])

        # Destroy old view
        if self.current_view:
            self.current_view.destroy()

        # Instantiate new view
        if view_name == "dashboard":
            self.current_view = DashboardFrame(self.content_container, navigate_fn=self.navigate_to)
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
            self.current_view = ProfileFrame(self.content_container)

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
