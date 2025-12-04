import webbrowser
import subprocess
import time
import os
import sys

# Determina il percorso del progetto e del database
project_dir = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    project_dir = sys._MEIPASS  # Percorso corretto se è un eseguibile

database_path = os.path.join(project_dir, "database.db")

# Se il database non esiste, crealo
if not os.path.exists(database_path):
    from populate_db import populate_users
    populate_users()

# Avvia il backend FastAPI
backend_process = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=project_dir,
    stdout=subprocess.DEVNULL,  # ✅ Evita che i log blocchino l'esecuzione
    stderr=subprocess.DEVNULL
)

# Attendi che il server FastAPI sia pronto
time.sleep(3)  # 🔴 Potrebbe servire più tempo su alcuni PC

# ✅ Controlla se il server è attivo prima di aprire la pagina
import socket
def is_server_running(host="127.0.0.1", port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) == 0

# Attendi fino a che il server non è pronto
max_attempts = 2
attempts = 0
while attempts < max_attempts:
    if is_server_running():
        break
    attempts += 1
    time.sleep(1)  # Attendi prima di riprovare

# Apri automaticamente la pagina web
frontend_path = os.path.join(project_dir, "index.html")
print(f"📂 Percorso dell'HTML: {frontend_path}")
if os.path.exists(frontend_path):
    webbrowser.open(f"file://{frontend_path}")
else:
    print("❌ Errore: il file index.html non è stato trovato!")

# Mantieni attivo il backend senza bloccare l'esecuzione
try:
    backend_process.wait()
except KeyboardInterrupt:
    backend_process.terminate()
