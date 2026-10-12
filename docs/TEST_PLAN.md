# Test Plan Specification

- **Project:** Restaurant Billing System
- **Subject:** BBAT104 — Fundamentals of Total Quality Management
- **Student Name:** Jay Paneru
- **Registration Number:** 2410302024
- **Assigned Quality Goal:** Q08 — Improve User Satisfaction
- **Test Framework:** pytest 9.1+ with Python 3.12+
- **Document Version:** 1.0.0
- **Status:** Baselined & Verified

---

## 1. Testing Strategy & Objectives

The primary objective of testing in this project is to provide statistical and empirical proof that **Total Quality Management Goal Q08 (Improve User Satisfaction)** and all core Point-of-Sale billing requirements are completely fulfilled.

### Core Testing Pillars:
1. **Zero Data Discrepancy:** Verify that all financial calculations use exact Decimal arithmetic with zero rounding error.
2. **Poka-Yoke Mistake-Proofing:** Verify that invalid prices, zero/negative quantities, and invalid states are rejected gracefully before database storage.
3. **Database Isolation:** All automated tests execute against an isolated temporary SQLite database fixture (`tmp_path / "test.db"`). The user's production application database is never touched or polluted during automated test runs.
4. **Idempotence & State Consistency:** Verify schema creation, seed population, and state transitions are consistent across restarts.

---

## 2. Test Scope & Test Module Matrix

| Test Module | Target System Area | Key Scenarios Covered |
|-------------|-------------------|----------------------|
| `tests/test_database.py` | Schema & Migrations | Table existence, idempotent migrations, seed data population |
| `tests/test_database_manager.py` | Connection & Transactions | Foreign key enforcement, atomic transaction rollback on exception |
| `tests/test_security.py` | Security & Cryptography | PBKDF2-HMAC-SHA256 hashing, constant-time compare, password rules |
| `tests/test_validators.py` | Poka-Yoke Validation | Username, price decimals, integer quantities, discounts, tax rates |
| `tests/test_auth_service.py` | Authentication & RBAC | Admin/cashier login, wrong passwords, logout, session clearance |
| `tests/test_menu_service.py` | Menu Management | CRUD operations, duplicate category check, invalid prices, search |
| `tests/test_order_service.py` | Order Lifecycle | Multi-item cart, quantity checks, availability, state transitions |
| `tests/test_billing_service.py` | Financial Billing | Exact Decimal precision, discount, tax, receipt text, price snapshots |
| `tests/test_dashboard_service.py` | Interactive Dashboard | Zero-division guard on empty database, live KPI queries, top dishes |
| `tests/test_report_service.py` | Visual Analytics | Matplotlib figure rendering for dark and light modes, distributions |
| `tests/test_profile_service.py` | Profile & Preferences | Account data retrieval, name update, password update, tax/theme save |
| `tests/test_theme_manager.py` | Theme Persistence | Dark/light toggle, subscriber callbacks, database persistence |
| `tests/test_logger.py` | Logging & Audit | Sanitized log output, credential redaction |

---

## 3. Test Execution Criteria

- **Pass Criteria:** 100% of automated unit and integration tests must execute with zero failures and zero unhandled exceptions.
- **Regression Policy:** Any defect discovered during QA must have a reproducible test case added to the suite before marking the defect as RESOLVED in `quality/defects.csv`.
- **Environment:** Run tests via `pytest -v` or `pytest -v --durations=10`.
