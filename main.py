import sys
import os
from pathlib import Path

from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QPushButton
from PyQt6.QtCore import QTimer, Qt, QObject, QEvent

load_dotenv()


def _start(app: QApplication) -> None:
    from src.ui.login import LoginDialog
    login = LoginDialog()
    if login.exec() != LoginDialog.DialogCode.Accepted:
        app.quit()
        return

    from src.ui.main_window import MainWindow
    window = MainWindow(user=login.user)
    window.logout_requested.connect(lambda: QTimer.singleShot(0, lambda: _start(app)))
    window.show()


class _ButtonCursorFilter(QObject):
    def eventFilter(self, obj, event):
        if isinstance(obj, QPushButton):
            if event.type() == QEvent.Type.Enter:
                obj.setCursor(Qt.CursorShape.PointingHandCursor)
            elif event.type() == QEvent.Type.Leave:
                obj.unsetCursor()
        return False


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Supermarket Manager")
    app.setQuitOnLastWindowClosed(False)

    _filter = _ButtonCursorFilter(app)
    app.installEventFilter(_filter)

    qss_path = Path(__file__).parent / "assets" / "style.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    _start(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
