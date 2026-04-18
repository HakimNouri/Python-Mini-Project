# Supermarket Management System

A desktop application for managing a supermarket — products, sales, receipts, monthly reports, and user accounts. Built with Python and PyQt6, backed by a local MongoDB database.

![Python](https://img.shields.io/badge/Python-3.13%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.7%2B-green)
![MongoDB](https://img.shields.io/badge/MongoDB-local-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Screenshots

> Dashboard · Products · New Sale · Receipts · Reports

---

## Features

- **Dashboard** — live stat cards (total products, out-of-stock, daily revenue, today's sales), low-stock warning banner, yesterday revenue comparison
- **Products** — searchable & sortable table, add / edit / delete, stock colour-coding, CSV export
- **Sales** — browse-and-pick product flow, editable price and quantity, cart management, payment method selection, receipt preview before saving
- **Receipts** — date-range filter with quick presets, inline receipt preview panel, receipt-number search
- **Reports** — monthly revenue bar/line chart, top-5 products chart, auto-updates on selection change
- **Users** — admin-only user management (add, edit, delete), role-based access (admin / staff)
- **Auth** — bcrypt-hashed passwords, login dialog, logout without restarting the process
- **Notifications** — fade-out toast notifications for all CRUD actions

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.11 or newer |
| MongoDB Community | 6.0 or newer |
| Git | any |

---

## Installation

### 1 — Clone the repository

```bash
git clone https://github.com/your-username/store-app.git
cd store-app
```

### 2 — Create and activate a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Install and start MongoDB

Download MongoDB Community from https://www.mongodb.com/try/download/community and follow the installer for your OS. Make sure `mongod` is running on the default port **27017** before launching the app.

Quick check:
```bash
mongod --version   # should print a version number
```

### 5 — Configure the environment

Copy the example config and edit as needed:

```bash
cp .env.example .env
```

`.env` options:

```
MONGO_URI=mongodb://localhost:27017   # connection string
DB_NAME=supermarket                   # database name
STORE_NAME=My Supermarket             # displayed in the UI and on receipts
```

> If `.env.example` is not present, create `.env` manually with the values above.

### 6 — Run the app

```bash
python main.py
```

On first launch a default admin account is created automatically:

| Username | Password |
|---|---|
| `admin` | `admin123` |

> Change this password immediately via the **Users** page after logging in.

---

## Running the Tests

Tests use a separate `test_supermarket` database that is created and dropped automatically — your data is never touched.

```bash
python -m pytest tests/ -v
```

---

## Project Structure

```
store-app/
├── main.py                  # Entry point
├── requirements.txt
├── .env                     # Local config (not committed)
├── assets/
│   ├── style.qss            # Qt stylesheet
│   └── arrow_down.svg       # Dropdown arrow icon
├── receipts/                # Generated receipt .txt files (auto-created)
├── src/
│   ├── database.py          # MongoDB connection singleton
│   ├── models/              # Product, Sale, SaleItem dataclasses
│   ├── services/            # Business logic + custom exceptions
│   └── ui/                  # PyQt6 pages and widgets
└── tests/                   # pytest test suite
```

Full architecture details are in [DOCUMENTATION.md](DOCUMENTATION.md).

---

## Default Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+1` | Dashboard |
| `Ctrl+2` | Products |
| `Ctrl+3` | New Sale |
| `Ctrl+4` | Receipts |
| `Ctrl+5` | Reports |
| `Ctrl+6` | Users *(admin only)* |

---

## Troubleshooting

**App won't start / connection error at login**
Make sure MongoDB is running: `mongod` (or check your OS service manager).

**`ModuleNotFoundError: No module named 'PyQt6'`**
Your virtual environment is not activated, or dependencies weren't installed. Run `pip install -r requirements.txt` inside the activated venv.

**Charts don't render**
Ensure `matplotlib` installed correctly: `pip install matplotlib`. On some Linux systems you may also need `python3-tk`.

**Receipts folder missing**
It is created automatically on the first confirmed sale. You can also create it manually: `mkdir receipts`.

---

## License

MIT — see [LICENSE](LICENSE) for details.
