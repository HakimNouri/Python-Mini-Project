from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
    QSpinBox, QDialogButtonBox, QLabel, QVBoxLayout, QTextEdit,
)

from src.models.product import Product


class ProductFormDialog(QDialog):
    def __init__(self, parent=None, product: Product | None = None):
        super().__init__(parent)
        self._existing = product
        self.setWindowTitle("Edit Product" if product else "Add Product")
        self.setMinimumWidth(380)
        self._build_ui()
        if product:
            self._populate(product)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._code = QLineEdit()
        self._code_err = QLabel()
        self._code_err.setStyleSheet("color: #e74c3c; font-size: 11px;")

        self._name = QLineEdit()
        self._name_err = QLabel()
        self._name_err.setStyleSheet("color: #e74c3c; font-size: 11px;")

        self._category = QLineEdit()

        self._price = QDoubleSpinBox()
        self._price.setRange(0.01, 9_999_999.99)
        self._price.setDecimals(2)
        self._price_err = QLabel()
        self._price_err.setStyleSheet("color: #e74c3c; font-size: 11px;")

        self._qty = QSpinBox()
        self._qty.setRange(0, 9_999_999)

        self._desc = QTextEdit()
        self._desc.setFixedHeight(70)

        form.addRow("Code *", self._code)
        form.addRow("", self._code_err)
        form.addRow("Name *", self._name)
        form.addRow("", self._name_err)
        form.addRow("Category", self._category)
        form.addRow("Price (DZD) *", self._price)
        form.addRow("", self._price_err)
        form.addRow("Stock Qty", self._qty)
        form.addRow("Description", self._desc)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

        if self._existing:
            self._code.setReadOnly(True)
            self._code.setStyleSheet("background: #ecf0f1; color: #7f8c8d;")

    def _populate(self, p: Product):
        self._code.setText(p.code)
        self._name.setText(p.name)
        self._category.setText(p.category)
        self._price.setValue(p.price)
        self._qty.setValue(p.quantity)
        self._desc.setPlainText(p.description)

    def _on_accept(self):
        self._code_err.clear()
        self._name_err.clear()
        self._price_err.clear()
        self._code.setProperty("error", "false")
        self._name.setProperty("error", "false")
        self._price.setProperty("error", "false")
        self._restyle(self._code)
        self._restyle(self._name)

        try:
            self.get_product()
            self.accept()
        except ValueError as e:
            msg = str(e)
            if "code" in msg.lower():
                self._code_err.setText(msg)
                self._code.setProperty("error", "true")
                self._restyle(self._code)
                self._code.setFocus()
            elif "name" in msg.lower():
                self._name_err.setText(msg)
                self._name.setProperty("error", "true")
                self._restyle(self._name)
                self._name.setFocus()
            elif "price" in msg.lower():
                self._price_err.setText(msg)
                self._price.setFocus()

    @staticmethod
    def _restyle(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def get_product(self) -> Product:
        p = Product(
            code=self._code.text().strip(),
            name=self._name.text().strip(),
            category=self._category.text().strip(),
            price=self._price.value(),
            quantity=self._qty.value(),
            description=self._desc.toPlainText().strip(),
            _id=self._existing._id if self._existing else None,
        )
        p.validate()
        return p
