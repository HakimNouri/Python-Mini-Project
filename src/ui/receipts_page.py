import os
from datetime import datetime, timezone

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDateEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QLineEdit, QSplitter, QTextEdit, QFrame, QHeaderView,
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont

from src.services.sale_service import list_sales
from src.services.receipt_service import RECEIPTS_DIR


class ReceiptsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path: str | None = None
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        # ── Title + receipt search ───────────────────────────────
        title_row = QHBoxLayout()
        title = QLabel("Receipts")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        self._receipt_search = QLineEdit()
        self._receipt_search.setPlaceholderText("Search receipt no…")
        self._receipt_search.setFixedWidth(180)
        self._receipt_search.textChanged.connect(self._filter_by_no)
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(QLabel("Receipt no:"))
        title_row.addWidget(self._receipt_search)
        layout.addLayout(title_row)

        # ── Quick presets ────────────────────────────────────────
        preset_row = QHBoxLayout()
        self._preset_btns: list[QPushButton] = []
        for label, handler in [
            ("Today",      self._preset_today),
            ("This Week",  self._preset_week),
            ("This Month", self._preset_month),
            ("All",        self._preset_all),
        ]:
            btn = QPushButton(label)
            btn.setProperty("role", "preset")
            btn.setCheckable(True)
            btn.clicked.connect(
                lambda _, b=btn, h=handler: self._activate_preset(b, h)
            )
            self._preset_btns.append(btn)
            preset_row.addWidget(btn)
        preset_row.addSpacing(16)

        # ── Date range ───────────────────────────────────────────
        self._date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self._date_from.setCalendarPopup(True)
        self._date_to = QDateEdit(QDate.currentDate())
        self._date_to.setCalendarPopup(True)
        btn_filter = QPushButton("Filter")
        btn_filter.clicked.connect(self._load)
        preset_row.addWidget(QLabel("From:"))
        preset_row.addWidget(self._date_from)
        preset_row.addWidget(QLabel("To:"))
        preset_row.addWidget(self._date_to)
        preset_row.addWidget(btn_filter)
        preset_row.addStretch()
        layout.addLayout(preset_row)

        # ── Splitter: table | preview panel ─────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: table
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["Receipt No", "Date", "Total (DZD)", "Payment", "Items"]
        )
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(0, 110)
        self._table.setColumnWidth(2, 110)
        self._table.setColumnWidth(3, 90)
        self._table.setColumnWidth(4, 60)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.cellClicked.connect(self._on_row_clicked)
        splitter.addWidget(self._table)

        # Right: preview panel
        preview_panel = QFrame()
        preview_panel.setStyleSheet("background: #ffffff; border-left: 1px solid #dce1e7;")
        pv_layout = QVBoxLayout(preview_panel)
        pv_layout.setContentsMargins(10, 10, 10, 10)

        pv_title = QLabel("Receipt Preview")
        pv_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #2c3e50;")
        pv_layout.addWidget(pv_title)

        self._preview_edit = QTextEdit()
        self._preview_edit.setReadOnly(True)
        self._preview_edit.setFont(QFont("Courier New", 10))
        self._preview_edit.setPlaceholderText("Click a row to preview the receipt…")
        self._preview_edit.setStyleSheet("border: none; background: #ffffff;")
        pv_layout.addWidget(self._preview_edit)

        self._open_btn = QPushButton("Open in Text Editor")
        self._open_btn.setProperty("role", "secondary")
        self._open_btn.setEnabled(False)
        self._open_btn.clicked.connect(self._open_in_editor)
        pv_layout.addWidget(self._open_btn)

        splitter.addWidget(preview_panel)
        splitter.setSizes([580, 340])
        layout.addWidget(splitter)

    # ── Presets ──────────────────────────────────────────────────
    def _activate_preset(self, btn: QPushButton, handler):
        for b in self._preset_btns:
            b.setChecked(False)
            b.style().unpolish(b)
            b.style().polish(b)
        btn.setChecked(True)
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        handler()

    def _preset_today(self):
        today = QDate.currentDate()
        self._date_from.setDate(today)
        self._date_to.setDate(today)
        self._load()

    def _preset_week(self):
        today = QDate.currentDate()
        self._date_from.setDate(today.addDays(-today.dayOfWeek() + 1))
        self._date_to.setDate(today)
        self._load()

    def _preset_month(self):
        today = QDate.currentDate()
        self._date_from.setDate(QDate(today.year(), today.month(), 1))
        self._date_to.setDate(today)
        self._load()

    def _preset_all(self):
        self._date_from.setDate(QDate(2000, 1, 1))
        self._date_to.setDate(QDate.currentDate())
        self._load()

    # ── Load data ─────────────────────────────────────────────────
    def refresh(self):
        self._load()

    def _load(self):
        d_from = self._date_from.date().toPyDate()
        d_to   = self._date_to.date().toPyDate()
        dt_from = datetime(d_from.year, d_from.month, d_from.day, tzinfo=timezone.utc)
        dt_to   = datetime(d_to.year, d_to.month, d_to.day, 23, 59, 59, tzinfo=timezone.utc)
        sales = list_sales(dt_from, dt_to)

        self._table.setRowCount(0)
        for i, sale in enumerate(sales):
            self._table.insertRow(i)
            self._table.setItem(i, 0, QTableWidgetItem(sale.receipt_no))
            self._table.setItem(i, 1, QTableWidgetItem(
                sale.date.strftime("%d-%m-%Y %H:%M")
            ))
            total_item = QTableWidgetItem(f"{sale.total:.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(i, 2, total_item)
            self._table.setItem(i, 3, QTableWidgetItem(sale.payment_method.capitalize()))
            self._table.setItem(i, 4, QTableWidgetItem(str(len(sale.items))))

        self._filter_by_no()

    # ── Receipt number filter ─────────────────────────────────────
    def _filter_by_no(self):
        text = self._receipt_search.text().strip().lower()
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            match = (not text) or (item and item.text().lower().startswith(text))
            self._table.setRowHidden(row, not match)

    # ── Row selection → preview ───────────────────────────────────
    def _on_row_clicked(self, row: int, _col: int):
        item = self._table.item(row, 0)
        if item:
            self._show_preview(item.text())

    def _show_preview(self, receipt_no: str):
        path = RECEIPTS_DIR / f"receipt_{receipt_no}.txt"
        if path.exists():
            self._preview_edit.setPlainText(path.read_text(encoding="utf-8"))
            self._current_path = str(path)
            self._open_btn.setEnabled(True)
        else:
            self._preview_edit.setPlainText("Receipt file not found on disk.")
            self._current_path = None
            self._open_btn.setEnabled(False)

    def _open_in_editor(self):
        if self._current_path:
            os.startfile(self._current_path)
