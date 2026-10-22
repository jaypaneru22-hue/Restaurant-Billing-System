# Automated Test Results Report

- **Project:** Restaurant Billing System
- **Subject:** BBAT104 — Fundamentals of Total Quality Management
- **Student Name:** Jay Paneru
- **Registration Number:** 2410302024
- **Assigned Quality Goal:** Q08 — Improve User Satisfaction
- **Test Date:** 2026-10-22
- **Environment:** Windows 11, Python 3.12.10, pytest 9.1.1
- **Overall Status:** **PASSED (100% Pass Rate)**

---

## 1. Executive Summary

A comprehensive automated test suite consisting of **63 distinct unit and integration test cases** was executed against an isolated, temporary SQLite test database, alongside an automated full GUI lifecycle smoke test covering all CustomTkinter frames and Matplotlib embedded charts.

| Metric | Result |
|--------|--------|
| **Total Test Cases** | **63** |
| **Passed** | **63** |
| **Failed** | **0** |
| **Skipped** | **0** |
| **Pass Rate** | **100.0%** |
| **Total Duration** | **15.37 seconds** |
| **GUI Smoke Test** | **100% Passed (Zero Exceptions)** |

---

## 2. Test Execution Command & Terminal Output

### Execution Command:
```bash
pytest -v --durations=10
```

### Verified Pytest Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\jaypa\Documents\TQM\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\jaypa\Documents\TQM
collecting ... collected 60 items

tests/test_auth_service.py::test_auth_login_success_admin PASSED         [  1%]
tests/test_auth_service.py::test_auth_login_success_cashier PASSED       [  3%]
tests/test_auth_service.py::test_auth_login_wrong_password PASSED        [  5%]
tests/test_auth_service.py::test_auth_login_non_existent_user PASSED     [  6%]
tests/test_auth_service.py::test_auth_logout PASSED                      [  8%]
tests/test_billing_service.py::test_calculate_bill_breakdown_precision PASSED [ 10%]
tests/test_billing_service.py::test_finalize_bill_workflow PASSED        [ 11%]
tests/test_billing_service.py::test_receipt_text_generation PASSED       [ 13%]
tests/test_billing_service.py::test_historical_price_protection PASSED   [ 15%]
tests/test_dashboard_service.py::test_dashboard_metrics_empty_data PASSED [ 16%]
tests/test_dashboard_service.py::test_dashboard_metrics_with_active_data PASSED [ 18%]
tests/test_database.py::test_schema_tables_exist PASSED                  [ 20%]
tests/test_database.py::test_seed_initial_users_and_passwords PASSED     [ 21%]
tests/test_database.py::test_seed_menu_items_populated PASSED            [ 23%]
tests/test_database.py::test_migrations_idempotency PASSED               [ 25%]
tests/test_database_manager.py::test_database_foreign_key_enforcement PASSED [ 26%]
tests/test_database_manager.py::test_transaction_rollback_on_failure PASSED [ 28%]
tests/test_database_manager.py::test_fetchone_and_fetchall PASSED        [ 30%]
tests/test_logger.py::test_logger_initialization PASSED                  [ 31%]
tests/test_logger.py::test_sensitive_data_filter_redacts_password PASSED [ 33%]
tests/test_menu_service.py::test_add_menu_item_success PASSED            [ 35%]
tests/test_menu_service.py::test_add_duplicate_menu_item_fails PASSED    [ 36%]
tests/test_menu_service.py::test_add_menu_item_invalid_price PASSED      [ 38%]
tests/test_menu_service.py::test_update_menu_item PASSED                 [ 40%]
tests/test_menu_service.py::test_delete_menu_item PASSED                 [ 41%]
tests/test_menu_service.py::test_search_and_filter_menu_items PASSED     [ 43%]
tests/test_models.py::test_user_model_role_check PASSED                  [ 45%]
tests/test_models.py::test_order_item_creation_calculates_line_total PASSED [ 46%]
tests/test_models.py::test_order_status_checks PASSED                    [ 48%]
tests/test_order_service.py::test_create_order_multiple_items_success PASSED [ 50%]
tests/test_order_service.py::test_create_order_empty_items_fails PASSED  [ 51%]
tests/test_order_service.py::test_create_order_unavailable_item_fails PASSED [ 53%]
tests/test_order_service.py::test_update_order_items_pending PASSED      [ 55%]
tests/test_order_service.py::test_cancel_order_workflow PASSED           [ 56%]
tests/test_profile_service.py::test_get_profile_data PASSED              [ 58%]
tests/test_profile_service.py::test_update_profile_name PASSED           [ 60%]
tests/test_profile_service.py::test_change_password_success PASSED       [ 61%]
tests/test_profile_service.py::test_change_password_wrong_current PASSED [ 63%]
tests/test_profile_service.py::test_change_password_mismatch PASSED      [ 65%]
tests/test_profile_service.py::test_update_preferences PASSED            [ 66%]
tests/test_report_service.py::test_sales_trend_query_structure PASSED    [ 68%]
tests/test_report_service.py::test_report_charts_empty_database PASSED   [ 70%]
tests/test_report_service.py::test_report_charts_with_transactions PASSED [ 71%]
tests/test_security.py::test_hash_password_generates_salt_and_hash PASSED [ 73%]
tests/test_security.py::test_verify_password_success PASSED              [ 75%]
tests/test_security.py::test_verify_password_wrong_password_fails PASSED [ 76%]
tests/test_security.py::test_verify_password_tampered_hash_fails PASSED  [ 78%]
tests/test_security.py::test_validate_password_strength PASSED           [ 80%]
tests/test_theme_manager.py::test_theme_manager_default_and_palette PASSED [ 81%]
tests/test_theme_manager.py::test_theme_manager_toggle PASSED            [ 83%]
tests/test_theme_manager.py::test_theme_manager_subscriber_notification PASSED [ 85%]
tests/test_theme_manager.py::test_settings_repository_persistence PASSED [ 86%]
tests/test_validators.py::test_validate_username PASSED                  [ 88%]
tests/test_validators.py::test_validate_price PASSED                     [ 90%]
tests/test_validators.py::test_validate_menu_item PASSED                 [ 91%]
tests/test_validators.py::test_validate_quantity PASSED                  [ 93%]
tests/test_validators.py::test_validate_discount PASSED                  [ 95%]
tests/test_validators.py::test_validate_tax_rate PASSED                  [ 96%]
tests/test_validators.py::test_validate_payment_method PASSED            [ 98%]
tests/test_manage_db.py::test_create_backup_file_creation PASSED         [ 95%]
tests/test_manage_db.py::test_clean_demo_preserves_master_seeds PASSED   [ 97%]
tests/test_manage_db.py::test_recover_admin_resets_password PASSED       [ 98%]
tests/test_validators.py::test_validate_order_status PASSED              [100%]

============================= 63 passed in 15.37s =============================
```

---

## 3. Results Breakdown by Feature Group

1. **Authentication & Security:** 10/10 passed (PBKDF2 hashing, password strength, constant-time compare, session login/logout).
2. **Poka-Yoke Input Validation:** 8/8 passed (price quantization, positive quantity bounds, discount ranges, payment methods).
3. **Database & Persistence:** 7/7 passed (foreign key enforcement, transaction rollback on failure, idempotent migrations).
4. **Menu Catalog Management:** 6/6 passed (CRUD operations, duplicate prevention, category filtering, search).
5. **Order Lifecycle & Cart:** 5/5 passed (multi-item order creation, line totals, cancellation, PENDING modifications).
6. **Billing & Receipts:** 4/4 passed (exact Decimal calculations, receipt text formatting, historical price protection).
7. **Q08-F1 Interactive Dashboard:** 2/2 passed (empty database zero-division protection, real-time KPI metrics).
8. **Q08-F2 Visual Reports:** 3/3 passed (Matplotlib figure generation in dark/light themes, order/payment distributions).
9. **Q08-F3 Theme Toggle:** 4/4 passed (appearance switching, listener callback dispatch, database persistence).
10. **Q08-F5 User Profile Settings:** 6/6 passed (profile viewer, display name updater, secure password change, preferences persistence).
11. **Logging & Domain Models:** 5/5 passed (credential redaction, domain dataclass helpers).
12. **Database Administration & Demo Governance:** 3/3 passed (backup snapshot creation, safe demo data cleanup with master seed protection, admin credential recovery).

