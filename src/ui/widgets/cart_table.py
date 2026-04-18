from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHBoxLayout, QHeaderView,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from src.models.sale import SaleItem


class CartTable(QWidget):
    cart_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[SaleItem] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Product", "Qty", "Unit Price", "Subtotal", ""])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(1, 60)
        self._table.setColumnWidth(2, 100)
        self._table.setColumnWidth(3, 100)
        self._table.setColumnWidth(4, 80)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)

        bottom = QHBoxLayout()
        self._total_label = QLabel("Total: 0.00 DZD")
        self._total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        bottom.addStretch()
        bottom.addWidget(self._total_label)

        layout.addWidget(self._table)
        layout.addLayout(bottom)

    def add_item(self, item: SaleItem) -> None:
        for existing in self._items:
            if existing.product_code == item.product_code:
                existing.quantity += item.quantity
                self._refresh()
                self.cart_changed.emit()
                return
        self._items.append(item)
        self._refresh()
        self.cart_changed.emit()

    def remove_item(self, row: int) -> None:
        if 0 <= row < len(self._items):
            self._items.pop(row)
            self._refresh()
            self.cart_changed.emit()

    def clear(self) -> None:
        self._items.clear()
        self._refresh()
        self.cart_changed.emit()

    def get_items(self) -> list[SaleItem]:
        return list(self._items)

    def get_total(self) -> float:
        return round(sum(i.subtotal for i in self._items), 2)

    def item_count(self) -> int:
        return len(self._items)

    def highlight_row(self, row: int, error: bool = True) -> None:
        bg = QColor("#fadbd8") if error else QColor("#ffffff")
        for col in range(self._table.columnCount() - 1):
            cell = self._table.item(row, col)
            if cell:
                cell.setBackground(bg)

    def _refresh(self) -> None:
        self._table.setRowCount(0)
        for i, item in enumerate(self._items):
            self._table.insertRow(i)
            self._table.setItem(i, 0, QTableWidgetItem(item.product_name))
            self._table.setItem(i, 1, QTableWidgetItem(str(item.quantity)))
            self._table.setItem(i, 2, QTableWidgetItem(f"{item.unit_price:.2f}"))
            self._table.setItem(i, 3, QTableWidgetItem(f"{item.subtotal:.2f}"))
            btn = QPushButton("Remove")
            btn.setProperty("role", "danger")
            btn.clicked.connect(lambda _, r=i: self.remove_item(r))
            self._table.setCellWidget(i, 4, btn)
        self._total_label.setText(f"Total: {self.get_total():.2f} DZD")
