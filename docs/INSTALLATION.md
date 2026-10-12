# Environment Setup & Installation Guide

- **Project:** Restaurant Billing System
- **Subject:** BBAT104 — Fundamentals of Total Quality Management
- **Student Name:** Jay Paneru
- **Registration Number:** 2410302024
- **Assigned Quality Goal:** Q08 — Improve User Satisfaction
- **Document Version:** 1.0.0

---

## 1. System Requirements & Prerequisites

### 1.1 Supported Operating Systems
- **Windows:** Windows 10 / Windows 11 (64-bit)
- **Linux:** Ubuntu 20.04+, Debian 11+, Fedora 36+
- **macOS:** macOS Monterey (12.0) or newer

### 1.2 Runtime Prerequisites
- **Python:** Python 3.10 to 3.12 (Python 3.12 recommended)
- **Package Manager:** `pip` (bundled with Python)
- **Version Control:** `git` (2.30+)
- **Display Support:** Standard desktop GUI windowing environment (DirectX/Tkinter on Windows; X11 or Wayland with `python3-tk` on Linux).

---

## 2. Step-by-Step Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/jaypaneru22-hue/Restaurant-Billing-System.git
cd Restaurant-Billing-System
```

### Step 2: Create Virtual Environment
Isolating dependencies within a virtual environment ensures reproducible execution:

**On Windows (PowerShell / Command Prompt):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell displays an execution policy error, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

Verify installed packages:
```bash
pip list
```
Key packages installed:
- `customtkinter>=5.2.0` (Modern desktop graphical user interface)
- `matplotlib>=3.8.0` (Analytical sales and quality charts)
- `pytest>=8.0.0` (Automated testing framework)
- `Pillow>=10.0.0` (Image and icon scaling)
- `darkdetect>=0.8.0` (OS appearance mode detection)

### Step 4: Verify Database & Headless Self-Test
Before starting the GUI, run the headless validation check:
```bash
python main.py --headless-check
```
*Expected Output:*
`System verified cleanly in headless mode. All database tables and seeds operational.`

### Step 5: Launch the Application
```bash
python main.py
```
Log in using either:
- **Admin:** `admin` / `Admin@123`
- **Cashier:** `cashier1` / `Cashier@123`

---

## 3. Running Automated Tests

All tests execute against a temporary test database, preserving application data:
```bash
# Run all unit and integration tests
pytest -v

# Run with slowest test execution analysis
pytest -v --durations=10
```

---

## 4. Troubleshooting Common Issues

1. **`ModuleNotFoundError: No module named '_tkinter'` (Linux):**
   - Install the system Tk package: `sudo apt-get install python3-tk`.
2. **`Python was not found; run without arguments to install...` (Windows):**
   - Ensure Python was added to your PATH environment variable during installation, or invoke using the full path: `C:\Users\<user>\AppData\Local\Programs\Python\Python312\python.exe`.
3. **Database File Locked:**
   - SQLite files can lock if multiple processes are writing concurrently. Close any other running instances of the app.
