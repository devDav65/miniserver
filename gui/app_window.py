import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from server.app import create_app, load_config
from core.network import get_server_url


class AppWindow:
    """
    Fenêtre principale de l'application.
    Lance le serveur Flask dans un thread séparé et
    affiche les 4 onglets : Fichiers, Transferts, QR Code, Paramètres.
    """

    def __init__(self):
        self.config = load_config()
        self.event_queue = queue.Queue()
        self.server_thread = None
        self.flask_app = None

        # ── Fenêtre racine ────────────────────────────────────
        self.root = tk.Tk()
        self.root.title("MiniServer")
        self.root.geometry("720x520")
        self.root.minsize(600, 420)
        self.root.configure(bg="#f5f5f4")

        self._build_ui()
        self._start_server()
        self._poll_events()   # démarre la boucle de lecture de la queue

    # ─────────────────────────────────────────────────────────
    # Construction de l'UI
    # ─────────────────────────────────────────────────────────

    def _build_ui(self):
        """Construit le header, les onglets et la status bar."""

        # ── Header ───────────────────────────────────────────
        header = tk.Frame(self.root, bg="#ffffff", height=52)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        tk.Label(
            header, text="  MiniServer",
            font=("Helvetica", 14, "bold"),
            bg="#ffffff", fg="#1c1c1a"
        ).pack(side="left", padx=8)

        self.status_dot = tk.Label(header, text="●", font=("Helvetica", 12),
                                   bg="#ffffff", fg="#d1d1cf")
        self.status_dot.pack(side="right", padx=(0, 12))

        self.status_label = tk.Label(header, text="Démarrage…",
                                     font=("Helvetica", 11),
                                     bg="#ffffff", fg="#737370")
        self.status_label.pack(side="right", padx=4)

        # ── Séparateur ───────────────────────────────────────
        tk.Frame(self.root, bg="#e2e2e0", height=1).pack(fill="x")

        # ── Notebook (onglets) ────────────────────────────────
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background="#f5f5f4", borderwidth=0)
        style.configure("TNotebook.Tab", padding=[16, 8], font=("Helvetica", 11))

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=0, pady=0)

        # Import ici pour éviter les imports circulaires
        from gui.tab_files     import FilesTab
        from gui.tab_transfers import TransfersTab
        from gui.tab_qrcode    import QRCodeTab
        from gui.tab_settings  import SettingsTab

        self.tab_files     = FilesTab(self.notebook, self.config)
        self.tab_transfers = TransfersTab(self.notebook)
        self.tab_qrcode    = QRCodeTab(self.notebook, self.config)
        self.tab_settings  = SettingsTab(self.notebook, self.config, self)

        self.notebook.add(self.tab_files.frame,     text="  Fichiers  ")
        self.notebook.add(self.tab_transfers.frame,  text="  Transferts  ")
        self.notebook.add(self.tab_qrcode.frame,    text="  QR Code  ")
        self.notebook.add(self.tab_settings.frame,  text="  Paramètres  ")

        # ── Status bar (bas) ──────────────────────────────────
        bar = tk.Frame(self.root, bg="#ffffff", height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Frame(bar, bg="#e2e2e0", height=1).pack(fill="x")

        self.bar_label = tk.Label(bar, text="", font=("Helvetica", 10),
                                  bg="#ffffff", fg="#737370")
        self.bar_label.pack(side="left", padx=12)

    # ─────────────────────────────────────────────────────────
    # Serveur Flask dans un thread daemon
    # ─────────────────────────────────────────────────────────

    def _start_server(self):
        """Lance Flask dans un thread daemon (s'arrête avec la GUI)."""
        self.flask_app = create_app(self.config, self.event_queue)
        port = self.config["server"]["port"]

        def run():
            self.flask_app.run(
                host=self.config["server"]["host"],
                port=port,
                debug=False,
                use_reloader=False,   # IMPORTANT : pas de double thread
            )

        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()

        url = get_server_url(port)
        self._set_status(f"En ligne — {url}", online=True)
        self.tab_qrcode.set_url(url)
        self.bar_label.config(text=url)

    # ─────────────────────────────────────────────────────────
    # Boucle de lecture de la queue d'événements
    # ─────────────────────────────────────────────────────────

    def _poll_events(self):
        """
        Lit la queue toutes les 200 ms et dispatch les événements
        vers les onglets concernés.
        Tkinter n'est pas thread-safe : on ne peut pas toucher
        les widgets depuis le thread Flask — cette méthode
        fait le pont depuis le thread principal.
        """
        try:
            while True:
                event = self.event_queue.get_nowait()
                self._dispatch(event)
        except queue.Empty:
            pass
        # Replanifie dans 200 ms
        self.root.after(200, self._poll_events)

    def _dispatch(self, event: dict):
        """Route un événement vers le bon onglet."""
        t = event.get("type")
        d = event.get("data", {})

        if t == "upload":
            self.tab_transfers.add_event("upload", d)
            self.tab_files.refresh(self.config["shared_folder"])

        elif t == "download":
            self.tab_transfers.add_event("download", d)

        elif t == "delete":
            self.tab_transfers.add_event("delete", d)
            self.tab_files.refresh(self.config["shared_folder"])

        elif t == "connection":
            self.tab_transfers.add_event("connection", d)

    # ─────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────

    def _set_status(self, text: str, online: bool = True):
        color = "#16a34a" if online else "#dc2626"
        self.status_dot.config(fg=color)
        self.status_label.config(text=text)

    def reload_config(self, new_config: dict):
        """Appelé depuis SettingsTab quand l'utilisateur sauvegarde."""
        self.config = new_config
        self.tab_qrcode.set_url(get_server_url(new_config["server"]["port"]))

    def run(self):
        """Lance la boucle principale Tkinter."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        if messagebox.askokcancel("Quitter", "Arrêter le serveur et quitter ?"):
            self.root.destroy()