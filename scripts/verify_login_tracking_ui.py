"""Script to verify Account Status & Last Session tracking and capture UI screenshot."""
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import db
from repositories.user_repository import user_repository
from services.auth_service import auth_service
from ui.theme_manager import theme_manager
from utils.brand_assets import _IMAGE_CACHE

import customtkinter as ctk
from PIL import ImageGrab


def verify_login_tracking():
    print("=" * 60)
    print("RESTOPRO: VERIFYING LOGIN TRACKING & ACCOUNT STATUS")
    print("=" * 60)

    # 1. Test authentications for all 5 roles
    roles = [
        ("admin", "Admin@123", "ADMIN"),
        ("manager1", "Manager@123", "MANAGER"),
        ("cashier1", "Cashier@123", "CASHIER"),
        ("chef1", "Chef@123", "CHEF"),
        ("customer1", "Customer@123", "CUSTOMER"),
    ]

    for user, pwd, role in roles:
        ok, msg, u = auth_service.login(user, pwd)
        assert ok is True, f"Login failed for {user}: {msg}"
        db_user = user_repository.get_by_username(user)
        assert db_user.last_login is not None, f"last_login is None for {user}"
        print(f"Role: {role:<10} | User: @{user:<10} | Status: {'Active' if db_user.is_active else 'Deactivated':<11} | Last Session: {db_user.format_last_login()}")

    # 2. Test failed login (wrong password)
    prev_admin_login = user_repository.get_by_username("admin").last_login
    ok, msg, _ = auth_service.login("admin", "WrongPassword!99")
    assert ok is False
    assert user_repository.get_by_username("admin").last_login == prev_admin_login
    print("Failed login guard verified: last_login remained unchanged.")

    # 3. Create a test user who has NEVER logged in
    test_uname = "new_staff_audit"
    existing = user_repository.get_by_username(test_uname)
    if existing:
        with db.transaction() as conn:
            conn.cursor().execute("DELETE FROM users WHERE username = ?;", (test_uname,))

    from utils.security import hash_password
    created = user_repository.create(
        username=test_uname,
        password_hash=hash_password("Audit@123"),
        full_name="Audit Tester (Never Logged In)",
        role="CASHIER",
        is_active=True
    )
    assert created.last_login is None
    assert created.format_last_login() == "Never logged in"
    print(f"Never-logged-in user verified: @{test_uname} shows '{created.format_last_login()}'")

    print("ALL LOGIN TRACKING DATABASE ASSERTIONS PASSED.")


def capture_staff_activity_ui():
    """Mounts StaffActivityFrame and saves a screenshot."""
    print("Rendering StaffActivityFrame in CustomTkinter...")
    _IMAGE_CACHE.clear()

    theme_manager.apply_theme("dark")
    root = ctk.CTk()
    root.geometry("1100x720")
    root.title("RestoPro — Staff Activity & Session Telemetry")

    from ui.staff_activity import StaffActivityFrame
    frame = StaffActivityFrame(root)
    frame.pack(fill="both", expand=True)

    root.update_idletasks()
    root.update()

    # Capture window screenshot
    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()

    # Save to artifacts directory
    artifact_dir = Path(r"C:\Users\jaypa\.gemini\antigravity\brain\8c320227-f5be-45fb-9cd9-48cc564ae2f6")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "admin_staff_sessions_dark.png"

    try:
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        img.save(str(out_path))
        print(f"Captured screenshot to {out_path}")
    except Exception as e:
        print(f"Failed to grab screenshot: {e}")

    root.destroy()
    _IMAGE_CACHE.clear()

    # Capture UserManagementFrame
    print("Rendering UserManagementFrame in CustomTkinter...")
    root2 = ctk.CTk()
    root2.geometry("1100x720")
    root2.title("RestoPro — Staff Account Administration")

    from ui.users import UserManagementFrame
    u_frame = UserManagementFrame(root2)
    u_frame.pack(fill="both", expand=True)

    root2.update_idletasks()
    root2.update()

    x2 = root2.winfo_rootx()
    y2 = root2.winfo_rooty()
    w2 = root2.winfo_width()
    h2 = root2.winfo_height()

    out_path2 = artifact_dir / "admin_user_management_dark.png"
    try:
        img2 = ImageGrab.grab(bbox=(x2, y2, x2 + w2, y2 + h2))
        img2.save(str(out_path2))
        print(f"Captured screenshot to {out_path2}")
    except Exception as e:
        print(f"Failed to grab user management screenshot: {e}")

    root2.destroy()
    _IMAGE_CACHE.clear()


if __name__ == "__main__":
    verify_login_tracking()
    capture_staff_activity_ui()
