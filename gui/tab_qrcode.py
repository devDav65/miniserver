import threading, webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QPixmap, QCursor

from gui.theme import get_colors


def _make_style(c: dict) -> str:
    return f"""
QWidget {{
    background-color: {c['bg']};
    font-family: {c['sans']};
}}
QLabel#page-title {{
    color: {c['text']};
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.3px;
}}
QLabel#page-sub {{
    color: {c['muted']};
    font-size: 12px;
    font-weight: 400;
}}
QLabel#url-chip {{
    color: {c['accent']};
    background: {c['accent_dim']};
    border: 1px solid {c['accent_mid']};
    border-radius: 10px;
    padding: 9px 22px;
    font-family: {c['mono']};
    font-size: 13px;
}}
QLabel#qr-box {{
    background: #ffffff;
    border-radius: 18px;
    padding: 18px;
}}
QPushButton#btn-accent {{
    background: {c['accent_dim']};
    color: {c['accent']};
    border: 1px solid {c['accent_mid']};
    border-radius: 9px;
    padding: 10px 26px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#btn-accent:hover {{
    background: {c['accent_mid']};
    border-color: {c['accent']};
}}
QPushButton#btn-ghost {{
    background: transparent;
    color: {c['muted']};
    border: 1px solid {c['border2']};
    border-radius: 9px;
    padding: 10px 26px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#btn-ghost:hover {{
    color: {c['text']};
    border-color: {c['border2']};
    background: {c['surface2']};
}}
"""


class _Sig(QObject):
    done = pyqtSignal(bytes)
    fail = pyqtSignal(str)


class QRCodeTab(QWidget):
    def __init__(self, config, colors: dict = None):
        super().__init__()
        self.config = config
        self.url = ""
        self._c = colors or get_colors(True)
        self.setStyleSheet(_make_style(self._c))
        self._build()

    def apply_theme(self, colors: dict):
        self._c = colors
        self.setStyleSheet(_make_style(colors))

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(0)
        lay.setContentsMargins(48, 56, 48, 56)

        # Title block
        title = QLabel("Scanner pour se connecter")
        title.setObjectName("page-title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        lay.addSpacing(6)
        sub = QLabel("Tous les appareils sur le même Wi-Fi peuvent se connecter")
        sub.setObjectName("page-sub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)

        lay.addSpacing(24)

        # URL chip
        self.url_chip = QLabel("En attente…")
        self.url_chip.setObjectName("url-chip")
        self.url_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.url_chip.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.url_chip.mousePressEvent = lambda _: webbrowser.open(self.url) if self.url else None
        lay.addWidget(self.url_chip, alignment=Qt.AlignmentFlag.AlignCenter)

        lay.addSpacing(28)

        # QR code display
        self.qr_lbl = QLabel()
        self.qr_lbl.setObjectName("qr-box")
        self.qr_lbl.setFixedSize(236, 236)
        self.qr_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_lbl.setText("Génération…")
        self.qr_lbl.setStyleSheet(
            "QLabel { background:#ffffff; border-radius:18px; color:#b0b0b0; font-size:12px; }"
        )
        lay.addWidget(self.qr_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        lay.addSpacing(32)

        # Action buttons
        btns = QHBoxLayout(); btns.setSpacing(10)
        self.btn_open = QPushButton("Ouvrir dans le navigateur")
        self.btn_open.setObjectName("btn-accent")
        self.btn_open.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open.clicked.connect(lambda: webbrowser.open(self.url) if self.url else None)
        btns.addWidget(self.btn_open)

        self.btn_copy = QPushButton("Copier l'URL")
        self.btn_copy.setObjectName("btn-ghost")
        self.btn_copy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_copy.clicked.connect(self._copy)
        btns.addWidget(self.btn_copy)
        lay.addLayout(btns)

    def set_url(self, url: str):
        self.url = url
        self.url_chip.setText(url)
        self._sig = _Sig()
        self._sig.done.connect(self._show)
        self._sig.fail.connect(lambda e: self.qr_lbl.setText(f"Erreur : {e}"))
        threading.Thread(target=self._gen, daemon=True).start()

    def _gen(self):
        try:
            import qrcode, io
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=8, border=2
            )
            qr.add_data(self.url); qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO(); img.save(buf, format="PNG")
            self._sig.done.emit(buf.getvalue())
        except Exception as e:
            self._sig.fail.emit(str(e))

    def _show(self, data: bytes):
        px = QPixmap(); px.loadFromData(data)
        px = px.scaled(
            200, 200,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.qr_lbl.setPixmap(px)

    def _copy(self):
        if self.url:
            QApplication.clipboard().setText(self.url)
            orig = self.btn_copy.text()
            self.btn_copy.setText("Copié ✓")
            self.btn_copy.setStyleSheet(f"""
                QPushButton {{
                    background: {self._c['success']}18;
                    color: {self._c['success']};
                    border: 1px solid {self._c['success']}40;
                    border-radius: 9px;
                    padding: 10px 26px;
                    font-size: 13px;
                    font-weight: 600;
                }}
            """)
            QTimer.singleShot(1800, lambda: (
                self.btn_copy.setText(orig),
                self.btn_copy.setStyleSheet("")
            ))