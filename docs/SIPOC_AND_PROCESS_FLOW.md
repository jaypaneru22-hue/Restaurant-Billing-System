# SIPOC MODEL & PROCESS FLOW DOCUMENTATION
## Total Quality Management (TQM) — BBAT104
**Academic Course:** BBAT104 — Fundamentals of Total Quality Management  
**Student Name:** Jay Paneru | **Registration Number:** 2410302024  
**Quality Goal:** Q08 — Improve User Satisfaction | **Session:** 2026–27

---

## 1. High-Level SIPOC Model

The **SIPOC** framework (Suppliers, Inputs, Process, Outputs, Customers) provides a holistic boundary for the Restaurant Management Platform, illustrating how upstream resources transform into downstream customer value.

```mermaid
flowchart LR
    S["Suppliers<br/>• Food Vendors<br/>• System Admin<br/>• Floor Staff"] --> I["Inputs<br/>• Menu Catalog<br/>• Table Reservations<br/>• Raw Ingredients<br/>• Guest Orders"]
    I --> P["Core Process<br/>• Order Capture<br/>• Kitchen KDS Prep<br/>• Billing & Settle<br/>• CSAT Feedback"]
    P --> O["Outputs<br/>• Prepared Dishes<br/>• Printed Invoices<br/>• Shift Audits<br/>• NPS Telemetry"]
    O --> C["Customers<br/>• Dining Guests<br/>• Cashiers & Waiters<br/>• Executive Chefs<br/>• General Manager"]
```

### Detailed SIPOC Matrix

| Element | Specification & Operational Boundary |
| :--- | :--- |
| **Suppliers** | • **System Administrator:** System configuration, role permissions, tax & restaurant profile.<br/>• **Kitchen Stewards & Vendors:** Food ingredients, inventory restock alerts.<br/>• **Cashier & Service Staff:** Dine-in table assignments, order entry, payment tendering.<br/>• **Dining Guests:** Order preferences, custom split requests, dining feedback & ratings. |
| **Inputs** | • **Menu Master Data:** Dish names, categories, pricing, 86 availability status.<br/>• **Customer Data:** Guest name, contact, table number, dining party size.<br/>• **Payment Instruments:** Physical Cash, Simulated Credit/Debit Cards, Simulated UPI VPAs.<br/>• **Financial Parameters:** 5.0% Goods & Services Tax (GST), authorized promotional discounts. |
| **Process** | 1. **Order Capture:** Cashier/Customer inputs order line items with quantity validation.<br/>2. **Kitchen KDS Dispatch:** Live ticket generation with cooking timers and status transitions.<br/>3. **Food Production & Expediting:** Kitchen cooks dishes, updates status to `READY`.<br/>4. **Billing & Settlement:** Subtotal computation, tax/discount calculation, split payments.<br/>5. **Drawer Reconciliation:** Shift closeout, cash drawer variance tracking.<br/>6. **Quality Feedback (Q08):** Star rating collection and Net Promoter Score (NPS) logging. |
| **Outputs** | • **Accurate Customer Invoices:** Thermal receipt printout with tax breakdown and QR verification.<br/>• **Timely Prepared Food:** Cooked meals dispatched with minimal latency.<br/>• **Shift Closeout Reports:** Exportable summary of cash, card, and UPI collections.<br/>• **Executive Analytics:** Sales trend charts, payment method distribution, staff activity logs. |
| **Customers** | • **Dining Guests:** High-satisfaction dining experience with transparent order tracking.<br/>• **Counter Cashiers:** Ergonomic, mistake-proofed POS interface with keyboard accelerators.<br/>• **Kitchen Chefs:** Clutter-free digital ticket board replacing lost paper tickets.<br/>• **Restaurant Management & Regulators:** Audit-compliant financial logs and tax reporting. |

---

## 2. End-to-End Operational Process Flows

### Flow 1: Point-of-Sale Order & Settlement Flow
```mermaid
sequenceDiagram
    autonumber
    actor Customer as Dining Guest
    actor Cashier as Cashier Terminal
    participant POS as Billing Service
    participant DB as SQLite (WAL)
    actor Chef as Kitchen (KDS)

    Customer->>Cashier: Request Dine-in / Takeaway Order
    Cashier->>POS: Add menu items & table number
    POS->>POS: Poka-Yoke: Validate stock availability (86 check)
    POS->>DB: Commit Order (Status: PENDING)
    DB-->>Chef: Push order to Kitchen Queue
    Chef->>Chef: Accept & Cook (PENDING -> PREPARING -> READY)
    Customer->>Cashier: Request Bill & Payment
    Cashier->>POS: Select Payment Method (Cash / Card / UPI / Split)
    POS->>POS: Poka-Yoke: Verify tender >= final total
    POS->>DB: Finalize Bill (Status: PAID)
    POS-->>Cashier: Display Thermal Receipt Dialog
    Cashier->>Customer: Hand itemized receipt & change
```

### Flow 2: Kitchen Expediter Lifecycle Flow
```mermaid
stateDiagram-v2
    [*] --> PENDING: Order Placed at POS / Portal
    PENDING --> ACCEPTED: Chef Accepts Ticket
    ACCEPTED --> PREPARING: Cooking Commences (Timer Active)
    PREPARING --> READY: Food Plated & Inspected
    READY --> COMPLETED: Dispatched to Table & Billed
    COMPLETED --> [*]

    state PENDING {
        [*] --> NewTicket
        NewTicket --> HighWaitAlert: Elapsed > 15 min
    }
```

### Flow 3: Split Billing Reconciliation Flow
```mermaid
flowchart TD
    A["Select Bill for Settlement"] --> B{"Choose Split Mode"}
    B -->|Equal Party Split| C["Divide Final Total by N Guests"]
    C --> D["Penny Reconciliation Algorithm"]
    D --> E["Distribute Remaining 1-Paise Remainders"]
    B -->|Custom Amount Split| F["Enter Custom Share per Party"]
    F --> G{"Sum(Shares) == Final Total?"}
    G -->|No - Variance != 0| H["Display Variance Alert: Cannot Settle"]
    H --> F
    G -->|Yes - Variance == 0| I["Lock Shares & Confirm Settlement"]
    E --> I
    I --> J["Record Bill as Payment Method: SPLIT"]
    J --> K["Print Itemized Receipt"]
```

---
*Authored by Jay Paneru (2410302024) for BBAT104 Total Quality Management.*
