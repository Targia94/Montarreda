from sqlalchemy import Column, Integer, String, Date, Time, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    timbrature = relationship("Timbratura", back_populates="utente", cascade="all, delete-orphan")


class Timbratura(Base):
    __tablename__ = "timbrature"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_utente = Column(Integer, ForeignKey("users.id"), nullable=False)
    data = Column(Date, nullable=False)  # Giorno della timbratura
    orario_ingresso = Column(Time, nullable=False)  # Solo ore e minuti
    orario_uscita = Column(Time, nullable=False)  # Solo ore e minuti
    tempo_lavorativo = Column(Integer, nullable=False)  # Calcolato in minuti

    utente = relationship("User", back_populates="timbrature")


class Lavoro(Base):
    __tablename__ = "lavoro"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(Date, nullable=False)  # Giorno dell'attività
    cliente = Column(String, nullable=False)  # Nome del cliente
    # ore = Column(Float, nullable=False)  # Ore lavorate
    contratto = Column(Float, nullable=False)  # Importo guadagnato
    saldato = Column(Float, nullable=False)  # Importo guadagnato
    commessa = Column(String, nullable=False)  # MOV / OLIE
    saldo = Column(String, nullable=False)  # Pagato / Pagato in negozio / Sospeso
    extra_consegna = Column(Float, nullable=True)  # Extra Consegna (opzionale)


