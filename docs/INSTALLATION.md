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
```
> **Windows Security Tip:** If PowerShell script execution is disabled (`Activate.ps1 cannot be loaded`), activation is **not** necessary! You can invoke the virtual environment's Python directly:
> ```powershell
> .\.venv\Scripts\python.exe -m pip install -r requirements.txt
> .\.venv\Scripts\python.exe main.py
> ```
> Or simply double-click [`run_app.bat`](../run_app.bat).

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Install Required Dependencies
```bash
# Using direct venv python on Windows:
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Or within activated shell:
pip install -r requirements.txt
```

Verify installed packages:
```bash
.\.venv\Scripts\python.exe -m pip list
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
.\.venv\Scripts\python.exe main.py --headless-check
```
*Expected Output:*
`System verified cleanly in headless mode. All database tables and seeds operational.`

### Step 5: Launch the Application

**Option A (Easiest — One Click on Windows):**
Double-click `run_app.bat` from File Explorer or run in terminal:
```powershell
.\run_app.bat
```

**Option B (Direct Python invocation):**
```powershell
.\.venv\Scripts\python.exe main.py
```

Log in using either:
- **Admin:** `admin` / `Admin@123`
- **Cashier:** `cashier1` / `Cashier@123`

---

## 3. Database Administration & Demo Data Governance

The project includes an administration CLI tool [`scripts/manage_db.py`](../scripts/manage_db.py) for placement demonstrations and data audits:

```bash
# Check current database status and row counts:
.\.venv\Scripts\python.exe scripts\manage_db.py status

# Create a timestamped backup snapshot in data/backups/:
.\.venv\Scripts\python.exe scripts\manage_db.py backup

# Clean demo orders/bills for a clean presentation (preserves users & menu):
.\.venv\Scripts\python.exe scripts\manage_db.py clean-demo --confirm

# Seed realistic demonstration orders across the past 5 days for charts:
.\.venv\Scripts\python.exe scripts\manage_db.py seed-demo

# Recover or reset the default administrator password (Admin@123):
.\.venv\Scripts\python.exe scripts\manage_db.py recover-admin

# Complete database reset with master seeds:
.\.venv\Scripts\python.exe scripts\manage_db.py reset --confirm
```

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
