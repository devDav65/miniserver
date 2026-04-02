import os, webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor, QFont

from core.file_manager import list_files, delete_file
from gui.theme import get_colors


def _make_style(c: dict) -> str:
    return f"""
QWidget {{
    background-color: {c['bg']};
    color: {c['text']};
    font-family: {c['sans']};
}}
QFrame#toolbar {{
    background-color: {c['surface']};
    border-bottom: 1px solid {c['border']};
    min-height: 54px;
    max-height: 54px;
}}
QLabel#title {{
    color: {c['text']};
    font-size: 14px;
    font-weight: 700;
}}
QLabel#count {{
    color: {c['muted']};
    font-size: 11px;
    background: {c['surface2']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 2px 10px;
}}
QPushButton#btn-primary {{
    background: {c['accent_dim']};
    color: {c['accent']};
    border: 1px solid {c['accent_mid']};
    border-radius: 8px;
    padding: 7px 18px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton#btn-primary:hover {{
    background: {c['accent_mid']};
    border-color: {c['accent']};
}}
QTableWidget {{
    background-color: {c['bg']};
    color: {c['text2']};
    border: none;
    gridline-color: transparent;
    font-size: 13px;
    outline: none;
}}
QTableWidget::item {{
    padding: 0 18px;
    border-bottom: 1px solid {c['border']};
}}
QTableWidget::item:selected {{
    background-color: {c['surface2']};
    color: {c['text']};
}}
QHeaderView::section {{
    background-color: {c['surface']};
    color: {c['muted']};
    border: none;
    border-bottom: 1px solid {c['border']};
    padding: 9px 18px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    font-family: {c['sans']};
}}
QScrollBar:vertical {{
    background: {c['bg']};
    width: 5px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {c['border2']};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QMenu {{
    background-color: {c['surface']};
    color: {c['text2']};
    border: 1px solid {c['border2']};
    border-radius: 10px;
    padding: 6px;
    font-size: 13px;
    font-family: {c['sans']};
}}
QMenu::item {{
    padding: 8px 20px;
    border-radius: 6px;
}}
QMenu::item:selected {{
    background-color: {c['surface2']};
    color: {c['accent']};
}}
QMenu::separator {{
    background: {c['border']};
    height: 1px;
    margin: 4px 8px;
}}
"""


def _del_btn_style(c: dict) -> str:
    return f"""
        QPushButton {{
            background: transparent;
            color: {c['danger']};
            border: 1px solid {c['danger']}2a;
            border-radius: 7px;
            padding: 5px 14px;
            font-size: 12px;
            font-weight: 500;
            font-family: {c['sans']};
        }}
        QPushButton:hover {{
            background: {c['danger']}12;
            border-color: {c['danger']}55;
        }}
    """


class FilesTab(QWidget):
    def __init__(self, config: dict, colors: dict = None):
        super().__init__()
        self.config = config
        self._c = colors or get_colors(True)
        self.setStyleSheet(_make_style(self._c))
        self._build()
        self.refresh(config["shared_folder"])

    def apply_theme(self, colors: dict):
        self._c = colors
        self.setStyleSheet(_make_style(colors))
        self.refresh(self.config["shared_folder"])

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Toolbar
        tb_frame = QFrame(); tb_frame.setObjectName("toolbar")
        tb = QHBoxLayout(tb_frame); tb.setContentsMargins(24, 0, 20, 0); tb.setSpacing(10)

        lbl = QLabel("Fichiers partagés"); lbl.setObjectName("title")
        tb.addWidget(lbl)
        self.count_lbl = QLabel("—"); self.count_lbl.setObjectName("count")
        tb.addWidget(self.count_lbl)
        tb.addStretch()

        btn_folder = QPushButton("Ouvrir le dossier"); btn_folder.setObjectName("btn-primary")
        btn_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_folder.clicked.connect(self._open_folder)
        tb.addWidget(btn_folder)
        lay.addWidget(tb_frame)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["NOM", "TAILLE", "MODIFIÉ LE", ""])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._ctx_menu)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 164)
        self.table.setColumnWidth(3, 126)
        self.table.verticalHeader().setDefaultSectionSize(50)
        lay.addWidget(self.table)

        # Empty state
        self.empty = QLabel(
            "Aucun fichier partagé\n\nGlisse des fichiers sur la page web pour commencer."
        )
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setStyleSheet(
            f"color: {self._c['muted']}; font-size: 13px; line-height: 2; "
            f"font-family: {self._c['sans']};"
        )
        self.empty.hide()
        lay.addWidget(self.empty)

    def refresh(self, folder: str):
        files = list_files(folder)
        self.table.setRowCount(0)

        self.empty.setStyleSheet(
            f"color: {self._c['muted']}; font-size: 13px; line-height: 2; "
            f"font-family: {self._c['sans']};"
        )

        if not files:
            self.table.hide(); self.empty.show()
            self.count_lbl.setText("Aucun fichier")
            return

        self.empty.hide(); self.table.show()
        n = len(files)
        self.count_lbl.setText(f"{n} fichier{'s' if n > 1 else ''}")

        for f in files:
            r = self.table.rowCount(); self.table.insertRow(r)

            n_item = QTableWidgetItem(f"  {f['name']}")
            n_item.setForeground(QColor(self._c["text"]))
            self.table.setItem(r, 0, n_item)

            s_item = QTableWidgetItem(f['size_str'])
            s_item.setForeground(QColor(self._c["muted"]))
            s_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r, 1, s_item)

            d_item = QTableWidgetItem(f['modified'])
            d_item.setForeground(QColor(self._c["muted"]))
            d_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 2, d_item)

            del_btn = QPushButton("Supprimer")
            del_btn.setStyleSheet(_del_btn_style(self._c))
            del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            del_btn.clicked.connect(lambda _, name=f['name']: self._delete(name))
            self.table.setCellWidget(r, 3, del_btn)

    def _ctx_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0: return
        name = self.table.item(row, 0).text().strip()
        menu = QMenu(self)
        menu.addAction("Télécharger", lambda: self._download(name))
        menu.addSeparator()
        act = menu.addAction("Supprimer")
        act.triggered.connect(lambda: self._delete(name))
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _open_folder(self):
        webbrowser.open(f"file://{os.path.abspath(self.config['shared_folder'])}")

    def _download(self, name: str):
        from core.network import get_local_ip
        webbrowser.open(
            f"http://{get_local_ip()}:{self.config['server']['port']}/download/{name}"
        )

    def _delete(self, name: str):
        r = QMessageBox.question(
            self, "Supprimer", f"Supprimer « {name} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if r == QMessageBox.StandardButton.Yes:
            if delete_file(self.config["shared_folder"], name):
                self.refresh(self.config["shared_folder"])
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de supprimer le fichier.")