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

The application automatically centers itself on your primary display dynamically, adapting cleanly to both 1366×768 laptop screens and high-resolution desktop monitors without fixed coordinate cutoffs or spilling off-screen. All child dialogs (POS Settlement, Itemized Receipt, Dish Dialog, Keyboard Shortcuts) also center relative to the main application window.

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

## 4. End-to-End Cashier Point-of-Sale (POS) Workflow

### Step 1: Open Point of Sale View
1. Press `Alt+N` or click **"➕ New POS Order"** on the navigation sidebar.
2. The POS view features a responsive two-column ergonomic layout:
   - **Left Panel:** Dish Catalog with search bar, quick category pills (`All`, `Beverages`, `Starters`, `Main Course`, `Breads & Rice`, `Desserts`), and dish cards with price and "in cart" badges.
   - **Right Panel:** Live Cart Ticket with table selector pills (`T1`, `T2`, `T3`, `Parcel`), customer name, item steppers (`[-]` `[qty]` `[+]`), line totals, estimated 5% GST, and grand total.

### Step 2: Add Menu Items & Adjust Quantities
1. Filter dishes using the category pill bar or type in the real-time search box.
2. Click **"➕ Add"** on any dish to add it to the active order ticket.
   - *Poka-Yoke Guard:* Menu item prices are strictly validated as positive whole Indian Rupee amounts (e.g. ₹50, ₹100, ₹250). Decimal points (such as `10.50` or `.50`) are rejected at both UI and service levels.
3. In the cart panel:
   - Use the **`+`** and **`-`** buttons to adjust quantities.
   - Click the red **`✕`** icon to delete a single item, or click **"Clear Cart"** to reset the ticket.
   - The ticket subtotal, estimated GST, and grand total update automatically in real time.

### Step 3: Settle the Bill & Process Payment
1. **Empty Order Prevention:** The **"Proceed to Payment 💳"** and **"Save Pending ⏳"** buttons are automatically disabled while the cart is empty. If directly triggered, the application rejects the action with a clear warning: *"Please add at least one item before proceeding."* No empty records or partial transactions can ever be committed to SQLite.
2. Once at least one dish is added, click **"Proceed to Payment 💳"** (or click **"Save Pending ⏳"** to hold the ticket).
3. The **POS Settlement Modal** opens with guaranteed bottom action bar visibility (pinned bottom controls):
   - **Order Summary:** Line items review with exact unit prices and quantities.
   - **Financial Calculations:** Live Discount % and GST % inputs with immediate Decimal recalculation.
   - **Payment Method Selector:** Choose between `CASH`, `CARD`, or `UPI`:
     - **💵 CASH Payment:** Enter tendered cash amount (or click quick tender buttons: `Exact`, `+₹100`, `+₹500`, `+₹1000`). The system computes and displays **Change to Return** in emerald green or flags insufficient cash in real time.
     - **💳 DEMO CARD Payment:** Features a prominent academic test notice banner. Enter cardholder name, 16-digit card number, expiry (MM/YY), and CVV, or click **"✨ Fill Demo Card"** for instant 1-click test details. (No real banking data is transmitted or stored).
     - **📱 DEMO UPI Payment:** Enter a simulated UPI ID (e.g. `guest@upi` or click **"✨ Demo ID"** to auto-fill). Displays simulated QR code scanner instructions for Google Pay, PhonePe, Paytm, and BHIM UPI.
   - **Safety & Cancellation:** Click **"✕ Cancel Payment (Esc)"** at any time to close the modal safely without billing. The order ticket remains in `PENDING` status.
3. Click **"Confirm Payment & Settle Bill 💳"**:
   - The button automatically disables during commit to prevent double-clicks or duplicate billing.
   - Atomically records the bill, transitions order status to `COMPLETED`, and immediately opens the itemized tax receipt.

### Step 4: Print & Reprint Receipts
1. The **Receipt Preview Dialog** displays a professional, itemized monospace receipt containing:
   - Restaurant banner, BBAT104 project details, and student registration number.
   - Unique Bill Number (`BILL-YYYYMMDD-XXXX`) and Order Number (`ORD-YYYYMMDD-XXXX`).
   - Date, time, table, customer, line items, Subtotal, Discount, GST tax, and Net Payable Total.
   - Payment method and settlement status.
2. Click **"🖨️ Print Receipt"** to dispatch the receipt directly to your default Windows printer or printer spooler. The receipt is also automatically saved as a permanent text file in `data/receipts/RECEIPT_<bill_number>_<timestamp>.txt`.
   - If no physical printer is connected or active, the application displays a friendly message confirming the receipt file was saved on disk, and reveals an **"📂 Open File"** button to open and print it from Windows Notepad.
   - Press **`Esc`** or click **"Close (Esc)"** when finished.
3. To reprint any past bill, navigate to **"📜 Orders History"** (`Alt+O`), locate the order, and click **"View Receipt 🧾"**.

