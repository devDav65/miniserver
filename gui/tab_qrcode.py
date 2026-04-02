import tkinter as tk
from tkinter import ttk, messagebox
import threading


class QRCodeTab:
    """
    Onglet 'QR Code' — affiche le QR code de l'URL du serveur.
    Le QR est généré dans un thread pour ne pas bloquer la GUI.
    """

    def __init__(self, parent: ttk.Notebook, config: dict):
        self.config = config
        self.current_url = ""
        self.frame = tk.Frame(parent, bg="#f5f5f4")
        self._build()

    def _build(self):

        # ── Titre ─────────────────────────────────────────────
        tk.Label(
            self.frame, text="Scanne ce QR code pour accéder au serveur",
            font=("Helvetica", 12), bg="#f5f5f4", fg="#1c1c1a"
        ).pack(pady=(28, 6))

        # ── URL texte ─────────────────────────────────────────
        self.url_label = tk.Label(
            self.frame, text="Chargement…",
            font=("Courier", 12), bg="#f5f5f4", fg="#2563eb",
            cursor="hand2"
        )
        self.url_label.pack(pady=(0, 16))
        self.url_label.bind("<Button-1>", lambda e: self._open_browser())

        # ── Image QR ──────────────────────────────────────────
        self.qr_canvas = tk.Canvas(
            self.frame, width=220, height=220,
            bg="#ffffff", highlightthickness=1,
            highlightbackground="#e2e2e0"
        )
        self.qr_canvas.pack(pady=(0, 16))

        self.qr_placeholder = self.qr_canvas.create_text(
            110, 110, text="Génération…",
            font=("Helvetica", 11), fill="#a8a8a4"
        )

        # ── Boutons ───────────────────────────────────────────
        btn_frame = tk.Frame(self.frame, bg="#f5f5f4")
        btn_frame.pack()

        tk.Button(
            btn_frame, text="Ouvrir dans le navigateur",
            font=("Helvetica", 10), relief="flat",
            bg="#2563eb", fg="#ffffff", cursor="hand2",
            padx=14, pady=6,
            command=self._open_browser
        ).pack(side="left", padx=6)

        tk.Button(
            btn_frame, text="Copier l'URL",
            font=("Helvetica", 10), relief="flat",
            bg="#f5f5f4", fg="#2563eb", cursor="hand2",
            padx=14, pady=6,
            command=self._copy_url
        ).pack(side="left", padx=6)

    def set_url(self, url: str):
        """
        Met à jour l'URL et régénère le QR code.
        Appelé depuis app_window après démarrage du serveur.
        """
        self.current_url = url
        self.url_label.config(text=url)
        # Génère dans un thread pour ne pas geler la GUI
        threading.Thread(target=self._generate_qr, daemon=True).start()

    def _generate_qr(self):
        """Génère le QR et l'affiche dans le canvas (thread séparé)."""
        try:
            from core.qr_generator import generate_qr_tkinter
            photo = generate_qr_tkinter(self.current_url, size=200)
            if photo:
                # Retour au thread principal pour toucher les widgets
                self.frame.after(0, lambda: self._show_qr(photo))
        except Exception as e:
            self.frame.after(0, lambda: self.qr_canvas.itemconfig(
                self.qr_placeholder, text=f"Erreur QR : {e}"
            ))

    def _show_qr(self, photo):
        """Affiche l'image QR dans le canvas (thread principal)."""
        # Garde une référence pour éviter le garbage collection
        self._photo = photo
        self.qr_canvas.delete("all")
        self.qr_canvas.create_image(110, 110, image=photo)

    def _open_browser(self):
        if self.current_url:
            import webbrowser
            webbrowser.open(self.current_url)

    def _copy_url(self):
        if self.current_url:
            self.frame.clipboard_clear()
            self.frame.clipboard_append(self.current_url)
            messagebox.showinfo("Copié", "URL copiée dans le presse-papiers !")