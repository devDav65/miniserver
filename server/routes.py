from flask import Flask, request
from server.handlers import (
    handle_index,
    handle_upload,
    handle_download,
    handle_delete,
    handle_auth,
)


def register_routes(app: Flask):
    """
    Déclare toutes les URLs du serveur.
    Séparé de app.py pour garder chaque fichier focused.
    """

    # ── Page principale ──────────────────────────────────────────
    # GET /  →  affiche la liste des fichiers
    @app.route("/", methods=["GET"])
    def index():
        return handle_index()

    # ── Upload ───────────────────────────────────────────────────
    # POST /upload  →  reçoit un ou plusieurs fichiers
    @app.route("/upload", methods=["POST"])
    def upload():
        return handle_upload()

    # ── Download ─────────────────────────────────────────────────
    # GET /download/<filename>  →  envoie le fichier au client
    @app.route("/download/<path:filename>", methods=["GET"])
    def download(filename):
        return handle_download(filename)

    # ── Suppression ──────────────────────────────────────────────
    # DELETE /delete/<filename>  →  supprime le fichier du dossier
    @app.route("/delete/<path:filename>", methods=["DELETE"])
    def delete(filename):
        return handle_delete(filename)

    # ── Authentification (mode PIN) ───────────────────────────────
    # POST /auth  →  vérifie le PIN, retourne un cookie de session
    @app.route("/auth", methods=["POST"])
    def auth():
        return handle_auth()

    # ── Gestion des erreurs ───────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Ressource introuvable"}, 404

    @app.errorhandler(413)
    def file_too_large(e):
        return {"error": "Fichier trop volumineux"}, 413

    @app.errorhandler(500)
    def server_error(e):
        return {"error": "Erreur interne du serveur"}, 500