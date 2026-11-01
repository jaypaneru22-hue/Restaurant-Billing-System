"""User Profile and Preference Settings view (Q08-F5)."""
import customtkinter as ctk
from services.profile_service import ProfileService, profile_service
from services.auth_service import AuthService, auth_service
from ui.theme_manager import theme_manager
from config.settings import DEFAULT_TAX_RATE


class ProfileFrame(ctk.CTkFrame):
    """User profile management, password security updates, and theme preferences (Q08-F5)."""

    def __init__(
        self,
        master,
        initial_tab: str = "profile",
        profile_svc: ProfileService = profile_service,
        auth_svc: AuthService = auth_service,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.initial_tab = initial_tab
        self.profile_svc = profile_svc
        self.auth_svc = auth_svc

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self.load_profile_data()
        if initial_tab == "settings":
            self.tab_selector.set("⚙️ System Settings")
            self._switch_tab("⚙️ System Settings")
        else:
            self.tab_selector.set("👤 User Profile")
            self._switch_tab("👤 User Profile")

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(
            title_box,
            text="👤 User Profile & Settings",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Manage your account identity, security credentials, and system preferences (Q08-F5)",
            font=ctk.CTkFont(size=12),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        # Tab Segmented Button
        self.tab_selector = ctk.CTkSegmentedButton(
            header,
            values=["👤 User Profile", "⚙️ System Settings"],
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            selected_color=palette["accent"],
            selected_hover_color=palette["accent_hover"],
            command=self._switch_tab
        )
        self.tab_selector.pack(side="right")

        # Scrollable container for cards
        self.container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # =====================================================================
        # TAB 1: USER PROFILE CARD
        # =====================================================================
        self.card_info = ctk.CTkFrame(self.container, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])

        ctk.CTkLabel(
            self.card_info,
            text="Account Information",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w", padx=20, pady=(15, 10))

        grid_frame = ctk.CTkFrame(self.card_info, fg_color="transparent")
        grid_frame.pack(fill="x", padx=20, pady=(0, 15))

        # Username
        ctk.CTkLabel(grid_frame, text="Username:", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).grid(row=0, column=0, sticky="w", pady=6)
        self.lbl_username = ctk.CTkLabel(grid_frame, text="-", font=ctk.CTkFont(size=13, weight="bold"), text_color=palette["text_primary"])
        self.lbl_username.grid(row=0, column=1, sticky="w", padx=15, pady=6)

        # Role
        ctk.CTkLabel(grid_frame, text="Role:", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).grid(row=1, column=0, sticky="w", pady=6)
        self.lbl_role = ctk.CTkLabel(grid_frame, text="-", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["accent"])
        self.lbl_role.grid(row=1, column=1, sticky="w", padx=15, pady=6)

        # Member Since
        ctk.CTkLabel(grid_frame, text="Member Since:", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).grid(row=2, column=0, sticky="w", pady=6)
        self.lbl_created = ctk.CTkLabel(grid_frame, text="-", font=ctk.CTkFont(size=12), text_color=palette["text_secondary"])
        self.lbl_created.grid(row=2, column=1, sticky="w", padx=15, pady=6)

        # Full Name Input
        ctk.CTkLabel(grid_frame, text="Full Name:", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).grid(row=3, column=0, sticky="w", pady=6)
        self.entry_name = ctk.CTkEntry(grid_frame, width=300, height=36, font=ctk.CTkFont(size=13))
        self.entry_name.grid(row=3, column=1, sticky="w", padx=15, pady=6)

        self.btn_save_profile = ctk.CTkButton(
            self.card_info,
            text="Save Profile Name",
            width=160,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._handle_save_profile
        )
        self.btn_save_profile.pack(anchor="w", padx=20, pady=(0, 15))

        self.lbl_profile_msg = ctk.CTkLabel(self.card_info, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_profile_msg.pack(anchor="w", padx=20, pady=(0, 10))

        # =====================================================================
        # TAB 2: SYSTEM PREFERENCES & SECURITY
        # =====================================================================
        # Card 2: Workspace & Theme Preferences
        self.card_pref = ctk.CTkFrame(self.container, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])

        ctk.CTkLabel(
            self.card_pref,
            text="Workspace & Theme Preferences",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w", padx=20, pady=(15, 10))

        pref_grid = ctk.CTkFrame(self.card_pref, fg_color="transparent")
        pref_grid.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(pref_grid, text="Theme Mode:", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).grid(row=0, column=0, sticky="w", pady=6)
        self.seg_theme = ctk.CTkSegmentedButton(pref_grid, values=["light", "dark"], width=200, height=32)
        self.seg_theme.grid(row=0, column=1, sticky="w", padx=15, pady=6)

        ctk.CTkLabel(pref_grid, text="Default Tax Rate (%):", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).grid(row=1, column=0, sticky="w", pady=6)
        self.entry_tax = ctk.CTkEntry(pref_grid, width=200, height=36, font=ctk.CTkFont(size=13))
        self.entry_tax.grid(row=1, column=1, sticky="w", padx=15, pady=6)

        btn_save_pref = ctk.CTkButton(
            self.card_pref,
            text="Apply & Persist Preferences",
            width=220,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=palette["success"],
            hover_color=palette["accent_hover"],
            command=self._handle_save_preferences
        )
        btn_save_pref.pack(anchor="w", padx=20, pady=(0, 15))

        self.lbl_pref_msg = ctk.CTkLabel(self.card_pref, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_pref_msg.pack(anchor="w", padx=20, pady=(0, 10))

        # Card 3: Security & Password Update
        self.card_sec = ctk.CTkFrame(self.container, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])

        ctk.CTkLabel(
            self.card_sec,
            text="Security & Password Change",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w", padx=20, pady=(15, 10))

        sec_grid = ctk.CTkFrame(self.card_sec, fg_color="transparent")
        sec_grid.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(sec_grid, text="Current Password:", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).grid(row=0, column=0, sticky="w", pady=6)
        self.entry_curr_pass = ctk.CTkEntry(sec_grid, width=300, height=36, show="•")
        self.entry_curr_pass.grid(row=0, column=1, sticky="w", padx=15, pady=6)

        ctk.CTkLabel(sec_grid, text="New Password:", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).grid(row=1, column=0, sticky="w", pady=6)
        self.entry_new_pass = ctk.CTkEntry(sec_grid, width=300, height=36, show="•")
        self.entry_new_pass.grid(row=1, column=1, sticky="w", padx=15, pady=6)

        ctk.CTkLabel(sec_grid, text="Confirm Password:", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).grid(row=2, column=0, sticky="w", pady=6)
        self.entry_conf_pass = ctk.CTkEntry(sec_grid, width=300, height=36, show="•")
        self.entry_conf_pass.grid(row=2, column=1, sticky="w", padx=15, pady=6)

        btn_save_pass = ctk.CTkButton(
            self.card_sec,
            text="Update Password",
            width=180,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._handle_change_password
        )
        btn_save_pass.pack(anchor="w", padx=20, pady=(0, 15))

        self.lbl_pass_msg = ctk.CTkLabel(self.card_sec, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_pass_msg.pack(anchor="w", padx=20, pady=(0, 10))

    def _switch_tab(self, selected_tab: str):
        if "Profile" in selected_tab:
            self.card_info.pack(fill="x", pady=(0, 15), padx=5)
            self.card_pref.pack_forget()
            self.card_sec.pack_forget()
        else:
            self.card_info.pack_forget()
            self.card_pref.pack(fill="x", pady=(0, 15), padx=5)
            self.card_sec.pack(fill="x", pady=(0, 15), padx=5)

    def load_profile_data(self):
        user = self.auth_svc.current_user
        if not user:
            return
        data = self.profile_svc.get_profile_data(user.id)
        if not data:
            return

        self.lbl_username.configure(text=data["username"])
        self.lbl_role.configure(text=data["role"])
        self.lbl_created.configure(text=str(data["created_at"] or "N/A"))

        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, data["full_name"])

        self.seg_theme.set(data["theme"])

        self.entry_tax.delete(0, "end")
        self.entry_tax.insert(0, str(data["default_tax_rate"]))

    def _handle_save_profile(self):
        user = self.auth_svc.current_user
        if not user:
            return
        new_name = self.entry_name.get().strip()
        ok, msg = self.profile_svc.update_profile(user.id, new_name)
        palette = theme_manager.get_palette()
        color = palette["success"] if ok else palette["danger"]
        self.lbl_profile_msg.configure(text=msg, text_color=color)
        if ok:
            user.full_name = new_name

    def _handle_save_preferences(self):
        user = self.auth_svc.current_user
        if not user:
            return
        theme_val = self.seg_theme.get()
        tax_val = self.entry_tax.get().strip()

        ok, msg = self.profile_svc.update_preferences(user.id, theme_val, tax_val)
        palette = theme_manager.get_palette()
        color = palette["success"] if ok else palette["danger"]
        self.lbl_pref_msg.configure(text=msg, text_color=color)

        if ok:
            theme_manager.apply_theme(theme_val, user_id=user.id)

    def _handle_change_password(self):
        user = self.auth_svc.current_user
        if not user:
            return
        curr_p = self.entry_curr_pass.get()
        new_p = self.entry_new_pass.get()
        conf_p = self.entry_conf_pass.get()

        ok, msg = self.profile_svc.change_password(user.id, curr_p, new_p, conf_p)
        palette = theme_manager.get_palette()
        color = palette["success"] if ok else palette["danger"]
        self.lbl_pass_msg.configure(text=msg, text_color=color)

        if ok:
            self.entry_curr_pass.delete(0, "end")
            self.entry_new_pass.delete(0, "end")
            self.entry_conf_pass.delete(0, "end")
