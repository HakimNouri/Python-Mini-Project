from datetime import datetime, timedelta, timezone

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QFrame,
    QLabel, QPushButton, QHBoxLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.database import get_products, get_sales
from src.services.sale_service import daily_revenue


class StatCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title: str, clickable: bool = False, parent=None):
        super().__init__(parent)
        self._clickable = clickable
        self.setObjectName("statCard")
        self.setMinimumSize(180, 110)
        if clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._value = QLabel("—")
        self._value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value.setStyleSheet("font-size: 30px; font-weight: bold; color: #2c3e50;")

        self._title = QLabel(title)
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet("font-size: 12px; color: #7f8c8d;")

        self._delta = QLabel()
        self._delta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._delta.setStyleSheet("font-size: 11px;")
        self._delta.hide()

        layout.addWidget(self._value)
        layout.addWidget(self._title)
        layout.addWidget(self._delta)

    def set_value(self, v):
        self._value.setText(str(v))

    def set_delta(self, pct: float | None):
        if pct is None:
            self._delta.hide()
            return
        self._delta.show()
        if pct >= 0:
            self._delta.setText(f"▲ +{pct:.1f}% vs yesterday")
            self._delta.setStyleSheet("font-size: 11px; color: #27ae60;")
        else:
            self._delta.setText(f"▼ {pct:.1f}% vs yesterday")
            self._delta.setStyleSheet("font-size: 11px; color: #e74c3c;")

    def mousePressEvent(self, event):
        if self._clickable:
            self.clicked.emit()
        super().mousePressEvent(event)


class DashboardPage(QWidget):
    navigate_to = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_refresh)
        layout.addLayout(header)

        # Low-stock banner
        self._banner = QFrame()
        self._banner.setObjectName("lowStockBanner")
        banner_row = QHBoxLayout(self._banner)
        banner_row.setContentsMargins(10, 6, 10, 6)
        self._banner_label = QLabel()
        self._banner_label.setStyleSheet("color: #7d6608; font-weight: bold;")
        banner_link = QPushButton("View Products →")
        banner_link.setProperty("role", "secondary")
        banner_link.setFixedHeight(26)
        banner_link.clicked.connect(lambda: self.navigate_to.emit(1))
        banner_row.addWidget(self._banner_label)
        banner_row.addStretch()
        banner_row.addWidget(banner_link)
        self._banner.hide()
        layout.addWidget(self._banner)

        # Stat cards
        grid = QGridLayout()
        grid.setSpacing(16)

        self._card_total   = StatCard("Total Products",       clickable=False)
        self._card_oos     = StatCard("Out of Stock",         clickable=True)
        self._card_sales   = StatCard("Today's Sales",        clickable=True)
        self._card_revenue = StatCard("Today's Revenue (DZD)", clickable=False)

        self._card_oos.clicked.connect(lambda: self.navigate_to.emit(1))
        self._card_sales.clicked.connect(lambda: self.navigate_to.emit(3))

        grid.addWidget(self._card_total,   0, 0)
        grid.addWidget(self._card_oos,     0, 1)
        grid.addWidget(self._card_sales,   1, 0)
        grid.addWidget(self._card_revenue, 1, 1)

        layout.addLayout(grid)
        layout.addStretch()

    def refresh(self):
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = now - timedelta(days=1)

        # Cards
        self._card_total.set_value(get_products().count_documents({}))
        self._card_oos.set_value(get_products().count_documents({"quantity": 0}))
        self._card_sales.set_value(
            get_sales().count_documents({"date": {"$gte": today_start}})
        )

        today_rev = daily_revenue(now)
        yest_rev  = daily_revenue(yesterday)
        self._card_revenue.set_value(f"{today_rev:.2f}")
        if yest_rev > 0:
            self._card_revenue.set_delta((today_rev - yest_rev) / yest_rev * 100)
        else:
            self._card_revenue.set_delta(None)

        # Low-stock banner
        low = get_products().count_documents({"quantity": {"$gt": 0, "$lte": 5}})
        if low > 0:
            self._banner_label.setText(
                f"⚠  {low} product(s) are running low on stock (≤ 5 units)."
            )
            self._banner.show()
        else:
            self._banner.hide()
