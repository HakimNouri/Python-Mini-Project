from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import QTimer, QPropertyAnimation

_COLORS = {
    "info":    ("#3498db", "#ffffff"),
    "success": ("#27ae60", "#ffffff"),
    "warning": ("#f39c12", "#ffffff"),
    "error":   ("#e74c3c", "#ffffff"),
}


class Toast(QWidget):
    def __init__(self, parent: QWidget, message: str, severity: str = "info"):
        super().__init__(parent)
        bg, fg = _COLORS.get(severity, _COLORS["info"])

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        lbl = QLabel(message)
        lbl.setStyleSheet(f"color: {fg}; background: transparent; font-weight: bold; font-size: 13px;")
        layout.addWidget(lbl)

        self.setStyleSheet(f"background-color: {bg}; border-radius: 6px;")
        self.adjustSize()

        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setDuration(500)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self.deleteLater)

        self._reposition()
        self.show()
        self.raise_()
        QTimer.singleShot(2500, self._anim.start)

    def _reposition(self):
        p = self.parentWidget()
        if p:
            self.adjustSize()
            self.move(p.width() - self.width() - 24, p.height() - self.height() - 24)
