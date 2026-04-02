import io
import logging
import qrcode
from qrcode.image.pil import PilImage

logger = logging.getLogger(__name__)


def generate_qr(url: str, box_size: int = 8, border: int = 2) -> PilImage:
    """
    Génère un QR code à partir d'une URL.

    Args:
        url      : URL complète ex "http://192.168.1.42:8080"
        box_size : taille en pixels de chaque case du QR (défaut 8)
        border   : nombre de cases de marge blanche autour (défaut 2)

    Returns:
        Image Pillow (PIL.Image) — à afficher dans la GUI ou sauvegarder
    """
    qr = qrcode.QRCode(
        version=None,           # taille automatique selon le contenu
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    logger.info(f"QR code généré pour : {url}")
    return img


def generate_qr_bytes(url: str, box_size: int = 8, border: int = 2) -> bytes:
    """
    Génère un QR code et retourne les bytes PNG bruts.
    Utile pour envoyer le QR via une route HTTP (/qrcode.png).

    Args:
        url      : URL complète
        box_size : taille d'une case en pixels
        border   : marge en nombre de cases

    Returns:
        bytes PNG
    """
    img = generate_qr(url, box_size, border)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_qr_tkinter(url: str, size: int = 200):
    """
    Génère un QR code redimensionné pour l'affichage dans Tkinter.
    Retourne un objet ImageTk.PhotoImage.

    Args:
        url  : URL complète
        size : taille finale en pixels (carré) — défaut 200

    Returns:
        ImageTk.PhotoImage (utilisable directement dans un Label Tkinter)
    """
    try:
        from PIL import ImageTk
    except ImportError:
        logger.error("Pillow non installé — pip install Pillow")
        return None

    img = generate_qr(url, box_size=4, border=2)
    img_pil = img.get_image() if hasattr(img, "get_image") else img._img
    img_resized = img_pil.resize((size, size))
    return ImageTk.PhotoImage(img_resized)