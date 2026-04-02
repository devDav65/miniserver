import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app_window import run_app

if __name__ == "__main__":
    run_app()