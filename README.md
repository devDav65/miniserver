# MiniServer

Un serveur de partage de fichiers local, léger et sans internet, avec interface graphique Python.

Lancez l'app sur votre PC, scannez le QR code avec votre téléphone, et partagez des fichiers avec tous les appareils connectés au même Wi-Fi — sans installer quoi que ce soit côté client.

---

## Aperçu

```
┌─────────────────────────────────┐
│  App Python (GUI)               │
│  ┌──────────┬──────────────┐    │
│  │ Fichiers │  Transferts  │    │     ┌──────────────┐
│  ├──────────┴──────────────┤    │◄───►│ Navigateur   │
│  │ Paramètres │  QR Code   │    │     │ mobile / PC  │
│  └───────────────────────── ┘   │     └──────────────┘
│         Serveur Flask :8080     │
└─────────────────────────────────┘
        Réseau Wi-Fi local
```

---

## Fonctionnalités

- Partage de fichiers sur le réseau local (Wi-Fi) sans internet
- Interface graphique Tkinter avec 4 onglets
- Page web responsive accessible depuis n'importe quel navigateur
- Upload par drag & drop avec barre de progression
- Téléchargement direct depuis le navigateur
- Génération automatique du QR code (URL locale)
- Détection automatique de l'IP locale
- Modes d'authentification : ouvert / PIN / token
- Logs en temps réel dans la GUI
- Configuration via `config.json`

---

## Prérequis

- Python 3.10 ou supérieur
- `tkinter` (inclus dans Python standard)
- Les dépendances listées dans `requirements.txt`

---

## Installation

**1. Cloner ou télécharger le projet**

```bash
git clone https://github.com/ton-user/miniserver.git
cd miniserver
```

**2. Créer un environnement virtuel (recommandé)**

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**3. Installer les dépendances**

```bash
pip install -r requirements.txt
```

**4. (Optionnel) Copier et adapter la configuration**

```bash
cp config.example.json config.json
```

---

## Lancement

```bash
python main.py
```

La fenêtre s'ouvre, le serveur démarre automatiquement sur le port configuré (défaut : `8080`).

Les autres appareils sur le même Wi-Fi accèdent au serveur via :

```
http://<IP_DE_TON_PC>:8080
```

L'URL exacte et le QR code sont affichés dans l'onglet **QR Code** de la GUI.

---

## Structure du projet

```
miniserver/
│
├── main.py                  # Point d'entrée
├── requirements.txt         # Dépendances pip
├── config.json              # Configuration locale (ignoré par git)
├── config.example.json      # Modèle de configuration
│
├── server/
│   ├── app.py               # Instance Flask
│   ├── routes.py            # Définition des routes HTTP
│   └── handlers.py          # Logique upload / download
│
├── core/
│   ├── file_manager.py      # Gestion des fichiers partagés
│   ├── network.py           # Détection IP, mDNS
│   ├── auth.py              # Authentification
│   └── qr_generator.py      # Génération du QR code
│
├── gui/
│   ├── app_window.py        # Fenêtre principale
│   ├── tab_files.py         # Onglet fichiers
│   ├── tab_transfers.py     # Onglet transferts
│   ├── tab_settings.py      # Onglet paramètres
│   └── tab_qrcode.py        # Onglet QR code
│
├── templates/
│   ├── base.html            # Layout HTML commun
│   └── index.html           # Page principale (liste + upload)
│
├── static/
│   ├── css/style.css        # Styles de l'interface web
│   └── js/upload.js         # Drag & drop, progression
│
├── shared/                  # Dossier partagé (contenu ignoré par git)
└── logs/                    # Logs d'accès et d'erreurs
```

---

## Configuration

Tous les réglages se font dans `config.json` :

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false
  },
  "shared_folder": "./shared",
  "auth": {
    "mode": "open",
    "pin": ""
  },
  "ui": {
    "theme": "light",
    "language": "fr"
  },
  "max_file_size_mb": 500,
  "allowed_extensions": []
}
```

| Clé | Valeurs possibles | Description |
|---|---|---|
| `server.port` | ex: `8080` | Port d'écoute du serveur |
| `shared_folder` | chemin relatif ou absolu | Dossier où les fichiers sont stockés |
| `auth.mode` | `open`, `pin`, `token` | Mode d'authentification |
| `auth.pin` | ex: `"1234"` | PIN requis si mode `pin` |
| `max_file_size_mb` | ex: `500` | Taille max des fichiers uploadés |
| `allowed_extensions` | ex: `[".pdf", ".jpg"]` | Liste blanche d'extensions (vide = tout autorisé) |

---

## Comment ça marche

1. `main.py` lance deux threads en parallèle : la **GUI Tkinter** et le **serveur Flask**
2. Flask écoute sur toutes les interfaces réseau (`0.0.0.0`) au port configuré
3. Le module `network.py` détecte l'IP locale automatiquement
4. Un QR code est généré avec cette URL et affiché dans la GUI
5. Les clients scannent le QR ou tapent l'URL dans leur navigateur
6. Les fichiers uploadés sont sauvegardés dans `shared/`
7. Les événements (upload, connexion) transitent via une `queue.Queue` pour mettre à jour la GUI en temps réel

---

## Sécurité

Ce serveur est conçu pour un usage sur **réseau local de confiance** uniquement.

- Ne pas exposer sur internet (pas de redirection de port)
- Utiliser le mode `pin` ou `token` sur les réseaux Wi-Fi partagés (café, bureau)
- Le `config.json` est exclu du dépôt git pour ne pas exposer les credentials

---

## Dépendances principales

| Package | Usage |
|---|---|
| `flask` | Serveur HTTP et routing |
| `werkzeug` | Sécurisation des noms de fichiers |
| `qrcode[pil]` | Génération du QR code |
| `Pillow` | Rendu image du QR code |
| `zeroconf` | Découverte automatique via mDNS |
| `ifaddr` | Détection de l'IP locale |
| `bcrypt` | Hashage du PIN |
| `humanize` | Affichage lisible des tailles de fichiers |

---

## Licence

MIT — libre d'utilisation, modification et distribution.
