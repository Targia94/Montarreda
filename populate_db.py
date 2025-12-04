from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Base, User

# Utenti iniziali
users_data = [
    {"full_name": "Carlo D'Elia"},
    {"full_name": "Giovanni Tarantino"},
    {"full_name": "Samuele Tarantino"},
]


def populate_users():
    """Popola il database con gli utenti iniziali, evitando duplicati."""

    # 🔹 Assicura che il database e le tabelle esistano
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        nuovi_utenti = 0  # Contatore utenti aggiunti

        for user in users_data:
            existing_user = db.query(User).filter_by(full_name=user["full_name"]).first()
            if not existing_user:
                new_user = User(full_name=user["full_name"])
                db.add(new_user)
                nuovi_utenti += 1  # Aggiunge al contatore

        db.commit()


if __name__ == "__main__":
    populate_users()
