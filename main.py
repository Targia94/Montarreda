import sys
import os
from fastapi import FastAPI
import uvicorn
from fastapi.openapi.docs import get_swagger_ui_html
from routes import router  # ✅ Importa correttamente
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Accetta richieste da qualsiasi origine (puoi specificare il frontend)
    allow_credentials=True,
    allow_methods=["*"],   # ✅ Permette tutti i metodi HTTP (GET, POST, OPTIONS, ecc.)
    allow_headers=["*"],   # ✅ Permette tutti gli header
)

app.include_router(router)


@app.get("/swagger", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")


# Endpoint per generare l'OpenAPI JSON
@app.get("/openapi.json", include_in_schema=False)
async def get_openapi():
    return app.openapi()


@app.get("/")
def home():
    return {"message": "Benvenuto nell'App di gestione!"}


# Avvia il server FastAPI
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
