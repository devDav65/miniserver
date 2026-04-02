import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser

from core.file_manager import list_files


class FilesTab:
    """
    Onglet 'Fichiers' — affiche la liste des fichiers du dossier partagé.
    Se rafraîchit automatiquement à chaque upload/suppression via la queue.
    """

    def __init__(self, parent: ttk.Notebook, config: dict):
        self.config = config
        self.frame = tk.Frame(parent, bg="#f5f5f4")
        self._build()
        self.refresh(config["shared_folder"])

    def _build(self):
        """Construit le tableau de fichiers avec scrollbar."""

        # ── Toolbar ───────────────────────────────────────────
        toolbar = tk.Frame(self.frame, bg="#ffffff", height=44)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)

        tk.Label(toolbar, text="Fichiers partagés",
                 font=("Helvetica", 12, "bold"),
                 bg="#ffffff", fg="#1c1c1a").pack(side="left", padx=14)

        tk.Button(
            toolbar, text="Ouvrir le dossier",
            font=("Helvetica", 10), relief="flat",
            bg="#f5f5f4", fg="#2563eb", cursor="hand2",
            command=self._open_folder
        ).pack(side="right", padx=12)

        tk.Frame(self.frame, bg="#e2e2e0", height=1).pack(fill="x")

        # ── Treeview ──────────────────────────────────────────
        cols = ("name", "size", "modified")
        self.tree = ttk.Treeview(
            self.frame, columns=cols,
            show="headings", selectmode="browse"
        )

        self.tree.heading("name",     text="Nom")
        self.tree.heading("size",     text="Taille")
        self.tree.heading("modified", text="Modifié le")

        self.tree.column("name",     width=340, anchor="w")
        self.tree.column("size",     width=90,  anchor="e")
        self.tree.column("modified", width=140, anchor="center")

        scrollbar = ttk.Scrollbar(self.frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=12)
        scrollbar.pack(side="right", fill="y", pady=12, padx=(0, 12))

        # ── Menu contextuel (clic droit) ──────────────────────
        self.menu = tk.Menu(self.frame, tearoff=0)
        self.menu.add_command(label="Télécharger", command=self._download_selected)
        self.menu.add_command(label="Supprimer",   command=self._delete_selected)
        self.tree.bind("<Button-3>", self._show_menu)

        # ── Label "vide" ──────────────────────────────────────
        self.empty_label = tk.Label(
            self.frame,
            text="Aucun fichier partagé\nGlisse des fichiers sur la page web pour commencer.",
            font=("Helvetica", 11), bg="#f5f5f4", fg="#737370",
            justify="center"
        )

    def refresh(self, folder: str):
        """Recharge la liste depuis le disque. Thread-safe via after()."""
        def _do():
            files = list_files(folder)
            # Vider le tree
            for item in self.tree.get_children():
                self.tree.delete(item)
            if files:
                self.empty_label.place_forget()
                for f in files:
                    self.tree.insert("", "end", iid=f["name"],
                                     values=(f["name"], f["size_str"], f["modified"]))
            else:
                self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        self.frame.after(0, _do)

    # ─── Actions ──────────────────────────────────────────────

    def _open_folder(self):
        path = os.path.abspath(self.config["shared_folder"])
        webbrowser.open(f"file://{path}")

    def _show_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.menu.post(event.x_root, event.y_root)

    def _download_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        port = self.config["server"]["port"]
        from core.network import get_local_ip
        url = f"http://{get_local_ip()}:{port}/download/{sel[0]}"
        webbrowser.open(url)

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        name = sel[0]
        if messagebox.askyesno("Supprimer", f"Supprimer « {name} » ?"):
            from core.file_manager import delete_file
            ok = delete_file(self.config["shared_folder"], name)
            if ok:
                self.tree.delete(name)
            else:
                messagebox.showerror("Erreur", "Impossible de supprimer le fichier.")