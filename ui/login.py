"""Login view for user authentication with credential validation and quick demo login."""
import customtkinter as ctk
from typing import Callable
from services.auth_service import AuthService, auth_service
from ui.theme_manager import theme_manager
from config.settings import APP_NAME, ACADEMIC_SUBJECT, REGISTRATION_NUMBER, QUALITY_GOAL


class LoginFrame(ctk.CTkFrame):
    """Modern POS authentication screen with error feedback, demo shortcuts, and theme alignment."""

    def __init__(self, master, on_login_success: Callable, auth_svc: AuthService = auth_service, **kwargs):
        super().__init__(master, **kwargs)
        self.on_login_success = on_login_success
        self.auth_svc = auth_svc

        self._build_ui()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_secondary"])

        # Center card container
        card = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=16, border_width=1, border_color=palette["border"], width=440)
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Header & Metadata
        header_box = ctk.CTkFrame(card, fg_color="transparent")
        header_box.pack(padx=35, pady=(28, 12))

        ctk.CTkLabel(
            header_box,
            text=f"🍽️ {APP_NAME}",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack()

        ctk.CTkLabel(
            header_box,
            text=f"Point of Sale & Quality Management System\n{ACADEMIC_SUBJECT} • Reg: {REGISTRATION_NUMBER}",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"],
            justify="center"
        ).pack(pady=(4, 0))

        # Username entry
        user_lbl = ctk.CTkLabel(card, text="Username", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"], anchor="w")
        user_lbl.pack(fill="x", padx=35, pady=(4, 2))
        self.username_entry = ctk.CTkEntry(
            card,
            width=340,
            height=38,
            placeholder_text="Enter username",
            font=ctk.CTkFont(size=13)
        )
        self.username_entry.pack(padx=35, pady=(0, 10))
        self.username_entry.insert(0, "admin")

        # Password entry
        pass_lbl = ctk.CTkLabel(card, text="Password", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"], anchor="w")
        pass_lbl.pack(fill="x", padx=35, pady=(4, 2))
        self.password_entry = ctk.CTkEntry(
            card,
            width=340,
            height=38,
            placeholder_text="Enter password",
            show="•",
            font=ctk.CTkFont(size=13)
        )
        self.password_entry.pack(padx=35, pady=(0, 12))
        self.password_entry.insert(0, "Admin@123")

        # Bind Enter key to submit
        self.username_entry.bind("<Return>", lambda e: self._handle_login())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())

        # Error notification label
        self.error_label = ctk.CTkLabel(
            card,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=palette["danger"]
        )
        self.error_label.pack(fill="x", padx=35, pady=(0, 6))

        # Login action button
        login_btn = ctk.CTkButton(
            card,
            text="Sign In to POS 🚀",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            width=340,
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._handle_login
        )
        login_btn.pack(padx=35, pady=(0, 16))

        # One-Click Demo Login Helpers
        demo_box = ctk.CTkFrame(card, fg_color=palette["bg_secondary"], corner_radius=10, border_width=1, border_color=palette["border"])
        demo_box.pack(fill="x", padx=35, pady=(0, 24))

        ctk.CTkLabel(
            demo_box,
            text="⚡ One-Click Demo Logins (Viva / Interview):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", padx=12, pady=(10, 6))

        demo_btns_row = ctk.CTkFrame(demo_box, fg_color="transparent")
        demo_btns_row.pack(fill="x", padx=12, pady=(0, 10))

        btn_admin = ctk.CTkButton(
            demo_btns_row,
            text="Admin (Full Access)",
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color=palette["bg_card"],
            hover_color=palette["border"],
            text_color=palette["accent"],
            command=self._quick_login_admin
        )
        btn_admin.pack(side="left", expand=True, fill="x", padx=(0, 4))

        btn_cashier = ctk.CTkButton(
            demo_btns_row,
            text="Cashier (Billing)",
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color=palette["bg_card"],
            hover_color=palette["border"],
            text_color=palette["text_primary"],
            command=self._quick_login_cashier
        )
        btn_cashier.pack(side="right", expand=True, fill="x", padx=(4, 0))

    def _quick_login_admin(self):
        self.username_entry.delete(0, "end")
        self.username_entry.insert(0, "admin")
        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, "Admin@123")
        self._handle_login()

    def _quick_login_cashier(self):
        self.username_entry.delete(0, "end")
        self.username_entry.insert(0, "cashier1")
        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, "Cashier@123")
        self._handle_login()

    def _handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        ok, msg, user = self.auth_svc.login(username, password)
        if not ok:
            self.error_label.configure(text=msg)
            return

        self.error_label.configure(text="")
        if user:
            from repositories.settings_repository import SettingsRepository
            settings = SettingsRepository().get_by_user_id(user.id)
            if settings:
                theme_manager.apply_theme(settings.theme)

        self.on_login_success(user)
