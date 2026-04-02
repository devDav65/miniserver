import tkinter as tk
from tkinter import ttk
from datetime import datetime


class TransfersTab:
    """
    Onglet 'Transferts' — journal en temps réel des événements :
    connexions, uploads, téléchargements, suppressions.
    Les événements arrivent via app_window._dispatch() depuis la queue.
    """

    # Couleurs par type d'événement
    COLORS = {
        "upload":     "#16a34a",   # vert
        "download":   "#2563eb",   # bleu
        "delete":     "#dc2626",   # rouge
        "connection": "#737370",   # gris
    }

    ICONS = {
        "upload":     "↑",
        "download":   "↓",
        "delete":     "✕",
        "connection": "→",
    }

    def __init__(self, parent: ttk.Notebook):
        self.frame = tk.Frame(parent, bg="#f5f5f4")
        self._build()

    def _build(self):

        # ── Toolbar ───────────────────────────────────────────
        toolbar = tk.Frame(self.frame, bg="#ffffff", height=44)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)

        tk.Label(toolbar, text="Journal des transferts",
                 font=("Helvetica", 12, "bold"),
                 bg="#ffffff", fg="#1c1c1a").pack(side="left", padx=14)

        tk.Button(
            toolbar, text="Effacer",
            font=("Helvetica", 10), relief="flat",
            bg="#f5f5f4", fg="#737370", cursor="hand2",
            command=self._clear
        ).pack(side="right", padx=12)

        tk.Frame(self.frame, bg="#e2e2e0", height=1).pack(fill="x")

        # ── Zone de logs avec scrollbar ───────────────────────
        container = tk.Frame(self.frame, bg="#f5f5f4")
        container.pack(fill="both", expand=True, padx=12, pady=12)

        self.text = tk.Text(
            container,
            font=("Courier", 11),
            bg="#ffffff", fg="#1c1c1a",
            relief="flat",
            borderwidth=1,
            state="disabled",
            wrap="word",
            cursor="arrow",
        )
        scrollbar = ttk.Scrollbar(container, orient="vertical",
                                  command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)

        self.text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Tags de couleur pour chaque type d'événement
        for evt_type, color in self.COLORS.items():
            self.text.tag_configure(evt_type, foreground=color)
        self.text.tag_configure("time", foreground="#a8a8a4")

        self._log_system("Serveur démarré — en attente de connexions…")

    def add_event(self, event_type: str, data: dict):
        """
        Ajoute une ligne dans le journal.
        Appelé depuis app_window._dispatch() (thread principal).
        """
        icon = self.ICONS.get(event_type, "·")
        time_str = datetime.now().strftime("%H:%M:%S")

        if event_type == "upload":
            msg = f"{icon} {data.get('ip','?')} — upload : {data.get('filename','?')} ({data.get('size',0)} o)"
        elif event_type == "download":
            msg = f"{icon} {data.get('ip','?')} — téléchargement : {data.get('filename','?')}"
        elif event_type == "delete":
            msg = f"{icon} {data.get('ip','?')} — suppression : {data.get('filename','?')}"
        elif event_type == "connection":
            msg = f"{icon} Connexion depuis {data.get('ip','?')}"
        else:
            msg = f"· {event_type} : {data}"

        self._append_line(time_str, msg, event_type)

    def _append_line(self, time_str: str, msg: str, tag: str):
        """Insère une ligne colorée dans le widget Text."""
        self.text.configure(state="normal")
        self.text.insert("end", f"[{time_str}] ", "time")
        self.text.insert("end", msg + "\n", tag)
        self.text.see("end")   # auto-scroll vers le bas
        self.text.configure(state="disabled")

    def _log_system(self, msg: str):
        self._append_line(
            datetime.now().strftime("%H:%M:%S"),
            msg, "connection"
        )

    def _clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")
        self._log_system("Journal effacé.")