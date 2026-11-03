"""Captures high-resolution visual evidence of RestoPro logo on Login and Signup screens."""
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import ImageGrab
import customtkinter as ctk

from config.settings import DEFAULT_THEME
from ui.theme_manager import theme_manager
from ui.login import LoginFrame, CustomerRegisterDialog
from ui.main_window import MainWindow
from services.auth_service import auth_service
from utils.brand_assets import apply_window_icon

ARTIFACTS_DIR = Path(r"C:\Users\jaypa\.gemini\antigravity\brain\8c320227-f5be-45fb-9cd9-48cc564ae2f6")


def capture_window(win, filename: str):
    win.update_idletasks()
    win.update()
    time.sleep(0.3)
    x = win.winfo_rootx()
    y = win.winfo_rooty()
    w = win.winfo_width()
    h = win.winfo_height()
    
    # Grab window bbox
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    dest_path = ARTIFACTS_DIR / filename
    img.save(dest_path)
    print(f"[+] Saved screenshot: {dest_path} ({img.size})")
    return dest_path


def run_captures():
    print("=" * 60)
    print("Capturing RestoPro Brand Asset Evidence")
    print("=" * 60)
    
    app = ctk.CTk()
    app.title("RestoPro — Enterprise Restaurant Management Platform")
    app.geometry("1240x750")
    apply_window_icon(app)

    # 1. Dark Mode Login Screen
    theme_manager.apply_theme("dark")
    login_frame = LoginFrame(app, on_login_success=lambda u: None)
    login_frame.pack(fill="both", expand=True)
    app.update()
    time.sleep(0.4)
    capture_window(app, "restopro_login_dark.png")

    # 2. Light Mode Login Screen
    login_frame._handle_theme_toggle()
    app.update()
    time.sleep(0.4)
    capture_window(app, "restopro_login_light.png")

    # 3. Light Mode Customer Signup Screen
    reg_dlg_light = CustomerRegisterDialog(app, on_registered=lambda u: None)
    reg_dlg_light.update()
    time.sleep(0.4)
    capture_window(reg_dlg_light, "restopro_signup_light.png")
    reg_dlg_light.destroy()

    # 4. Dark Mode Customer Signup Screen
    theme_manager.apply_theme("dark")
    login_frame._handle_theme_toggle()
    reg_dlg_dark = CustomerRegisterDialog(app, on_registered=lambda u: None)
    reg_dlg_dark.update()
    time.sleep(0.4)
    capture_window(reg_dlg_dark, "restopro_signup_dark.png")
    reg_dlg_dark.destroy()

    # 5. Sidebar Branding with RestoPro Emblem Icon
    login_frame.destroy()
    auth_service.login("admin", "Admin@123")
    main_win = MainWindow(app, on_logout=lambda: None)
    main_win.pack(fill="both", expand=True)
    app.update()
    time.sleep(0.4)
    capture_window(app, "restopro_sidebar_branding.png")

    main_win.destroy()
    app.destroy()
    print("=" * 60)
    print("All Brand Asset Screenshots Captured Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run_captures()
