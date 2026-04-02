import os
import queue
import datetime
from flask import current_app, request, render_template, send_from_directory, jsonify, session
from werkzeug.utils import secure_filename
from core.file_manager import list_files as fm_list_files


# ─────────────────────────────────────────────────────────────────
# Registre des propriétaires : { "nom_fichier": "ip_uploader" }
# Stocké en mémoire — réinitialisé au redémarrage du serveur.
# ─────────────────────────────────────────────────────────────────
_file_owners: dict[str, str] = {}


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _shared_folder() -> str:
    return current_app.config["SHARED_FOLDER"]


def _push_event(event_type: str, data: dict):
    q: queue.Queue = current_app.config.get("EVENT_QUEUE")
    if q:
        q.put({"type": event_type, "data": data, "time": datetime.datetime.now().isoformat()})


def _is_allowed(filename: str) -> bool:
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", [])
    if not allowed:
        return True
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed


def _is_authenticated() -> bool:
    mode = current_app.config.get("AUTH_MODE", "open")
    if mode == "open":
        return True
    if mode == "pin":
        return session.get("authenticated") is True
    if mode == "token":
        expected = current_app.config.get("AUTH_PIN", "")
        header = request.headers.get("Authorization", "")
        return header == f"Bearer {expected}"
    return False


def _is_server_host() -> bool:
    """
    Retourne True si la requête vient du PC hôte lui-même
    (127.0.0.1 ou ::1).
    """
    return request.remote_addr in ("127.0.0.1", "::1")


def _can_delete(filename: str) -> bool:
    """
    Règle de suppression :
      - L'hôte (127.0.0.1) peut tout supprimer.
      - Un client peut supprimer uniquement les fichiers qu'il a uploadés.
      - Les fichiers sans propriétaire connu (ex: déposés manuellement
        dans shared/) ne peuvent être supprimés que par l'hôte.
    """
    if _is_server_host():
        return True
    owner = _file_owners.get(filename)
    if owner is None:
        return False
    return owner == request.remote_addr


def _list_files() -> list[dict]:
    return fm_list_files(_shared_folder())


# ─────────────────────────────────────────────────────────────────
# Handlers
# ─────────────────────────────────────────────────────────────────

def handle_index():
    if not _is_authenticated():
        return render_template("auth.html"), 401

    files = _list_files()
    client_ip = request.remote_addr
    is_host = _is_server_host()

    # Pour chaque fichier, on indique si le client courant peut le supprimer
    for f in files:
        owner = _file_owners.get(f["name"])
        f["can_delete"] = is_host or (owner == client_ip)
        f["owner_ip"]   = owner or "—"

    _push_event("connection", {"ip": client_ip})
    return render_template("index.html", files=files, is_host=is_host)


def handle_upload():
    if not _is_authenticated():
        return jsonify({"error": "Non autorisé"}), 401

    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400

    uploaded = []
    errors = []
    uploader_ip = request.remote_addr

    for file in request.files.getlist("file"):
        if file.filename == "":
            continue

        filename = secure_filename(file.filename)

        if not _is_allowed(filename):
            errors.append(f"{filename} : extension non autorisée")
            continue

        dest = os.path.join(_shared_folder(), filename)
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest):
            filename = f"{base}_{counter}{ext}"
            dest = os.path.join(_shared_folder(), filename)
            counter += 1

        file.save(dest)
        size = os.path.getsize(dest)

        # Enregistre le propriétaire
        _file_owners[filename] = uploader_ip

        uploaded.append({"name": filename, "size": size, "can_delete": True})

        _push_event("upload", {
            "filename": filename,
            "size": size,
            "ip": uploader_ip,
        })

    if errors:
        return jsonify({"uploaded": uploaded, "errors": errors}), 207

    return jsonify({"uploaded": uploaded}), 200


def handle_download(filename: str):
    if not _is_authenticated():
        return jsonify({"error": "Non autorisé"}), 401

    safe_name = secure_filename(filename)
    folder = _shared_folder()

    if not os.path.isfile(os.path.join(folder, safe_name)):
        return jsonify({"error": "Fichier introuvable"}), 404

    _push_event("download", {"filename": safe_name, "ip": request.remote_addr})
    return send_from_directory(folder, safe_name, as_attachment=True)


def handle_delete(filename: str):
    if not _is_authenticated():
        return jsonify({"error": "Non autorisé"}), 401

    safe_name = secure_filename(filename)
    path = os.path.join(_shared_folder(), safe_name)

    if not os.path.isfile(path):
        return jsonify({"error": "Fichier introuvable"}), 404

    # Vérification du propriétaire
    if not _can_delete(safe_name):
        return jsonify({"error": "Non autorisé — seul celui qui a uploadé ce fichier peut le supprimer."}), 403

    os.remove(path)
    _file_owners.pop(safe_name, None)

    _push_event("delete", {"filename": safe_name, "ip": request.remote_addr})
    return jsonify({"deleted": safe_name}), 200


def handle_auth():
    mode = current_app.config.get("AUTH_MODE", "open")
    if mode != "pin":
        return jsonify({"error": "Auth non requise"}), 400

    data = request.get_json(silent=True) or {}
    pin_input = str(data.get("pin", ""))
    pin_expected = str(current_app.config.get("AUTH_PIN", ""))

    if pin_input == pin_expected and pin_expected != "":
        session["authenticated"] = True
        return jsonify({"success": True}), 200

    return jsonify({"error": "PIN incorrect"}), 401