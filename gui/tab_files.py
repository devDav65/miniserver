import os, webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QMenu, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor, QFont
from core.file_manager import list_files, delete_file

BG      = "#0f0f13"
SURFACE = "#16161d"
BORDER  = "#25252f"
ACCENT  = "#6c8fff"
TEXT    = "#e8e8f0"
MUTED   = "#5a5a72"
DANGER  = "#ff5e7a"

STYLE = f"""
QWidget {{ background-color: {BG}; color: {TEXT}; }}
QFrame#toolbar {{
    background-color: {SURFACE};
    border-bottom: 1px solid {BORDER};
    min-height: 56px; max-height: 56px;
}}
QLabel#title  {{ color: {TEXT}; font-size: 15px; font-weight: 600; }}
QLabel#count  {{ color: {MUTED}; font-size: 12px; }}

QPushButton#btn-primary {{
    background-color: {ACCENT}22;
    color: {ACCENT};
    border: 1px solid {ACCENT}55;
    border-radius: 7px;
    padding: 7px 18px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton#btn-primary:hover {{
    background-color: {ACCENT}33;
    border-color: {ACCENT}99;
}}

QTableWidget {{
    background-color: {BG};
    color: #c8c8dc;
    border: none;
    gridline-color: transparent;
    font-size: 13px;
    outline: none;
}}
QTableWidget::item {{
    padding: 0 16px;
    border-bottom: 1px solid {BORDER};
}}
QTableWidget::item:selected {{
    background-color: {SURFACE};
    color: {TEXT};
}}
QHeaderView::section {{
    background-color: {SURFACE};
    color: {MUTED};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 8px 16px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QScrollBar:vertical {{
    background: {BG}; width: 5px; border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 3px; min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}

QMenu {{
    background-color: #1c1c26;
    color: #c8c8dc;
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px;
    font-size: 13px;
}}
QMenu::item {{ padding: 8px 18px; border-radius: 5px; }}
QMenu::item:selected {{ background-color: {SURFACE}; color: {ACCENT}; }}
QMenu::separator {{ background: {BORDER}; height: 1px; margin: 4px 8px; }}
"""

class FilesTab(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.setStyleSheet(STYLE)
        self._build()
        self.refresh(config["shared_folder"])

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)
        lay.setSpacing(0)

        # Toolbar
        tb_frame = QFrame(); tb_frame.setObjectName("toolbar")
        tb = QHBoxLayout(tb_frame); tb.setContentsMargins(22,0,22,0); tb.setSpacing(12)
        lbl = QLabel("Fichiers partagés"); lbl.setObjectName("title"); tb.addWidget(lbl)
        self.count_lbl = QLabel("—"); self.count_lbl.setObjectName("count"); tb.addWidget(self.count_lbl)
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
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(3, 120)
        self.table.verticalHeader().setDefaultSectionSize(48)
        lay.addWidget(self.table)

        # Empty state
        self.empty = QLabel("Aucun fichier partagé\n\nGlisse des fichiers sur la page web pour commencer.")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setStyleSheet(f"color:{MUTED}; font-size:13px; line-height:2;")
        self.empty.hide()
        lay.addWidget(self.empty)

    def refresh(self, folder: str):
        files = list_files(folder)
        self.table.setRowCount(0)
        if not files:
            self.table.hide(); self.empty.show()
            self.count_lbl.setText("Aucun fichier")
            return
        self.empty.hide(); self.table.show()
        n = len(files)
        self.count_lbl.setText(f"{n} fichier{'s' if n>1 else ''}")
        for f in files:
            r = self.table.rowCount(); self.table.insertRow(r)
            n_item = QTableWidgetItem(f"  {f['name']}")
            n_item.setForeground(QColor(TEXT))
            self.table.setItem(r, 0, n_item)
            s_item = QTableWidgetItem(f['size_str'])
            s_item.setForeground(QColor(MUTED))
            s_item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r, 1, s_item)
            d_item = QTableWidgetItem(f['modified'])
            d_item.setForeground(QColor(MUTED))
            d_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 2, d_item)
            del_btn = QPushButton("Supprimer")
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {DANGER};
                    border: 1px solid {DANGER}33; border-radius: 6px;
                    padding: 5px 14px; font-size: 12px;
                }}
                QPushButton:hover {{ background:{DANGER}15; border-color:{DANGER}66; }}
            """)
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
        webbrowser.open(f"http://{get_local_ip()}:{self.config['server']['port']}/download/{name}")

    def _delete(self, name: str):
        r = QMessageBox.question(self, "Supprimer", f"Supprimer « {name} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            if delete_file(self.config["shared_folder"], name):
                self.refresh(self.config["shared_folder"])
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de supprimer le fichier.")