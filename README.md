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
├── quality/                    # TQM artifacts, checksheets, Pareto & Fishbone scripts
│   ├── defects.csv
│   ├── checksheet.csv
│   ├── fmea.csv
│   ├── pdca_log.csv
│   └── generate_charts.py
│
├── tests/                      # Automated pytest unit & integration test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_database.py
│   ├── test_security.py
│   ├── test_validators.py
│   ├── test_auth_service.py
│   ├── test_menu_service.py
│   ├── test_order_service.py
│   ├── test_billing_service.py
│   ├── test_dashboard_service.py
│   ├── test_report_service.py
│   ├── test_profile_service.py
│   └── test_theme_manager.py
│
└── docs/                       # Comprehensive technical and TQM documentation
    ├── SRS.md                  # Software Requirements Specification
    ├── ARCHITECTURE.md         # Component diagrams & data flows
    ├── DATABASE_DESIGN.md      # Relational schema & constraints
    ├── TEST_PLAN.md            # Test strategies & test matrices
    ├── TEST_RESULTS.md         # Automated test logs & pass rates
    ├── TQM_REPORT.md           # SIPOC, CTQ, FMEA, Pareto, Fishbone & PDCA
    ├── USER_MANUAL.md          # Step-by-step cashier & manager guide
    ├── INSTALLATION.md         # Environment setup instructions
    ├── GITHUB_WORKFLOW.md      # Branching & commit policy
    └── COMMIT_TRACKER.md       # Verifiable commit history log
```

---

## 🚀 Installation & Quick Start

### 1. Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Git

### 2. Setup Virtual Environment
```bash
# Clone the repository (if not already local)
git clone https://github.com/jaypaneru22-hue/Restaurant-Billing-System.git
cd Restaurant-Billing-System

# Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On Linux / macOS:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python main.py
```

### 5. Default Demonstration Credentials
- **Username:** `admin`
- **Password:** `Admin@123`
*(A seeded cashier account `cashier1` / `Cashier@123` is also provided for role testing).*

---

## 🧪 Running Automated Tests

A dedicated isolated test database is utilized during automated testing to safeguard application data:

```bash
# Run the entire test suite
pytest -v

# Run with coverage summary
pytest -v --durations=10
```

---

## 📊 Total Quality Management (TQM) Methodology

This project applies core TQM principles:
- **SIPOC:** Full Order-to-Billing process mapping.
- **CTQ Tree:** Linking customer satisfaction drivers to concrete technical criteria.
- **FMEA:** Risk prioritization with Risk Priority Number ($RPN = S \times O \times D$) reduction.
- **Poka-Yoke:** Real-time UI validation, integer quantities, and exact decimal arithmetic.
- **Statistical Quality Control:** Defect checksheet, Pareto analysis ($80/20$ rule), Ishikawa fishbone root cause diagnosis, and iterative PDCA cycles.

For in-depth analysis, refer to [docs/TQM_REPORT.md](docs/TQM_REPORT.md).
