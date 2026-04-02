import queue
from server.app import create_app, load_config
from core.network import get_local_ip, get_server_url
from core.file_manager import list_files, get_folder_stats
from core.auth import verify_pin, generate_token

# Charge la config
config = load_config("config.json")

# Crée l'app sans GUI (queue = None)
q = queue.Queue()
app = create_app(config, event_queue=q)

if __name__ == "__main__":
    print("Serveur démarré sur http://localhost:8080")
    print("Dossier partagé :", app.config["SHARED_FOLDER"])
    print("Mode auth :", app.config["AUTH_MODE"])
    app.run(host="0.0.0.0", port=8080, debug=True)

print("IP locale      :", get_local_ip())
print("URL serveur    :", get_server_url(8080))
print("Fichiers       :", list_files("./shared"))
print("Stats dossier  :", get_folder_stats("./shared"))
print("Token généré   :", generate_token())
print("PIN correct    :", verify_pin("1234", "1234"))
print("PIN incorrect  :", verify_pin("0000", "1234"))