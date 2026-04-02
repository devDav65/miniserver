import queue
import threading
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon

from server.app import create_app, load_config
from core.network import get_server_url

STYLE = """
QMainWindow, QWidget {
    background-color: #0d0d0f;
    color: #e8e8e8;
    font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
}
QFrame#sidebar {
    background-color: #111115;
    border-right: 1px solid #1e1e28;
    min-width: 200px;
    max-width: 200px;
}
QPushButton#nav-btn {
    background: transparent;
    color: #666680;
    border: none;
    text-align: left;
    padding: 11px 20px;
    font-size: 13px;
    border-radius: 0px;
}
QPushButton#nav-btn:hover {
    background-color: #1a1a22;
    color: #c0c0d8;
}
QPushButton#nav-btn[active=true] {
    background-color: #16161f;
    color: #00d4ff;
    border-left: 2px solid #00d4ff;
}
QFrame#header {
    background-color: #111115;
    border-bottom: 1px solid #1e1e28;
    min-height: 52px;
    max-height: 52px;
}
QLabel#logo {
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#status-badge {
    background-color: #0a2a1a;
    color: #00d4ff;
    border: 1px solid #00d4ff40;
    border-radius: 10px;
    padding: 2px 12px;
    font-size: 11px;
}
QFrame#content {
    background-color: #0d0d0f;
}
QFrame#statusbar {
    background-color: #111115;
    border-top: 1px solid #1e1e28;
    min-height: 26px;
    max-height: 26px;
}
QLabel#statusbar-text {
    color: #444460;
    font-size: 11px;
    font-family: 'SF Mono', 'Consolas', monospace;
}
"""


class EventBridge(QObject):
    """Pont thread-safe entre Flask et Qt (signaux Qt)."""
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
        # Timer Qt pour lire la queue toutes les 150ms
        self._timer = QTimer()
        self._timer.timeout.connect(self._poll_events)
        self._timer.start(150)

    def _build_ui(self):
        self.setWindowTitle("MiniServer")
        self.resize(900, 580)
        self.setMinimumSize(720, 480)
        self.setStyleSheet(STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("header")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)

        logo = QLabel("⬡  MINISERVER")
        logo.setObjectName("logo")
        h_layout.addWidget(logo)
        h_layout.addStretch()

        self.status_badge = QLabel("● EN LIGNE")
        self.status_badge.setObjectName("status-badge")
        h_layout.addWidget(self.status_badge)

        root_layout.addWidget(header)

        # ── Body (sidebar + content) ──────────────────────────
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(0, 16, 0, 16)
        side_layout.setSpacing(2)

        self.nav_buttons = []
        nav_items = [
            ("  Fichiers",     "files"),
            ("  Transferts",   "transfers"),
            ("  QR Code",      "qrcode"),
            ("  Paramètres",   "settings"),
        ]
        for label, name in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("nav-btn")
            btn.setProperty("page", name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, n=name: self._switch_page(n))
            side_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        side_layout.addStretch()

        # Version en bas de sidebar
        ver = QLabel("v1.0.0")
        ver.setStyleSheet("color: #333350; font-size: 10px; padding: 0 20px;")
        side_layout.addWidget(ver)

        body_layout.addWidget(self.sidebar)

        # Stack de pages
        self.stack = QStackedWidget()
        self.stack.setObjectName("content")

        from gui.tab_files     import FilesTab
        from gui.tab_transfers import TransfersTab
        from gui.tab_qrcode    import QRCodeTab
        from gui.tab_settings  import SettingsTab

        self.tab_files     = FilesTab(self.config)
        self.tab_transfers = TransfersTab()
        self.tab_qrcode    = QRCodeTab(self.config)
        self.tab_settings  = SettingsTab(self.config, self)

        self.stack.addWidget(self.tab_files)
        self.stack.addWidget(self.tab_transfers)
        self.stack.addWidget(self.tab_qrcode)
        self.stack.addWidget(self.tab_settings)

        body_layout.addWidget(self.stack)
        root_layout.addWidget(body)

        # ── Status bar ────────────────────────────────────────
        statusbar = QFrame()
        statusbar.setObjectName("statusbar")
        sb_layout = QHBoxLayout(statusbar)
        sb_layout.setContentsMargins(16, 0, 16, 0)
        self.sb_text = QLabel("")
        self.sb_text.setObjectName("statusbar-text")
        sb_layout.addWidget(self.sb_text)
        root_layout.addWidget(statusbar)

        self._switch_page("files")

    def _switch_page(self, name: str):
        pages = ["files", "transfers", "qrcode", "settings"]
        idx = pages.index(name) if name in pages else 0
        self.stack.setCurrentIndex(idx)
        for btn in self.nav_buttons:
            active = btn.property("page") == name
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _start_server(self):
        self.flask_app = create_app(self.config, self.event_queue)
        port = self.config["server"]["port"]

        def run():
            self.flask_app.run(
                host=self.config["server"]["host"],
                port=port,
                debug=False,
                use_reloader=False,
            )

        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()

        url = get_server_url(port)
        self.status_badge.setText(f"● EN LIGNE  {url}")
        self.sb_text.setText(f"Serveur actif → {url}")
        self.tab_qrcode.set_url(url)

    def _poll_events(self):
        try:
            while True:
                event = self.event_queue.get_nowait()
                self.bridge.new_event.emit(event)
        except queue.Empty:
            pass

    def _dispatch(self, event: dict):
        t = event.get("type")
        d = event.get("data", {})
        if t == "upload":
            self.tab_transfers.add_event("upload", d)
            self.tab_files.refresh(self.config["shared_folder"])
        elif t == "download":
            self.tab_transfers.add_event("download", d)
        elif t == "delete":
            self.tab_transfers.add_event("delete", d)
            self.tab_files.refresh(self.config["shared_folder"])
        elif t == "connection":
            self.tab_transfers.add_event("connection", d)

    def reload_config(self, new_config: dict):
        self.config = new_config
        url = get_server_url(new_config["server"]["port"])
        self.tab_qrcode.set_url(url)
        self.sb_text.setText(f"Config mise à jour → {url}")

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Quitter",
            "Arrêter le serveur et quitter ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def run_app():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = AppWindow()
    window.show()
    sys.exit(app.exec())