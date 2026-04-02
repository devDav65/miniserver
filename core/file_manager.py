import os
import datetime
import logging

logger = logging.getLogger(__name__)


def _format_size(size_bytes: int) -> str:
    """Convertit un nombre d'octets en chaîne lisible (KB, MB, GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.2f} GB"


def list_files(folder: str) -> list[dict]:
    """
    Liste tous les fichiers du dossier partagé.

    Args:
        folder : chemin absolu du dossier partagé

    Returns:
        liste de dicts triée par nom :
        {
            "name"     : "photo.jpg",
            "size"     : 204800,
            "size_str" : "200.0 KB",
            "modified" : "02/04/2026 09:30",
            "path"     : "/home/david/miniserver/shared/photo.jpg"
        }
    """
    if not os.path.isdir(folder):
        logger.error(f"Dossier introuvable : {folder}")
        return []

    files = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        stat = os.stat(path)
        files.append({
            "name":     name,
            "size":     stat.st_size,
            "size_str": _format_size(stat.st_size),
            "modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
            "path":     path,
        })
    return files


def get_file_info(folder: str, filename: str) -> dict | None:
    """
    Retourne les infos d'un fichier précis.

    Returns:
        dict avec name/size/size_str/modified/path
        ou None si le fichier n'existe pas.
    """
    path = os.path.join(folder, filename)
    if not os.path.isfile(path):
        return None
    stat = os.stat(path)
    return {
        "name":     filename,
        "size":     stat.st_size,
        "size_str": _format_size(stat.st_size),
        "modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
        "path":     path,
    }


def delete_file(folder: str, filename: str) -> bool:
    """
    Supprime un fichier du dossier partagé.

    Returns:
        True si supprimé, False si fichier introuvable.
    """
    path = os.path.join(folder, filename)
    if not os.path.isfile(path):
        logger.warning(f"Suppression impossible, fichier introuvable : {path}")
        return False
    os.remove(path)
    logger.info(f"Fichier supprimé : {filename}")
    return True


def get_folder_stats(folder: str) -> dict:
    """
    Retourne des statistiques globales sur le dossier partagé.
    Utilisé dans l'onglet Paramètres de la GUI.

    Returns:
        {
            "count"         : 5,
            "total_size"    : 1048576,
            "total_size_str": "1.0 MB"
        }
    """
    files = list_files(folder)
    total = sum(f["size"] for f in files)
    return {
        "count":          len(files),
        "total_size":     total,
        "total_size_str": _format_size(total),
    }