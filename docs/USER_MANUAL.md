# Restaurant Billing System — Comprehensive User Manual

- **Subject:** BBAT104 — Fundamentals of Total Quality Management
- **Course Assignment:** Restaurant Billing System
- **Student Name:** Jay Paneru
- **Registration Number:** 2410302024
- **Assigned Quality Goal:** **Q08 — Improve User Satisfaction**
- **Academic Session:** 2026–27
- **Application Version:** 1.0.0

---

## 1. System Overview & Getting Started

The **Restaurant Billing System** is an offline Point-of-Sale (POS) and managerial billing desktop application engineered with Python 3.12, CustomTkinter, and SQLite3. It is designed to maximize transaction speed, prevent billing discrepancies, and provide continuous operational visibility.

### 1.1 Launching the Application
From the project workspace directory in your terminal or PowerShell:
```bash
python main.py
```
*(Alternatively, you may launch with the virtual environment interpreter: `.venv\Scripts\python.exe main.py`)*

### 1.2 Demonstration User Accounts
The application initializes with two seeded demonstration accounts:
- **Administrator Role:**
  - **Username:** `admin`
  - **Password:** `Admin@123`
  - *Full administrative privileges: menu editing, analytics, and user settings.*
- **Cashier Role:**
  - **Username:** `cashier1`
  - **Password:** `Cashier@123`
  - *Front-desk cashier permissions for fast order entry and bill settlements.*

---

## 2. Navigating the Interface & Keyboard Accelerators (Q08-F4)

The application provides a consistent top header bar, left navigation sidebar, and global keyboard accelerators for mouse-free cashier workflows:

| Shortcut | Destination / Action | Description |
|----------|----------------------|-------------|
| **`Alt + D` / `Ctrl + D`** | **📊 Dashboard** | Jump to Interactive Operational Dashboard |
| **`Alt + N` / `Ctrl + N`** | **➕ New Order** | Open Point-of-Sale dish selection & cart |
| **`Alt + M` / `Ctrl + M`** | **📋 Menu Catalog** | Manage menu items, prices, and categories |
| **`Alt + O` / `Ctrl + O`** | **📜 Orders History**| View all pending and completed orders |
| **`Alt + R` / `Ctrl + R`** | **📈 Visual Reports**| Open analytical Matplotlib quality charts |
| **`Alt + P` / `Ctrl + P`** | **👤 User Profile** | Open account profile and security settings |
| **`Alt + T`** | **🌓 Toggle Theme** | Toggle between Dark Mode and Light Mode |
| **`Escape`** | **Dismiss / Close** | Close any open modal dialog (Receipt, Bill, Add Dish) |

---

## 3. Assigned Q08 Features Walkthrough

### Feature 1: Interactive Dashboard (Q08-F1)
- **Navigation:** Press `Alt+D` or click **"📊 Dashboard"** on the sidebar.
- **Key Metrics Displayed:**
  - **Today's Sales (₹):** Live total of all bills finalized today.
  - **Completed Orders:** Count of paid orders today.
  - **Pending Orders:** Active orders currently awaiting settlement.
  - **Average Order Value (₹):** Real-time calculated revenue per completed transaction.
- **Recent Transactions:** The last 5 orders appear on the left table, with customer name, table number, order status, and final amount.
- **Top Selling Dishes:** Ranked list of the 5 most popular menu items by total volume sold.
- **Quick Action Buttons:** Directly launch a New Order or click **"🔄 Refresh"** to poll the latest database totals.

### Feature 2: Visual Analytical Reports (Q08-F2)
- **Navigation:** Press `Alt+R` or click **"📈 Visual Reports"** on the sidebar.
- **Filter Controls:** Use the **"Period"** segmented button to switch between **7 Days**, **14 Days**, and **30 Days**.
- **Charts Overview:**
  1. **Daily Sales Trend:** Bar chart illustrating daily revenue in Rupees (₹) with exact value annotations above each bar.
  2. **Top Menu Items by Volume:** Horizontal bar chart highlighting the most frequently ordered dishes.
  3. **Order Status Distribution:** Donut chart showing the percentage breakdown of `COMPLETED`, `PENDING`, and `CANCELLED` tickets.
  4. **Payment Methods Breakdown:** Distribution of payments processed via `CASH`, `CARD`, and `UPI`.
- **Dynamic Re-theming:** Charts automatically redraw with high-contrast palettes when toggling between dark and light themes!

### Feature 3: Persistent Theme Toggle (Q08-F3)
- **Navigation:** Press `Alt+T` or click the **"🌙 Dark Mode" / "☀️ Light Mode"** button in the top right header.
- **Functionality:** Smoothly flips the entire interface—including buttons, form entries, cards, and embedded charts—between dark and light modes.
- **Persistence:** Your theme preference is permanently saved in the SQLite `user_settings` table and automatically restored whenever you log back in.

### Feature 4: Keyboard Accelerators (Q08-F4)
- Accelerators are permanently active throughout the application.
- To view the shortcuts legend at any time, click the **"⌨️ Shortcuts"** button in the header bar.

### Feature 5: User Profile & Security Settings (Q08-F5)
- **Navigation:** Press `Alt+P` or click **"👤 User Profile"** on the sidebar.
- **Account Identity:** View username, system role (`ADMIN` or `CASHIER`), and account registration date.
- **Update Display Name:** Edit the **Full Name** field and click **"Save Profile Name"**.
- **Update Workspace Preferences:** Set your preferred default theme (`dark` or `light`) and default tax rate (e.g. `5.0%`), then click **"Apply & Persist Preferences"**.
- **Security & Password Update:** Enter your current password, type a new password (min. 6 characters with letters and numbers), confirm the new password, and click **"Update Password"**. The system verifies your current credentials and stores the new PBKDF2-HMAC-SHA256 salted hash.

---

## 4. End-to-End Cashier Billing Workflow

### Step 1: Open New Order Cart
1. Press `Alt+N` or click **"➕ New Order"**.
2. Enter the **Table No** (e.g., `Table 4` or `Takeaway`) and **Customer Name**.

### Step 2: Add Menu Items
1. Browse dishes from the catalog on the left, or use the **Search** bar or **Category** filter.
2. Click **"➕ Add"** on any dish to add it to the active order cart on the right.
3. In the cart, use the **`+`** and **`-`** buttons to adjust quantities. The item line totals and order subtotal update in real time.

### Step 3: Settle the Bill
1. Click **"Proceed to Bill 💳"**.
2. The **Bill Settlement Dialog** appears:
   - Review line items and subtotal.
   - Enter an optional **Discount Percentage (%)** (e.g. `5` or `10`).
   - Confirm the **GST Tax Rate (%)** (default `5.0%`).
   - Select the **Payment Method:** `CASH`, `CARD`, or `UPI`.
   - The dialog immediately recalculates the discount amount, tax amount, and net payable total using exact Decimal arithmetic.
3. Click **"Finalize & Issue Receipt 🧾"**.
4. The transaction commits atomically to the SQLite database, and the order status is set to `COMPLETED`.

### Step 4: Print & Reprint Receipts
1. The **Receipt Preview Dialog** displays a professional, itemized monospace receipt containing:
   - Restaurant banner, BBAT104 project details, and student registration number.
   - Unique Bill Number (`BILL-YYYYMMDD-XXXX`) and Order Number (`ORD-YYYYMMDD-XXXX`).
   - Date, time, table, and customer.
   - Line items with quantities, unit prices, and amounts.
   - Subtotal, Discount, GST tax, and Net Payable Total.
   - Payment method and status.
2. Click **"📋 Copy to Clipboard"** to copy the text for thermal printers or press **`Esc`** to close.
3. To reprint any past bill, navigate to **"📜 Orders History"** (`Alt+O`), locate the order, and click **"View Receipt 🧾"**.
