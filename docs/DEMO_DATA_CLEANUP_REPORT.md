# RestoPro — Safe Demo Data Cleanup & Manual Testing Preparation Report

**Project Name:** RestoPro — Restaurant Management Platform  
**Academic Subject:** BBAT104 — Fundamentals of Total Quality Management  
**Quality Goal:** Q08 — Improve User Satisfaction  
**Execution Date:** 2026-11-04  
**Status:** COMPLETE & VERIFIED — READY FOR MANUAL END-TO-END TESTING  

---

## 1. Executive Summary

In preparation for authentic manual end-to-end testing across all six user roles (**Admin, Manager, Cashier, Chef, Waiter, and Customer**), the operational SQLite database (`data/restaurant.db`) was audited and safely purged of all confirmed demo, dummy, sample, and test transactional records.

All legitimate application configurations, user accounts, master menu catalog items, table floor layouts, tax parameters, and enterprise profiles have been strictly preserved. Automatic demo data generation on application startup and restart has been permanently disabled. All dashboards, telemetry cards, and analytical reports now dynamically calculate metrics from real operational records and display genuine zero states without division errors or synthetic numbers.

---

## 2. Pre-Cleanup Database Backup & Verification

Prior to executing any cleanup script or modifying records, a verified online SQLite backup was created and validated:

- **Backup File Location:** `data/backups/restaurant_pre_cleanup_20261104_075323.bak`
- **Secondary Pre-Verification Snapshot:** `data/backups/restaurant_pre_cleanup_20261104_080815.bak`
- **Backup Size:** 160.0 KB (163,840 bytes)
- **SQLite Integrity Check:** `ok`
- **Foreign Key Constraints:** Enabled and verified (`PRAGMA foreign_key_check` returned 0 violations)
- **Tables Backed Up:** 14 tables, 487 total records preserved in archive.

---

## 3. Database Inventory: Master vs. Purged Data

| Table Name | Pre-Cleanup Rows | Demo Records Purged | Legitimate Records Preserved | Status / Remarks |
| :--- | :---: | :---: | :---: | :--- |
| `users` | 6 | 0 | 6 | **Preserved:** All 6 role accounts (`admin`, `manager1`, `cashier1`, `chef1`, `waiter1`, `customer1`). |
| `menu_items` | 27 | 0 | 27 | **Preserved:** Full master catalog across 6 categories (Starters, Mains, Breads, Rice, Desserts, Beverages). |
| `restaurant_tables` | 10 | 0 | 10 | **Preserved:** All 10 dining tables (`T-1` to `T-4`, `P-1`, `P-2`, `F-1`, `F-2`, `C-1`, `C-2`). Reset status to `VACANT`, `active_order_id = NULL`. |
| `restaurant_profile` | 1 | 0 | 1 | **Preserved:** RestoPro Gourmet Dining profile (GSTIN, FSSAI, Address, Contact). |
| `billing_config` | 1 | 0 | 1 | **Preserved:** 5% CGST, 5% SGST, zero service charge, invoice prefix `INV-`. |
| `orders` | 115 | 115 | 0 | **Purged:** All historical sample/test customer & counter orders. |
| `order_items` | 174 | 174 | 0 | **Purged:** All line items linked to demo orders. |
| `bills` | 45 | 45 | 0 | **Purged:** All demo settlements, payment allocations, and generated receipts. |
| `customer_feedback` | 6 | 6 | 0 | **Purged:** Synthetic reviews seeded during older schema runs. |
| `service_requests` | 6 | 6 | 0 | **Purged:** Sample waiter assistance call requests. |
| `audit_logs` | 89 | 50 | 39 | **Cleaned:** Purged transactional logs referencing deleted demo orders/bills; preserved system configuration, user creation, and authentication logs. |
| `sqlite_sequence` | - | Reset | - | Auto-increment sequence counters for `orders`, `order_items`, `bills`, `customer_feedback`, and `service_requests` reset to 0. |

---

## 4. Disabling Automatic Demo Data Generation

Code modifications were made across the codebase to ensure no script, migration, or startup routine automatically seeds mock transactions:

1. **Application Entrypoint (`main.py`):**
   - Changed default startup flag from `--no-demo-seed` (which previously seeded sample orders whenever the database was empty) to `--seed-demo` (default `False`).
   - Clean startup runs `python main.py` directly without creating any dummy orders, bills, or feedback.
2. **Database Migrations (`database/migrations.py`):**
   - Removed automatic insertion of mock customer feedback rows (`seed_customer_feedback` routine deprecated).
3. **Audit Log UI (`ui/audit.py`):**
   - Removed `_seed_recent_audit_if_empty()` which previously injected fake `BILL_SETTLED` events into empty audit logs.
4. **Customer Feedback UI (`ui/feedback.py`):**
   - Updated KPI calculation logic to handle empty tables gracefully (`No reviews yet`, `0% (No data)` instead of synthetic fallback scores).
5. **Chef KDS Frame (`ui/chef_kds.py`):**
   - Parameterized `order_repo` and bound database queries to the active repository manager (`self.order_repo.db`), eliminating hardcoded global references and guaranteeing isolation during tests.
6. **Test Isolation (`tests/test_customer_checkout_flow.py` & `tests/test_chef_kds_refresh.py`):**
   - Refactored test suites to operate strictly on isolated SQLite databases generated via `tmp_path` fixtures, guaranteeing test runs never leak transactional records into `data/restaurant.db`.

---

## 5. Verification of All Six User Roles

All 6 authenticated roles were verified using `scripts/verify_roles_and_dashboards.py`. Password authentication, session tracking, and role-based permissions were confirmed intact:

| Role | Username | Full Name / Title | Password | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | `admin` | Jay Paneru (Administrator) | `Admin@123` | **VERIFIED:** Access to User Management, Enterprise Settings, Backup/Restore, System Logs. |
| **Manager** | `manager1` | Operations Floor Manager | `Manager@123` | **VERIFIED:** Access to Live Floor Management, Active Orders, Waiter Assignments, Reports. |
| **Cashier** | `cashier1` | Senior Billing Cashier | `Cashier@123` | **VERIFIED:** Access to POS Counter Billing, Order Settlement, Invoice Generation. |
| **Chef** | `chef1` | Vikram (Executive Head Chef) | `Chef@123` | **VERIFIED:** Access to Kitchen Display System (KDS), Ticket Progression (PENDING → READY). |
| **Waiter** | `waiter1` | Rahul Sharma (Floor Server) | `Waiter@123` | **VERIFIED:** Access to Waiter Floor Portal (Assigned Tables, Ready Pickups, Served History). |
| **Customer** | `customer1` | Jay | `Customer@123` | **VERIFIED:** Access to Customer Food Menu, Live Cart, Dine-in Checkout, Order Status Tracking. |

---

## 6. Zero-State Dashboard & Analytical Metrics Verification

Verified via `scripts/verify_empty_dashboard_metrics.py`:

- **Admin Dashboard:**
  - Active Users: `6` | Total Staff: `6`
  - Total Orders: `0` | Total Sales / Revenue: `₹0.00` | Average Order Value: `₹0.00`
  - Active Menu Items: `27` | Table Count: `10`
  - Status: `ONLINE • HEALTHY`
- **Manager Dashboard:**
  - Floor Revenue Today: `₹0.00` | Total Orders Today: `0` | Active In-Service: `0`
- **Cashier POS:**
  - Shift Sales: `₹0.00` | Shift Invoices: `0` | Active Pending Invoices: `0`
- **Chef KDS:**
  - Total Tickets: `0` | Incoming / New: `0` | Preparing: `0` | Ready: `0`
- **Waiter Floor Portal:**
  - Orders Waiting for Pickup: `0` | Orders In Service: `0` | Served Today: `0` | Customer Requests: `0`
- **Report & Analytics Service:**
  - Daily Sales Trend: Empty zero baseline rendered without crash.
  - Top Selling Items: Clean informational message (`No sales recorded yet`).
  - Order Status Distribution: Clean informational message (`No orders available`).
  - Payment Method Breakdown: Clean informational message (`No completed payments yet`).

---

## 7. Application Startup & Restart Verification

The application startup was tested with `python main.py --headless-check`:
1. Application initializes database connection cleanly.
2. Runs schema migration check (schema version up to date).
3. Verifies default users and master catalog exist without creating duplicate rows.
4. Skips demo seeding.
5. Database row counts immediately after startup and exit:
   - `orders`: `0`
   - `order_items`: `0`
   - `bills`: `0`
   - `customer_feedback`: `0`
   - `service_requests`: `0`

---

## 8. Manual Testing Readiness Checklist

The application is completely prepared for the user to execute manual end-to-end testing:

- [x] **Step 1:** Customer orders meal through Customer Portal (`customer1` / `Customer@123`) or Cashier creates counter ticket (`cashier1` / `Cashier@123`).
- [x] **Step 2:** Chef views live order ticket on Kitchen Display System (`chef1` / `Chef@123`), moves ticket from `PENDING` → `ACCEPTED` → `PREPARING` → `READY`.
- [x] **Step 3:** Waiter views ready order on Waiter Dashboard (`waiter1` / `Waiter@123`), collects order (`PICKED_UP`) and delivers to table (`SERVED`).
- [x] **Step 4:** Cashier generates invoice and settles bill (`cashier1` / `Cashier@123`) via Cash, Demo Card, or Demo UPI.
- [x] **Step 5:** Customer submits genuine feedback and rating.
- [x] **Step 6:** Manager and Admin observe live telemetry, revenue updates, and audit trail reflections across their dashboards.
