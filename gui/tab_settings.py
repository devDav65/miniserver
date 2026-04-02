import json, os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFrame,
    QRadioButton, QButtonGroup, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor

from gui.theme import get_colors


def _make_style(c: dict) -> str:
    return f"""
QWidget {{
    background-color: {c['bg']};
    color: {c['text']};
    font-family: {c['sans']};
}}
QFrame#card {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 16px;
}}
QFrame#card-inner {{
    background: transparent;
}}
QLabel#section-title {{
    color: {c['text']};
    font-size: 15px;
    font-weight: 700;
    letter-spacing: -0.2px;
}}
QLabel#section-sub {{
    color: {c['muted']};
    font-size: 12px;
    font-weight: 400;
}}
QLabel#field-lbl {{
    color: {c['muted']};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
    font-family: {c['sans']};
}}
QLabel#hint {{
    color: {c['dimmer']};
    font-size: 11px;
}}
QLineEdit {{
    background: {c['surface2']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: 9px;
    padding: 10px 14px;
    font-size: 13px;
    font-family: {c['mono']};
    selection-background-color: {c['surface3']};
}}
QLineEdit:focus {{
    border-color: {c['accent']};
    background: {c['bg']};
}}
QLineEdit:disabled {{
    color: {c['dimmer']};
    background: {c['surface']};
    border-color: {c['border']};
}}
QRadioButton {{
    color: {c['muted']};
    font-size: 13px;
    spacing: 8px;
    font-family: {c['sans']};
}}
QRadioButton:checked {{
    color: {c['accent']};
    font-weight: 600;
}}
QRadioButton::indicator {{
    width: 15px;
    height: 15px;
    border-radius: 8px;
    border: 1.5px solid {c['border2']};
    background: transparent;
}}
QRadioButton::indicator:checked {{
    background: {c['accent']};
    border-color: {c['accent']};
}}
QRadioButton::indicator:hover {{
    border-color: {c['accent']};
}}
QPushButton#btn-save {{
    background: {c['accent_dim']};
    color: {c['accent']};
    border: 1px solid {c['accent_mid']};
    border-radius: 9px;
    padding: 12px 40px;
    font-size: 13px;
    font-weight: 600;
    font-family: {c['sans']};
}}
QPushButton#btn-save:hover {{
    background: {c['accent_mid']};
    border-color: {c['accent']};
}}
QPushButton#btn-browse {{
    background: {c['surface2']};
    color: {c['muted']};
    border: 1px solid {c['border']};
    border-radius: 9px;
    padding: 10px 12px;
    font-size: 13px;
    min-width: 36px;
    font-family: {c['sans']};
}}
QPushButton#btn-browse:hover {{
    color: {c['text']};
    border-color: {c['border2']};
    background: {c['surface3']};
}}
QFrame#divider {{
    background: {c['border']};
    max-height: 1px;
    border: none;
}}
"""


class SettingsTab(QWidget):
    def __init__(self, config, app_window, colors: dict = None):
        super().__init__()
        self.config = config
        self.app_window = app_window
        self._c = colors or get_colors(True)
        self.setStyleSheet(_make_style(self._c))
        self._build()

    def apply_theme(self, colors: dict):
        self._c = colors
        self.setStyleSheet(_make_style(colors))

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setContentsMargins(40, 36, 40, 36)

        card = QFrame(); card.setObjectName("card"); card.setFixedWidth(540)
        cl = QVBoxLayout(card); cl.setContentsMargins(36, 32, 36, 32); cl.setSpacing(24)

        # Title block
        title_row = QVBoxLayout(); title_row.setSpacing(4)
        title = QLabel("Paramètres du serveur"); title.setObjectName("section-title")
        title_row.addWidget(title)
        sub = QLabel("Configuration du serveur local et des accès")
        sub.setObjectName("section-sub")
        title_row.addWidget(sub)
        cl.addLayout(title_row)

        div = QFrame(); div.setObjectName("divider"); cl.addWidget(div)

        grid = QGridLayout()
        grid.setVerticalSpacing(20)
        grid.setHorizontalSpacing(18)
        grid.setColumnMinimumWidth(0, 136)

        # ── Port
        self._lbl(grid, 0, "PORT")
        pr = QHBoxLayout(); pr.setSpacing(10)
        self.inp_port = QLineEdit(str(self.config["server"]["port"]))
        self.inp_port.setFixedWidth(96)
        pr.addWidget(self.inp_port)
        h = QLabel("Redémarrage requis pour appliquer"); h.setObjectName("hint")
        pr.addWidget(h); pr.addStretch()
        grid.addLayout(pr, 0, 1)

        # ── Dossier partagé
        self._lbl(grid, 1, "DOSSIER PARTAGÉ")
        fr = QHBoxLayout(); fr.setSpacing(8)
        self.inp_folder = QLineEdit(self.config["shared_folder"])
        fr.addWidget(self.inp_folder)
        bb = QPushButton("…"); bb.setObjectName("btn-browse"); bb.setFixedWidth(38)
        bb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        bb.clicked.connect(self._browse); fr.addWidget(bb)
        grid.addLayout(fr, 1, 1)

        # ── Authentification
        self._lbl(grid, 2, "AUTHENTIFICATION")
        ar = QHBoxLayout(); ar.setSpacing(18)
        self.auth_grp = QButtonGroup(self)
        for i, (lbl, val) in enumerate([("Ouvert", "open"), ("PIN", "pin"), ("Token", "token")]):
            rb = QRadioButton(lbl); rb.setProperty("value", val)
            if val == self.config["auth"]["mode"]: rb.setChecked(True)
            rb.toggled.connect(self._toggle_pin)
            self.auth_grp.addButton(rb, i); ar.addWidget(rb)
        ar.addStretch()
        grid.addLayout(ar, 2, 1)

        # ── PIN / Token
        self._lbl(grid, 3, "PIN / TOKEN")
        self.inp_pin = QLineEdit(self.config["auth"].get("pin", ""))
        self.inp_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_pin.setPlaceholderText("Non requis en mode Ouvert")
        grid.addWidget(self.inp_pin, 3, 1)

        # ── Taille maximale
        self._lbl(grid, 4, "TAILLE MAX (MB)")
        mr = QHBoxLayout()
        self.inp_size = QLineEdit(str(self.config.get("max_file_size_mb", 500)))
        self.inp_size.setFixedWidth(96)
        mr.addWidget(self.inp_size); mr.addStretch()
        grid.addLayout(mr, 4, 1)

        cl.addLayout(grid)

        div2 = QFrame(); div2.setObjectName("divider"); cl.addWidget(div2)

        self.btn_save = QPushButton("Sauvegarder")
        self.btn_save.setObjectName("btn-save")
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.clicked.connect(self._save)
        cl.addWidget(self.btn_save, alignment=Qt.AlignmentFlag.AlignCenter)

        outer.addWidget(card)
        self._toggle_pin()

    def _lbl(self, grid, row, text):
        l = QLabel(text); l.setObjectName("field-lbl")
        l.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(l, row, 0)

    def _toggle_pin(self):
        btn = self.auth_grp.checkedButton()
        self.inp_pin.setEnabled(bool(btn and btn.property("value") != "open"))

    def _browse(self):
        p = QFileDialog.getExistingDirectory(self, "Choisir le dossier partagé")
        if p: self.inp_folder.setText(p)

    def _save(self):
        try:
            port = int(self.inp_port.text()); assert 1024 <= port <= 65535
        except:
            QMessageBox.critical(self, "Erreur", "Port invalide (1024–65535).")
            return
        try:
            max_mb = int(self.inp_size.text()); assert max_mb > 0
        except:
            QMessageBox.critical(self, "Erreur", "Taille max invalide.")
            return
        folder = self.inp_folder.text().strip()
        if not folder:
            QMessageBox.critical(self, "Erreur", "Dossier vide.")
            return
        os.makedirs(folder, exist_ok=True)
        btn = self.auth_grp.checkedButton()
        self.config.update({
            "server": {**self.config["server"], "port": port},
            "shared_folder": folder,
            "auth": {"mode": btn.property("value") if btn else "open", "pin": self.inp_pin.text()},
            "max_file_size_mb": max_mb,
        })
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        self.app_window.reload_config(self.config)

        # Visual feedback
        sc = self._c["success"]
        self.btn_save.setText("Sauvegardé ✓")
        self.btn_save.setStyleSheet(
            f"background:{sc}18; color:{sc}; border:1px solid {sc}40; "
            f"border-radius:9px; padding:12px 40px; font-size:13px; font-weight:600;"
        )
        QTimer.singleShot(2200, lambda: (
            self.btn_save.setText("Sauvegarder"),
            self.btn_save.setStyleSheet("")
        ))