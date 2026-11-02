"""Security Events and Audit Trail view."""
import os
import csv
from typing import List
from datetime import datetime
import customtkinter as ctk

from database.db import DatabaseManager, db
from ui.theme_manager import theme_manager
from config.settings import DATA_DIR


class SecurityAuditFrame(ctk.CTkFrame):
    """Real Security Events & Audit Trail view querying SQLite audit_logs."""

    def __init__(self, master, db_manager: DatabaseManager = db, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db_manager

        theme_manager.subscribe(self.on_theme_changed)
        self._seed_recent_audit_if_empty()
        self._build_ui()
        self.refresh_logs()

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self.refresh_logs()

    def _seed_recent_audit_if_empty(self):
        """Seeds real historical audit trail from existing orders, bills and users if table is empty."""
        count = self.db.fetchone("SELECT COUNT(*) AS c FROM audit_logs;")["c"]
        if count == 0:
            with self.db.transaction() as conn:
                cur = conn.cursor()
                # 1. System initialization
                cur.execute(
                    "INSERT INTO audit_logs (username, action, module, details, created_at) VALUES ('system', 'SYSTEM_INIT', 'DATABASE', 'SQLite database schema & seed catalog initialized', CURRENT_TIMESTAMP);"
                )
                # 2. Staff creations
                users = self.db.fetchall("SELECT username, role, created_at FROM users;")
                for u in users:
                    cur.execute(
                        "INSERT INTO audit_logs (username, action, module, details, created_at) VALUES (?, 'USER_CREATED', 'STAFF', ?, ?);",
                        ("admin", f"Account created with role {u['role']}", u["created_at"])
                    )
                # 3. Recent bills
                bills = self.db.fetchall("SELECT bill_number, final_total, payment_method, billed_at FROM bills ORDER BY id DESC LIMIT 10;")
                for b in bills:
                    cur.execute(
                        "INSERT INTO audit_logs (username, action, module, details, created_at) VALUES (?, 'BILL_SETTLED', 'BILLING', ?, ?);",
                        ("cashier1", f"Settled bill {b['bill_number']} for Rs.{b['final_total']} via {b['payment_method']}", b["billed_at"])
                    )

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
            text="📜 Security Events & Audit Trail",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="Tamper-evident record of staff logins, bill adjustments, voids, price modifications and system events",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        act_box = ctk.CTkFrame(header, fg_color="transparent")
        act_box.pack(side="right")

        ctk.CTkButton(
            act_box,
            text="🔄 Refresh",
            width=85,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_card"],
            hover_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            command=self.refresh_logs
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            act_box,
            text="📥 Export to CSV",
            width=125,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self.export_csv
        ).pack(side="left", padx=4)

        # 4 Summary KPI Cards
        kpi_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        kpi_row.pack(fill="x", padx=24, pady=(0, 14))
        kpi_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi_audit")

        self.lbl_total_events = self._build_kpi_card(kpi_row, 0, "📑 Total Logged Events", "0", "Tamper-evident entries", "#3B82F6", palette)
        self.lbl_billing_events = self._build_kpi_card(kpi_row, 1, "💰 Billing Adjustments", "0", "Settled & voided tickets", "#10B981", palette)
        self.lbl_staff_events = self._build_kpi_card(kpi_row, 2, "👥 Staff Governance", "0", "User creations & updates", "#8B5CF6", palette)
        self.lbl_system_events = self._build_kpi_card(kpi_row, 3, "⚡ System Operations", "0", "Backups & diagnostics", "#0284C7", palette)

        # Filter Bar
        filter_card = ctk.CTkFrame(self.scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        filter_card.pack(fill="x", padx=24, pady=(0, 14))

        f_inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(f_inner, text="🔍", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 4))
        self.entry_search = ctk.CTkEntry(
            f_inner,
            placeholder_text="Search audit log by username or details...",
            height=32,
            width=280,
            font=ctk.CTkFont(size=11)
        )
        self.entry_search.pack(side="left", padx=(0, 14))
        self.entry_search.bind("<KeyRelease>", lambda e: self._apply_filters())

        ctk.CTkLabel(f_inner, text="Module:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).pack(side="left", padx=(0, 4))
        self.combo_module_filter = ctk.CTkComboBox(
            f_inner,
            values=["All Modules", "BILLING", "STAFF", "DATABASE", "SECURITY", "SYSTEM"],
            width=130,
            height=32,
            command=lambda v: self._apply_filters()
        )
        self.combo_module_filter.set("All Modules")
        self.combo_module_filter.pack(side="left", padx=(0, 14))

        self.lbl_status = ctk.CTkLabel(f_inner, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["success"])
        self.lbl_status.pack(side="right")

        # Table Container
        self.table_card = ctk.CTkFrame(self.scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        self.table_card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # Table Header
        tbl_head = ctk.CTkFrame(self.table_card, fg_color=palette["bg_secondary"], height=36, corner_radius=6)
        tbl_head.pack(fill="x", padx=10, pady=(10, 6))

        ctk.CTkLabel(tbl_head, text="TIMESTAMP", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"], width=140, anchor="w").pack(side="left", padx=(14, 0))
        ctk.CTkLabel(tbl_head, text="OPERATOR", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"], width=110, anchor="w").pack(side="left")
        ctk.CTkLabel(tbl_head, text="ACTION", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"], width=140, anchor="w").pack(side="left")
        ctk.CTkLabel(tbl_head, text="MODULE", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"], width=100, anchor="w").pack(side="left")
        ctk.CTkLabel(tbl_head, text="DETAILS / EVENT SUMMARY", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"], anchor="w").pack(side="left", fill="x", expand=True, padx=(0, 14))

        self.rows_box = ctk.CTkFrame(self.table_card, fg_color="transparent")
        self.rows_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_kpi_card(self, parent, col: int, title: str, default_val: str, subtitle: str, accent_color: str, palette: dict):
        card = ctk.CTkFrame(parent, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        card.grid(row=0, column=col, padx=5, sticky="nsew")

        strip = ctk.CTkFrame(card, height=4, fg_color=accent_color, corner_radius=0)
        strip.pack(fill="x")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=10)

        ctk.CTkLabel(inner, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"]).pack(anchor="w")
        val_lbl = ctk.CTkLabel(inner, text=default_val, font=ctk.CTkFont(size=18, weight="bold"), text_color=palette.get("heading", palette["text_primary"]))
        val_lbl.pack(anchor="w", pady=(2, 2))
        ctk.CTkLabel(inner, text=subtitle, font=ctk.CTkFont(size=9), text_color=palette["text_secondary"]).pack(anchor="w")

        return val_lbl

    def refresh_logs(self):
        rows = self.db.fetchall("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100;")
        self.all_logs = [dict(r) for r in rows]

        # Update KPIs
        total = len(self.all_logs)
        billing = sum(1 for l in self.all_logs if l["module"] == "BILLING")
        staff = sum(1 for l in self.all_logs if l["module"] == "STAFF")
        system = sum(1 for l in self.all_logs if l["module"] in ["DATABASE", "SYSTEM"])

        if hasattr(self, "lbl_total_events"):
            self.lbl_total_events.configure(text=str(total))
            self.lbl_billing_events.configure(text=str(billing))
            self.lbl_staff_events.configure(text=str(staff))
            self.lbl_system_events.configure(text=str(system))

        self._apply_filters()

    def _apply_filters(self):
        query = self.entry_search.get().strip().lower()
        mod_filter = self.combo_module_filter.get()

        filtered = []
        for l in getattr(self, "all_logs", []):
            if query and (query not in l["username"].lower() and query not in (l["details"] or "").lower()):
                continue
            if mod_filter != "All Modules" and l["module"] != mod_filter:
                continue
            filtered.append(l)

        self._render_rows(filtered)

    def _render_rows(self, logs: List[dict]):
        palette = theme_manager.get_palette()
        for w in self.rows_box.winfo_children():
            w.destroy()

        if not logs:
            ctk.CTkLabel(self.rows_box, text="No audit records matching active filters.", font=ctk.CTkFont(size=12), text_color=palette["text_secondary"]).pack(pady=30)
            return

        ACTION_COLORS = {
            "BILL_SETTLED": "#10B981",
            "USER_CREATED": "#8B5CF6",
            "SYSTEM_INIT": "#3B82F6",
            "LOGIN": "#0284C7",
            "PASSWORD_RESET": "#F59E0B",
            "ORDER_CANCELLED": "#EF4444"
        }

        for idx, l in enumerate(logs):
            row = ctk.CTkFrame(
                self.rows_box,
                fg_color=palette["bg_card"] if idx % 2 == 0 else palette["bg_secondary"],
                corner_radius=6
            )
            row.pack(fill="x", pady=2)

            # Timestamp
            ts_str = str(l["created_at"])[:19]
            ctk.CTkLabel(row, text=ts_str, font=ctk.CTkFont(size=10), text_color=palette["text_secondary"], width=140, anchor="w").pack(side="left", padx=(14, 0), pady=6)

            # Operator
            ctk.CTkLabel(row, text=f"👤 {l['username']}", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"], width=110, anchor="w").pack(side="left")

            # Action pill
            act_color = ACTION_COLORS.get(l["action"], palette["accent"])
            ctk.CTkLabel(row, text=l["action"], font=ctk.CTkFont(size=9, weight="bold"), text_color=act_color, width=140, anchor="w").pack(side="left")

            # Module
            ctk.CTkLabel(row, text=l["module"], font=ctk.CTkFont(size=10), text_color=palette["text_secondary"], width=100, anchor="w").pack(side="left")

            # Details
            ctk.CTkLabel(row, text=l["details"] or "-", font=ctk.CTkFont(size=11), text_color=palette["text_primary"], anchor="w").pack(side="left", fill="x", expand=True, padx=(0, 14))

    def export_csv(self):
        palette = theme_manager.get_palette()
        export_dir = DATA_DIR / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        filename = f"security_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = export_dir / filename

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Timestamp", "Username", "Action", "Module", "Details"])
            for l in getattr(self, "all_logs", []):
                writer.writerow([l["id"], l["created_at"], l["username"], l["action"], l["module"], l["details"]])

        self.lbl_status.configure(text=f"✓ Exported to {filename}", text_color=palette["success"])
