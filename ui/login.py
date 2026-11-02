"""Login view for commercial staff authentication with role-based routing."""
import json
from pathlib import Path
from typing import Callable, Optional
import customtkinter as ctk

from services.auth_service import AuthService, auth_service
from ui.theme_manager import theme_manager
from config.settings import APP_NAME, DATA_DIR
from utils.window_utils import center_dialog


class ForgotPasswordDialog(ctk.CTkToplevel):
    """Informational dialog for enterprise credential recovery."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Credential Recovery")
        self.resizable(False, False)
        center_dialog(self, master, target_width=440, target_height=260)
        self.grab_set()

        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        card = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card,
            text="🔒 Staff Credential Recovery",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w", padx=18, pady=(16, 8))

        ctk.CTkLabel(
            card,
            text="To ensure database security and financial compliance,\nstaff passwords cannot be reset automatically at this terminal.\n\nPlease contact your Restaurant Administrator or Store Manager\nto issue a secure password reset via Staff Management.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"],
            justify="left"
        ).pack(anchor="w", padx=18, pady=(0, 16))

        ctk.CTkButton(
            card,
            text="Got It (Esc)",
            width=100,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self.destroy
        ).pack(anchor="e", padx=18, pady=(0, 16))

        self.bind("<Escape>", lambda e: self.destroy())


class LoginFrame(ctk.CTkFrame):
    """Modern SaaS commercial authentication interface inspired by industry POS solutions."""

    def __init__(self, master, on_login_success: Callable, auth_svc: AuthService = auth_service, **kwargs):
        super().__init__(master, **kwargs)
        self.on_login_success = on_login_success
        self.auth_svc = auth_svc
        self._remember_file = DATA_DIR / ".remember_staff.json"
        self._password_visible = False
        self._is_submitting = False

        self._build_ui()
        self._load_remembered_staff()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_secondary"])

        # Center elevation card
        card = ctk.CTkFrame(
            self,
            fg_color=palette["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=palette["border"],
            width=460
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        # 1. Header & Brand Identity Area
        header_box = ctk.CTkFrame(card, fg_color="transparent")
        header_box.pack(fill="x", padx=36, pady=(32, 16))

        brand_badge = ctk.CTkFrame(header_box, fg_color=palette["accent_light"], corner_radius=8)
        brand_badge.pack(anchor="center", pady=(0, 10))

        ctk.CTkLabel(
            brand_badge,
            text="🍽️ RESTAURANT MANAGEMENT PLATFORM",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette["accent"]
        ).pack(padx=12, pady=4)

        ctk.CTkLabel(
            header_box,
            text="Staff Sign In",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="center")

        ctk.CTkLabel(
            header_box,
            text="Authorized staff terminal • Enter your assigned credentials",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"],
            justify="center"
        ).pack(anchor="center", pady=(4, 0))

        # 2. Form Inputs
        form_box = ctk.CTkFrame(card, fg_color="transparent")
        form_box.pack(fill="x", padx=36, pady=(0, 12))

        # Username / Staff ID
        ctk.CTkLabel(
            form_box,
            text="Staff ID or Username",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette.get("form_label", palette["text_primary"]),
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self.username_entry = ctk.CTkEntry(
            form_box,
            height=38,
            placeholder_text="e.g. admin or cashier1",
            font=ctk.CTkFont(size=12)
        )
        self.username_entry.pack(fill="x", pady=(0, 12))

        # Password
        ctk.CTkLabel(
            form_box,
            text="Password",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette.get("form_label", palette["text_primary"]),
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        pass_row = ctk.CTkFrame(form_box, fg_color="transparent")
        pass_row.pack(fill="x", pady=(0, 10))

        self.password_entry = ctk.CTkEntry(
            pass_row,
            height=38,
            placeholder_text="Enter secure password",
            show="•",
            font=ctk.CTkFont(size=12)
        )
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_toggle_pass = ctk.CTkButton(
            pass_row,
            text="👁️",
            width=38,
            height=38,
            font=ctk.CTkFont(size=13),
            fg_color=palette["bg_secondary"],
            hover_color=palette["border"],
            text_color=palette["text_primary"],
            command=self._toggle_password_visibility
        )
        self.btn_toggle_pass.pack(side="right")

        # Remember me & Forgot Password Row
        action_row = ctk.CTkFrame(form_box, fg_color="transparent")
        action_row.pack(fill="x", pady=(2, 10))

        self.remember_var = ctk.BooleanVar(value=False)
        self.chk_remember = ctk.CTkCheckBox(
            action_row,
            text="Remember Staff ID",
            variable=self.remember_var,
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"],
            checkbox_width=18,
            checkbox_height=18
        )
        self.chk_remember.pack(side="left")

        btn_forgot = ctk.CTkButton(
            action_row,
            text="Forgot Password?",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=palette["bg_secondary"],
            text_color=palette["accent"],
            width=100,
            command=self._open_forgot_password
        )
        btn_forgot.pack(side="right")

        # Error notification strip
        self.error_label = ctk.CTkLabel(
            form_box,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette["danger"],
            wraplength=380,
            justify="center"
        )
        self.error_label.pack(fill="x", pady=(0, 8))

        # Sign In Submit Button
        self.btn_login = ctk.CTkButton(
            form_box,
            text="Sign In to Terminal 🚀",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            text_color="#FFFFFF",
            command=self._handle_login
        )
        self.btn_login.pack(fill="x", pady=(0, 6))

        # 3. Footer Security Indicator
        footer_box = ctk.CTkFrame(card, fg_color="transparent")
        footer_box.pack(fill="x", padx=36, pady=(0, 24))

        ctk.CTkLabel(
            footer_box,
            text="🔒 256-bit PBKDF2 Password Hashing • Role-Enforced RBAC",
            font=ctk.CTkFont(size=10),
            text_color=palette["text_secondary"],
            justify="center"
        ).pack(anchor="center")

        # Keyboard Navigation bindings
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())

    def _toggle_password_visibility(self):
        """Toggles between hidden dots and visible plaintext password."""
        self._password_visible = not self._password_visible
        if self._password_visible:
            self.password_entry.configure(show="")
            self.btn_toggle_pass.configure(text="🔒")
        else:
            self.password_entry.configure(show="•")
            self.btn_toggle_pass.configure(text="👁️")

    def _open_forgot_password(self):
        ForgotPasswordDialog(self.winfo_toplevel())

    def _load_remembered_staff(self):
        """Pre-populates the username if the user previously opted to remember it."""
        try:
            if self._remember_file.exists():
                with open(self._remember_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    staff_id = data.get("staff_id", "")
                    if staff_id:
                        self.username_entry.delete(0, "end")
                        self.username_entry.insert(0, staff_id)
                        self.remember_var.set(True)
                        self.password_entry.focus_set()
                        return
        except Exception:
            pass
        self.username_entry.focus_set()

    def _save_remembered_staff(self, staff_id: str):
        """Persists or clears staff ID based on the Remember Me toggle."""
        try:
            if self.remember_var.get() and staff_id:
                with open(self._remember_file, "w", encoding="utf-8") as f:
                    json.dump({"staff_id": staff_id}, f)
            else:
                if self._remember_file.exists():
                    self._remember_file.unlink()
        except Exception:
            pass

    def _handle_login(self):
        """Validates credentials, establishes session, and triggers role-based routing."""
        if self._is_submitting:
            return

        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username:
            self.error_label.configure(text="Please enter your Staff ID or username.")
            self.username_entry.focus_set()
            return

        if not password:
            self.error_label.configure(text="Please enter your password.")
            self.password_entry.focus_set()
            return

        self._is_submitting = True
        self.btn_login.configure(state="disabled", text="Authenticating Terminal...")
        self.update_idletasks()

        ok, msg, user = self.auth_svc.login(username, password)
        if not ok or not user:
            self._is_submitting = False
            self.btn_login.configure(state="normal", text="Sign In to Terminal 🚀")
            self.error_label.configure(text=msg)
            return

        self._save_remembered_staff(username)
        self.error_label.configure(text="")

        # Apply personalized theme if configured
        from repositories.settings_repository import SettingsRepository
        settings = SettingsRepository().get_by_user_id(user.id)
        if settings:
            theme_manager.apply_theme(settings.theme)

        # Notify application coordinator of authenticated user
        self.on_login_success(user)
