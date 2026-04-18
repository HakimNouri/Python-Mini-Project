from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
)
from PyQt6.QtGui import QFont


class ReceiptPreviewDialog(QDialog):
    def __init__(self, preview_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Receipt Preview")
        self.setMinimumSize(420, 480)
        self._build_ui(preview_text)

    def _build_ui(self, text: str):
        layout = QVBoxLayout(self)

        lbl = QLabel("Review the receipt before confirming the sale:")
        lbl.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(lbl)

        editor = QTextEdit()
        editor.setReadOnly(True)
        editor.setPlainText(text)
        editor.setFont(QFont("Courier New", 10))
        editor.setStyleSheet("background: #ffffff; border: 1px solid #dce1e7;")
        layout.addWidget(editor)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("role", "secondary")
        btn_cancel.clicked.connect(self.reject)

        btn_confirm = QPushButton("Confirm & Save")
        btn_confirm.setProperty("role", "success")
        btn_confirm.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_confirm)
        layout.addLayout(btn_row)
