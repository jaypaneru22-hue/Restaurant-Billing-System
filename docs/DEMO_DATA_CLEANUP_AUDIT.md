# RESTOPRO — DEMO DATA CLEANUP & AUDIT REPORT

**Project:** RestoPro — Enterprise Restaurant Management Platform  
**Academic Subject:** BBAT104 — Fundamentals of Total Quality Management  
**Date of Audit:** November 4, 2026  
**Auditor:** Quality Engineering & Database Administration  
**Operational Database Path:** `data/restaurant.db` (Absolute: `C:\Users\jaypa\Documents\TQM\data\restaurant.db`)

---

## 1. Executive Summary

This document presents the complete pre-cleanup audit of the SQLite operational database for the RestoPro Restaurant Management Platform.

The objective is to prepare the platform for authentic, end-to-end manual testing across all six user roles:
1. **Admin** (`admin`)
2. **Manager** (`manager1`)
3. **Cashier** (`cashier1`)
4. **Chef** (`chef1`)
5. **Waiter** (`waiter1`)
6. **Customer** (`customer1`)

To achieve true zero-state testing, all automatically seeded sample transactions, demo feedback, temporary service requests, and test orders must be safely removed without impacting master catalog data, restaurant profile, staff credentials, tax/billing configurations, or table definitions.

---

## 2. Database Inspection Summary

The database was inspected using `sqlite3` PRAGMA and table scan utilities. A total of **14 tables** were identified:

| Table Name | Total Records | Classification | Proposed Action |
| :--- | :---: | :--- | :--- |
| `users` | 6 | **Legitimate Master Data** | **PRESERVE** (All 6 active staff & customer accounts) |
| `user_settings` | 7 | **Legitimate Master Data** | **PRESERVE** (Theme, currency, tax rates) |
| `menu_items` | 27 | **Legitimate Master Data** | **PRESERVE** (Full menu catalog & pricing) |
| `restaurant_tables` | 10 | **Legitimate Master Data** | **PRESERVE** (10 physical tables with capacities & zones) |
| `restaurant_profile` | 1 | **Legitimate Master Data** | **PRESERVE** (GSTIN, FSSAI, address, headers) |
| `billing_config` | 1 | **Legitimate Master Data** | **PRESERVE** (CGST/SGST 2.5%, discount policy) |
| `roles_permissions` | 0 | **Legitimate Configuration** | **PRESERVE** (Role-based permission table schema) |
| `orders` | 115 | **Demo / Test Data** | **SAFE DELETE** (Foreign key root for transactions) |
| `order_items` | 174 | **Demo / Test Data** | **SAFE DELETE** (Line items of demo orders) |
| `bills` | 45 | **Demo / Test Data** | **SAFE DELETE** (Finalized test bills & payments) |
| `customer_feedback` | 6 | **Demo / Test Data** | **SAFE DELETE** (Sample mock feedback) |
| `service_requests` | 6 | **Demo / Test Data** | **SAFE DELETE** (Sample floor requests) |
| `audit_logs` | 79 | **Mixed / Demo Data** | **SAFE PURGE** (Reset transaction audit events; retain clean baseline) |
| `sqlite_sequence` | 10 | **SQLite System Internal** | **RESET** (Autoincrement reset for cleaned tables) |

---

## 3. Detailed Entity Analysis

### A. Legitimate Application Configuration (STRICTLY PRESERVED)

1. **Staff & Customer Accounts (`users`)**:
   - `admin` (ID 1): Administrator (Jay Paneru), Role: `ADMIN`, Active: Yes
   - `cashier1` (ID 2): Senior Billing Cashier, Role: `CASHIER`, Active: Yes
   - `manager1` (ID 5): Operations Floor Manager, Role: `MANAGER`, Active: Yes
   - `chef1` (ID 10): Executive Head Chef (Vikram), Role: `CHEF`, Active: Yes
   - `customer1` (ID 11): Guest Diner (Jay), Role: `CUSTOMER`, Active: Yes
   - `waiter1` (ID 14): Floor Server (Rahul Sharma), Role: `WAITER`, Active: Yes
   *Validation:* All 6 roles have valid BCrypt/SHA-256 hashed credentials. No accounts will be removed or altered.

2. **Menu Catalog (`menu_items`)**:
   - 27 dishes across 6 categories: *Beverages*, *Starters*, *Main Course*, *Breads*, *Desserts*, *Rice & Biryani*.
   - Genuine prices ranging from ₹30 (Masala Chai) to ₹320 (Butter Chicken / Mutton Biryani).
   *Validation:* Master catalog required for all POS, Chef KDS, and Customer ordering workflows. Must remain intact.

3. **Seating Layout (`restaurant_tables`)**:
   - 10 tables: `T-1`, `T-2`, `T-3`, `T-4` (Main Dining), `P-1`, `P-2` (Patio Garden), `F-1`, `F-2` (Family Section), `C-1`, `C-2` (Counter / Bar).
   - All currently in `VACANT` status with `active_order_id = NULL`.
   *Validation:* Essential for Customer table booking, Manager floor management, and Waiter floor service.

4. **Restaurant Profile & Tax Configuration (`restaurant_profile`, `billing_config`)**:
   - Restaurant Name: *TQM Multi-Cuisine Restaurant*
   - GSTIN: `07AAAAA0000A1Z5`, FSSAI: `10019011000123`
   - CGST: 2.5%, SGST: 2.5% (Total GST: 5.0%), Service Charge: 0.0%
   *Validation:* Required for Cashier tax computation and receipt printing.

---

### B. Confirmed Demo & Test Business Records (SCHEDULED FOR REMOVAL)

1. **`orders` (115 records)**:
   - Contains orders created during development, automated tests, and previous demonstration runs (`ORD-20261022-0001` to `ORD-20261104-0001`).
   - Customers: "Rahul Verma", "Pooja Nair", "Amitabh Sen", "Sneha Kulkarni", "Test Diner", "Integration Test Guest", etc.
   - Statuses: 45 `COMPLETED`, 53 `PENDING`, 8 `CANCELLED`, 4 `PICKED_UP`, 3 `READY`, 2 `SERVED`.
   *Action:* Complete deletion.

2. **`order_items` (174 records)**:
   - Line items belonging to the 115 demo orders.
   *Action:* Complete deletion prior to deleting `orders` to satisfy foreign-key constraints.

3. **`bills` (45 records)**:
   - Billing records tied to completed demo orders with payment methods `CASH`, `CARD`, `UPI`.
   *Action:* Complete deletion prior to deleting `orders`.

4. **`customer_feedback` (6 records)**:
   - 5 seeded mock feedbacks ("Outstanding butter chicken...", "Paneer tikka was exceptionally fresh...", etc.) plus 1 test review.
   *Action:* Complete deletion.

5. **`service_requests` (6 records)**:
   - 6 test service requests ("Water", "Extra Cutlery", "Napkins") created during waiter feature integration.
   *Action:* Complete deletion.

6. **`audit_logs` (79 records)**:
   - Contains operational logs for demo orders (`BILL_SETTLED`, `ORDER_PLACED`, `ORDER_PICKED_UP`, `REQUEST_ACCEPTED`).
   *Action:* Purge transaction-specific audit events to provide a clean baseline for manual testing.

---

### C. Records That Cannot Be Confidently Classified

- **None.** Every record in the database has been definitively identified as either core master/configuration data or demo/test operational transactions.

---

## 4. Automatic Demo-Data Generators Identified

A thorough scan of the codebase revealed three locations that automatically generate demo data upon startup:

1. **`main.py` (`seed_demo_transactions()`)**:
   - Line 27: Function `seed_demo_transactions()` checks if `orders` table is empty (`SELECT COUNT(*) FROM orders;`). If count is 0, it automatically creates 10 orders and finalized bills.
   - Line 146: `if not args.no_demo_seed:` automatically invokes this on standard `python main.py` execution!
   - *Fix:* Remove automatic invocation from `main.py`. Startup must remain clean by default.

2. **`database/migrations.py` (`customer_feedback` auto-seed)**:
   - Lines 309–323: If `customer_feedback` count is 0, automatically inserts 5 sample reviews.
   - *Fix:* Disable automatic insertion of sample feedback during migration/init.

3. **`ui/audit.py` (`_seed_recent_audit_if_empty()`)**:
   - Line 35: Injects mock `BILL_SETTLED` entries into `audit_logs` if empty.
   - *Fix:* Remove automatic insertion of mock billing audit logs.

---

## 5. Execution Plan

1. **Create Timestamped Database Backup**:
   - Copy `data/restaurant.db` to `data/backups/restaurant_pre_cleanup_YYYYMMDD_HHMMSS.bak`.
   - Verify backup integrity using SQLite test connection and table count.
2. **Execute Transactional Deletion**:
   - Use atomic SQLite transaction with foreign keys enabled.
   - Delete dependent child records first (`bills`, `order_items`, `service_requests`, `customer_feedback`), then parent records (`orders`).
   - Clear transaction logs from `audit_logs`.
   - Reset `sqlite_sequence` counters for transaction tables.
3. **Disable Automatic Seed Routines**:
   - Update `main.py` so that `seed_demo_transactions()` requires an explicit CLI flag (`--seed-demo`) and does NOT run by default.
   - Remove automatic feedback seeding from `database/migrations.py`.
   - Remove mock billing seeding from `ui/audit.py`.
4. **Post-Cleanup Verification**:
   - Verify 0 orders, 0 bills, 0 order_items, 0 customer_feedback, 0 service_requests.
   - Verify 6 users, 27 menu items, 10 tables, 1 restaurant profile, 1 billing config preserved.
   - Verify application starts cleanly with 100% genuine zero-data dashboards (₹0 revenue, 0 orders, no division-by-zero errors).
