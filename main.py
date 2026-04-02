import sys
import os

# Assure que le dossier racine du projet est dans le path Python
# (nécessaire quand on lance depuis un autre répertoire)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app_window import AppWindow


def main():
    app = AppWindow()
    app.run()


if __name__ == "__main__":
    main()