import socket
import logging

logger = logging.getLogger(__name__)


def get_local_ip() -> str:
    """
    Détecte l'IP locale de la machine sur le réseau Wi-Fi.

    Astuce : on ouvre une socket UDP vers 8.8.8.8 (Google DNS)
    sans vraiment envoyer de paquet — Python choisit automatiquement
    l'interface réseau active, ce qui nous donne notre IP locale.

    Returns:
        IP locale ex: "192.168.1.42"
        ou "127.0.0.1" si aucune interface réseau trouvée.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.warning(f"Impossible de détecter l'IP locale : {e}")
        return "127.0.0.1"


def get_server_url(port: int) -> str:
    """
    Retourne l'URL complète du serveur.

    Args:
        port : port d'écoute du serveur Flask

    Returns:
        ex: "http://192.168.1.42:8080"
    """
    ip = get_local_ip()
    return f"http://{ip}:{port}"


def get_all_interfaces() -> list[dict]:
    """
    Liste toutes les interfaces réseau disponibles avec leur IP.
    Utile pour l'onglet Paramètres de la GUI.

    Returns:
        liste de dicts {"name": "eth0", "ip": "192.168.1.42"}
    """
    interfaces = []
    try:
        hostname = socket.gethostname()
        all_ips = socket.getaddrinfo(hostname, None)
        seen = set()
        for item in all_ips:
            ip = item[4][0]
            if ip not in seen and not ip.startswith("::") and ip != "127.0.0.1":
                seen.add(ip)
                interfaces.append({"name": hostname, "ip": ip})
    except Exception as e:
        logger.warning(f"Erreur listage interfaces : {e}")
    return interfaces