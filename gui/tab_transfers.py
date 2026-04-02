from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QTextEdit
)
from PyQt6.QtGui import QColor, QTextCursor, QTextCharFormat, QFont, QCursor
from PyQt6.QtCore import Qt

from gui.theme import get_colors


EVT_LABELS = {
    "upload":     "UPLOAD",
    "download":   "DOWNLOAD",
    "delete":     "DELETE",
    "connection": "CONNECT",
    "system":     "SYSTEM",
}

# Event colors are semantic and consistent across themes
EVT_COLORS_DARK = {
    "upload":     "#4ade80",
    "download":   "#60a5fa",
    "delete":     "#f87171",
    "connection": "#94a3b8",
    "system":     "#3a3a58",
}
EVT_COLORS_LIGHT = {
    "upload":     "#15803d",
    "download":   "#2563eb",
    "delete":     "#dc2626",
    "connection": "#64748b",
    "system":     "#9090b8",
}


def _make_style(c: dict) -> str:
    return f"""
QWidget {{
    background-color: {c['bg']};
    font-family: {c['sans']};
}}
QFrame#toolbar {{
    background-color: {c['surface']};
    border-bottom: 1px solid {c['border']};
    min-height: 54px;
    max-height: 54px;
}}
QLabel#title {{
    color: {c['text']};
    font-size: 14px;
    font-weight: 700;
}}
QLabel#evtcount {{
    color: {c['muted']};
    font-size: 11px;
    background: {c['surface2']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 2px 10px;
}}
QPushButton#clear-btn {{
    background: transparent;
    color: {c['muted']};
    border: 1px solid {c['border']};
    border-radius: 7px;
    padding: 6px 18px;
    font-size: 12px;
    font-weight: 500;
}}
QPushButton#clear-btn:hover {{
    color: {c['text']};
    border-color: {c['border2']};
    background: {c['surface2']};
}}
QTextEdit {{
    background-color: {c['bg']};
    color: {c['text2']};
    border: none;
    font-family: {c['mono']};
    font-size: 12px;
    padding: 16px 22px;
    selection-background-color: {c['surface3']};
}}
QScrollBar:vertical {{
    background: {c['bg']};
    width: 5px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {c['border2']};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


class TransfersTab(QWidget):
    def __init__(self, colors: dict = None):
        super().__init__()
        self._c = colors or get_colors(True)
        self._dark = True
        self._count = 0
        self.setStyleSheet(_make_style(self._c))
        self._build()

    def apply_theme(self, colors: dict):
        self._dark = colors.get("bg", "#0b0b0f") == get_colors(True)["bg"]
        self._c = colors
        self.setStyleSheet(_make_style(colors))

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Toolbar
        tb = QFrame(); tb.setObjectName("toolbar")
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(24, 0, 20, 0); tbl.setSpacing(10)

        title = QLabel("Journal des transferts"); title.setObjectName("title")
        tbl.addWidget(title)

        self.cnt_lbl = QLabel("0 événement")
        self.cnt_lbl.setObjectName("evtcount")
        tbl.addWidget(self.cnt_lbl)
        tbl.addStretch()

        btn = QPushButton("Effacer"); btn.setObjectName("clear-btn")
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.clicked.connect(self._clear)
        tbl.addWidget(btn)
        lay.addWidget(tb)

        self.log = QTextEdit(); self.log.setReadOnly(True)
        lay.addWidget(self.log)
        self._write("system", "Serveur démarré — en attente de connexions…", "")

    def add_event(self, evt: str, data: dict):
        ts = datetime.now().strftime("%H:%M:%S")
        if evt == "upload":
            msg = f"{data.get('ip','?')}  ·  {data.get('filename','?')}  ({data.get('size',0)} o)"
        elif evt == "download":
            msg = f"{data.get('ip','?')}  ·  {data.get('filename','?')}"
        elif evt == "delete":
            msg = f"{data.get('ip','?')}  ·  {data.get('filename','?')}"
        else:
            msg = f"{data.get('ip','?')}"
        self._write(evt, msg, ts)
        self._count += 1
        self.cnt_lbl.setText(f"{self._count} événement{'s' if self._count > 1 else ''}")

    def _write(self, evt: str, msg: str, ts: str):
        c = self.log.textCursor()
        c.movePosition(QTextCursor.MoveOperation.End)

        evt_colors = EVT_COLORS_DARK if self._c["bg"] < "#808080" else EVT_COLORS_LIGHT

        # Timestamp
        if ts:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(self._c["dimmer"]))
            c.setCharFormat(fmt)
            c.insertText(f"{ts}   ")

        # Badge
        color = evt_colors.get(evt, self._c["muted"])
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        f = QFont(); f.setWeight(QFont.Weight.Bold); fmt.setFont(f)
        c.setCharFormat(fmt)
        c.insertText(f"{EVT_LABELS.get(evt, '·'):<10}")

        # Message
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self._c["text2"]))
        c.setCharFormat(fmt)
        c.insertText(f" {msg}\n")

        self.log.setTextCursor(c)
        self.log.ensureCursorVisible()

    def _clear(self):
        self.log.clear()
        self._count = 0
        self.cnt_lbl.setText("0 événement")
        self._write("system", "Journal effacé.", "")