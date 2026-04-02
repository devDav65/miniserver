import queue
import threading
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QCursor, QIcon

from server.app import create_app, load_config
from core.network import get_server_url

DARK = {
    "bg":         "#0f0f13",
    "surface":    "#16161d",
    "surface2":   "#1c1c26",
    "border":     "#25252f",
    "accent":     "#6c8fff",
    "accent_dim": "#6c8fff22",
    "text":       "#e8e8f0",
    "muted":      "#5a5a72",
    "dimmer":     "#2e2e3a",
}

STYLE = f"""
* {{ font-family: 'Inter', 'SF Pro Display', 'Segoe UI', sans-serif; }}
QMainWindow, QWidget {{ background-color: {DARK['bg']}; color: {DARK['text']}; }}

/* ── Sidebar ── */
QFrame#sidebar {{
    background-color: {DARK['surface']};
    border-right: 1px solid {DARK['border']};
    min-width: 210px; max-width: 210px;
}}
QPushButton#nav-btn {{
    background: transparent;
    color: {DARK['muted']};
    border: none;
    text-align: left;
    padding: 10px 18px 10px 22px;
    font-size: 13px;
    border-radius: 0;
}}
QPushButton#nav-btn:hover {{
    background-color: {DARK['surface2']};
    color: {DARK['text']};
}}
QPushButton#nav-btn[active=true] {{
    background-color: {DARK['surface2']};
    color: {DARK['accent']};
    border-left: 2px solid {DARK['accent']};
    padding-left: 20px;
    font-weight: 600;
}}

/* ── Header ── */
QFrame#header {{
    background-color: {DARK['surface']};
    border-bottom: 1px solid {DARK['border']};
    min-height: 56px; max-height: 56px;
}}
QLabel#logo {{
    color: {DARK['text']};
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
QLabel#status-pill {{
    background-color: {DARK['accent_dim']};
    color: {DARK['accent']};
    border: 1px solid {DARK['accent']};
    border-radius: 10px;
    padding: 3px 12px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}

/* ── Statusbar ── */
QFrame#statusbar {{
    background-color: {DARK['surface']};
    border-top: 1px solid {DARK['border']};
    min-height: 28px; max-height: 28px;
}}
QLabel#sb-text {{
    color: {DARK['muted']};
    font-size: 11px;
    font-family: 'SF Mono', 'JetBrains Mono', 'Consolas', monospace;
}}

/* ── Sidebar section label ── */
QLabel#nav-section {{
    color: {DARK['dimmer']};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    padding: 0 22px;
}}
"""


class EventBridge(QObject):
    new_event = pyqtSignal(dict)


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.event_queue = queue.Queue()
        self.bridge = EventBridge()
        self.bridge.new_event.connect(self._dispatch)
        self._build_ui()
        self._start_server()
        self._timer = QTimer()
        self._timer.timeout.connect(self._poll_events)
        self._timer.start(150)

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowTitle("MiniServer")
        self.resize(980, 620)
        self.setMinimumSize(760, 500)
        self.setStyleSheet(STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame(); header.setObjectName("header")
        hl = QHBoxLayout(header); hl.setContentsMargins(22, 0, 22, 0)
        logo = QLabel("MiniServer"); logo.setObjectName("logo")
        hl.addWidget(logo)
        hl.addStretch()
        self.status_pill = QLabel("● Démarrage…")
        self.status_pill.setObjectName("status-pill")
        hl.addWidget(self.status_pill)
        root.addWidget(header)

        # Body
        body = QWidget()
        bl = QHBoxLayout(body); bl.setContentsMargins(0,0,0,0); bl.setSpacing(0)

        # Sidebar
        sidebar = QFrame(); sidebar.setObjectName("sidebar")
        sl = QVBoxLayout(sidebar); sl.setContentsMargins(0,20,0,20); sl.setSpacing(2)

        nav_section = QLabel("NAVIGATION"); nav_section.setObjectName("nav-section")
        sl.addWidget(nav_section)
        sl.addSpacing(8)

        self._nav_btns = []
        pages = [("  Fichiers",   "files"),
                 ("  Transferts", "transfers"),
                 ("  QR Code",    "qrcode"),
                 ("  Paramètres", "settings")]
        for label, name in pages:
            b = QPushButton(label); b.setObjectName("nav-btn")
            b.setProperty("page", name)
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.clicked.connect(lambda _, n=name: self._go(n))
            sl.addWidget(b); self._nav_btns.append(b)

        sl.addStretch()
        ver = QLabel("v1.0.0")
        ver.setStyleSheet(f"color:{DARK['dimmer']}; font-size:10px; padding:0 22px;")
        sl.addWidget(ver)
        bl.addWidget(sidebar)

        # Pages
        self.stack = QStackedWidget()
        from gui.tab_files     import FilesTab
        from gui.tab_transfers import TransfersTab
        from gui.tab_qrcode    import QRCodeTab
        from gui.tab_settings  import SettingsTab
        self.tab_files     = FilesTab(self.config)
        self.tab_transfers = TransfersTab()
        self.tab_qrcode    = QRCodeTab(self.config)
        self.tab_settings  = SettingsTab(self.config, self)
        for tab in [self.tab_files, self.tab_transfers, self.tab_qrcode, self.tab_settings]:
            self.stack.addWidget(tab)
        bl.addWidget(self.stack)
        root.addWidget(body)

        # Statusbar
        sb = QFrame(); sb.setObjectName("statusbar")
        sbl = QHBoxLayout(sb); sbl.setContentsMargins(18,0,18,0)
        self.sb_text = QLabel(""); self.sb_text.setObjectName("sb-text")
        sbl.addWidget(self.sb_text)
        root.addWidget(sb)

        self._go("files")

    def _go(self, name: str):
        idx = ["files","transfers","qrcode","settings"].index(name)
        self.stack.setCurrentIndex(idx)
        for b in self._nav_btns:
            active = b.property("page") == name
            b.setProperty("active", active)
            b.style().unpolish(b); b.style().polish(b)

    # ── Server ────────────────────────────────────────────────

    def _start_server(self):
        self.flask_app = create_app(self.config, self.event_queue)
        port = self.config["server"]["port"]
        threading.Thread(
            target=lambda: self.flask_app.run(
                host=self.config["server"]["host"], port=port,
                debug=False, use_reloader=False),
            daemon=True).start()
        url = get_server_url(port)
        self.status_pill.setText(f"● En ligne  {url}")
        self.sb_text.setText(url)
        self.tab_qrcode.set_url(url)

    def _poll_events(self):
        try:
            while True:
                self.bridge.new_event.emit(self.event_queue.get_nowait())
        except queue.Empty:
            pass

    def _dispatch(self, event: dict):
        t, d = event.get("type"), event.get("data", {})
        if t in ("upload","delete"):
            self.tab_transfers.add_event(t, d)
            self.tab_files.refresh(self.config["shared_folder"])
        elif t in ("download","connection"):
            self.tab_transfers.add_event(t, d)

    def reload_config(self, cfg: dict):
        self.config = cfg
        url = get_server_url(cfg["server"]["port"])
        self.tab_qrcode.set_url(url)
        self.sb_text.setText(url)

    def closeEvent(self, e):
        r = QMessageBox.question(self, "Quitter", "Arrêter le serveur et quitter ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        e.accept() if r == QMessageBox.StandardButton.Yes else e.ignore()


def run_app():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = AppWindow(); w.show()
    sys.exit(app.exec())