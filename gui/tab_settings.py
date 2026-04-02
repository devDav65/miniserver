import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class SettingsTab:
    """
    Onglet 'Paramètres' — permet de modifier port, dossier partagé
    et mode d'authentification. Sauvegarde dans config.json.
    """

    def __init__(self, parent: ttk.Notebook, config: dict, app_window):
        self.config = config
        self.app_window = app_window   # pour appeler reload_config()
        self.frame = tk.Frame(parent, bg="#f5f5f4")
        self._build()

    def _build(self):

        # ── Conteneur centré ──────────────────────────────────
        inner = tk.Frame(self.frame, bg="#ffffff",
                         relief="flat", bd=0)
        inner.place(relx=0.5, rely=0.5, anchor="center",
                    width=460, height=370)

        tk.Label(inner, text="Paramètres du serveur",
                 font=("Helvetica", 13, "bold"),
                 bg="#ffffff", fg="#1c1c1a").grid(
                     row=0, column=0, columnspan=3,
                     sticky="w", padx=24, pady=(22, 18))

        # ── Port ──────────────────────────────────────────────
        self._row_label(inner, 1, "Port")
        self.port_var = tk.StringVar(value=str(self.config["server"]["port"]))
        tk.Entry(inner, textvariable=self.port_var,
                 font=("Helvetica", 11), width=10,
                 relief="solid", bd=1).grid(
                     row=1, column=1, sticky="w", pady=8)
        tk.Label(inner, text="(redémarrage requis)",
                 font=("Helvetica", 9), bg="#ffffff",
                 fg="#a8a8a4").grid(row=1, column=2, sticky="w", padx=8)

        # ── Dossier partagé ───────────────────────────────────
        self._row_label(inner, 2, "Dossier partagé")
        self.folder_var = tk.StringVar(value=self.config["shared_folder"])
        folder_frame = tk.Frame(inner, bg="#ffffff")
        folder_frame.grid(row=2, column=1, columnspan=2, sticky="ew", pady=8)

        tk.Entry(folder_frame, textvariable=self.folder_var,
                 font=("Helvetica", 10), width=24,
                 relief="solid", bd=1).pack(side="left")

        tk.Button(
            folder_frame, text="…",
            font=("Helvetica", 10), relief="flat",
            bg="#f5f5f4", fg="#1c1c1a", cursor="hand2",
            padx=6, command=self._browse_folder
        ).pack(side="left", padx=4)

        # ── Mode auth ─────────────────────────────────────────
        self._row_label(inner, 3, "Authentification")
        self.auth_var = tk.StringVar(value=self.config["auth"]["mode"])
        modes = [("Ouvert", "open"), ("PIN", "pin"), ("Token", "token")]
        auth_frame = tk.Frame(inner, bg="#ffffff")
        auth_frame.grid(row=3, column=1, columnspan=2, sticky="w", pady=8)
        for label, val in modes:
            tk.Radiobutton(
                auth_frame, text=label, variable=self.auth_var, value=val,
                font=("Helvetica", 10), bg="#ffffff",
                command=self._toggle_pin_field
            ).pack(side="left", padx=(0, 10))

        # ── PIN ───────────────────────────────────────────────
        self._row_label(inner, 4, "PIN / Token")
        self.pin_var = tk.StringVar(value=self.config["auth"].get("pin", ""))
        self.pin_entry = tk.Entry(inner, textvariable=self.pin_var,
                                  font=("Helvetica", 11), width=20,
                                  relief="solid", bd=1, show="●")
        self.pin_entry.grid(row=4, column=1, sticky="w", pady=8)
        self._toggle_pin_field()

        # ── Taille max ────────────────────────────────────────
        self._row_label(inner, 5, "Taille max (MB)")
        self.maxsize_var = tk.StringVar(
            value=str(self.config.get("max_file_size_mb", 500)))
        tk.Entry(inner, textvariable=self.maxsize_var,
                 font=("Helvetica", 11), width=10,
                 relief="solid", bd=1).grid(
                     row=5, column=1, sticky="w", pady=8)

        # ── Séparateur ────────────────────────────────────────
        tk.Frame(inner, bg="#e2e2e0", height=1).grid(
            row=6, column=0, columnspan=3, sticky="ew",
            padx=24, pady=(12, 0))

        # ── Bouton sauvegarder ────────────────────────────────
        tk.Button(
            inner, text="Sauvegarder",
            font=("Helvetica", 11), relief="flat",
            bg="#2563eb", fg="#ffffff", cursor="hand2",
            padx=18, pady=8,
            command=self._save
        ).grid(row=7, column=0, columnspan=3, pady=18)

        inner.columnconfigure(1, weight=1)

    # ─── Helpers ──────────────────────────────────────────────

    def _row_label(self, parent, row, text):
        tk.Label(parent, text=text,
                 font=("Helvetica", 11), bg="#ffffff",
                 fg="#1c1c1a", width=16, anchor="w").grid(
                     row=row, column=0, sticky="w", padx=(24, 0), pady=8)

    def _toggle_pin_field(self):
        """Active/désactive le champ PIN selon le mode choisi."""
        if self.auth_var.get() == "open":
            self.pin_entry.config(state="disabled")
        else:
            self.pin_entry.config(state="normal")

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Choisir le dossier partagé")
        if path:
            self.folder_var.set(path)

    def _save(self):
        """Valide, met à jour config.json et notifie app_window."""
        try:
            port = int(self.port_var.get())
            assert 1024 <= port <= 65535
        except (ValueError, AssertionError):
            messagebox.showerror("Erreur", "Port invalide (1024–65535).")
            return

        try:
            max_mb = int(self.maxsize_var.get())
            assert max_mb > 0
        except (ValueError, AssertionError):
            messagebox.showerror("Erreur", "Taille max invalide.")
            return

        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showerror("Erreur", "Le dossier partagé ne peut pas être vide.")
            return
        os.makedirs(folder, exist_ok=True)

        # Mise à jour du dict config
        self.config["server"]["port"]       = port
        self.config["shared_folder"]        = folder
        self.config["auth"]["mode"]         = self.auth_var.get()
        self.config["auth"]["pin"]          = self.pin_var.get()
        self.config["max_file_size_mb"]     = max_mb

        # Sauvegarde sur disque
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

        # Notifie la fenêtre principale
        self.app_window.reload_config(self.config)
        messagebox.showinfo("Sauvegardé", "Paramètres enregistrés.\nRedémarre l'app pour appliquer le changement de port.")