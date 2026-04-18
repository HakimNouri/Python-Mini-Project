from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QMessageBox, QHeaderView,
)
from PyQt6.QtCore import Qt

from src.services.auth_service import list_users, create_user, update_user, delete_user


class _UserDialog(QDialog):
    def __init__(self, parent=None, username: str = "", role: str = "staff"):
        super().__init__(parent)
        self._edit_mode = bool(username)
        self.setWindowTitle("Edit User" if self._edit_mode else "Add User")
        self.setFixedWidth(320)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._username = QLineEdit(username)
        self._username.setReadOnly(self._edit_mode)
        self._username.setPlaceholderText("username")
        form.addRow("Username:", self._username)

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText(
            "leave blank to keep current" if self._edit_mode else "required"
        )
        form.addRow("Password:", self._password)

        self._role = QComboBox()
        self._role.addItems(["staff", "admin"])
        self._role.setCurrentText(role)
        form.addRow("Role:", self._role)

        layout.addLayout(form)

        self._err = QLabel()
        self._err.setStyleSheet("color: #e74c3c; font-size: 12px;")
        layout.addWidget(self._err)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("role", "secondary")
        btn_cancel.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Save")
        btn_ok.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_ok.clicked.connect(self._validate)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _validate(self):
        username = self._username.text().strip()
        password = self._password.text()
        if not username:
            self._err.setText("Username is required.")
            return
        if not self._edit_mode and not password:
            self._err.setText("Password is required.")
            return
        self.accept()

    @property
    def values(self) -> tuple[str, str, str]:
        return (
            self._username.text().strip(),
            self._password.text(),
            self._role.currentText(),
        )


class UsersPage(QWidget):
    def __init__(self, current_user: dict | None = None, parent=None):
        super().__init__(parent)
        self._current_user = current_user or {}
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Users")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        btn_add = QPushButton("+ Add User")
        btn_add.clicked.connect(self._add)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_add)
        layout.addLayout(header)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Username", "Role", "Actions"])
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(1, 100)
        self._table.setColumnWidth(2, 160)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(36)
        layout.addWidget(self._table)

    def _load(self):
        self._table.setRowCount(0)
        for i, user in enumerate(list_users()):
            self._table.insertRow(i)
            self._table.setItem(i, 0, QTableWidgetItem(user["username"]))
            self._table.setItem(i, 1, QTableWidgetItem(user["role"].capitalize()))

            actions = QHBoxLayout()
            actions.setContentsMargins(4, 2, 4, 2)
            actions.setSpacing(6)

            btn_edit = QPushButton("Edit")
            btn_edit.setProperty("role", "secondary")
            btn_edit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn_edit.clicked.connect(
                lambda _, u=user["username"], r=user["role"]: self._edit(u, r)
            )

            btn_del = QPushButton("Delete")
            btn_del.setProperty("role", "danger")
            btn_del.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            is_self = user["username"] == self._current_user.get("username")
            btn_del.setEnabled(not is_self)
            btn_del.setToolTip("Cannot delete your own account" if is_self else "")
            btn_del.clicked.connect(lambda _, u=user["username"]: self._delete(u))

            actions.addWidget(btn_edit)
            actions.addWidget(btn_del)
            actions.addStretch()

            container = QWidget()
            container.setLayout(actions)
            self._table.setCellWidget(i, 2, container)

    def _add(self):
        dlg = _UserDialog(self)
        if dlg.exec() != _UserDialog.DialogCode.Accepted:
            return
        username, password, role = dlg.values
        try:
            create_user(username, password, role)
            self._load()
            self._toast(f"User '{username}' created.", "success")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _edit(self, username: str, role: str):
        dlg = _UserDialog(self, username=username, role=role)
        if dlg.exec() != _UserDialog.DialogCode.Accepted:
            return
        _, password, new_role = dlg.values
        update_user(username, password or None, new_role)
        self._load()
        self._toast(f"User '{username}' updated.", "success")

    def _delete(self, username: str):
        reply = QMessageBox.question(
            self, "Delete User",
            f"Delete user '{username}'? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_user(username)
            self._load()
            self._toast(f"User '{username}' deleted.", "info")

    def _toast(self, msg: str, severity: str = "info"):
        mw = self.window()
        if hasattr(mw, "show_toast"):
            mw.show_toast(msg, severity)
