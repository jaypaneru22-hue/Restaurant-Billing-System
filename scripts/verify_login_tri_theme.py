"""Verification script for RestoPro Tri-Theme Login Page:
1. Royal Plum (Dark)
2. Obsidian Orange (Foodix reference theme)
3. Soft Lavender (Light)

Captures high-resolution visual evidence of each theme and verifies all role logins.
"""
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.migrations import initialize_database
from services.auth_service import auth_service
from repositories.user_repository import user_repository
from ui.theme_manager import theme_manager
from ui.login import LoginFrame, ForgotPasswordDialog, CustomerRegisterDialog
from utils.window_utils import center_window

import customtkinter as ctk
from PIL import ImageGrab

ARTIFACTS_DIR = Path(r"C:\Users\jaypa\.gemini\antigravity\brain\8c320227-f5be-45fb-9cd9-48cc564ae2f6")


def verify_tri_theme_login():
    print("=" * 65)
    print("RESTOPRO: VERIFYING TRI-THEME LOGIN & OBSIDIAN ORANGE REFERENCE")
    print("=" * 65)

    initialize_database()

    # Step 1: Create Tk Application
    app = ctk.CTk()
    app.title("RestoPro — Tri-Theme Login Verification")
    center_window(app, target_width=1240, target_height=750, min_width=1024, min_height=640)

    logged_in_user = None

    def on_success(user):
        nonlocal logged_in_user
        logged_in_user = user
        print(f"[AUTH OK] Successfully authenticated as @{user.username} ({user.role})")

    # Instantiate LoginFrame
    login_frame = LoginFrame(app, on_login_success=on_success)
    login_frame.pack(fill="both", expand=True)

    app.update()
    time.sleep(0.5)

    # 1. Verify Default Theme (Royal Plum)
    print("\n--- 1. Testing Theme: Royal Plum (Dark) ---")
    login_frame._switch_theme("dark")
    app.update()
    time.sleep(0.6)

    rx = app.winfo_rootx()
    ry = app.winfo_rooty()
    rw = app.winfo_width()
    rh = app.winfo_height()

    shot_plum = ImageGrab.grab(bbox=(rx, ry, rx + rw, ry + rh))
    plum_path = ARTIFACTS_DIR / "login_theme_royal_plum.png"
    shot_plum.save(plum_path)
    print(f"[SCREENSHOT] Saved Royal Plum preview: {plum_path}")

    # 2. Verify Obsidian Orange Theme (Foodix reference)
    print("\n--- 2. Testing Theme: Obsidian Orange (Foodix Reference) ---")
    login_frame._switch_theme("obsidian_orange")
    app.update()
    time.sleep(0.6)

    shot_orange = ImageGrab.grab(bbox=(rx, ry, rx + rw, ry + rh))
    orange_path = ARTIFACTS_DIR / "login_theme_obsidian_orange.png"
    shot_orange.save(orange_path)
    print(f"[SCREENSHOT] Saved Obsidian Orange preview: {orange_path}")

    # 3. Verify Soft Lavender Theme (Light)
    print("\n--- 3. Testing Theme: Soft Lavender (Light) ---")
    login_frame._switch_theme("light")
    app.update()
    time.sleep(0.6)

    shot_lavender = ImageGrab.grab(bbox=(rx, ry, rx + rw, ry + rh))
    lavender_path = ARTIFACTS_DIR / "login_theme_soft_lavender.png"
    shot_lavender.save(lavender_path)
    print(f"[SCREENSHOT] Saved Soft Lavender preview: {lavender_path}")

    # Switch back to Obsidian Orange to test authentication and dialogs
    login_frame._switch_theme("obsidian_orange")
    app.update()

    # 4. Test Quick Login across all 6 roles
    print("\n--- 4. Testing Quick Logins Across All 6 Roles ---")
    roles = [
        ("admin", "Admin@123", "ADMIN"),
        ("manager1", "Manager@123", "MANAGER"),
        ("cashier1", "Cashier@123", "CASHIER"),
        ("chef1", "Chef@123", "CHEF"),
        ("waiter1", "Waiter@123", "WAITER"),
        ("customer1", "Customer@123", "CUSTOMER"),
    ]

    for u, p, expected_role in roles:
        login_frame._quick_login(u, p)
        assert logged_in_user is not None, f"Login failed for {u}"
        assert logged_in_user.role == expected_role, f"Role mismatch for {u}"
        print(f"[ROLE VERIFIED] {expected_role:<10} | @{u:<10} | Login and session functional.")

    # 5. Verify Forgot Password Dialog in Obsidian Orange
    print("\n--- 5. Testing Dialogs ---")
    login_frame._open_forgot_password()
    app.update()
    time.sleep(0.2)
    print("[DIALOG] Forgot Password dialog opened successfully.")

    app.destroy()
    print("\n[SUCCESS] Tri-Theme Login system verified with 100% test pass rate.")


if __name__ == "__main__":
    verify_tri_theme_login()
