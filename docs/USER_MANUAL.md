# RESTAURANT MANAGEMENT PLATFORM — USER OPERATING MANUAL
## Comprehensive Operational Guide for Admin, Manager, Cashier, Chef, and Customer Roles
**Academic Subject:** BBAT104 — Fundamentals of Total Quality Management  
**Student Name:** Jay Paneru | **Registration Number:** 2410302024  
**Quality Goal:** Q08 — Improve User Satisfaction | **Release:** Enterprise Master v1.0.0

---

## 1. Getting Started & Sign In

### Default System Accounts (Demo Credentials)
The platform is pre-seeded with 5 functional accounts representing all restaurant personas:

| Persona / Role | Username | Password | Default Initial Screen |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin` | `Admin123!` | Executive Governance Overview |
| **Store / Floor Manager** | `manager1` | `Manager123!` | Operations Floor & Table Plan |
| **Counter Cashier** | `cashier1` | `Cashier123!` | Shift Overview & Counter Billing |
| **Executive Chef** | `chef1` | `Chef123!` | Kitchen Display System (KDS) Queue |
| **Dining Guest / Customer** | `customer1` | `Customer123!` | Dining Experience & Order Tracker |

*Tip: On the Sign-In screen, you can click any of the 1-Click Quick Demo buttons (`Admin`, `Manager`, `Cashier`, `Chef`, `Guest`) to prefill credentials and log in instantly.*

### New Customer Account Registration
1. On the login screen, click **"🍽️ New Guest? Register Dining Account"**.
2. Enter your Full Name, desired Username, and a secure password ($\ge 6$ characters).
3. Click **"Register & Sign In 🚀"**. You will be logged into your dedicated Dining Experience Portal.

---

## 2. Role 1: System Administrator Guide

### A. Executive Governance Dashboard
- **Live KPI Telemetry:** 7 real-time cards displaying Today's Gross Sales, Total Invoices, Average Order Value, Active Tables, Active Staff, Menu Items, and Overall CSAT Rating.
- **Analytics Charts:** Switchable daily/monthly revenue trends and payment method distribution charts.
- **Recent Invoices & Staff Feed:** Inspect live orders and administrative activity logs.

### B. Staff & Account Management
- **Add Staff:** Click *"Add Staff Account"*, input username, full name, role (`ADMIN`, `MANAGER`, `CASHIER`, `CHEF`, `CUSTOMER`), and password.
- **Deactivate / Activate Staff:** Toggle staff account status. Deactivated users cannot log into the terminal.
- **Password Reset:** Securely reset staff passwords with PBKDF2 hashing.
- **Poka-Yoke Guard:** System strictly prohibits deleting or deactivating the last active administrator account.

### C. Enterprise Settings & System Health
- **Billing & Tax Rules:** Configure default GST rate (default: 5.0%), maximum allowable promotional discount, and currency symbol (`₹`).
- **Database Backup & Restoration:** One-click snapshot backups saved with verified integrity checks to `data/backups/`. Restore points can be selected and tested safely.
- **Security Audit Logs:** Searchable audit trail recording every administrative login, setting modification, and user credential change.

---

## 3. Role 2: Floor Manager Guide

### A. Floor & Table Management
- **Zone View:** Visual floor plan divided into **Main Dining**, **Patio Garden**, **Family Section**, and **Counter / Bar**.
- **Table Occupancy Indicators:** Color-coded status pills:
  - 🟢 `VACANT`: Ready for seating.
  - 🟡 `OCCUPIED`: Diners currently seated.
  - 🟠 `BILL_REQUESTED`: Guests requested check.
  - 🔵 `CLEANING`: Table being sanitized.
- **Poka-Yoke Vacate Guard:** A table cannot be marked `VACANT` if an unsettled active order is still tied to it.

### B. Live Active Orders & Kitchen Monitoring
- Real-time list of all cooking orders across the restaurant.
- Filter by status: `ALL`, `PENDING`, `ACCEPTED`, `PREPARING`, `READY`.
- Ability to assist counter staff by clicking *"Settle Order"* to open cashier billing.

### C. 86 Dish Availability Catalog
- Search and toggle availability of any dish instantly.
- Dishes marked **Unavailable (86'd)** are immediately grayed out and blocked from order entry across both Cashier POS and Customer Dining portals.

### D. Shift Monitoring
- View all active staff shifts, transaction counts, and generated revenue.
- Review end-of-day drawer variance logs.

---

## 4. Role 3: Counter Cashier Guide

### A. POS Counter Billing & Order Entry
1. Navigate to **"🛒 Counter Billing"** (Hot-key: `Alt+N`).
2. Select or enter Table Number (e.g. `T1`, `P2`, or `Takeaway`).
3. Enter Guest Name or leave default `"Walk-in Customer"`.
4. Filter catalog by category (`Beverages`, `Starters`, `Main Course`, `Breads & Rice`, `Desserts`).
5. Click dish cards to add items to the cart. Adjust quantities with `+` / `-` buttons.
6. Click **"Proceed to Bill 💳"** to open payment settlement.

### B. Billing Settlement & Payment Methods
- **Cash Settlement:** Enter tendered cash amount. The system instantly calculates and displays change due. Poka-Yoke validation blocks completing the bill if tendered cash is less than the net payable amount.
- **Simulated Card Payment:** Enter cardholder name and simulated card digits. Safe demonstration mode (no real banking data stored).
- **Simulated UPI Payment:** Enter UPI ID (e.g. `guest@okhdfcbank`) or display demo QR code.
- **✂️ Split Bill Settlement:**
  - Click **"✂️ Split Bill"** to open party division dialog.
  - **Equal Split:** Select party size (2 to 10 guests). The system calculates exact shares down to the last paisa.
  - **Custom Split:** Allocate custom amounts per guest. Validation ensures the sum matches the total with ₹0.00 variance.
  - Click **"Confirm Split Settlement"** to finalize.

### C. Thermal Receipt Printing
- Upon settlement, the **Thermal Receipt Dialog** opens.
- Features formatted itemized breakdown, tax details, payment method, and QR verification stamp.
- Click **"🖨️ Print Receipt"** to export a clean text receipt to `data/receipts/`.

### D. Shift Closeout & Drawer Reconciliation
1. Navigate to **"💼 Shift Closeout"** (Hot-key: `Alt+Z`).
2. Review system-calculated totals: Total Orders, Gross Sales, Cash Collected, Card Collected, UPI Collected.
3. Enter physical counted cash in the drawer.
4. The system calculates **Drawer Variance** (`Counted - Expected`).
5. Click **"Close Shift & Print Reconciliation"** to lock the shift.

---

## 5. Role 4: Executive Chef Guide (KDS)

### A. Kitchen Display System (KDS) Live Queue
1. Log in as `chef1` (Password: `Chef123!`).
2. The KDS screen presents a real-time order queue organized as visual KOT cards.
3. Filter tickets by tabs: `ALL`, `PENDING (NEW)`, `ACCEPTED`, `PREPARING`, `READY`.

### B. Ticket Lifecycle & Cooking Timers
- Every KOT card displays:
  - Table Number & Order Number.
  - Wait Time Timer (updates live in minutes).
  - High-Wait Alert Badge: Turns Crimson with visual alert if ticket elapsed time $> 15$ minutes.
  - Itemized dish names with exact quantities.
- **Workflow Buttons:**
  - `Accept Order` $\to$ Moves status from `PENDING` to `ACCEPTED`.
  - `Start Cooking` $\to$ Moves status to `PREPARING`.
  - `Mark Ready` $\to$ Moves status to `READY` (signals waitstaff for pickup).

---

## 6. Role 5: Customer Dining Portal Guide

### A. Guest Dining Hub
- Guests access a tailored, distraction-free interface.
- View restaurant highlights, chef recommendations, and dining announcements.

### B. Live Order Status Tracker
- Diners can observe the exact stage of their meal in real time:
  $$\text{Order Placed} \longrightarrow \text{Kitchen Accepted} \longrightarrow \text{Cooking in Progress} \longrightarrow \text{Ready for Serving} \longrightarrow \text{Served \& Billed}$$
- Complete reassurance with zero wait-time anxiety.

### C. Quality Feedback & Net Promoter Score (NPS)
- Guests can rate their dining experience:
  - **Food Quality Rating:** 1 to 5 Stars.
  - **Service Speed Rating:** 1 to 5 Stars.
  - **Net Promoter Score (NPS):** 0 to 10 likelihood to recommend scale.
  - **Review Comments:** Free-form feedback directly forwarded to the Manager Feedback panel.

---

## 7. Global Keyboard Accelerators

| Shortcut Key | Action Performed |
| :--- | :--- |
| `Alt + D` / `Ctrl + D` | Navigate to Dashboard / Shift Overview |
| `Alt + N` / `Ctrl + N` | Navigate to New POS Order (Billing) |
| `Alt + E` | Navigate to Floor & Table Management Plan |
| `Alt + M` / `Ctrl + M` | Navigate to Menu Catalog Management |
| `Alt + A` | Navigate to Live Kitchen Queue / Active Orders |
| `Alt + F` | Navigate to 86 Dish Stockout List |
| `Alt + O` / `Ctrl + O` | Navigate to Orders History & Receipts |
| `Alt + R` / `Ctrl + R` | Navigate to Sales Reports & Operational Analytics |
| `Alt + Z` | Navigate to Shift Closeout Reconciliation |
| `Alt + P` / `Ctrl + P` | Navigate to User Profile |
| `Alt + S` / `Ctrl + S` | Navigate to Terminal Settings |
| `Alt + T` | Toggle UI Theme (Midnight Obsidian Dark / Light) |
| `Escape` | Dismiss active modal dialog / receipt viewer |

---
*Authored by Jay Paneru (2410302024) for BBAT104 Total Quality Management.*
