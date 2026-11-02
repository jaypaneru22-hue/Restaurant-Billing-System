# SOFTWARE REQUIREMENTS SPECIFICATION (SRS)
## Professional Restaurant Management Platform — Enterprise Specification
**Academic Subject:** BBAT104 — Fundamentals of Total Quality Management  
**Student Name:** Jay Paneru | **Registration Number:** 2410302024  
**Quality Goal:** Q08 — Improve User Satisfaction | **Session:** 2026–27  
**Document Identifier:** SRS-ENT-BBAT104-Q08-2026 | **Version:** 2.0.0 (Master Release)

---

## 1. System Overview & Scope

The **Restaurant Management Platform** is a production-grade, role-based desktop enterprise application designed to manage the end-to-end operational lifecycle of modern food and beverage establishments.

The platform provides dedicated, isolated interfaces tailored to five distinct personas:
1. **System Administrator:** Executive governance, staff user accounts, role-based security, billing/tax settings, automated database backup & disaster recovery, audit logging, system diagnostics.
2. **Floor Manager:** Zone-based floor layout and table occupancy monitoring, active orders supervision, 86 dish availability control, staff activity audit, shift monitoring.
3. **Counter Cashier:** Rapid Point-of-Sale order capture, tender change calculation, demo card and UPI simulation, equal and custom split billing with penny-balanced reconciliation, thermal receipt generation, shift drawer closeout.
4. **Executive Chef:** Real-time Kitchen Display System (KDS), cooking duration timers, high-wait visual aging alerts (>15 min), interactive order status progression, instant stockout toggling.
5. **Dining Guest / Customer:** Account self-registration, dining menu exploration, 5-stage live order tracking timeline, customer-isolated order history, 1-5 star quality reviews and Net Promoter Score (NPS) telemetry.

---

## 2. Functional Requirements by Module

### 2.1 Module 1: Authentication & Access Control (RBAC)
- **FR-AUTH-01:** System shall authenticate users against salted PBKDF2 (HMAC-SHA256) password hashes.
- **FR-AUTH-02:** System shall enforce strict role-based access control (RBAC), intercepting unauthorized navigation attempts and redirecting to default authorized screens.
- **FR-AUTH-03:** System shall reject authentication attempts for deactivated user accounts.
- **FR-AUTH-04:** System shall provide dining guest self-registration while validating username uniqueness and minimum password length ($\ge 6$ characters).
- **FR-AUTH-05 (Poka-Yoke):** System shall prevent deleting or deactivating the last active administrator account.

### 2.2 Module 2: Point-of-Sale (POS) & Billing Settlement
- **FR-POS-01:** System shall compute subtotal, configurable Goods and Services Tax (GST, default 5.0%), and authorized promotional discounts (max 50.0%) using exact `Decimal` arithmetic.
- **FR-POS-02 (Poka-Yoke):** System shall prevent accepting cash tender amounts lower than the invoice final total and display calculated change due.
- **FR-POS-03:** System shall provide demo simulated card and UPI payment validation without storing unencrypted PAN or sensitive banking data.
- **FR-POS-04 (Split Billing):** System shall support Equal Party Split (2 to 10 guests) with automated 1-paise discrepancy distribution ensuring exact zero variance.
- **FR-POS-05 (Custom Split):** System shall support custom amount splitting and validate that the sum of allocated shares equals the final total before permitting finalization.
- **FR-POS-06:** System shall generate an itemized thermal receipt with restaurant branding, tax breakdown, payment method, and verification stamp.

### 2.3 Module 3: Floor & Table Management
- **FR-TBL-01:** System shall display a floor plan divided into four operational zones: Main Dining, Patio Garden, Family Section, and Counter / Bar.
- **FR-TBL-02:** System shall support 4 distinct table occupancy states: `VACANT`, `OCCUPIED`, `BILL_REQUESTED`, and `CLEANING`.
- **FR-TBL-03 (Poka-Yoke):** System shall prohibit transitioning a table to `VACANT` if an unresolved active order exists for that table.

### 2.4 Module 4: Kitchen Display System (KDS)
- **FR-KDS-01:** System shall display all active kitchen orders as visual Kitchen Order Ticket (KOT) cards.
- **FR-KDS-02:** System shall maintain live preparation timers per ticket and display a high-wait visual Crimson Alert for orders exceeding 15 minutes.
- **FR-KDS-03:** System shall support one-click status transitions across the cooking lifecycle: `PENDING` $\to$ `ACCEPTED` $\to$ `PREPARING` $\to$ `READY`.
- **FR-KDS-04:** System shall provide instant 86 catalog toggling, disabling out-of-stock items across all ordering terminals in real time.

### 2.5 Module 5: Customer Dining Portal & Feedback (Q08)
- **FR-CUST-01:** System shall provide guests with a 5-stage order progression timeline: Placed $\to$ Accepted $\to$ Preparing $\to$ Ready $\to$ Served.
- **FR-CUST-02:** System shall enforce strict data isolation such that customer queries only return their own order history and receipts.
- **FR-CUST-03:** System shall capture dining feedback including 1-5 Star Food Quality, 1-5 Star Service Speed, 0-10 Net Promoter Score (NPS), and review comments.

### 2.6 Module 6: Shift Closeout & Financial Reconciliation
- **FR-SFT-01:** System shall compute shift summaries including order volume, gross revenue, and collection totals breakdown by payment instrument (Cash, Card, UPI, Split).
- **FR-SFT-02:** System shall calculate cash drawer discrepancy (`Counted Cash - System Expected Cash`) and record variance in persistent audit logs.

### 2.7 Module 7: Administration, Diagnostics & Disaster Recovery
- **FR-ADM-01:** System shall provide verified one-click database snapshot backups stored in `data/backups/`.
- **FR-ADM-02:** System shall inspect SQLite header validity and execute `PRAGMA integrity_check` before applying database restoration.
- **FR-ADM-03:** System shall record an immutable audit trail of all administrative actions, staff credential resets, and tax rate modifications.

---

## 3. Non-Functional Requirements (NFRs)

- **NFR-PERF-01 (Latency):** POS item addition, price lookups, and bill calculation shall complete within 150 milliseconds.
- **NFR-PERF-02 (Concurrency):** Database shall utilize SQLite Write-Ahead Logging (WAL) to enable unblocked concurrent reads during active write transactions.
- **NFR-ERGO-01 (Display):** All interfaces and modal dialogs shall fit within standard 1366×768 laptop resolutions without clipping action buttons.
- **NFR-ERGO-02 (Theming):** Application shall adhere to the Midnight Obsidian design system with high-contrast surfaces (`#111118`), vibrant accents (`#6657F5`), and instant Light/Dark switching.
- **NFR-RELI-01 (Zero Defect):** Codebase shall achieve 100% pass rate on automated regression tests with zero unhandled exceptions.

---
*Authored by Jay Paneru (2410302024) for BBAT104 Total Quality Management.*
