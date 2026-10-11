# Software Requirements Specification (SRS)
## Restaurant Billing System with Total Quality Management (TQM) Integration

- **Document Identifier:** SRS-BBAT104-Q08-2026
- **Subject:** BBAT104 — Fundamentals of Total Quality Management
- **Course Assignment:** Restaurant Billing System
- **Student Name:** Jay Paneru
- **Registration Number:** 2410302024
- **Assigned Quality Goal:** Q08 — Improve User Satisfaction
- **Academic Session:** 2026–27
- **Document Version:** 1.0.0
- **Status:** Approved / Base-lined

---

## 1. Document Control & Version History

| Version | Date | Author | Description of Changes | Status |
|---------|------|--------|------------------------|--------|
| 1.0.0 | 2026-10-11 | Jay Paneru (2410302024) | Initial comprehensive specification covering core billing workflows and Q08 Quality Features | Baselined |

---

## 2. Purpose and Scope

### 2.1 Purpose
This document specifies the software requirements for the Restaurant Billing System developed for course **BBAT104 (Fundamentals of Total Quality Management)**. The project bridges enterprise software engineering with TQM methodologies, specifically focusing on **Quality Goal Q08: Improve User Satisfaction**.

### 2.2 Scope
The application is a standalone desktop management and Point-of-Sale (POS) billing system built using Python 3.12, CustomTkinter, and SQLite3. It encompasses:
1. Secure user authentication and session management.
2. Dynamic menu catalog management with categorization and price controls.
3. Rapid order creation, editing, and real-time computation of item and bill totals.
4. Transaction-safe billing with exact financial calculations (using Python `Decimal` / integer arithmetic), discount and tax management, and receipt reprinting.
5. Implementation of five dedicated Q08 User Satisfaction features:
   - **Interactive Live Dashboard** with real-time sales and order volume KPIs.
   - **Visual Reports** providing Matplotlib analytical charts.
   - **Persistent Theme Toggle** (Dark/Light mode).
   - **Keyboard Shortcuts** for high-efficiency cashier operations.
   - **User Profile Settings** with persistent theme preferences and credential updates.
6. Rigorous TQM documentation including SIPOC, CTQ Tree, FMEA, Defect Checksheet, Pareto Analysis, Fishbone Root Cause Diagram, and PDCA continuous improvement cycles.

---

## 3. Problem Statement & Project Objectives

### 3.1 Problem Statement
Traditional entry-level restaurant billing software often suffers from:
- Cluttered, unintuitive user interfaces that cause cashier fatigue and order entry errors.
- Float-rounding discrepancies in invoice totals and tax calculations.
- Data loss or incomplete state transitions when network or process errors occur.
- Lack of immediate visual feedback on daily sales and popular items for store managers.
- Inflexible themes causing eye strain in varied ambient dining environments.

### 3.2 Project Objectives
1. **Engineering Excellence:** Deliver a modular, maintainable Python application separating UI, business logic, repository persistence, and domain models.
2. **Quality Goal Q08 Fulfillment:** Improve User Satisfaction by reducing checkout friction, providing instant operational feedback, personalizing operator workspace preferences, and ensuring zero billing calculation discrepancies.
3. **Poka-Yoke (Mistake Proofing):** Prevent order entry mistakes through rigorous input validation, explicit quantity thresholds, and database foreign key integrity.
4. **Statistical Quality Control:** Capture defects systematically in checksheets, analyze root causes using Ishikawa diagrams, and direct improvement efforts via Pareto analysis and PDCA cycles.

---

## 4. Stakeholders & User Roles

| Stakeholder / Role | Primary Responsibilities | Key Quality Expectation |
|--------------------|--------------------------|-------------------------|
| **Cashier / Operator** | Take orders, customize quantities, generate final bills, issue printed receipts | Rapid keystroke-friendly workflow, clear error prompts, no lag |
| **Store Manager** | Monitor today's revenue, review best-selling items, adjust menu availability | Accurate real-time dashboard KPIs, readable analytical graphs |
| **System Administrator** | Manage operator accounts, review audit logs, ensure database backups | Role-based data separation, secure password hashing, atomic transactions |
| **Customer (End Consumer)**| Receive transparent, legible, accurate bills without item total errors | Instant, accurate billing and professional printed receipt |
| **Academic Evaluator** | Assess implementation completeness, code architecture, and TQM principles | Adherence to assignment syllabus, git commit discipline, statistical artifacts |

---

## 5. Functional Requirements (FR)

### 5.1 Authentication & Security (AUTH)
- **FR-001:** The system shall authenticate users using username and securely hashed passwords (PBKDF2-HMAC-SHA256 with salt). Passwords must never be stored in plaintext.
- **FR-002:** The system shall maintain an in-memory session tracking the active user's identity, role, and preferences.
- **FR-003:** The system shall allow users to log out safely, clearing active session state and returning to the login screen.
- **FR-004:** The system shall display user-friendly error messages upon invalid credentials without disclosing whether the username or password was incorrect.

### 5.2 Menu Management (MENU)
- **FR-010:** The system shall allow authorized users to create new menu items with name, category, price, and active availability status.
- **FR-011:** The system shall allow editing and deletion of existing menu items.
- **FR-012:** The system shall prevent duplicate menu item names within the same category.
- **FR-013:** The system shall validate that prices are positive decimal values greater than zero.
- **FR-014:** The system shall provide real-time search and category filtering for rapid item lookup.
- **FR-015:** Deleting or altering a menu item price shall never alter the historical price or name recorded on past invoices (Historical Price Protection).

### 5.3 Order Management (ORD)
- **FR-020:** The system shall support creating an order containing multiple distinct menu items with individual quantities.
- **FR-021:** The system shall calculate item line totals in real time (`quantity * unit_price`).
- **FR-022:** The system shall permit adding, incrementing, decrementing, and removing items before final confirmation.
- **FR-023:** The system shall validate that item quantity is a strictly positive integer ($\ge 1$).
- **FR-024:** The system shall track order statuses: `PENDING`, `COMPLETED`, `CANCELLED`.
- **FR-025:** The system shall prevent invalid state transitions (e.g., modifying or re-billing an already `COMPLETED` order).

### 5.4 Billing & Receipts (BILL)
- **FR-030:** The system shall generate a unique bill reference code (e.g., `BILL-YYYYMMDD-XXXX`).
- **FR-031:** The system shall compute Subtotal, Tax (configurable percentage, e.g. 5%), Discount (fixed or percentage), and Final Net Total using exact decimal arithmetic (`Decimal`).
- **FR-032:** The system shall validate discounts such that discount amounts cannot exceed the subtotal.
- **FR-033:** The system shall support payment methods: `CASH`, `CARD`, `UPI`.
- **FR-034:** The system shall persist the completed bill, payment method, line items snapshot, and timestamps within an atomic SQLite transaction.
- **FR-035:** The system shall format and display an itemized printable receipt and support receipt reprinting from order history.

---

## 6. Q08 Quality Features Specifications

### Feature 1: Interactive Dashboard (Q08-F1)
- **FR-040:** The system shall calculate and display key operational metrics computed directly from database queries:
  - Today's Total Sales Revenue ($\text{INR } ₹$).
  - Completed Orders count today.
  - Pending Orders count.
  - Average Order Value (AOV) today.
  - Recent Orders table (last 5 transactions with customer, status, total).
  - Top 5 Popular Menu Items by sales volume.
- **FR-041:** The dashboard metrics shall handle empty databases gracefully without runtime exceptions or divide-by-zero crashes.
- **FR-042:** The dashboard shall provide one-click quick action buttons to navigate directly to New Order, Menu Catalog, or Visual Reports.

### Feature 2: Visual Reports (Q08-F2)
- **FR-050:** The system shall embed interactive Matplotlib charts directly in the GUI:
  - **Chart 1:** Daily Sales Trend (Line/Bar chart showing revenue across dates).
  - **Chart 2:** Best-Selling Menu Items (Horizontal bar chart ranking top items).
  - **Chart 3:** Order Status Breakdown (Pie or donut chart of Completed vs Pending vs Cancelled).
  - **Chart 4:** Payment Method Distribution (Distribution of Cash, Card, UPI).
- **FR-051:** Charts shall adapt dynamically to the active color theme (dark background in dark mode, light background in light mode).
- **FR-052:** When no transaction data exists for a period, the report view shall display a clean "No data available for selected period" placeholder rather than crashing.

### Feature 3: Persistent Theme Toggle (Q08-F3)
- **FR-060:** The system shall allow switching between Light Mode and Dark Mode at any time.
- **FR-061:** Theme changes shall apply dynamically across all views without requiring application restart.
- **FR-062:** The selected theme preference shall be persisted in the user settings table in the database and restored automatically upon subsequent logins.

### Feature 4: Keyboard Shortcuts (Q08-F4)
- **FR-070:** The system shall provide keyboard accelerators for primary navigation:
  - `Alt+N` / `Ctrl+N`: Navigate to New Order creation.
  - `Alt+D` / `Ctrl+D`: Navigate to Interactive Dashboard.
  - `Alt+M` / `Ctrl+M`: Navigate to Menu Management.
  - `Alt+R` / `Ctrl+R`: Navigate to Visual Reports.
  - `Alt+P` / `Ctrl+P`: Navigate to User Profile Settings.
  - `Escape`: Close active modal dialog or clear current selection.
- **FR-071:** Shortcuts shall be visibly annotated on buttons and listed in the User Manual.

### Feature 5: User Profile Settings (Q08-F5)
- **FR-080:** The system shall allow the logged-in user to view their account information (Username, Full Name, Role, Created Date).
- **FR-081:** The system shall allow the user to update their display name and default theme preference.
- **FR-082:** The system shall allow secure password change requiring confirmation of the current password and verification of new password complexity rules.

---

## 7. Non-Functional Requirements (NFR)

- **NFR-001 (Accuracy & Integrity):** All monetary calculations must use fixed-point arithmetic (`Decimal`). Float inaccuracies (e.g., $0.1 + 0.2 = 0.30000000000000004$) are strictly prohibited.
- **NFR-002 (Performance):** UI view transitions and order line item calculations must execute in under 100 milliseconds on standard desktop hardware.
- **NFR-003 (Reliability & Atomicity):** Order completion and billing records must commit in a single database transaction. Partial commits upon error are prohibited.
- **NFR-004 (Usability & Ergonomics):** The interface must maintain minimum 14pt high-contrast typography, clear status indicators, and keyboard-first cashier workflows.
- **NFR-005 (Portability):** The software must execute on Windows 10/11, macOS, and Linux without external database engine servers.
- **NFR-006 (Maintainability):** Code must follow standard PEP 8 conventions, strict layered architecture, and complete docstrings.
- **NFR-007 (Auditability):** All significant events (user login, price edits, order cancellations, database errors) must be logged to a rotating application log file without logging sensitive credentials.

---

## 8. Technology Stack & Constraints

- **Programming Language:** Python 3.12+
- **GUI Framework:** CustomTkinter (built on Tkinter, supporting modern themes and high-DPI scaling)
- **Plotting & Analytics:** Matplotlib (`FigureCanvasTkAgg` embedded directly in CustomTkinter frames)
- **Database Engine:** SQLite3 (standard library, zero-configuration local relational database)
- **Security:** Standard library `hashlib` (PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte random salt)
- **Testing Framework:** pytest (automated unit and integration testing)
- **Version Control:** Git & GitHub (minimum 30 verified commits)
- **Constraint:** Zero reliance on cloud services for core offline point-of-sale billing.

---

## 9. Requirement Traceability Matrix (RTM)

| Req ID | Requirement Summary | Implementation Module | Test Module | Verification Method |
|--------|---------------------|-----------------------|-------------|---------------------|
| FR-001 | Hashed Authentication | `utils/security.py`, `services/auth_service.py` | `tests/test_security.py`, `test_auth_service.py` | Automated unit tests |
| FR-010 | Menu CRUD & Filtering | `repositories/menu_repository.py`, `services/menu_service.py` | `tests/test_menu_service.py` | Automated unit tests |
| FR-015 | Historical Price Integrity | `database/schema.py`, `services/billing_service.py` | `tests/test_billing_service.py` | Integration test |
| FR-020 | Multi-item Order Engine | `services/order_service.py` | `tests/test_order_service.py` | Automated unit tests |
| FR-031 | Decimal Billing Accuracy | `services/billing_service.py` | `tests/test_billing_service.py` | Automated unit tests |
| FR-034 | Transaction-safe Billing | `repositories/order_repository.py`, `database/db.py` | `tests/test_billing_service.py` | Rollback simulation test |
| FR-040 | Interactive Dashboard | `services/dashboard_service.py`, `ui/dashboard.py` | `tests/test_dashboard_service.py` | Automated & UI tests |
| FR-050 | Visual Reports (Matplotlib) | `services/report_service.py`, `ui/reports.py` | `tests/test_report_service.py` | Automated & UI tests |
| FR-060 | Persistent Theme Toggle | `ui/theme_manager.py`, `repositories/settings_repository.py` | `tests/test_theme_manager.py` | Automated unit tests |
| FR-070 | Keyboard Shortcuts | `ui/main_window.py` | `tests/test_shortcuts.py` | Manual & unit tests |
| FR-080 | Profile & Password Change | `services/profile_service.py`, `ui/profile.py` | `tests/test_profile_service.py` | Automated unit tests |
| NFR-001| Financial Exactness | `services/billing_service.py` | `tests/test_billing_service.py` | Money precision tests |
| NFR-007| Secure Logging | `utils/logger.py` | `tests/test_logger.py` | Audit log verification |

---

## 10. TQM Alignment & Kaizen Roadmap
This SRS serves as the baseline contract for quality verification. All functional specifications directly feed into the Critical-to-Quality (CTQ) tree, Failure Mode and Effects Analysis (FMEA), and ongoing Plan-Do-Check-Act (PDCA) quality improvement cycles documented in `docs/TQM_REPORT.md`.
