import threading, webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QPixmap, QCursor

BG      = "#0f0f13"
SURFACE = "#16161d"
BORDER  = "#25252f"
ACCENT  = "#6c8fff"
TEXT    = "#e8e8f0"
MUTED   = "#5a5a72"

STYLE = f"""
QWidget {{ background-color:{BG}; }}
QLabel#page-title {{ color:{TEXT}; font-size:16px; font-weight:600; }}
QLabel#url-chip {{
    color:{ACCENT};
    background:{ACCENT}15;
    border: 1px solid {ACCENT}33;
    border-radius: 8px;
    padding: 8px 20px;
    font-family:'JetBrains Mono','SF Mono','Consolas',monospace;
    font-size: 13px;
}}
QLabel#qr-box {{
    background:#ffffff;
    border-radius:14px;
    padding: 14px;
}}
QLabel#helper {{
    color:{MUTED};
    font-size: 12px;
}}
QPushButton#btn-accent {{
    background:{ACCENT}20; color:{ACCENT};
    border:1px solid {ACCENT}44; border-radius:8px;
    padding:9px 24px; font-size:13px; font-weight:600;
}}
QPushButton#btn-accent:hover {{
    background:{ACCENT}30; border-color:{ACCENT}88;
}}
QPushButton#btn-ghost {{
    background:transparent; color:{MUTED};
    border:1px solid {BORDER}; border-radius:8px;
    padding:9px 24px; font-size:13px;
}}
QPushButton#btn-ghost:hover {{ color:{TEXT}; border-color:#3a3a4e; }}
"""

class _Sig(QObject):
    done = pyqtSignal(bytes)
    fail = pyqtSignal(str)

class QRCodeTab(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.url = ""
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(18)
        lay.setContentsMargins(40, 48, 40, 48)

        title = QLabel("Scanner pour se connecter"); title.setObjectName("page-title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(title)

        self.url_chip = QLabel("En attente…"); self.url_chip.setObjectName("url-chip")
        self.url_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.url_chip.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.url_chip.mousePressEvent = lambda _: webbrowser.open(self.url) if self.url else None
        lay.addWidget(self.url_chip, alignment=Qt.AlignmentFlag.AlignCenter)

        self.qr_lbl = QLabel(); self.qr_lbl.setObjectName("qr-box")
        self.qr_lbl.setFixedSize(224, 224)
        self.qr_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_lbl.setText("Génération…")
        self.qr_lbl.setStyleSheet("QLabel{background:#fff;border-radius:14px;color:#aaa;font-size:12px;}")
        lay.addWidget(self.qr_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        helper = QLabel("Tous les appareils sur le même Wi-Fi peuvent se connecter")
        helper.setObjectName("helper"); helper.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(helper)

        btns = QHBoxLayout(); btns.setSpacing(10)
        self.btn_open = QPushButton("Ouvrir dans le navigateur"); self.btn_open.setObjectName("btn-accent")
        self.btn_open.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open.clicked.connect(lambda: webbrowser.open(self.url) if self.url else None)
        btns.addWidget(self.btn_open)
        self.btn_copy = QPushButton("Copier l'URL"); self.btn_copy.setObjectName("btn-ghost")
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
            qr = qrcode.QRCode(version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=8, border=2)
            qr.add_data(self.url); qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO(); img.save(buf, format="PNG")
            self._sig.done.emit(buf.getvalue())
        except Exception as e:
            self._sig.fail.emit(str(e))

    def _show(self, data: bytes):
        px = QPixmap(); px.loadFromData(data)
        px = px.scaled(196, 196,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        self.qr_lbl.setPixmap(px)

    def _copy(self):
        if self.url:
            QApplication.clipboard().setText(self.url)
            orig = self.btn_copy.text()
            self.btn_copy.setText("Copié ✓")
            self.btn_copy.setStyleSheet(self.btn_copy.styleSheet()
                .replace(MUTED, "#4ade80").replace(BORDER, "#4ade8033"))
            QTimer.singleShot(1800, lambda: (
                self.btn_copy.setText(orig),
                self.btn_copy.setStyleSheet("")
            ))