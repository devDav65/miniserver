import hashlib
import secrets
import logging

logger = logging.getLogger(__name__)


def hash_pin(pin: str) -> str:
    """
    Hash un PIN avec SHA-256.
    On n'utilise pas bcrypt ici pour garder la vérification rapide
    (le PIN est court, SHA-256 suffit avec un salt fixe par session).

    Args:
        pin : ex "1234"

    Returns:
        hash hex : ex "03ac674216f3e15c..."
    """
    return hashlib.sha256(pin.encode()).hexdigest()


def verify_pin(pin_input: str, pin_expected: str) -> bool:
    """
    Compare le PIN saisi avec le PIN attendu.
    Utilise secrets.compare_digest pour éviter les timing attacks.

    Args:
        pin_input    : PIN tapé par l'utilisateur
        pin_expected : PIN stocké dans config.json

    Returns:
        True si les deux correspondent
    """
    if not pin_expected:
        logger.warning("Aucun PIN configuré, auth refusée")
        return False
    return secrets.compare_digest(
        pin_input.strip(),
        pin_expected.strip()
    )


def generate_token(length: int = 32) -> str:
    """
    Génère un token aléatoire sécurisé pour le mode 'token'.
    À appeler une fois à la création de la config, puis stocker
    le résultat dans config.json > auth > pin.

    Args:
        length : longueur du token en caractères (défaut 32)

    Returns:
        ex: "a3f9c2e1d4b7..." (hex)
    """
    return secrets.token_hex(length // 2)


def get_auth_mode_label(mode: str) -> str:
    """
    Retourne un label lisible du mode auth pour la GUI.

    Args:
        mode : "open" | "pin" | "token"

    Returns:
        ex: "Ouvert (sans authentification)"
    """
    labels = {
        "open":  "Ouvert (sans authentification)",
        "pin":   "PIN requis",
        "token": "Token Bearer requis",
    }
    return labels.get(mode, "Inconnu")