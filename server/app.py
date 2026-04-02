import json
import os
import queue
from flask import Flask


def load_config(path="config.json"):
    """Charge la configuration depuis config.json."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), path)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_app(config: dict, event_queue: queue.Queue = None) -> Flask:
    """
    Crée et configure l'instance Flask.

    Args:
        config      : dictionnaire chargé depuis config.json
        event_queue : file d'événements partagée avec la GUI
                      (None si on lance sans GUI)

    Returns:
        app : instance Flask prête à être lancée
    """
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"),
    )

    # ── Configuration Flask ──────────────────────────────────────
    app.config["MAX_CONTENT_LENGTH"] = config["max_file_size_mb"] * 1024 * 1024
    app.config["SHARED_FOLDER"] = os.path.abspath(config["shared_folder"])
    app.config["AUTH_MODE"] = config["auth"]["mode"]
    app.config["AUTH_PIN"] = config["auth"]["pin"]
    app.config["ALLOWED_EXTENSIONS"] = config.get("allowed_extensions", [])
    app.config["EVENT_QUEUE"] = event_queue
    app.secret_key = os.urandom(24)

    # ── Création du dossier partagé si inexistant ─────────────────
    os.makedirs(app.config["SHARED_FOLDER"], exist_ok=True)

    # ── Enregistrement des routes ────────────────────────────────
    from server.routes import register_routes
    register_routes(app)

    return app