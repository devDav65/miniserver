import os
import queue
import datetime
from flask import current_app, request, render_template, send_from_directory, jsonify, session
from werkzeug.utils import secure_filename


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _shared_folder() -> str:
    """Retourne le chemin absolu du dossier partagé."""
    return current_app.config["SHARED_FOLDER"]


def _push_event(event_type: str, data: dict):
    """
    Envoie un événement à la GUI via la queue.
    Si pas de GUI (event_queue = None), on ignore silencieusement.
    """
    q: queue.Queue = current_app.config.get("EVENT_QUEUE")
    if q:
        q.put({"type": event_type, "data": data, "time": datetime.datetime.now().isoformat()})


def _is_allowed(filename: str) -> bool:
    """Vérifie que l'extension est autorisée (liste blanche)."""
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", [])
    if not allowed:
        return True
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed


def _is_authenticated() -> bool:
    """
    Vérifie si la requête est authentifiée selon le mode configuré.
      - open  : toujours True
      - pin   : vérifie la session Flask
      - token : vérifie le header Authorization: Bearer <token>
    """
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


def _list_files() -> list[dict]:
    """
    Retourne la liste des fichiers du dossier partagé.
    Chaque fichier est un dict : name, size, modified.
    """
    folder = _shared_folder()
    files = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            stat = os.stat(path)
            files.append({
                "name": name,
                "size": stat.st_size,
                "modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
            })
    return files


# ─────────────────────────────────────────────────────────────────
# Handlers
# ─────────────────────────────────────────────────────────────────

def handle_index():
    """
    GET /
    Affiche la page principale avec la liste des fichiers.
    Redirige vers la page d'auth si nécessaire.
    """
    if not _is_authenticated():
        return render_template("auth.html"), 401

    files = _list_files()
    _push_event("connection", {"ip": request.remote_addr})
    return render_template("index.html", files=files)


def handle_upload():
    """
    POST /upload
    Reçoit un fichier, le valide, le sauvegarde dans shared/.
    Retourne du JSON pour que upload.js puisse mettre à jour l'UI.
    """
    if not _is_authenticated():
        return jsonify({"error": "Non autorisé"}), 401

    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400

    uploaded = []
    errors = []

    for file in request.files.getlist("file"):
        if file.filename == "":
            continue

        filename = secure_filename(file.filename)

        if not _is_allowed(filename):
            errors.append(f"{filename} : extension non autorisée")
            continue

        dest = os.path.join(_shared_folder(), filename)

        # Si le fichier existe déjà, on ajoute un suffixe
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest):
            filename = f"{base}_{counter}{ext}"
            dest = os.path.join(_shared_folder(), filename)
            counter += 1

        file.save(dest)
        size = os.path.getsize(dest)
        uploaded.append({"name": filename, "size": size})

        _push_event("upload", {
            "filename": filename,
            "size": size,
            "ip": request.remote_addr,
        })

    if errors:
        return jsonify({"uploaded": uploaded, "errors": errors}), 207

    return jsonify({"uploaded": uploaded}), 200


def handle_download(filename: str):
    """
    GET /download/<filename>
    Envoie le fichier au navigateur pour téléchargement.
    """
    if not _is_authenticated():
        return jsonify({"error": "Non autorisé"}), 401

    safe_name = secure_filename(filename)
    folder = _shared_folder()

    if not os.path.isfile(os.path.join(folder, safe_name)):
        return jsonify({"error": "Fichier introuvable"}), 404

    _push_event("download", {
        "filename": safe_name,
        "ip": request.remote_addr,
    })

    return send_from_directory(folder, safe_name, as_attachment=True)


def handle_delete(filename: str):
    """
    DELETE /delete/<filename>
    Supprime le fichier du dossier partagé.
    """
    if not _is_authenticated():
        return jsonify({"error": "Non autorisé"}), 401

    safe_name = secure_filename(filename)
    path = os.path.join(_shared_folder(), safe_name)

    if not os.path.isfile(path):
        return jsonify({"error": "Fichier introuvable"}), 404

    os.remove(path)

    _push_event("delete", {
        "filename": safe_name,
        "ip": request.remote_addr,
    })

    return jsonify({"deleted": safe_name}), 200


def handle_auth():
    """
    POST /auth
    Vérifie le PIN envoyé dans le body JSON.
    En cas de succès, marque la session comme authentifiée.
    """
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