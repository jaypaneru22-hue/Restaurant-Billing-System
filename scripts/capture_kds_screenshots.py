"""Capture screenshots of Chef KDS display for visual verification."""
import os
import customtkinter as ctk
from PIL import ImageGrab
from ui.chef_kds import ChefKDSFrame
from ui.theme_manager import theme_manager

OUTPUT_DIR = r"C:\Users\jaypa\.gemini\antigravity\brain\8c320227-f5be-45fb-9cd9-48cc564ae2f6"


def capture_kds_screenshot(theme_name: str, filename: str):
    theme_manager.apply_theme(theme_name)
    ctk.set_appearance_mode("dark" if theme_name == "dark" else "light")

    root = ctk.CTk()
    root.geometry("1100x750+100+100")
    root.title(f"RestoPro Chef KDS — {theme_name.capitalize()}")

    frame = ChefKDSFrame(root)
    frame.pack(fill="both", expand=True)

    root.update_idletasks()
    root.update()

    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()

    filepath = os.path.join(OUTPUT_DIR, filename)
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img.save(filepath)
    print(f"Captured: {filepath}")

    frame.destroy()
    root.destroy()


if __name__ == "__main__":
    capture_kds_screenshot("dark", "chef_kds_dark_verified.png")
    capture_kds_screenshot("light", "chef_kds_light_verified.png")
