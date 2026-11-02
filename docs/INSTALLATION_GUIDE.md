# INSTALLATION & SYSTEM DEPLOYMENT GUIDE
## Professional Restaurant Management Platform — Technical Setup Reference
**Academic Subject:** BBAT104 — Fundamentals of Total Quality Management  
**Student Name:** Jay Paneru | **Registration Number:** 2410302024  
**Quality Goal:** Q08 — Improve User Satisfaction | **Release:** Enterprise Master v1.0.0

---

## 1. System Requirements & Environment Prerequisites

### Hardware Requirements
- **Processor:** Intel Core i3 / AMD Ryzen 3 or higher.
- **RAM:** Minimum 4 GB RAM (8 GB recommended).
- **Display Resolution:** Optimized for standard POS and laptop resolutions: **1366×768**, 1920×1080 (Full HD), and 4K displays.
- **Disk Space:** Minimum 250 MB free disk space for SQLite database, WAL logs, backups, and thermal receipts.

### Software Prerequisites
- **Operating System:** Windows 10/11, macOS 12+, or Ubuntu Linux 22.04 LTS.
- **Python Runtime:** Python **3.10**, **3.11**, or **3.12** (Python 3.12.3 verified).
- **Core Dependencies:**
  - `customtkinter >= 5.2.0` (Modern GUI widgets and theme engine)
  - `matplotlib >= 3.7.0` (Executive telemetry charts)
  - `pytest >= 8.0.0` (Automated regression testing framework)

---

## 2. Step-by-Step Installation

### Step 1: Clone or Open the Project Repository
```bash
git clone https://github.com/jaypaneru/TQM.git
cd TQM
```

### Step 2: Create and Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On macOS / Linux (Bash):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
*(Alternatively, if running without requirements.txt: `pip install customtkinter matplotlib pytest`)*

### Step 4: Initialize SQLite Database & Schema Migrations
The application automatically checks and executes schema migrations on initial launch. To run the automated database setup explicitly:
```powershell
.\.venv\Scripts\python.exe scripts/manage_db.py init
```
This initializes `data/restaurant.db` with WAL mode enabled, creates all 11 relational tables, and seeds default accounts (`admin`, `manager1`, `cashier1`, `chef1`, `customer1`), 26 menu dishes, and 10 restaurant tables across 4 zones.

---

## 3. Running the Application

Launch the desktop application via:
```powershell
.\.venv\Scripts\python.exe main.py
```
Upon startup, the **Midnight Obsidian** authentication interface appears. Use any of the pre-seeded credentials or click one of the 1-click quick demo buttons.

---

## 4. Running the Automated Regression Test Suite

To verify system integrity, execute the full automated test suite:
```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

Expected output:
```
........................................................................ [ 56%]
.......................................................                  [100%]
127 passed in 62.06s
```

All 127 automated tests must pass with zero failures or errors.

---

## 5. Database Backup & Disaster Recovery Verification

### Manual Snapshot Backup
To create an instant database backup from the command line:
```powershell
.\.venv\Scripts\python.exe scripts/manage_db.py backup
```
Backups are saved to `data/backups/restaurant_YYYYMMDD_HHMMSS.bak`.

### Database Integrity Verification
To inspect SQLite foreign keys, schema consistency, and WAL logs:
```powershell
.\.venv\Scripts\python.exe scripts/manage_db.py health
```

---
*Authored by Jay Paneru (2410302024) for BBAT104 Total Quality Management.*
