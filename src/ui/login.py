import os

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QWidget,
)
from PyQt6.QtCore import Qt

from src.services.auth_service import authenticate
from src.services import AuthError

STORE_NAME = os.getenv("STORE_NAME", "My Supermarket")


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setFixedSize(420, 470)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.user: dict | None = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Dark header ──────────────────────────────────────────
        header = QWidget()
        header.setObjectName("loginHeader")
        header.setFixedHeight(160)
        header.setStyleSheet("QWidget#loginHeader { background-color: #2c3e50; }")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(12, 8, 12, 16)

        # Close label top-right (avoids global QPushButton stylesheet override)
        close_row = QHBoxLayout()
        close_row.addStretch()
        lbl_close = QLabel("✕")
        lbl_close.setFixedSize(28, 28)
        lbl_close.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_close.setCursor(Qt.CursorShape.PointingHandCursor)
        lbl_close.setStyleSheet(
            "QLabel { color: #ecf0f1; font-size: 14px; border-radius: 4px;"
            " background: transparent; }"
            "QLabel:hover { background-color: #e74c3c; }"
        )
        lbl_close.mousePressEvent = lambda _: self.reject()
        close_row.addWidget(lbl_close)
        h_layout.addLayout(close_row)

        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        store_lbl = QLabel(STORE_NAME.upper())
        store_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        store_lbl.setStyleSheet(
            "color: #ffffff; font-size: 22px; font-weight: bold;"
            " letter-spacing: 2px; background: transparent;"
        )
        sub_lbl = QLabel("Management System")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet(
            "color: #7f8c8d; font-size: 12px; background: transparent;"
        )
        text_layout.addWidget(store_lbl)
        text_layout.addWidget(sub_lbl)
        h_layout.addLayout(text_layout)
        h_layout.addStretch()
        root.addWidget(header)

        # ── Form card ────────────────────────────────────────────
        card = QWidget()
        card.setObjectName("loginCard")
        card.setStyleSheet("QWidget#loginCard { background-color: #ffffff; }")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 40, 48, 40)
        card_layout.setSpacing(20)

        sign_in = QLabel("Sign in to your account")
        sign_in.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #2c3e50; background: transparent;"
        )
        card_layout.addWidget(sign_in)

        def _field_group(label_text: str, widget) -> QVBoxLayout:
            grp = QVBoxLayout()
            grp.setSpacing(4)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 12px; color: #7f8c8d; background: transparent;")
            grp.addWidget(lbl)
            grp.addWidget(widget)
            return grp

        # Username
        self._username = QLineEdit()
        self._username.setPlaceholderText("Enter your username")
        self._username.setFixedHeight(38)
        card_layout.addLayout(_field_group("Username", self._username))
        card_layout.addSpacing(20)

        # Password
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText("Enter your password")
        self._password.setFixedHeight(38)
        self._password.returnPressed.connect(self._on_login)
        card_layout.addLayout(_field_group("Password", self._password))

        # Error label
        self._error = QLabel()
        self._error.setStyleSheet(
            "color: #e74c3c; font-size: 12px; background: transparent;"
        )
        self._error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error.setWordWrap(True)
        card_layout.addWidget(self._error)

        # Login button
        btn = QPushButton("Sign In")
        btn.setFixedHeight(40)
        btn.setDefault(True)
        btn.clicked.connect(self._on_login)
        card_layout.addWidget(btn)

        root.addWidget(card)

    def _on_login(self):
        self._error.clear()
        try:
            self.user = authenticate(
                self._username.text().strip(), self._password.text()
            )
            self.accept()
        except AuthError as e:
            self._error.setText(str(e))
            self._password.clear()
            self._password.setFocus()
        except Exception as e:
            self._error.setText(f"Connection error: {e}")
