"""Login view for user authentication with credential validation."""
import customtkinter as ctk
from typing import Callable
from services.auth_service import AuthService, auth_service
from ui.theme_manager import theme_manager
from config.settings import APP_NAME, ACADEMIC_SUBJECT, REGISTRATION_NUMBER, QUALITY_GOAL


class LoginFrame(ctk.CTkFrame):
    """Modern authentication screen with error feedback and credential hints."""

    def __init__(self, master, on_login_success: Callable, auth_svc: AuthService = auth_service, **kwargs):
        super().__init__(master, **kwargs)
        self.on_login_success = on_login_success
        self.auth_svc = auth_svc

        self._build_ui()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Center card container
        card = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=16, border_width=1, border_color=palette["border"])
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Header & Metadata
        title_lbl = ctk.CTkLabel(
            card,
            text=f"🍽️ {APP_NAME}",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=palette["text_primary"]
        )
        title_lbl.pack(padx=40, pady=(30, 4))

        sub_lbl = ctk.CTkLabel(
            card,
            text=f"{ACADEMIC_SUBJECT}\nReg No: {REGISTRATION_NUMBER}  |  Goal: {QUALITY_GOAL}",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        )
        sub_lbl.pack(padx=40, pady=(0, 20))

        # Username entry
        user_lbl = ctk.CTkLabel(card, text="Username", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"], anchor="w")
        user_lbl.pack(fill="x", padx=40, pady=(5, 2))
        self.username_entry = ctk.CTkEntry(
            card,
            width=300,
            height=38,
            placeholder_text="Enter username (e.g. admin)",
            font=ctk.CTkFont(size=13)
        )
        self.username_entry.pack(padx=40, pady=(0, 10))
        self.username_entry.insert(0, "admin")

        # Password entry
        pass_lbl = ctk.CTkLabel(card, text="Password", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"], anchor="w")
        pass_lbl.pack(fill="x", padx=40, pady=(5, 2))
        self.password_entry = ctk.CTkEntry(
            card,
            width=300,
            height=38,
            placeholder_text="Enter password",
            show="•",
            font=ctk.CTkFont(size=13)
        )
        self.password_entry.pack(padx=40, pady=(0, 15))
        self.password_entry.insert(0, "Admin@123")

        # Bind Enter key to submit
        self.username_entry.bind("<Return>", lambda e: self._handle_login())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())

        # Error notification label
        self.error_label = ctk.CTkLabel(
            card,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=palette["danger"]
        )
        self.error_label.pack(padx=40, pady=(0, 10))

        # Login action button
        login_btn = ctk.CTkButton(
            card,
            text="Sign In",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=300,
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._handle_login
        )
        login_btn.pack(padx=40, pady=(0, 20))

        # Demo credentials helper
        hint_box = ctk.CTkFrame(card, fg_color=palette["bg_secondary"], corner_radius=8)
        hint_box.pack(fill="x", padx=40, pady=(0, 25))
        hint_lbl = ctk.CTkLabel(
            hint_box,
            text="Demo Accounts:\n• Admin: admin / Admin@123\n• Cashier: cashier1 / Cashier@123",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"],
            justify="left"
        )
        hint_lbl.pack(padx=15, pady=10)

    def _handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        ok, msg, user = self.auth_svc.login(username, password)
        if not ok:
            self.error_label.configure(text=msg)
            return

        self.error_label.configure(text="")
        # Apply user's saved theme
        if user:
            from repositories.settings_repository import SettingsRepository
            settings = SettingsRepository().get_by_user_id(user.id)
            theme_manager.apply_theme(settings.theme)

        self.on_login_success(user)
