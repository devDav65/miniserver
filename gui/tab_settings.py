import json
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFrame,
    QRadioButton, QButtonGroup, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor

STYLE = """
QWidget { background-color: #0d0d0f; color: #c8c8d8; }

QFrame#card {
    background-color: #111115;
    border: 1px solid #1e1e28;
    border-radius: 12px;
}
QLabel#section-title {
    color: #ffffff;
    font-size: 14px;
    font-weight: 600;
    padding-bottom: 4px;
}
QLabel#field-label {
    color: #666680;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
}
QLabel#hint {
    color: #333350;
    font-size: 11px;
}
QLineEdit {
    background-color: #0a0a0c;
    color: #e8e8ff;
    border: 1px solid #1e1e28;
    border-radius: 7px;
    padding: 9px 14px;
    font-size: 13px;
    font-family: 'SF Mono', 'Consolas', monospace;
    selection-background-color: #1e1e2e;
}
QLineEdit:focus {
    border-color: #00d4ff40;
    background-color: #0c0c10;
}
QRadioButton {
    color: #666680;
    font-size: 13px;
    spacing: 8px;
}
QRadioButton:checked { color: #00d4ff; }
QRadioButton::indicator {
    width: 14px; height: 14px;
    border-radius: 7px;
    border: 1.5px solid #2a2a3a;
    background: transparent;
}
QRadioButton::indicator:checked {
    background: #00d4ff;
    border-color: #00d4ff;
}
QPushButton#save-btn {
    background: #00d4ff18;
    color: #00d4ff;
    border: 1px solid #00d4ff40;
    border-radius: 8px;
    padding: 11px 32px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
}
QPushButton#save-btn:hover {
    background: #00d4ff28;
    border-color: #00d4ff80;
}
QPushButton#browse-btn {
    background: #111115;
    color: #444460;
    border: 1px solid #1e1e28;
    border-radius: 7px;
    padding: 9px 14px;
    font-size: 12px;
}
QPushButton#browse-btn:hover { color: #c8c8d8; border-color: #2a2a3a; }
QFrame#divider { background-color: #1a1a22; max-height: 1px; }
"""


class SettingsTab(QWidget):
    def __init__(self, config: dict, app_window):
        super().__init__()
        self.config = config
        self.app_window = app_window
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setContentsMargins(40, 32, 40, 32)

        # ── Carte principale ──────────────────────────────────
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(500)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        title = QLabel("Paramètres du serveur")
        title.setObjectName("section-title")
        layout.addWidget(title)

        div = QFrame()
        div.setObjectName("divider")
        layout.addWidget(div)

        grid = QGridLayout()
        grid.setVerticalSpacing(16)
        grid.setHorizontalSpacing(16)
        grid.setColumnStretch(1, 1)

        # ── Port ──────────────────────────────────────────────
        self._label(grid, 0, "PORT")
        port_row = QHBoxLayout()
        self.port_input = QLineEdit(str(self.config["server"]["port"]))
        self.port_input.setFixedWidth(100)
        port_row.addWidget(self.port_input)
        hint = QLabel("Redémarrage requis")
        hint.setObjectName("hint")
        port_row.addWidget(hint)
        port_row.addStretch()
        grid.addLayout(port_row, 0, 1)

        # ── Dossier ───────────────────────────────────────────
        self._label(grid, 1, "DOSSIER PARTAGÉ")
        folder_row = QHBoxLayout()
        self.folder_input = QLineEdit(self.config["shared_folder"])
        folder_row.addWidget(self.folder_input)
        btn_browse = QPushButton("…")
        btn_browse.setObjectName("browse-btn")
        btn_browse.setFixedWidth(36)
        btn_browse.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_browse.clicked.connect(self._browse)
        folder_row.addWidget(btn_browse)
        grid.addLayout(folder_row, 1, 1)

        # ── Auth ──────────────────────────────────────────────
        self._label(grid, 2, "AUTHENTIFICATION")
        auth_row = QHBoxLayout()
        self.auth_group = QButtonGroup(self)
        for i, (label, val) in enumerate([("Ouvert", "open"), ("PIN", "pin"), ("Token", "token")]):
            rb = QRadioButton(label)
            rb.setProperty("value", val)
            if val == self.config["auth"]["mode"]:
                rb.setChecked(True)
            rb.toggled.connect(self._toggle_pin)
            self.auth_group.addButton(rb, i)
            auth_row.addWidget(rb)
        auth_row.addStretch()
        grid.addLayout(auth_row, 2, 1)

        # ── PIN ───────────────────────────────────────────────
        self._label(grid, 3, "PIN / TOKEN")
        self.pin_input = QLineEdit(self.config["auth"].get("pin", ""))
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setPlaceholderText("Laisser vide si mode ouvert")
        grid.addWidget(self.pin_input, 3, 1)

        # ── Taille max ────────────────────────────────────────
        self._label(grid, 4, "TAILLE MAX (MB)")
        size_row = QHBoxLayout()
        self.size_input = QLineEdit(str(self.config.get("max_file_size_mb", 500)))
        self.size_input.setFixedWidth(100)
        size_row.addWidget(self.size_input)
        size_row.addStretch()
        grid.addLayout(size_row, 4, 1)

        layout.addLayout(grid)

        div2 = QFrame()
        div2.setObjectName("divider")
        layout.addWidget(div2)

        # ── Bouton save ───────────────────────────────────────
        btn_save = QPushButton("Sauvegarder")
        btn_save.setObjectName("save-btn")
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.clicked.connect(self._save)
        layout.addWidget(btn_save, alignment=Qt.AlignmentFlag.AlignCenter)

        outer.addWidget(card)
        self._toggle_pin()

    def _label(self, grid, row, text):
        lbl = QLabel(text)
        lbl.setObjectName("field-label")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(lbl, row, 0)

    def _toggle_pin(self):
        checked = self.auth_group.checkedButton()
        if checked:
            mode = checked.property("value")
            self.pin_input.setEnabled(mode != "open")

    def _browse(self):
        path = QFileDialog.getExistingDirectory(self, "Choisir le dossier partagé")
        if path:
            self.folder_input.setText(path)

    def _save(self):
        try:
            port = int(self.port_input.text())
            assert 1024 <= port <= 65535
        except (ValueError, AssertionError):
            QMessageBox.critical(self, "Erreur", "Port invalide (1024–65535).")
            return

        try:
            max_mb = int(self.size_input.text())
            assert max_mb > 0
        except (ValueError, AssertionError):
            QMessageBox.critical(self, "Erreur", "Taille max invalide.")
            return

        folder = self.folder_input.text().strip()
        if not folder:
            QMessageBox.critical(self, "Erreur", "Le dossier partagé ne peut pas être vide.")
            return
        os.makedirs(folder, exist_ok=True)

        checked = self.auth_group.checkedButton()
        auth_mode = checked.property("value") if checked else "open"

        self.config["server"]["port"]   = port
        self.config["shared_folder"]    = folder
        self.config["auth"]["mode"]     = auth_mode
        self.config["auth"]["pin"]      = self.pin_input.text()
        self.config["max_file_size_mb"] = max_mb

        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

        self.app_window.reload_config(self.config)

        btn = self.sender()
        btn.setText("Sauvegardé ✓")
        btn.setStyleSheet(btn.styleSheet().replace("#00d4ff", "#00ff88"))
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: (
            btn.setText("Sauvegarder"),
            btn.setStyleSheet(btn.styleSheet().replace("#00ff88", "#00d4ff"))
        ) if btn else None)