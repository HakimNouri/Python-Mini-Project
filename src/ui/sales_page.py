import os
from datetime import datetime, timezone

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSpinBox, QDoubleSpinBox, QLabel, QMessageBox,
    QRadioButton, QButtonGroup, QFrame, QDialog,
)
from PyQt6.QtCore import Qt

from src.models.sale import Sale, SaleItem
from src.models.product import Product
from src.services import InsufficientStockError
from src.services.product_service import get_product
from src.services.sale_service import process_sale
from src.services.receipt_service import generate, receipt_text
from src.ui.widgets.cart_table import CartTable
from src.ui.widgets.receipt_preview import ReceiptPreviewDialog
from src.ui.widgets.product_picker import ProductPickerDialog


class _AddToCartDialog(QDialog):
    def __init__(self, product: Product, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add to Cart")
        self.setFixedWidth(300)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        name_lbl = QLabel(product.name)
        name_lbl.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(name_lbl)

        stock_lbl = QLabel(f"In stock: {product.quantity}")
        stock_lbl.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(stock_lbl)

        price_row = QHBoxLayout()
        price_row.addWidget(QLabel("Price (DZD):"))
        self._price = QDoubleSpinBox()
        self._price.setRange(0.01, 999_999.99)
        self._price.setDecimals(2)
        self._price.setValue(product.price)
        self._price.setFixedWidth(110)
        price_row.addWidget(self._price)
        price_row.addStretch()
        layout.addLayout(price_row)

        qty_row = QHBoxLayout()
        qty_row.addWidget(QLabel("Quantity:"))
        self._qty = QSpinBox()
        self._qty.setRange(1, max(1, product.quantity))
        self._qty.setValue(1)
        self._qty.setFixedWidth(90)
        qty_row.addWidget(self._qty)
        qty_row.addStretch()
        layout.addLayout(qty_row)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("role", "secondary")
        btn_cancel.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_cancel.clicked.connect(self.reject)
        btn_add = QPushButton("Add to Cart")
        btn_add.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_add.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_add)
        layout.addLayout(btn_row)

        if product.quantity == 0:
            btn_add.setEnabled(False)

    @property
    def quantity(self) -> int:
        return self._qty.value()

    @property
    def price(self) -> float:
        return self._price.value()


class SalesPage(QWidget):
    def __init__(self, store_name: str = "SUPERMARKET", parent=None):
        super().__init__(parent)
        self._store_name = store_name
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        # ── Header ───────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("New Sale")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        btn_add_product = QPushButton("+ Add Product")
        btn_add_product.clicked.connect(self._add_product)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_add_product)
        layout.addLayout(header)

        # ── Cart table ───────────────────────────────────────────
        self._cart = CartTable(self)
        self._cart.cart_changed.connect(self._on_cart_changed)
        layout.addWidget(self._cart)

        # ── Payment method ───────────────────────────────────────
        pay_frame = QFrame()
        pay_layout = QHBoxLayout(pay_frame)
        pay_layout.setContentsMargins(0, 0, 0, 0)
        pay_layout.addWidget(QLabel("Payment:"))
        self._payment_group = QButtonGroup(self)
        for method in ("Cash", "Card", "Other"):
            rb = QRadioButton(method)
            self._payment_group.addButton(rb)
            pay_layout.addWidget(rb)
        self._payment_group.buttons()[0].setChecked(True)
        pay_layout.addStretch()
        layout.addWidget(pay_frame)

        # ── Bottom bar ───────────────────────────────────────────
        bottom = QHBoxLayout()
        btn_clear = QPushButton("Clear Cart")
        btn_clear.setProperty("role", "secondary")
        btn_clear.clicked.connect(self._cart.clear)

        self._summary_label = QLabel("Cart is empty")
        self._summary_label.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #2c3e50;"
        )

        self._btn_confirm = QPushButton("Confirm Sale")
        self._btn_confirm.setProperty("role", "success")
        self._btn_confirm.setFixedHeight(36)
        self._btn_confirm.setEnabled(False)
        self._btn_confirm.clicked.connect(self._confirm)

        bottom.addWidget(btn_clear)
        bottom.addStretch()
        bottom.addWidget(self._summary_label)
        bottom.addSpacing(20)
        bottom.addWidget(self._btn_confirm)
        layout.addLayout(bottom)

    # ── Add product flow ──────────────────────────────────────────
    def _add_product(self):
        picker = ProductPickerDialog(self)
        if picker.exec() != ProductPickerDialog.DialogCode.Accepted:
            return
        p = get_product(picker.selected_code)
        if not p:
            return
        qty_dlg = _AddToCartDialog(p, self)
        if qty_dlg.exec() != _AddToCartDialog.DialogCode.Accepted:
            return
        self._cart.add_item(SaleItem(
            product_code=p.code,
            product_name=p.name,
            unit_price=qty_dlg.price,
            quantity=qty_dlg.quantity,
        ))

    # ── Helpers ───────────────────────────────────────────────────
    def _get_payment_method(self) -> str:
        for btn in self._payment_group.buttons():
            if btn.isChecked():
                return btn.text().lower()
        return "cash"

    def _toast(self, msg: str, severity: str = "info"):
        mw = self.window()
        if hasattr(mw, "show_toast"):
            mw.show_toast(msg, severity)

    def _on_cart_changed(self):
        count = self._cart.item_count()
        total = self._cart.get_total()
        if count:
            self._summary_label.setText(f"{count} item(s)  •  Total: {total:.2f} DZD")
            self._btn_confirm.setEnabled(True)
        else:
            self._summary_label.setText("Cart is empty")
            self._btn_confirm.setEnabled(False)

    # ── Confirm sale ──────────────────────────────────────────────
    def _confirm(self):
        items = self._cart.get_items()
        if not items:
            return

        payment = self._get_payment_method()
        total = self._cart.get_total()

        preview_sale = Sale(
            receipt_no="PREVIEW",
            date=datetime.now(timezone.utc),
            items=items,
            total=total,
            payment_method=payment,
        )
        preview = ReceiptPreviewDialog(
            receipt_text(preview_sale, self._store_name), self
        )
        if preview.exec() != ReceiptPreviewDialog.DialogCode.Accepted:
            return

        try:
            sale = process_sale(items, payment_method=payment)
            path = generate(sale, self._store_name)
            self._cart.clear()
            mw = self.window()
            if hasattr(mw, "on_sale_completed"):
                mw.on_sale_completed()
            self._toast(f"Sale #{sale.receipt_no} saved. Receipt: {path}", "success")

            msg = QMessageBox(self)
            msg.setWindowTitle("Sale Complete")
            msg.setText(f"Receipt #{sale.receipt_no} saved.\n\n{path}")
            msg.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
            open_btn = msg.addButton("Open Receipt", QMessageBox.ButtonRole.ActionRole)
            msg.exec()
            if msg.clickedButton() == open_btn:
                os.startfile(path)

        except InsufficientStockError as e:
            for i, item in enumerate(self._cart.get_items()):
                if item.product_code == e.code:
                    self._cart.highlight_row(i, error=True)
            QMessageBox.warning(self, "Insufficient Stock", str(e))
