import json, os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFrame,
    QRadioButton, QButtonGroup, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor

BG      = "#0f0f13"
SURFACE = "#16161d"
BORDER  = "#25252f"
ACCENT  = "#6c8fff"
TEXT    = "#e8e8f0"
MUTED   = "#5a5a72"
SUCCESS = "#4ade80"

STYLE = f"""
QWidget {{ background-color:{BG}; color:{TEXT}; }}

QFrame#card {{
    background-color:{SURFACE};
    border:1px solid {BORDER};
    border-radius:14px;
}}
QLabel#section-title {{
    color:{TEXT}; font-size:15px; font-weight:600;
}}
QLabel#field-lbl {{
    color:{MUTED}; font-size:10px; font-weight:700;
    letter-spacing:1px;
}}
QLabel#hint {{ color:#2e2e40; font-size:11px; }}

QLineEdit {{
    background:#0a0a0d; color:{TEXT};
    border:1px solid {BORDER}; border-radius:7px;
    padding:9px 14px; font-size:13px;
    font-family:'JetBrains Mono','SF Mono','Consolas',monospace;
    selection-background-color:#1c1c26;
}}
QLineEdit:focus {{ border-color:{ACCENT}55; background:#0c0c10; }}
QLineEdit:disabled {{ color:#2e2e40; background:#0a0a0d; }}

QRadioButton {{ color:{MUTED}; font-size:13px; spacing:8px; }}
QRadioButton:checked {{ color:{ACCENT}; }}
QRadioButton::indicator {{
    width:14px; height:14px;
    border-radius:7px; border:1.5px solid {BORDER};
    background:transparent;
}}
QRadioButton::indicator:checked {{
    background:{ACCENT}; border-color:{ACCENT};
}}

QPushButton#btn-save {{
    background:{ACCENT}20; color:{ACCENT};
    border:1px solid {ACCENT}44; border-radius:8px;
    padding:11px 36px; font-size:13px; font-weight:600;
}}
QPushButton#btn-save:hover {{ background:{ACCENT}30; border-color:{ACCENT}88; }}
QPushButton#btn-browse {{
    background:{SURFACE}; color:{MUTED};
    border:1px solid {BORDER}; border-radius:7px;
    padding:9px 12px; font-size:12px; min-width:32px;
}}
QPushButton#btn-browse:hover {{ color:{TEXT}; border-color:#3a3a4e; }}
QFrame#divider {{ background:{BORDER}; max-height:1px; }}
"""

class SettingsTab(QWidget):
    def __init__(self, config, app_window):
        super().__init__()
        self.config = config
        self.app_window = app_window
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setContentsMargins(40,32,40,32)

        card = QFrame(); card.setObjectName("card"); card.setFixedWidth(520)
        cl = QVBoxLayout(card); cl.setContentsMargins(32,28,32,28); cl.setSpacing(22)

        title = QLabel("Paramètres du serveur"); title.setObjectName("section-title")
        cl.addWidget(title)
        div = QFrame(); div.setObjectName("divider"); cl.addWidget(div)

        grid = QGridLayout(); grid.setVerticalSpacing(18); grid.setHorizontalSpacing(16)
        grid.setColumnMinimumWidth(0, 130)

        # Port
        self._lbl(grid, 0, "PORT")
        pr = QHBoxLayout()
        self.inp_port = QLineEdit(str(self.config["server"]["port"])); self.inp_port.setFixedWidth(90)
        pr.addWidget(self.inp_port)
        h = QLabel("Redémarrage requis pour appliquer"); h.setObjectName("hint"); pr.addWidget(h); pr.addStretch()
        grid.addLayout(pr, 0, 1)

        # Dossier
        self._lbl(grid, 1, "DOSSIER PARTAGÉ")
        fr = QHBoxLayout()
        self.inp_folder = QLineEdit(self.config["shared_folder"])
        fr.addWidget(self.inp_folder)
        bb = QPushButton("…"); bb.setObjectName("btn-browse"); bb.setFixedWidth(36)
        bb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        bb.clicked.connect(self._browse); fr.addWidget(bb)
        grid.addLayout(fr, 1, 1)

        # Auth
        self._lbl(grid, 2, "AUTHENTIFICATION")
        ar = QHBoxLayout(); ar.setSpacing(16)
        self.auth_grp = QButtonGroup(self)
        for i,(lbl,val) in enumerate([("Ouvert","open"),("PIN","pin"),("Token","token")]):
            rb = QRadioButton(lbl); rb.setProperty("value",val)
            if val == self.config["auth"]["mode"]: rb.setChecked(True)
            rb.toggled.connect(self._toggle_pin)
            self.auth_grp.addButton(rb,i); ar.addWidget(rb)
        ar.addStretch(); grid.addLayout(ar, 2, 1)

        # PIN
        self._lbl(grid, 3, "PIN / TOKEN")
        self.inp_pin = QLineEdit(self.config["auth"].get("pin",""))
        self.inp_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_pin.setPlaceholderText("Non requis en mode Ouvert")
        grid.addWidget(self.inp_pin, 3, 1)

        # Max size
        self._lbl(grid, 4, "TAILLE MAX (MB)")
        mr = QHBoxLayout()
        self.inp_size = QLineEdit(str(self.config.get("max_file_size_mb",500))); self.inp_size.setFixedWidth(90)
        mr.addWidget(self.inp_size); mr.addStretch()
        grid.addLayout(mr, 4, 1)

        cl.addLayout(grid)
        div2 = QFrame(); div2.setObjectName("divider"); cl.addWidget(div2)

        self.btn_save = QPushButton("Sauvegarder"); self.btn_save.setObjectName("btn-save")
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.clicked.connect(self._save)
        cl.addWidget(self.btn_save, alignment=Qt.AlignmentFlag.AlignCenter)

        outer.addWidget(card)
        self._toggle_pin()

    def _lbl(self, grid, row, text):
        l = QLabel(text); l.setObjectName("field-lbl")
        l.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
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
        except: QMessageBox.critical(self,"Erreur","Port invalide (1024–65535)."); return
        try:
            max_mb = int(self.inp_size.text()); assert max_mb > 0
        except: QMessageBox.critical(self,"Erreur","Taille max invalide."); return
        folder = self.inp_folder.text().strip()
        if not folder: QMessageBox.critical(self,"Erreur","Dossier vide."); return
        os.makedirs(folder, exist_ok=True)
        btn = self.auth_grp.checkedButton()
        self.config.update({
            "server": {**self.config["server"], "port": port},
            "shared_folder": folder,
            "auth": {"mode": btn.property("value") if btn else "open", "pin": self.inp_pin.text()},
            "max_file_size_mb": max_mb,
        })
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        with open(cfg_path,"w",encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        self.app_window.reload_config(self.config)
        # Feedback visuel
        self.btn_save.setText("Sauvegardé ✓")
        self.btn_save.setStyleSheet(f"background:{SUCCESS}20;color:{SUCCESS};border:1px solid {SUCCESS}44;border-radius:8px;padding:11px 36px;font-size:13px;font-weight:600;")
        QTimer.singleShot(2200, lambda: (
            self.btn_save.setText("Sauvegarder"),
            self.btn_save.setStyleSheet("")
        ))