import os
import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor

from core.file_manager import list_files, delete_file

STYLE = """
QWidget { background-color: #0d0d0f; color: #e8e8e8; }

QFrame#toolbar {
    background-color: #111115;
    border-bottom: 1px solid #1e1e28;
    min-height: 52px; max-height: 52px;
}
QLabel#title {
    color: #ffffff;
    font-size: 14px;
    font-weight: 600;
}
QPushButton#action-btn {
    background: #0d1f2d;
    color: #00d4ff;
    border: 1px solid #00d4ff30;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 12px;
}
QPushButton#action-btn:hover {
    background: #0f2840;
    border-color: #00d4ff80;
}
QTableWidget {
    background-color: #0d0d0f;
    color: #c8c8d8;
    border: none;
    gridline-color: #1a1a22;
    font-size: 13px;
    selection-background-color: #16161f;
    selection-color: #ffffff;
}
QTableWidget::item {
    padding: 10px 16px;
    border-bottom: 1px solid #14141c;
}
QTableWidget::item:selected {
    background-color: #16161f;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #111115;
    color: #444460;
    border: none;
    border-bottom: 1px solid #1e1e28;
    padding: 8px 16px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}
QScrollBar:vertical {
    background: #111115;
    width: 6px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #2a2a3a;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QMenu {
    background-color: #16161f;
    color: #c8c8d8;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item { padding: 8px 20px; border-radius: 4px; }
QMenu::item:selected { background-color: #1e1e2e; color: #00d4ff; }
"""


class FilesTab(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.setStyleSheet(STYLE)
        self._build()
        self.refresh(config["shared_folder"])

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Toolbar ───────────────────────────────────────────
        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(20, 0, 20, 0)

        title = QLabel("Fichiers partagés")
        title.setObjectName("title")
        tb.addWidget(title)

        self.count_label = QLabel("0 fichier")
        self.count_label.setStyleSheet("color: #444460; font-size: 12px;")
        tb.addWidget(self.count_label)
        tb.addStretch()

        btn_open = QPushButton("Ouvrir le dossier")
        btn_open.setObjectName("action-btn")
        btn_open.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_open.clicked.connect(self._open_folder)
        tb.addWidget(btn_open)

        layout.addWidget(toolbar)

        # ── Table ─────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["NOM", "TAILLE", "MODIFIÉ", ""])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_menu)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 110)
        self.table.verticalHeader().setDefaultSectionSize(44)

        layout.addWidget(self.table)

        # ── Empty state ───────────────────────────────────────
        self.empty = QLabel("Aucun fichier partagé\n\nGlisse des fichiers sur la page web pour commencer.")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setStyleSheet("color: #333350; font-size: 13px; line-height: 1.8;")
        self.empty.hide()
        layout.addWidget(self.empty)

    def refresh(self, folder: str):
        files = list_files(folder)
        self.table.setRowCount(0)

        if not files:
            self.table.hide()
            self.empty.show()
            self.count_label.setText("0 fichier")
            return

        self.empty.hide()
        self.table.show()
        self.count_label.setText(f"{len(files)} fichier{'s' if len(files) > 1 else ''}")

        for f in files:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(f"  {f['name']}")
            name_item.setForeground(QColor("#e8e8ff"))
            self.table.setItem(row, 0, name_item)

            size_item = QTableWidgetItem(f['size_str'])
            size_item.setForeground(QColor("#666680"))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, size_item)

            date_item = QTableWidgetItem(f['modified'])
            date_item.setForeground(QColor("#444460"))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, date_item)

            del_btn = QPushButton("Supprimer")
            del_btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #ff4466;
                    border: 1px solid #ff446630; border-radius: 5px;
                    padding: 4px 12px; font-size: 12px;
                }
                QPushButton:hover {
                    background: #1a0a10; border-color: #ff446680;
                }
            """)
            del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            del_btn.clicked.connect(lambda _, name=f['name']: self._delete_file(name))
            self.table.setCellWidget(row, 3, del_btn)

    def _show_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        name = self.table.item(row, 0).text().strip()
        menu = QMenu(self)
        menu.addAction("Télécharger", lambda: self._download_file(name))
        menu.addSeparator()
        act_del = menu.addAction("Supprimer")
        act_del.setForeground(QColor("#ff4466"))
        act_del.triggered.connect(lambda: self._delete_file(name))
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _open_folder(self):
        path = os.path.abspath(self.config["shared_folder"])
        webbrowser.open(f"file://{path}")

    def _download_file(self, name: str):
        from core.network import get_local_ip
        port = self.config["server"]["port"]
        webbrowser.open(f"http://{get_local_ip()}:{port}/download/{name}")

    def _delete_file(self, name: str):
        reply = QMessageBox.question(
            self, "Supprimer",
            f"Supprimer « {name} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok = delete_file(self.config["shared_folder"], name)
            if ok:
                self.refresh(self.config["shared_folder"])
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de supprimer le fichier.")