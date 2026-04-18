from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, QHeaderView,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from src.services.product_service import list_products


class ProductPickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_code: str | None = None
        self.setWindowTitle("Select Product")
        self.setMinimumSize(620, 420)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Search bar
        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by code, name or category…")
        self._search.setClearButtonEnabled(True)
        self._timer = QTimer(singleShot=True, interval=200)
        self._timer.timeout.connect(self._load)
        self._search.textChanged.connect(self._timer.start)
        search_row.addWidget(QLabel("Search:"))
        search_row.addWidget(self._search)
        layout.addLayout(search_row)

        # Table
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Code", "Name", "Category", "Price", "Stock"])
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(0, 90)
        self._table.setColumnWidth(2, 110)
        self._table.setColumnWidth(3, 80)
        self._table.setColumnWidth(4, 70)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(32)
        self._table.doubleClicked.connect(self._accept_selection)
        layout.addWidget(self._table)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("role", "secondary")
        btn_cancel.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_cancel.clicked.connect(self.reject)
        self._btn_select = QPushButton("Select")
        self._btn_select.setEnabled(False)
        self._btn_select.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._btn_select.clicked.connect(self._accept_selection)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self._btn_select)
        layout.addLayout(btn_row)

        self._table.itemSelectionChanged.connect(
            lambda: self._btn_select.setEnabled(bool(self._table.selectedItems()))
        )

    def _load(self):
        query = self._search.text().strip()
        products = list_products(query) if query else list_products()
        self._table.setRowCount(0)
        for i, p in enumerate(products):
            self._table.insertRow(i)
            self._table.setItem(i, 0, QTableWidgetItem(p.code))
            self._table.setItem(i, 1, QTableWidgetItem(p.name))
            self._table.setItem(i, 2, QTableWidgetItem(p.category))
            price_item = QTableWidgetItem(f"{p.price:.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(i, 3, price_item)
            qty_item = QTableWidgetItem(str(p.quantity))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if p.quantity == 0:
                qty_item.setForeground(QColor("#e74c3c"))
            elif p.quantity <= 5:
                qty_item.setForeground(QColor("#e67e22"))
            self._table.setItem(i, 4, qty_item)

    def _accept_selection(self):
        row = self._table.currentRow()
        if row < 0:
            return
        item = self._table.item(row, 0)
        if item:
            self.selected_code = item.text()
            self.accept()