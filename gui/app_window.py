import queue
import threading
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QCursor

from server.app import create_app, load_config
from core.network import get_server_url
from gui.theme import get_colors


def _make_app_style(c: dict) -> str:
    return f"""
* {{
    font-family: {c['sans']};
}}
QMainWindow, QWidget {{
    background-color: {c['bg']};
    color: {c['text']};
}}

/* ── Sidebar ── */
QFrame#sidebar {{
    background-color: {c['surface']};
    border-right: 1px solid {c['border']};
    min-width: 216px;
    max-width: 216px;
}}
QPushButton#nav-btn {{
    background: transparent;
    color: {c['muted']};
    border: none;
    border-left: 2px solid transparent;
    text-align: left;
    padding: 10px 18px 10px 22px;
    font-size: 13px;
    font-weight: 500;
    border-radius: 0;
}}
QPushButton#nav-btn:hover {{
    background-color: {c['surface2']};
    color: {c['text2']};
}}
QPushButton#nav-btn[active=true] {{
    background-color: {c['surface2']};
    color: {c['accent']};
    border-left: 2px solid {c['accent']};
    padding-left: 20px;
    font-weight: 700;
}}

/* ── Header ── */
QFrame#header {{
    background-color: {c['surface']};
    border-bottom: 1px solid {c['border']};
    min-height: 54px;
    max-height: 54px;
}}
QLabel#logo {{
    color: {c['text']};
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.3px;
}}
QLabel#logo-dot {{
    color: {c['accent']};
    font-size: 20px;
    font-weight: 900;
}}
QLabel#status-pill {{
    background-color: {c['accent_dim']};
    color: {c['accent']};
    border: 1px solid {c['accent_mid']};
    border-radius: 10px;
    padding: 3px 14px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.3px;
    font-family: {c['mono']};
}}
QPushButton#theme-btn {{
    background: {c['surface2']};
    color: {c['muted']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 14px;
    min-width: 34px;
    max-width: 34px;
    min-height: 28px;
    max-height: 28px;
}}
QPushButton#theme-btn:hover {{
    background: {c['surface3']};
    color: {c['text']};
    border-color: {c['border2']};
}}

/* ── Statusbar ── */
QFrame#statusbar {{
    background-color: {c['surface']};
    border-top: 1px solid {c['border']};
    min-height: 26px;
    max-height: 26px;
}}
QLabel#sb-text {{
    color: {c['muted']};
    font-size: 11px;
    font-family: {c['mono']};
}}
QLabel#sb-dot {{
    color: {c['success']};
    font-size: 9px;
}}

/* ── Sidebar section label ── */
QLabel#nav-section {{
    color: {c['dimmer']};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.8px;
    padding: 0 22px;
}}
QLabel#nav-version {{
    color: {c['dimmer']};
    font-size: 10px;
    padding: 0 22px;
}}
"""


class EventBridge(QObject):
    new_event = pyqtSignal(dict)


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self._dark = True
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
        c = get_colors(self._dark)
        self.setWindowTitle("MiniServer")
        self.resize(1000, 640)
        self.setMinimumSize(780, 520)
        self.setStyleSheet(_make_app_style(c))

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header
        header = QFrame(); header.setObjectName("header")
        hl = QHBoxLayout(header); hl.setContentsMargins(24, 0, 20, 0); hl.setSpacing(8)

        logo_row = QHBoxLayout(); logo_row.setSpacing(2)
        dot = QLabel("·"); dot.setObjectName("logo-dot")
        logo = QLabel("MiniServer"); logo.setObjectName("logo")
        logo_row.addWidget(dot)
        logo_row.addWidget(logo)
        hl.addLayout(logo_row)
        hl.addStretch()

        self.status_pill = QLabel("● Démarrage…")
        self.status_pill.setObjectName("status-pill")
        hl.addWidget(self.status_pill)
        hl.addSpacing(8)

        self.theme_btn = QPushButton("☀")
        self.theme_btn.setObjectName("theme-btn")
        self.theme_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.theme_btn.setToolTip("Basculer le thème")
        self.theme_btn.clicked.connect(self._toggle_theme)
        hl.addWidget(self.theme_btn)
        root.addWidget(header)

        # ── Body
        body = QWidget()
        bl = QHBoxLayout(body); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(0)

        # Sidebar
        sidebar = QFrame(); sidebar.setObjectName("sidebar")
        self._sidebar = sidebar
        sl = QVBoxLayout(sidebar); sl.setContentsMargins(0, 22, 0, 20); sl.setSpacing(2)

        nav_section = QLabel("NAVIGATION"); nav_section.setObjectName("nav-section")
        sl.addWidget(nav_section)
        sl.addSpacing(10)

        self._nav_btns = []
        pages = [
            ("   Fichiers",    "files"),
            ("   Transferts",  "transfers"),
            ("   QR Code",     "qrcode"),
            ("   Paramètres",  "settings"),
        ]
        for label, name in pages:
            b = QPushButton(label); b.setObjectName("nav-btn")
            b.setProperty("page", name)
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.clicked.connect(lambda _, n=name: self._go(n))
            sl.addWidget(b); self._nav_btns.append(b)

        sl.addStretch()
        ver = QLabel("v1.0.0"); ver.setObjectName("nav-version")
        sl.addWidget(ver)
        bl.addWidget(sidebar)

        # Pages
        self.stack = QStackedWidget()
        from gui.tab_files     import FilesTab
        from gui.tab_transfers import TransfersTab
        from gui.tab_qrcode    import QRCodeTab
        from gui.tab_settings  import SettingsTab
        self.tab_files     = FilesTab(self.config, c)
        self.tab_transfers = TransfersTab(c)
        self.tab_qrcode    = QRCodeTab(self.config, c)
        self.tab_settings  = SettingsTab(self.config, self, c)
        for tab in [self.tab_files, self.tab_transfers, self.tab_qrcode, self.tab_settings]:
            self.stack.addWidget(tab)
        bl.addWidget(self.stack)
        root.addWidget(body)

        # ── Statusbar
        sb = QFrame(); sb.setObjectName("statusbar")
        sbl = QHBoxLayout(sb); sbl.setContentsMargins(20, 0, 20, 0); sbl.setSpacing(6)
        self.sb_dot = QLabel("●"); self.sb_dot.setObjectName("sb-dot")
        sbl.addWidget(self.sb_dot)
        self.sb_text = QLabel(""); self.sb_text.setObjectName("sb-text")
        sbl.addWidget(self.sb_text)
        sbl.addStretch()
        root.addWidget(sb)

        self._go("files")

    def _go(self, name: str):
        idx = ["files", "transfers", "qrcode", "settings"].index(name)
        self.stack.setCurrentIndex(idx)
        for b in self._nav_btns:
            active = b.property("page") == name
            b.setProperty("active", active)
            b.style().unpolish(b); b.style().polish(b)

    def _toggle_theme(self):
        self._dark = not self._dark
        self._apply_theme()

    def _apply_theme(self):
        c = get_colors(self._dark)
        self.setStyleSheet(_make_app_style(c))
        self.theme_btn.setText("☀" if self._dark else "🌙")
        for tab in [self.tab_files, self.tab_transfers, self.tab_qrcode, self.tab_settings]:
            tab.apply_theme(c)
        # Refresh nav button active states
        for b in self._nav_btns:
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
        if t in ("upload", "delete"):
            self.tab_transfers.add_event(t, d)
            self.tab_files.refresh(self.config["shared_folder"])
        elif t in ("download", "connection"):
            self.tab_transfers.add_event(t, d)

    def reload_config(self, cfg: dict):
        self.config = cfg
        url = get_server_url(cfg["server"]["port"])
        self.tab_qrcode.set_url(url)
        self.sb_text.setText(url)

    def closeEvent(self, e):
        r = QMessageBox.question(
            self, "Quitter", "Arrêter le serveur et quitter ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        e.accept() if r == QMessageBox.StandardButton.Yes else e.ignore()


def run_app():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = AppWindow(); w.show()
    sys.exit(app.exec())