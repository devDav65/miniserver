import threading
import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QImage, QCursor, QFont

STYLE = """
QWidget { background-color: #0d0d0f; }
QLabel#page-title {
    color: #ffffff;
    font-size: 15px;
    font-weight: 600;
}
QLabel#url-label {
    color: #00d4ff;
    font-family: 'SF Mono', 'Consolas', monospace;
    font-size: 13px;
    padding: 10px 20px;
    background: #061820;
    border: 1px solid #00d4ff20;
    border-radius: 8px;
}
QLabel#qr-frame {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 16px;
}
QPushButton#primary-btn {
    background: #00d4ff18;
    color: #00d4ff;
    border: 1px solid #00d4ff40;
    border-radius: 8px;
    padding: 9px 22px;
    font-size: 13px;
}
QPushButton#primary-btn:hover {
    background: #00d4ff28;
    border-color: #00d4ff80;
}
QPushButton#secondary-btn {
    background: transparent;
    color: #666680;
    border: 1px solid #1e1e28;
    border-radius: 8px;
    padding: 9px 22px;
    font-size: 13px;
}
QPushButton#secondary-btn:hover {
    color: #c0c0d8;
    border-color: #2a2a3a;
}
"""


class QRSignal(QObject):
    done = pyqtSignal(object)


class QRCodeTab(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.current_url = ""
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 48, 40, 48)

        title = QLabel("Scanner pour accéder au serveur")
        title.setObjectName("page-title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.url_label = QLabel("Chargement…")
        self.url_label.setObjectName("url-label")
        self.url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.url_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.url_label.mousePressEvent = lambda _: webbrowser.open(self.current_url)
        layout.addWidget(self.url_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # QR image
        self.qr_label = QLabel()
        self.qr_label.setObjectName("qr-frame")
        self.qr_label.setFixedSize(220, 220)
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setText("Génération…")
        self.qr_label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border-radius: 12px;
                color: #aaaaaa;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.qr_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Boutons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_open = QPushButton("Ouvrir dans le navigateur")
        btn_open.setObjectName("primary-btn")
        btn_open.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_open.clicked.connect(lambda: webbrowser.open(self.current_url))
        btn_row.addWidget(btn_open)

        btn_copy = QPushButton("Copier l'URL")
        btn_copy.setObjectName("secondary-btn")
        btn_copy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_copy.clicked.connect(self._copy_url)
        btn_row.addWidget(btn_copy)

        layout.addLayout(btn_row)

    def set_url(self, url: str):
        self.current_url = url
        self.url_label.setText(url)
        self._sig = QRSignal()
        self._sig.done.connect(self._show_qr)
        threading.Thread(target=self._generate_qr, daemon=True).start()

    def _generate_qr(self):
        try:
            import qrcode
            from PIL import Image
            import io

            qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                               box_size=8, border=2)
            qr.add_data(self.current_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            self._sig.done.emit(buf.getvalue())
        except Exception as e:
            self._sig.done.emit(None)

    def _show_qr(self, png_bytes):
        if not png_bytes:
            self.qr_label.setText("Erreur QR")
            return
        pixmap = QPixmap()
        pixmap.loadFromData(png_bytes)
        pixmap = pixmap.scaled(188, 188,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        self.qr_label.setPixmap(pixmap)

    def _copy_url(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.current_url)
        orig = self.sender().text()
        self.sender().setText("Copié !")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self.sender().setText(orig) if self.sender() else None)