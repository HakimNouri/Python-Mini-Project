import csv

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QLabel,
    QFileDialog, QHeaderView,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from src.services import DuplicateCodeError, ProductInUseError
from src.services.product_service import (
    add_product, update_product, delete_product, list_products, get_product,
)
from src.ui.widgets.product_form import ProductFormDialog

_SORT_KEYS = {
    0: lambda p: p.code.lower(),
    1: lambda p: p.name.lower(),
    2: lambda p: p.category.lower(),
    3: lambda p: p.price,
    4: lambda p: p.quantity,
}


class ProductsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sort_col = 1
        self._sort_asc = True
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)

        # ── Header ──────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("Products")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by code, name or category…")
        self._search.setFixedWidth(280)
        self._search_timer = QTimer(singleShot=True, interval=250)
        self._search_timer.timeout.connect(self._load)
        self._search.textChanged.connect(self._search_timer.start)

        self._count_label = QLabel()
        self._count_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")

        btn_add = QPushButton("+ Add Product")
        btn_add.clicked.connect(self._add)

        btn_export = QPushButton("Export CSV")
        btn_export.setProperty("role", "secondary")
        btn_export.clicked.connect(self._export_csv)

        btn_low = QPushButton("Low Stock")
        btn_low.setProperty("role", "secondary")
        btn_low.setCheckable(True)
        btn_low.toggled.connect(self._on_low_stock_toggle)
        self._btn_low = btn_low

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self._search)
        header.addWidget(self._count_label)
        header.addWidget(btn_low)
        header.addWidget(btn_export)
        header.addWidget(btn_add)
        layout.addLayout(header)

        self._err_label = QLabel()
        self._err_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
        layout.addWidget(self._err_label)

        # ── Table ────────────────────────────────────────────────
        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(
            ["Code", "Name", "Category", "Price", "Stock", "Edit", "Delete"]
        )
        hdr = self._table.horizontalHeader()
        hdr.setStretchLastSection(False)
        hdr.setSortIndicatorShown(True)
        hdr.sectionClicked.connect(self._on_header_click)
        hdr.setSortIndicator(self._sort_col, Qt.SortOrder.AscendingOrder)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self._table.setColumnWidth(0, 90)
        self._table.setColumnWidth(2, 130)
        self._table.setColumnWidth(3, 90)
        self._table.setColumnWidth(4, 80)
        self._table.setColumnWidth(5, 75)
        self._table.setColumnWidth(6, 80)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setDefaultSectionSize(36)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

    # ── Sorting ─────────────────────────────────────────────────
    def _on_header_click(self, col: int):
        if col >= 5:
            return
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        order = (Qt.SortOrder.AscendingOrder if self._sort_asc
                 else Qt.SortOrder.DescendingOrder)
        self._table.horizontalHeader().setSortIndicator(col, order)
        self._load()

    def _on_low_stock_toggle(self, checked: bool):
        self._load()

    # ── Data load ───────────────────────────────────────────────
    def refresh(self):
        self._load()

    def _load(self):
        self._err_label.clear()
        query = self._search.text().strip()
        products = list_products(query)

        if self._btn_low.isChecked():
            products = [p for p in products if 0 < p.quantity <= 5]

        if self._sort_col in _SORT_KEYS:
            products.sort(key=_SORT_KEYS[self._sort_col], reverse=not self._sort_asc)

        self._count_label.setText(f"{len(products)} product(s)")
        self._table.setRowCount(0)

        for i, p in enumerate(products):
            self._table.insertRow(i)
            self._table.setItem(i, 0, QTableWidgetItem(p.code))
            self._table.setItem(i, 1, QTableWidgetItem(p.name))
            self._table.setItem(i, 2, QTableWidgetItem(p.category))
            self._table.setItem(i, 3, QTableWidgetItem(f"{p.price:.2f}"))

            stock_item = QTableWidgetItem(str(p.quantity))
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if p.quantity == 0:
                stock_item.setBackground(QColor("#fadbd8"))
                stock_item.setForeground(QColor("#e74c3c"))
            elif p.quantity <= 5:
                stock_item.setBackground(QColor("#fef9e7"))
                stock_item.setForeground(QColor("#f39c12"))
            self._table.setItem(i, 4, stock_item)

            btn_edit = QPushButton("Edit")
            btn_edit.setProperty("role", "secondary")
            btn_edit.setContentsMargins(0, 4, 0, 4)
            btn_edit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn_edit.clicked.connect(lambda _, code=p.code: self._edit(code))
            self._table.setCellWidget(i, 5, btn_edit)

            btn_del = QPushButton("Delete")
            btn_del.setProperty("role", "danger")
            btn_del.setContentsMargins(0, 4, 0, 4)
            btn_del.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn_del.clicked.connect(lambda _, code=p.code, name=p.name: self._delete(code, name))
            self._table.setCellWidget(i, 6, btn_del)

    def _toast(self, msg: str, severity: str = "info"):
        mw = self.window()
        if hasattr(mw, "show_toast"):
            mw.show_toast(msg, severity)

    # ── CRUD ────────────────────────────────────────────────────
    def _add(self):
        self._err_label.clear()
        dlg = ProductFormDialog(self)
        if dlg.exec():
            try:
                add_product(dlg.get_product())
                self._load()
                self._toast("Product added successfully.", "success")
            except DuplicateCodeError as e:
                self._err_label.setText(str(e))

    def _edit(self, code: str):
        p = get_product(code)
        if not p:
            return
        dlg = ProductFormDialog(self, product=p)
        if dlg.exec():
            edited = dlg.get_product()
            update_product(
                code,
                name=edited.name,
                category=edited.category,
                price=edited.price,
                quantity=edited.quantity,
                description=edited.description,
            )
            self._load()
            self._toast("Product updated.", "success")

    def _delete(self, code: str, name: str):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete '{name}' ({code})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_product(code)
                self._load()
                self._toast("Product deleted.", "info")
            except ProductInUseError as e:
                QMessageBox.warning(self, "Cannot Delete", str(e))

    # ── CSV export ───────────────────────────────────────────────
    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Products", "products.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        products = list_products(self._search.text().strip())
        fields = ["code", "name", "category", "price", "quantity", "description"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for p in products:
                writer.writerow(p.to_doc())
        self._toast(f"Exported {len(products)} products to CSV.", "success")
