import os

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QStackedWidget, QLabel, QListWidgetItem, QPushButton,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QShortcut, QKeySequence

from src.ui.dashboard import DashboardPage
from src.ui.products_page import ProductsPage
from src.ui.sales_page import SalesPage
from src.ui.receipts_page import ReceiptsPage
from src.ui.reports_page import ReportsPage
from src.ui.users_page import UsersPage

STORE_NAME = os.getenv("STORE_NAME", "My Supermarket")


class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, user: dict | None = None):
        super().__init__()
        self._user = user or {"username": "guest", "role": "staff"}
        self._is_logout = False
        self.setWindowTitle(f"{STORE_NAME} — Management")
        self.setMinimumSize(1060, 680)
        self._build_ui()
        self._setup_shortcuts()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──────────────────────────────────────────────
        topbar = QWidget()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(48)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(16, 0, 16, 0)
        store_lbl = QLabel(STORE_NAME.upper())
        store_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        user_lbl = QLabel(f"{self._user['username']}  [{self._user['role']}]")
        user_lbl.setStyleSheet("color: #ecf0f1; font-size: 12px;")
        tb_layout.addWidget(store_lbl)
        tb_layout.addStretch()
        tb_layout.addWidget(user_lbl)
        root.addWidget(topbar)

        # ── Body ─────────────────────────────────────────────────
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar container (nav list + logout button)
        sidebar_container = QWidget()
        sidebar_container.setObjectName("sidebarContainer")
        sidebar_container.setFixedWidth(170)
        sc_layout = QVBoxLayout(sidebar_container)
        sc_layout.setContentsMargins(0, 0, 0, 0)
        sc_layout.setSpacing(0)

        self._nav = QListWidget()
        self._nav.setObjectName("sidebar")
        nav_items = [
            ("Dashboard",  "Ctrl+1"),
            ("Products",   "Ctrl+2"),
            ("New Sale",   "Ctrl+3"),
            ("Receipts",   "Ctrl+4"),
            ("Reports",    "Ctrl+5"),
        ]
        if self._user.get("role") == "admin":
            nav_items.append(("Users", "Ctrl+6"))
        for label, hint in nav_items:
            item = QListWidgetItem(label)
            item.setToolTip(hint)
            self._nav.addItem(item)
        self._nav.setCursor(Qt.CursorShape.PointingHandCursor)
        self._nav.currentRowChanged.connect(self._switch_page)

        btn_logout = QPushButton("\u2192  Logout")
        btn_logout.setFixedHeight(40)
        btn_logout.clicked.connect(self._logout)
        btn_logout.setStyleSheet(
            "QPushButton { border: none; border-radius: 0;"
            " background: #2c3e50; color: #95a5a6; font-size: 13px;"
            " text-align: left; padding-left: 20px; }"
            "QPushButton:hover { background: #3d566e; color: #ecf0f1; }"
        )

        sc_layout.addWidget(self._nav)
        sc_layout.addWidget(btn_logout)

        # Page stack
        self._stack = QStackedWidget()
        self._dashboard = DashboardPage()
        self._products  = ProductsPage()
        self._sales     = SalesPage(store_name=STORE_NAME)
        self._receipts  = ReceiptsPage()
        self._reports   = ReportsPage()
        self._users     = UsersPage(current_user=self._user)

        self._pages = [
            self._dashboard,
            self._products,
            self._sales,
            self._receipts,
            self._reports,
            self._users,
        ]
        for page in self._pages:
            self._stack.addWidget(page)

        # Connect dashboard drill-down signal
        self._dashboard.navigate_to.connect(self._nav.setCurrentRow)

        body_layout.addWidget(sidebar_container)
        body_layout.addWidget(self._stack)
        root.addWidget(body)

        self._nav.setCurrentRow(0)

    def _setup_shortcuts(self):
        for key, idx in [("Ctrl+1", 0), ("Ctrl+2", 1), ("Ctrl+3", 2),
                         ("Ctrl+4", 3), ("Ctrl+5", 4), ("Ctrl+6", 5)]:
            QShortcut(QKeySequence(key), self,
                      activated=lambda i=idx: self._nav.setCurrentRow(i))

    def _switch_page(self, index: int):
        self._stack.setCurrentIndex(index)
        if index == 0:
            self._dashboard.refresh()

    def _logout(self):
        self._is_logout = True
        self.logout_requested.emit()
        self.close()

    def on_sale_completed(self):
        self._dashboard.refresh()
        self._products.refresh()
        self._receipts.refresh()

    def show_toast(self, message: str, severity: str = "info"):
        from src.ui.widgets.toast import Toast
        Toast(self, message, severity)

    def closeEvent(self, event):
        if not self._is_logout:
            from PyQt6.QtWidgets import QApplication
            QApplication.quit()
        event.accept()
