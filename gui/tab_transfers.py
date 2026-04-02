from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTextEdit
)
from PyQt6.QtGui import QFont, QColor, QTextCursor, QTextCharFormat, QCursor
from PyQt6.QtCore import Qt

STYLE = """
QWidget { background-color: #0d0d0f; }
QFrame#toolbar {
    background-color: #111115;
    border-bottom: 1px solid #1e1e28;
    min-height: 52px; max-height: 52px;
}
QLabel#title { color: #ffffff; font-size: 14px; font-weight: 600; }
QPushButton#clear-btn {
    background: transparent;
    color: #444460;
    border: 1px solid #1e1e28;
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 12px;
}
QPushButton#clear-btn:hover { color: #c8c8d8; border-color: #2a2a3a; }
QTextEdit {
    background-color: #0a0a0c;
    color: #c8c8d8;
    border: none;
    font-family: 'SF Mono', 'Consolas', 'JetBrains Mono', monospace;
    font-size: 12px;
    padding: 12px 16px;
    line-height: 1.6;
    selection-background-color: #1e1e2e;
}
QScrollBar:vertical {
    background: #0a0a0c;
    width: 5px;
}
QScrollBar::handle:vertical {
    background: #1e1e28;
    border-radius: 2px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

COLORS = {
    "upload":     "#00ff88",
    "download":   "#00d4ff",
    "delete":     "#ff4466",
    "connection": "#666680",
    "system":     "#444460",
}

ICONS = {
    "upload":     "↑ UPLOAD",
    "download":   "↓ DOWNLOAD",
    "delete":     "✕ DELETE",
    "connection": "→ CONNECT",
    "system":     "· SYSTEM",
}


class TransfersTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Toolbar ───────────────────────────────────────────
        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(20, 0, 20, 0)

        title = QLabel("Journal des transferts")
        title.setObjectName("title")
        tb.addWidget(title)
        tb.addStretch()

        self.event_count = QLabel("0 événement")
        self.event_count.setStyleSheet("color: #333350; font-size: 11px;")
        tb.addWidget(self.event_count)

        btn_clear = QPushButton("Effacer")
        btn_clear.setObjectName("clear-btn")
        btn_clear.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_clear.clicked.connect(self._clear)
        tb.addWidget(btn_clear)

        layout.addWidget(toolbar)

        # ── Log area ──────────────────────────────────────────
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self._count = 0
        self._add_line("system", "Serveur démarré — en attente de connexions…", "")

    def add_event(self, event_type: str, data: dict):
        time_str = datetime.now().strftime("%H:%M:%S")
        if event_type == "upload":
            msg = f"{data.get('ip','?')}  {data.get('filename','?')}  ({data.get('size',0)} o)"
        elif event_type == "download":
            msg = f"{data.get('ip','?')}  {data.get('filename','?')}"
        elif event_type == "delete":
            msg = f"{data.get('ip','?')}  {data.get('filename','?')}"
        elif event_type == "connection":
            msg = f"{data.get('ip','?')}"
        else:
            msg = str(data)
        self._add_line(event_type, msg, time_str)
        self._count += 1
        self.event_count.setText(f"{self._count} événement{'s' if self._count > 1 else ''}")

    def _add_line(self, event_type: str, msg: str, time_str: str):
        cursor = self.log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Timestamp
        if time_str:
            fmt_time = QTextCharFormat()
            fmt_time.setForeground(QColor("#2a2a3a"))
            cursor.setCharFormat(fmt_time)
            cursor.insertText(f"{time_str}  ")

        # Badge type
        fmt_badge = QTextCharFormat()
        color = COLORS.get(event_type, "#666680")
        fmt_badge.setForeground(QColor(color))
        badge_font = QFont("SF Mono", 11)
        badge_font.setWeight(QFont.Weight.Bold)
        fmt_badge.setFont(badge_font)
        cursor.setCharFormat(fmt_badge)
        cursor.insertText(ICONS.get(event_type, "·"))

        # Message
        fmt_msg = QTextCharFormat()
        fmt_msg.setForeground(QColor("#555570"))
        cursor.setCharFormat(fmt_msg)
        cursor.insertText(f"  {msg}\n")

        self.log.setTextCursor(cursor)
        self.log.ensureCursorVisible()

    def _clear(self):
        self.log.clear()
        self._count = 0
        self.event_count.setText("0 événement")
        self._add_line("system", "Journal effacé.", "")