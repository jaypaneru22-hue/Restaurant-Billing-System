# Restaurant Billing System (TQM Project)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![GUI-CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![Database-SQLite3](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![Tests-pytest](https://img.shields.io/badge/Tests-pytest-brightgreen.svg)](https://pytest.org/)
[![Quality-TQM_Q08](https://img.shields.io/badge/Quality_Goal-Q08_Improve_User_Satisfaction-orange.svg)](#)

A production-grade, modular Desktop Restaurant Billing and Point-of-Sale (POS) System developed as a college project for **BBAT104 — Fundamentals of Total Quality Management**.

---

## 📌 Project Overview

- **Subject:** BBAT104 — Fundamentals of Total Quality Management
- **Course Assignment:** Restaurant Billing System
- **Student Name:** Jay Paneru
- **Registration Number:** `2410302024`
- **Assigned Quality Goal:** **Q08 — Improve User Satisfaction**
- **Academic Session:** 2026–27
- **GitHub Repository:** [jaypaneru22-hue/Restaurant-Billing-System](https://github.com/jaypaneru22-hue/Restaurant-Billing-System)

---

## 🎯 Assigned Q08 Quality Features

To fulfill **Quality Goal Q08 (Improve User Satisfaction)**, this system integrates five dedicated quality features directly into the core workflow:

1. **📊 Interactive Live Dashboard:** Real-time calculation of today's sales revenue, completed orders count, pending order volume, average order value (AOV), recent orders list, and top 5 best-selling menu items.
2. **📈 Visual Analytical Reports:** Embedded Matplotlib charts illustrating daily sales trends, top-selling dishes, order fulfillment distribution, and payment method share.
3. **🌓 Persistent Theme Toggle:** Seamless switching between Dark Mode and Light Mode with user preference persisted in SQLite and restored automatically across sessions.
4. **⌨️ Cashier Keyboard Shortcuts:** Rapid transaction accelerators (`Alt+N` for New Order, `Alt+D` for Dashboard, `Alt+M` for Menu, `Alt+R` for Reports, `Alt+P` for Profile, `Esc` to cancel/dismiss).
5. **👤 User Profile & Preference Settings:** Secure profile viewer, display name updater, password change with hash verification, and persistent theme controls.

---

## 🏗️ Software Architecture

The application adopts a clean, layered architecture separating user interface presentation, business validation rules, data persistence, and database schema:

```
TQM/
├── main.py                     # Application entry point & launcher
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview & guide
├── .gitignore                  # Git ignore rules
│
├── config/                     # Application configuration & constants
│   ├── __init__.py
│   └── settings.py
│
├── database/                   # SQLite database engine, schema, migrations
│   ├── __init__.py
│   ├── db.py                   # Thread-safe connection manager & transaction helpers
│   ├── schema.py               # DDL table creation with foreign keys
│   └── migrations.py           # Seed data and schema migration utilities
│
├── models/                     # Strongly-typed domain entity dataclasses
│   ├── __init__.py
│   ├── user.py
│   ├── menu_item.py
│   ├── order.py
│   └── order_item.py
│
├── repositories/               # Direct SQL queries and data mapping
│   ├── __init__.py
│   ├── user_repository.py
│   ├── menu_repository.py
│   ├── order_repository.py
│   └── settings_repository.py
│
├── services/                   # Business rules, Decimal calculations, validations
│   ├── __init__.py
│   ├── auth_service.py
│   ├── menu_service.py
│   ├── order_service.py
│   ├── billing_service.py
│   ├── dashboard_service.py
│   ├── report_service.py
│   └── profile_service.py
│
├── ui/                         # CustomTkinter GUI views & Theme Manager
│   ├── __init__.py
│   ├── theme_manager.py
│   ├── login.py
│   ├── main_window.py
│   ├── dashboard.py
│   ├── menu.py
│   ├── orders.py
│   ├── billing.py
│   ├── reports.py
│   └── profile.py
│
├── utils/                      # Input validators, PBKDF2 hashing, rotating logger
│   ├── __init__.py
│   ├── validators.py
│   ├── security.py
│   └── logger.py
│
├── scripts/                     # Placement administration & database governance suite
│   └── manage_db.py            # Status, backup, clean-demo, seed-demo, recover-admin
│
├── quality/                    # TQM artifacts, checksheets, Pareto & Fishbone scripts
│   ├── defects.csv
│   ├── checksheet.csv
│   ├── fmea.csv
│   ├── pdca_log.csv
│   └── generate_charts.py
│
├── tests/                      # Automated pytest unit & integration test suite (63 tests)
│   ├── __init__.py
│   ├── conftest.py             # Shared pytest fixtures & temporary database factory
│   ├── test_auth_service.py
│   ├── test_billing_service.py
│   ├── test_dashboard_service.py
│   ├── test_database.py
│   ├── test_database_manager.py
│   ├── test_logger.py
│   ├── test_manage_db.py       # Backup, clean-demo & recovery tests
│   ├── test_menu_service.py
│   ├── test_models.py
│   ├── test_order_service.py
│   ├── test_profile_service.py
│   ├── test_report_service.py
│   ├── test_security.py
│   ├── test_theme_manager.py
│   └── test_validators.py
│
├── docs/                       # Comprehensive technical and TQM documentation
│   ├── SRS.md                  # Software Requirements Specification
│   ├── ARCHITECTURE.md         # Component diagrams & data flows
│   ├── DATABASE_DESIGN.md      # Relational schema & constraints
│   ├── TEST_PLAN.md            # Test strategies & test matrices
│   ├── TEST_RESULTS.md         # Automated test logs & pass rates
│   ├── TQM_REPORT.md           # SIPOC, CTQ, FMEA, Pareto, Fishbone & PDCA
│   ├── USER_MANUAL.md          # Step-by-step cashier & manager guide
│   ├── INSTALLATION.md         # Environment setup instructions
│   ├── GITHUB_WORKFLOW.md      # Branching & commit policy
│   └── COMMIT_TRACKER.md       # Verifiable commit history log
│
├── run_app.bat                 # One-click Windows desktop GUI launcher
├── main.py                     # Application entry point & GUI coordinator
└── requirements.txt            # Pinned dependency requirements
```

---

## 🚀 Installation & Quick Start

### 1. Prerequisites
- **Python:** 3.10 to 3.12 (Python 3.12 recommended)
- **Git**

### 2. Setup Virtual Environment
```bash
# Clone the repository (if not already local)
git clone https://github.com/jaypaneru22-hue/Restaurant-Billing-System.git
cd Restaurant-Billing-System

# Create virtual environment
python -m venv .venv
```

### 3. Install Dependencies
```bash
# On Windows (PowerShell / Command Prompt):
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# On Linux / macOS:
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the Application

#### Option A: One-Click Desktop Launcher (Windows)
Double-click [`run_app.bat`](run_app.bat) in File Explorer or run in terminal:
```powershell
.\run_app.bat
```

#### Option B: Direct Python Invocation (Windows PowerShell / CMD)
```powershell
.\.venv\Scripts\python.exe main.py
```
> **Windows Security Note:** This direct invocation bypasses PowerShell's `Activate.ps1 cannot be loaded` execution policy restriction without requiring administrator privileges or modifying system security settings.

#### Option C: Headless Verification Mode (CI/Server)
```powershell
.\.venv\Scripts\python.exe main.py --headless-check
```

### 5. Default Demonstration Credentials
- **Administrator:** `admin` / `Admin@123` *(Full access to Dashboard, Menu CRUD, Billing, Analytics, Profile, Theme)*
- **Cashier:** `cashier1` / `Cashier@123` *(Operational access to Dashboard, New Order POS, Order History, Billing, Profile, Theme)*

---

## 🛠️ Database Administration & Demo Governance

The project includes an administration CLI utility [`scripts/manage_db.py`](scripts/manage_db.py) to audit, backup, clean, and re-seed the SQLite database for placement interviews:

```powershell
# 1. Audit current database tables and row counts:
.\.venv\Scripts\python.exe scripts\manage_db.py status

# 2. Create an instant timestamped backup in data/backups/:
.\.venv\Scripts\python.exe scripts\manage_db.py backup

# 3. Clean demo transactions for a clean presentation (preserves users & menu):
.\.venv\Scripts\python.exe scripts\manage_db.py clean-demo --confirm

# 4. Seed 10 realistic demo transactions across past 5 days for charts:
.\.venv\Scripts\python.exe scripts\manage_db.py seed-demo

# 5. Recover or reset administrator credentials (Admin@123):
.\.venv\Scripts\python.exe scripts\manage_db.py recover-admin

# 6. Complete database reset with master seeds:
.\.venv\Scripts\python.exe scripts\manage_db.py reset --confirm
```

---

## 🧪 Automated Testing Suite

The project includes **63 automated unit and integration tests** (100% pass rate) with zero external network dependencies:

```powershell
# Run the complete test suite
.\.venv\Scripts\python.exe -m pytest -v

# Run with execution duration ranking
.\.venv\Scripts\python.exe -m pytest -v --durations=10
```

---

## 🎓 Placement Interview Guide & Technical Highlights

### 1. Problem Statement
Traditional restaurant point-of-sale systems suffer from slow mouse-dependent navigation, IEEE 754 floating-point rounding errors during tax calculation, accidental item deletion, and poor auditability. This project develops a reliable desktop Restaurant Billing System engineered under **Total Quality Management (TQM)** principles to achieve Quality Goal **Q08: Improve User Satisfaction**.

### 2. Architecture & Design Patterns
- **Layered Architecture:** Clear decoupling between UI (`ui/`), Business Logic (`services/`), Data Access (`repositories/`), and Persistence (`database/`). GUI event handlers never execute raw SQL queries.
- **Repository Pattern:** Encapsulates all parameterized SQL queries, schema mapping, and foreign key enforcement.
- **Observer Pattern:** Implemented in `ThemeManager` so that theme toggles dynamically update all active UI frames without requiring an application restart.
- **Factory & Dataclass Models:** Strongly typed entities (`User`, `MenuItem`, `Order`, `OrderItem`, `Bill`) ensure monetary precision and boundary safety.

### 3. Financial Exactness & Poka-Yoke (Mistake-Proofing)
- **No Float Arithmetic:** All currency calculations (subtotal, CGST, SGST, discounts, Grand Total) strictly utilize Python's `Decimal` module with explicit `Decimal("0.01")` half-even quantization.
- **Historical Price Protection:** Order items capture a static snapshot (`item_name`, `unit_price`) at the moment of ordering, preventing future menu catalog price changes from corrupting past financial invoices.
- **Input Error-Proofing:** Quantities are restricted to positive integers, discounts are capped at 50%, and destructive menu deletion requires explicit user confirmation via modal dialog.

### 4. Database Integrity
- SQLite with `PRAGMA foreign_keys = ON;` strictly enforced on every connection.
- Atomic ACID transactions (`db.transaction()`) guarantee that orders and itemized lines are committed together or completely rolled back on error.
- Sensitive data filtering redacts passwords from rotating log files (`logs/app.log`).

### 5. Honest Limitations & Future Scope
- **Single-Node Desktop Scope:** Designed as a local desktop SQLite application. It is not currently a distributed multi-terminal client-server system.
- **Future Enhancements:** Migration to client-server PostgreSQL for multi-counter dining establishments, Kitchen Display System (KDS) integration via WebSockets, and hardware thermal ESC/POS receipt printer support.

---

## 📊 Total Quality Management (TQM) Methodology

This project applies core TQM principles:
- **SIPOC:** Full Order-to-Billing process mapping.
- **CTQ Tree:** Linking customer satisfaction drivers to concrete technical criteria.
- **FMEA:** Risk prioritization with Risk Priority Number ($RPN = S \times O \times D$) reduction across 10 failure modes.
- **Poka-Yoke:** Real-time UI validation, integer quantities, and exact decimal arithmetic.
- **Statistical Quality Control:** Defect checksheet, Pareto analysis ($80/20$ rule), Ishikawa fishbone root cause diagnosis, and 6 iterative PDCA cycles.

For in-depth analysis, refer to [docs/TQM_REPORT.md](docs/TQM_REPORT.md).

