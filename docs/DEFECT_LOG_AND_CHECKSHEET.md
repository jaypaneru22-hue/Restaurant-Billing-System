# DEFECT LOG & QUALITY CHECKSHEET
## Total Quality Management (TQM) — Quality Assurance & Statistical Process Control
**Academic Course:** BBAT104 — Fundamentals of Total Quality Management  
**Student Name:** Jay Paneru | **Registration Number:** 2410302024  
**Quality Goal:** Q08 — Improve User Satisfaction | **Release:** Enterprise Master v1.0.0

---

## 1. Quality Checksheet Methodology

The **Defect Checksheet** is an essential tool in Total Quality Management (TQM) for real-time tracking, categorization, and root-cause classification of anomalies observed during software integration, user testing, and operational stress runs.

### Classification Categories:
- **Category A (Financial & Mathematical):** Price calculation, tax rates, rounding, tender change, split shares.
- **Category B (Security & Access Control):** Unauthorized view navigation, authentication bypass, data leakage.
- **Category C (Workflow & Poka-Yoke):** Premature submission, invalid quantity, out-of-stock ordering.
- **Category D (UI/UX & Ergonomics):** Off-screen buttons, color contrast failures, theme mismatch, shortcut traps.
- **Category E (Data Persistence & Schema):** SQLite locking, missing columns, foreign key violations.

---

## 2. Master Defect Log

| Defect ID | Date Logged | Category | Severity | Description of Observed Anomaly | Root Cause Analysis | Corrective & Preventive Action (CAPA) | Test Verification | Status |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- | :--- | :---: |
| **DEF-01** | 2026-11-01 | Cat A | High | `UnicodeEncodeError: 'charmap'` when outputting ₹ on Windows console | Windows cp1252 default shell encoding cannot encode UTF-8 currency symbol | Wrapped console outputs with fallback `Rs.` / enforced UTF-8 stdout handlers | `tests/test_billing.py` | **RESOLVED** |
| **DEF-02** | 2026-11-01 | Cat D | Critical | Bottom action buttons (Confirm Payment, Settle Bill) pushed off screen at 1366×768 | Parent container packed top down; dynamic content overflowed fixed dialog height | Inverted layout packing: bottom action bar packed with `side="bottom"` before middle scroll | `tests/test_theme_and_styling.py` | **RESOLVED** |
| **DEF-03** | 2026-11-02 | Cat B | Critical | Cashier user able to type navigation routes directly and access admin management views | View router relied solely on sidebar button hiding without service-level checks | Implemented server-side RBAC guard in `MainWindow.navigate_to()` and user repository | `tests/test_rbac.py` | **RESOLVED** |
| **DEF-04** | 2026-11-02 | Cat A | Medium | Three-way split of ₹100 resulted in ₹33.33 × 3 = ₹99.99, losing 1 paisa | Standard floating-point floor division truncated remainder | Developed penny-reconciliation algorithm distributing remainders to initial guest shares | `tests/test_split_billing.py` | **RESOLVED** |
| **DEF-05** | 2026-11-02 | Cat C | High | Waiter able to clear table to VACANT while dining guests still had active unpaid order | Table status update had no awareness of foreign key reference in `orders` table | Added Poka-Yoke check: table vacation blocked if unresolved active order exists in DB | `tests/test_table_management.py` | **RESOLVED** |
| **DEF-06** | 2026-11-02 | Cat E | High | `OperationalError: no such column: total_amount` in legacy shift summary queries | Legacy code referenced deprecated `total_amount` instead of schema-exact `final_total` | Refactored SQL statements across `ShiftMonitoringFrame` and `ShiftSummaryFrame` | `tests/test_shift_summary.py` | **RESOLVED** |
| **DEF-07** | 2026-11-02 | Cat E | Medium | Deleting last administrator account locked system out of administrative control | User deletion had no remaining administrator count check | Added Poka-Yoke check in `UserRepository.delete()` preventing deletion of last active admin | `tests/test_users.py` | **RESOLVED** |
| **DEF-08** | 2026-11-02 | Cat D | Low | Typing letter 'd' or 'm' in customer search triggered global navigation shortcuts | Root window keyboard bindings intercepted keypresses while entries held focus | Added `_can_trigger_shortcut()` guard checking if focused widget is `Entry` or `Text` | `tests/test_theme_and_styling.py` | **RESOLVED** |
| **DEF-09** | 2026-11-02 | Cat C | High | Customer dining order permitted selecting out-of-stock items | Order placement checked menu table without filtering `is_available = 1` | Added SQL condition `AND is_available = 1` and UI grayed-out badge on dining cards | `tests/test_menu.py` | **RESOLVED** |
| **DEF-10** | 2026-11-02 | Cat B | High | Customer able to view all orders in database including other dining guests' checks | Order history query lacked `WHERE user_id = current_user.id` scoping filter | Implemented strict customer tenant data isolation at service query layer | `tests/test_customer_portal.py` | **RESOLVED** |

---

## 3. Defect Frequency & Distribution Checksheet

```
+------------------------------------+--------------------------+---------+------------+
| Defect Category                    | Tally (Checksheet Marks) | Total   | Percentage |
+------------------------------------+--------------------------+---------+------------+
| Cat A: Financial & Mathematical    | ||                       | 2       | 20%        |
| Cat B: Security & Access Control   | ||                       | 2       | 20%        |
| Cat C: Workflow & Poka-Yoke        | ||                       | 2       | 20%        |
| Cat D: UI/UX & Ergonomics          | ||                       | 2       | 20%        |
| Cat E: Data Persistence & Schema   | ||                       | 2       | 20%        |
+------------------------------------+--------------------------+---------+------------+
| TOTAL DEFECTS LOGGED & RESOLVED    |                          | 10      | 100%       |
+------------------------------------+--------------------------+---------+------------+
```

### Cumulative Quality Metric:
- **Total Defects Identified:** 10
- **Total Defects Successfully Rectified:** 10 (100% resolution rate)
- **Open Defects:** 0
- **Automated Regression Suite Coverage:** 127/127 tests passing.

---
*Authored by Jay Paneru (2410302024) for BBAT104 Total Quality Management.*
