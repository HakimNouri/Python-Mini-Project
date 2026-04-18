from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QComboBox, QRadioButton, QButtonGroup,
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.services.sale_service import monthly_revenue_by_day, top_products

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._plot()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title = QLabel("Monthly Sales Report")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # ── Controls ─────────────────────────────────────────────
        controls = QHBoxLayout()
        now = datetime.now()

        self._month_cb = QComboBox()
        self._month_cb.blockSignals(True)
        self._month_cb.addItems(MONTHS)
        self._month_cb.setCurrentIndex(now.month - 1)
        self._month_cb.blockSignals(False)
        self._month_cb.currentIndexChanged.connect(self._plot)

        self._year_spin = QSpinBox()
        self._year_spin.setRange(2020, 2100)
        self._year_spin.blockSignals(True)
        self._year_spin.setValue(now.year)
        self._year_spin.blockSignals(False)
        self._year_spin.valueChanged.connect(self._plot)

        # Chart type toggle
        self._chart_group = QButtonGroup(self)
        self._chart_bar  = QRadioButton("Bar")
        self._chart_line = QRadioButton("Line")
        self._chart_bar.setChecked(True)
        self._chart_group.addButton(self._chart_bar)
        self._chart_group.addButton(self._chart_line)
        self._chart_bar.toggled.connect(lambda chk: self._plot() if chk else None)

        controls.addWidget(QLabel("Month:"))
        controls.addWidget(self._month_cb)
        controls.addWidget(QLabel("Year:"))
        controls.addWidget(self._year_spin)
        controls.addSpacing(16)
        controls.addWidget(QLabel("Chart:"))
        controls.addWidget(self._chart_bar)
        controls.addWidget(self._chart_line)
        controls.addStretch()
        layout.addLayout(controls)

        # Summary
        self._summary = QLabel()
        self._summary.setStyleSheet("font-size: 12px; color: #555;")
        layout.addWidget(self._summary)

        # Revenue chart
        self._figure = Figure(figsize=(8, 3.2), tight_layout=True)
        self._canvas = FigureCanvas(self._figure)
        layout.addWidget(self._canvas)

        # Top-5 section
        top5_lbl = QLabel("Top 5 Products This Month")
        top5_lbl.setStyleSheet("font-size: 15px; font-weight: bold; margin-top: 6px;")
        layout.addWidget(top5_lbl)

        self._figure2 = Figure(figsize=(8, 2.4), tight_layout=True)
        self._canvas2 = FigureCanvas(self._figure2)
        layout.addWidget(self._canvas2)

    # ── Plot ──────────────────────────────────────────────────────
    def _plot(self):
        month = self._month_cb.currentIndex() + 1
        year  = self._year_spin.value()
        data  = monthly_revenue_by_day(year, month)

        days     = list(data.keys())
        revenues = list(data.values())

        # ─ Revenue chart ─
        self._figure.clear()
        ax = self._figure.add_subplot(111)

        if self._chart_bar.isChecked():
            bars = ax.bar(days, revenues, color="#3498db", edgecolor="#2980b9", width=0.7)
            for bar in bars:
                h = bar.get_height()
                if h > 0:
                    ax.annotate(
                        f"{h:.0f}",
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7, color="#555",
                    )
        else:
            ax.plot(days, revenues, color="#3498db", marker="o",
                    linewidth=2, markersize=4)
            ax.fill_between(days, revenues, alpha=0.1, color="#3498db")

        ax.set_xlabel("Day")
        ax.set_ylabel("Revenue (DZD)")
        ax.set_title(f"{MONTHS[month - 1]} {year}")
        ax.set_xticks(days)
        ax.grid(True, alpha=0.3)
        self._canvas.draw()

        # Summary line
        total   = sum(revenues)
        nonzero = [r for r in revenues if r > 0]
        avg     = total / len(nonzero) if nonzero else 0
        best_day = max(data, key=lambda d: data[d]) if nonzero else "—"
        best_val = data.get(best_day, 0) if nonzero else 0
        self._summary.setText(
            f"Month Total: {total:,.2f} DZD  |  "
            f"Avg Daily: {avg:,.2f} DZD  |  "
            f"Best Day: {best_day} ({best_val:,.2f} DZD)"
        )

        # ─ Top-5 products chart ─
        top5 = top_products(year, month, limit=5)
        self._figure2.clear()
        ax2 = self._figure2.add_subplot(111)

        if top5:
            names  = [d["_id"][:20] for d in reversed(top5)]
            totals = [d["total"]    for d in reversed(top5)]
            bars2 = ax2.barh(names, totals, color="#2ecc71", edgecolor="#27ae60", height=0.5)
            for bar in bars2:
                w = bar.get_width()
                if w > 0:
                    ax2.annotate(
                        f"{w:,.0f}",
                        xy=(w, bar.get_y() + bar.get_height() / 2),
                        xytext=(4, 0), textcoords="offset points",
                        va="center", fontsize=8,
                    )
            ax2.set_xlabel("Revenue (DZD)")
            ax2.set_title("Top 5 Products")
            ax2.grid(True, alpha=0.3, axis="x")
        else:
            ax2.text(0.5, 0.5, "No sales data for this period",
                     ha="center", va="center", transform=ax2.transAxes,
                     color="#7f8c8d", fontsize=11)
            ax2.set_title("Top 5 Products")
            ax2.axis("off")

        self._canvas2.draw()
