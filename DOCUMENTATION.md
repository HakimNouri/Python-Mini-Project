# Supermarket Management System — Documentation

## Overview

A desktop application for managing a supermarket: products, sales, receipts, reports, and user accounts. Built entirely in Python with a local MongoDB database and a PyQt6 graphical interface.

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.13+ |
| GUI framework | PyQt6 | ≥ 6.7 |
| Database | MongoDB (local) | any |
| DB driver | pymongo | ≥ 4.7 |
| Charts | matplotlib | ≥ 3.9 |
| Auth hashing | bcrypt | ≥ 4.0 |
| Config | python-dotenv | ≥ 1.0 |
| Tests | pytest | ≥ 8.0 |

Configuration is read from a `.env` file at the project root:

```
MONGO_URI=mongodb://localhost:27017
DB_NAME=supermarket
STORE_NAME=My Supermarket
```

---

## Project Structure

```
Store App/
├── main.py                        # Entry point
├── requirements.txt
├── .env
├── assets/
│   ├── style.qss                  # Global Qt stylesheet
│   └── arrow_down.svg             # Custom dropdown arrow icon
├── receipts/                      # Auto-created; stores receipt .txt files
├── src/
│   ├── database.py                # MongoDB singleton + collection accessors
│   ├── models/
│   │   ├── product.py             # Product dataclass
│   │   └── sale.py                # Sale + SaleItem dataclasses
│   ├── services/
│   │   ├── __init__.py            # Custom exception hierarchy
│   │   ├── auth_service.py        # User auth + CRUD (bcrypt)
│   │   ├── product_service.py     # Product CRUD + stock management
│   │   ├── sale_service.py        # Sale processing + reporting queries
│   │   └── receipt_service.py     # Receipt text generation + file I/O
│   └── ui/
│       ├── login.py               # Frameless login dialog
│       ├── main_window.py         # Root window: sidebar, page stack, shortcuts
│       ├── dashboard.py           # Stats overview page
│       ├── products_page.py       # Product list, search, CRUD, CSV export
│       ├── sales_page.py          # New sale flow
│       ├── receipts_page.py       # Receipt history with inline preview
│       ├── reports_page.py        # Monthly revenue + top-5 charts
│       ├── users_page.py          # User management (admin only)
│       └── widgets/
│           ├── cart_table.py      # Cart table widget
│           ├── product_form.py    # Add/edit product dialog
│           ├── product_picker.py  # Searchable product selector dialog
│           ├── receipt_preview.py # Receipt preview dialog (before saving)
│           └── toast.py           # Fade-out notification widget
└── tests/
    ├── test_product_service.py
    ├── test_sale_service.py
    └── test_receipt_service.py
```

---

## Architecture

The app follows a **layered architecture** with strict one-way dependencies:

```
UI layer (PyQt6 widgets)
      │
      ▼
Service layer (business logic)
      │
      ▼
Model layer (dataclasses + serializers)
      │
      ▼
Database layer (pymongo + MongoDB)
```

- **Models** are plain Python `@dataclass` objects with `to_doc()` / `from_doc()` serializers. They know nothing about the database or UI.
- **Services** contain all business logic. They accept and return model objects and raise custom exceptions (`DuplicateCodeError`, `InsufficientStockError`, etc.) that the UI catches and displays.
- **UI pages** call service functions, handle exceptions, and never touch MongoDB directly.
- **`MainWindow`** owns all pages and provides two cross-page hooks: `show_toast()` and `on_sale_completed()`.

---

## Database

MongoDB is used as a document store via pymongo. Three collections:

### `products`
```json
{
  "code": "P001",
  "name": "Milk",
  "category": "Dairy",
  "price": 120.0,
  "quantity": 48,
  "description": ""
}
```
A unique index on `code` is created automatically on first run.

### `sales`
```json
{
  "receipt_no": "001",
  "date": "2024-01-15T10:30:00Z",
  "total": 360.0,
  "payment_method": "cash",
  "items": [
    {
      "product_code": "P001",
      "product_name": "Milk",
      "unit_price": 120.0,
      "quantity": 3
    }
  ]
}
```

### `users`
```json
{
  "username": "admin",
  "password": "<bcrypt hash>",
  "role": "admin"
}
```
An `admin/admin123` account is seeded automatically if no users exist.

---

## Feature Implementations

### Authentication (`src/ui/login.py`, `src/services/auth_service.py`)
A frameless `QDialog` with a dark header and a white form card. On submit, `authenticate()` looks up the user in MongoDB and verifies the password with `bcrypt.checkpw()`. The result is a `{"username": ..., "role": ...}` dict passed to `MainWindow`. The login loop in `main.py` uses `QTimer.singleShot` so that after logout the login dialog is shown again without restarting the process.

### Main Window (`src/ui/main_window.py`)
A `QMainWindow` with a fixed-width sidebar (`QListWidget`) and a `QStackedWidget` content area. `Ctrl+1–6` shortcuts navigate between pages. The sidebar is hidden from staff users for the Users page. After a sale `on_sale_completed()` is called, which refreshes the dashboard, products, and receipts pages simultaneously.

### Products (`src/ui/products_page.py`, `src/services/product_service.py`)
- **Search**: debounced with a 250 ms `QTimer` to avoid querying MongoDB on every keystroke. Results are shown with a count badge.
- **Sorting**: custom sort on column header click using a key function dict; `setSortingEnabled` is not used because it conflicts with `setCellWidget`.
- **Stock colouring**: rows with quantity 0 get a red background, 1–5 get orange.
- **Delete**: fetches the product name before the confirmation dialog. Checks the sales collection first; raises `ProductInUseError` if the product appears in any sale.
- **CSV export**: `QFileDialog` → `csv.DictWriter` over all products.
- **Add/Edit**: `ProductFormDialog` validates fields inline. On `DuplicateCodeError` the Code field is auto-focused and its border turns red via a `error="true"` Qt property + `unpolish/polish`.

### Sales (`src/ui/sales_page.py`)
1. **"+ Add Product"** opens `ProductPickerDialog` — a searchable table of all products.
2. After selection, `_AddToCartDialog` shows the product name, available stock, and editable price and quantity fields.
3. Confirming adds a `SaleItem` to `CartTable`, which emits `cart_changed` to update the summary bar and enable the Confirm button.
4. **Confirm Sale** shows `ReceiptPreviewDialog` first (read-only formatted receipt text). Only on "Confirm & Save" does `process_sale()` write to MongoDB, decrement stock atomically, and generate the `.txt` receipt file.

### Receipts (`src/ui/receipts_page.py`)
- Four quick-filter preset buttons (Today / This Week / This Month / All) set both date pickers and reload the table.
- The page uses a `QSplitter`: left side is the table, right side is an inline `QTextEdit` preview panel that loads the receipt file when a row is clicked.
- A receipt-number search field filters rows in real time using `setRowHidden`.

### Reports (`src/ui/reports_page.py`, `src/services/sale_service.py`)
- **Revenue chart**: aggregates daily totals using a MongoDB pipeline grouped by calendar day. Rendered with matplotlib `FigureCanvasQTAgg`. Supports Bar and Line modes toggled with `QRadioButton`.
- **Top-5 products**: a second aggregation unwinds the `items` array, groups by `product_name`, sums `subtotal`, and limits to 5. Rendered as a horizontal bar chart.
- Both charts update live when the month or year selector changes (no "Generate" button).

### Dashboard (`src/ui/dashboard.py`)
Four `StatCard` widgets (`QFrame` subclass) show: total products, out-of-stock count, today's sales count, and today's revenue with a delta vs. yesterday (green ▲ or red ▼). Cards are clickable and navigate to the relevant page. A yellow banner appears when any products have 1–5 units remaining.

### User Management (`src/ui/users_page.py`, `src/services/auth_service.py`)
Admin-only page (hidden from the sidebar for staff). Lists all users with Edit and Delete actions. Edit allows changing the password (leave blank to keep current) and role. The logged-in user's Delete button is disabled to prevent self-lockout.

### Toast Notifications (`src/ui/widgets/toast.py`)
A frameless `QWidget` that appears in the bottom-right corner of `MainWindow`. Uses `QGraphicsOpacityEffect` + `QPropertyAnimation` to fade out after 2.5 seconds over 500 ms. Four severity levels: `info` (blue), `success` (green), `warning` (orange), `error` (red).

### Receipts File Format (`src/services/receipt_service.py`)
`receipt_text(sale, store_name)` produces a fixed-width plain-text receipt (store name header, date, itemised list with columns Product/Qty/Price/Subtotal, total, payment method, footer). `generate()` calls it and writes the result to `receipts/receipt_{no}.txt`.

---

## Styling (`assets/style.qss`)

A single Qt Stylesheet file loaded at startup via `QApplication.setStyleSheet()`. Key conventions:

- **Colour palette** defined as comments at the top (no runtime variable support in QSS).
- **Button roles** via Qt property: `QPushButton[role="danger"]`, `[role="success"]`, `[role="secondary"]`, `[role="preset"]` — set with `btn.setProperty("role", "...")`.
- **Focus rings**: blue outline on focused inputs and buttons.
- **Error state**: `QLineEdit[error="true"]` turns the border red; toggled by setting the property and calling `unpolish/polish` to force a repaint.
- **Radio buttons**: custom circular indicator, solid blue fill when checked.
- **Dropdown arrow**: custom SVG (`assets/arrow_down.svg`) for `QComboBox` and `QDateEdit`.
- **Scrollbars**: slim 8 px bars with rounded handles.

---

## Custom Exception Hierarchy (`src/services/__init__.py`)

```
AppError
├── DuplicateCodeError      → duplicate product code on insert
├── ProductInUseError       → product appears in existing sales
├── InsufficientStockError  → requested qty exceeds available stock
└── AuthError               → wrong username or password
```

All are caught in the UI layer and surfaced as inline labels, toasts, or `QMessageBox` dialogs.

---

## Running the App

```bash
# Install dependencies
pip install -r requirements.txt

# Start MongoDB locally (default port 27017)

# Run
python main.py
```

Default login: **admin / admin123**

## Running Tests

```bash
python -m pytest tests/
```

Tests use a separate `test_supermarket` database that is dropped after each module.
