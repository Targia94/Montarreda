import os
from sqlalchemy import create_engine, text
import sys
from sqlalchemy.orm import sessionmaker, declarative_base

# 🔹 Verifica se il programma è eseguito da un eseguibile PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)  # Se eseguibile, usa la cartella dell'exe
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Se script, usa la cartella dello script

# 🔹 Percorso del database nella stessa cartella dell'eseguibile
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# 🔹 Configura il database
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 🔹 Controllo e creazione del database
if not os.path.exists(DATABASE_PATH):
    print(f"⚠️ Database non trovato in {DATABASE_PATH}, creazione in corso...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database creato con successo!")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_database_empty():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        return len(result.fetchall()) == 0
