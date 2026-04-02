from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QTextEdit
)
from PyQt6.QtGui import QColor, QTextCursor, QTextCharFormat, QFont, QCursor
from PyQt6.QtCore import Qt

BG      = "#0f0f13"
SURFACE = "#16161d"
BORDER  = "#25252f"
ACCENT  = "#6c8fff"
TEXT    = "#e8e8f0"
MUTED   = "#5a5a72"

EVT_COLORS = {
    "upload":     "#4ade80",
    "download":   "#60a5fa",
    "delete":     "#f87171",
    "connection": "#94a3b8",
    "system":     "#3a3a4e",
}
EVT_LABELS = {
    "upload":     "UPLOAD",
    "download":   "DOWNLOAD",
    "delete":     "DELETE",
    "connection": "CONNECT",
    "system":     "SYSTEM",
}

STYLE = f"""
QWidget {{ background-color: {BG}; }}
QFrame#toolbar {{
    background-color: {SURFACE};
    border-bottom: 1px solid {BORDER};
    min-height: 56px; max-height: 56px;
}}
QLabel#title  {{ color: {TEXT}; font-size: 15px; font-weight: 600; }}
QLabel#evtcount {{ color: {MUTED}; font-size: 12px; }}
QPushButton#clear-btn {{
    background: transparent; color: {MUTED};
    border: 1px solid {BORDER}; border-radius: 6px;
    padding: 6px 16px; font-size: 12px;
}}
QPushButton#clear-btn:hover {{ color: {TEXT}; border-color: #3a3a4e; }}
QTextEdit {{
    background-color: {BG}; color: #9090a8; border: none;
    font-family: 'JetBrains Mono','SF Mono','Consolas',monospace;
    font-size: 12px; padding: 14px 20px; line-height: 1.6;
    selection-background-color: #1c1c26;
}}
QScrollBar:vertical {{ background:{BG}; width:4px; }}
QScrollBar::handle:vertical {{ background:{BORDER}; border-radius:2px; min-height:20px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
"""

class TransfersTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(STYLE)
        self._count = 0
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        tb = QFrame(); tb.setObjectName("toolbar")
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(22,0,22,0); tbl.setSpacing(12)
        QLabel("Journal des transferts", objectName="title").setParent(tb)
        title = QLabel("Journal des transferts"); title.setObjectName("title"); tbl.addWidget(title)
        self.cnt_lbl = QLabel("0 événement"); self.cnt_lbl.setObjectName("evtcount"); tbl.addWidget(self.cnt_lbl)
        tbl.addStretch()
        btn = QPushButton("Effacer"); btn.setObjectName("clear-btn")
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.clicked.connect(self._clear); tbl.addWidget(btn)
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
        self.cnt_lbl.setText(f"{self._count} événement{'s' if self._count>1 else ''}")

    def _write(self, evt: str, msg: str, ts: str):
        c = self.log.textCursor()
        c.movePosition(QTextCursor.MoveOperation.End)

        # Timestamp
        if ts:
            fmt = QTextCharFormat(); fmt.setForeground(QColor("#2e2e40"))
            c.setCharFormat(fmt); c.insertText(f"{ts}   ")

        # Badge
        color = EVT_COLORS.get(evt, MUTED)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        f = QFont(); f.setWeight(QFont.Weight.Bold); fmt.setFont(f)
        c.setCharFormat(fmt)
        c.insertText(f"{EVT_LABELS.get(evt,'·'):<10}")

        # Message
        fmt = QTextCharFormat(); fmt.setForeground(QColor("#5a5a78"))
        c.setCharFormat(fmt); c.insertText(f" {msg}\n")

        self.log.setTextCursor(c)
        self.log.ensureCursorVisible()

    def _clear(self):
        self.log.clear(); self._count = 0
        self.cnt_lbl.setText("0 événement")
        self._write("system", "Journal effacé.", "")