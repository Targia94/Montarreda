import subprocess
import os
import time
import threading
import webbrowser
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from routes import router  # Assicurati che il tuo router sia corretto

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

project_dir = os.path.dirname(os.path.abspath(__file__))
database_path = os.path.join(project_dir, "database.db")

# Se il database è vuoto, popola i dati
from database import is_database_empty
if is_database_empty():
    from populate_db import populate_users
    populate_users()


@app.get("/swagger", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")


@app.get("/openapi.json", include_in_schema=False)
async def get_openapi():
    return app.openapi()


@app.get("/")
def home():
    return {"message": "Benvenuto nell'App di gestione!"}


# Funzione per avviare il server FastAPI in un thread separato
def start_api():
    uvicorn.run(app, host="127.0.0.1", port=8000, http="h11")


# Funzione per aprire il browser dopo che il server è attivo
def open_browser():
    time.sleep(2)  # Attendi che il server si avvii

    # Trova il percorso assoluto del file index.html
    base_path = os.path.dirname(os.path.abspath(__file__))  # Ottieni la cartella del file eseguibile
    file_path = os.path.join(base_path, "index.html")  # Costruisci il percorso assoluto

    # Apri il file HTML nel browser
    webbrowser.open(f"file://{file_path}")


if __name__ == "__main__":
    # Avvia il server FastAPI in un thread separato
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()

    # Avvia il browser
    open_browser()

    # Mantieni il programma in esecuzione
    api_thread.join()
