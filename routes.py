from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime, date, time
from models import Timbratura, User  # ✅ Import corretto
from pydantic import BaseModel
from typing import List
from sqlalchemy import func, extract
from models import Lavoro
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from database import get_db
from models import Timbratura, Lavoro, User
from fpdf import FPDF


router = APIRouter()


class LoginRequest(BaseModel):
    code: str


class TimbraturaRequest(BaseModel):
    id_utente: int
    data: str
    orario_ingresso: str
    orario_uscita: str


class TimbraturaUser(BaseModel):
    id_utente: int


class LavoroRequest(BaseModel):
    data: str  # Formato YYYY-MM-DD
    cliente: str
    contratto: float
    saldato: float
    commessa: str
    saldo: str
    extra_consegna: float = 0.0


class GiornoRequest(BaseModel):
    data: str  # Formato YYYY-MM-DD


def safe_text(text):
    """ Converte il testo per evitare errori di encoding in FPDF """
    if isinstance(text, str):
        return text.encode("latin-1", "ignore").decode("latin-1")
    return str(text)


@router.post("/login")
@router.post("/login", include_in_schema=False)
def login(payload: LoginRequest):
    if payload.code == "0000":
        return {"message": "Login riuscito", "token": "fake-token"}
    else:
        raise HTTPException(status_code=401, detail="Codice errato")


@router.post("/timbrature")
def inserisci_timbratura(payload: TimbraturaRequest, db: Session = Depends(get_db)):
    # Converti la data e gli orari
    giorno = datetime.strptime(payload.data, "%Y-%m-%d").date()  # Data separata
    ingresso = datetime.strptime(payload.orario_ingresso, "%H:%M").time()  # Solo ore/minuti
    uscita = datetime.strptime(payload.orario_uscita, "%H:%M").time()  # Solo ore/minuti

    if ingresso >= uscita:
        raise HTTPException(status_code=400, detail="L'orario di ingresso deve essere minore di quello di uscita.")

    # Controlla se esiste già una timbratura per lo stesso utente e giorno
    timbratura_esistente = db.query(Timbratura).filter(
        Timbratura.id_utente == payload.id_utente,
        Timbratura.data == giorno
    ).first()

    # Calcolo tempo lavorativo in minuti
    tempo_lavorativo = (datetime.combine(giorno, uscita) - datetime.combine(giorno, ingresso)).total_seconds() // 60

    if timbratura_esistente:
        return {
            "message": "Esiste già una timbratura per questo utente in questa data.",
            "timbratura": {
                "data": timbratura_esistente.data.strftime("%Y-%m-%d"),
                "orario_ingresso": timbratura_esistente.orario_ingresso.strftime("%H:%M"),
                "orario_uscita": timbratura_esistente.orario_uscita.strftime("%H:%M"),
                "tempo_lavorativo": timbratura_esistente.tempo_lavorativo
            },
            "modifica": True  # Indica al frontend che è possibile modificare
        }

    # Creazione nuova timbratura
    nuova_timbratura = Timbratura(
        id_utente=payload.id_utente,
        data=giorno,
        orario_ingresso=ingresso,
        orario_uscita=uscita,
        tempo_lavorativo=int(tempo_lavorativo)
    )

    db.add(nuova_timbratura)
    db.commit()
    db.refresh(nuova_timbratura)

    return {"message": "Timbratura registrata con successo!", "timbratura": nuova_timbratura}


@router.get("/timbrature")
def get_timbrature(utente: int, data: date, db: Session = Depends(get_db)):
    """
    Recupera le timbrature filtrate per utente, mese e anno della data fornita.
    """
    mese = data.month
    anno = data.year

    timbrature = db.query(Timbratura).filter(
        Timbratura.id_utente == utente,
        extract("month", Timbratura.data) == mese,
        extract("year", Timbratura.data) == anno
    ).order_by(Timbratura.data.asc(), Timbratura.orario_ingresso.asc()).all()

    return [
        {
            "id": t.id,
            "data": t.data.strftime("%Y-%m-%d"),
            "orario_ingresso": t.orario_ingresso.strftime("%H:%M"),
            "orario_uscita": t.orario_uscita.strftime("%H:%M"),
            "tempo_lavorativo": t.tempo_lavorativo
        }
        for t in timbrature
    ]


@router.delete("/timbrature/{timbratura_id}")
def elimina_timbratura(timbratura_id: int, db: Session = Depends(get_db)):
    """
    Elimina una timbratura esistente.
    """
    timbratura = db.query(Timbratura).filter(Timbratura.id == timbratura_id).first()

    if not timbratura:
        raise HTTPException(status_code=404, detail="Timbratura non trovata.")

    db.delete(timbratura)
    db.commit()
    return {"message": "Timbratura eliminata con successo."}


@router.get("/users")
@router.post("/users/", include_in_schema=False)
def get_users(db: Session = Depends(get_db)):
    utenti = db.query(User).all()

    return [{"id": user.id, "full_name": user.full_name} for user in utenti]


@router.post("/lavoro")
def get_lavoro(payload: GiornoRequest, db: Session = Depends(get_db)):
    giorno = datetime.strptime(payload.data, "%Y-%m-%d").date()

    lavori = db.query(Lavoro).filter(Lavoro.data == giorno).all()

    return [
        {
            "id": lavoro.id,
            "cliente": lavoro.cliente,
            # "ore": lavoro.ore,
            "contratto": lavoro.contratto,
            "saldato": lavoro.saldato,
            "commessa": lavoro.commessa,
            # "pagamento": lavoro.pagamento,
            "saldo": lavoro.saldo,
            "extra_consegna": lavoro.extra_consegna
        }
        for lavoro in lavori
    ]


@router.post("/lavoro/nuovo")
def inserisci_lavoro(payload: LavoroRequest, db: Session = Depends(get_db)):
    giorno = datetime.strptime(payload.data, "%Y-%m-%d").date()

    nuovo_lavoro = Lavoro(
        data=giorno,
        cliente=payload.cliente,
        contratto=payload.contratto,  # ✅ Usato "contratto" al posto di "importo"
        saldato=payload.saldato,  # ✅ Aggiunto il nuovo campo "saldato"
        commessa=payload.commessa,
        saldo=payload.saldo,
        extra_consegna=payload.extra_consegna or 0.0  # ✅ Impostato a 0.0 se non fornito
    )

    db.add(nuovo_lavoro)
    db.commit()
    db.refresh(nuovo_lavoro)

    return {"message": "Lavoro registrato con successo!", "lavoro": nuovo_lavoro}


@router.delete("/lavoro/{lavoro_id}")
def elimina_lavoro(lavoro_id: int, db: Session = Depends(get_db)):
    lavoro = db.query(Lavoro).filter(Lavoro.id == lavoro_id).first()

    if not lavoro:
        raise HTTPException(status_code=404, detail="Lavoro non trovato")

    db.delete(lavoro)
    db.commit()

    return {"message": "Lavoro eliminato con successo!"}


@router.get("/attivita")
def get_attivita(
    data_da: str,
    data_a: str,
    commessa: Optional[str] = Query(None, description="Filtro opzionale per commessa"),
    db: Session = Depends(get_db)
):
    """
    Recupera tutte le attività fatte in un mese e anno, con totale ore e importo.
    """
    try:
        # Converte le stringhe in oggetti datetime
        data_da = datetime.strptime(data_da, "%Y-%m-%d").date()
        data_a = datetime.strptime(data_a, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato data non valido. Usa YYYY-MM-DD.")

    query = db.query(Lavoro).filter(Lavoro.data.between(data_da, data_a))

    if commessa:
        query = query.filter(Lavoro.commessa == commessa)

    lavori = query.order_by(Lavoro.data).all()

    # Calcoli dei totali

    totale_contratto = sum(l.contratto for l in lavori)
    # totale_saldato = sum(l.saldato for l in lavori)
    extra_su_consegne = sum(l.extra_consegna or 0 for l in lavori)
    percentuale_trasporto = totale_contratto * 0.06
    totale_lordo = percentuale_trasporto + extra_su_consegne

    # Totali per tipo di saldo
    totale_contanti = sum(l.saldato for l in lavori if l.saldo == "Contanti")
    totale_assegni = sum(l.saldato for l in lavori if l.saldo == "Assegno")
    totale_bonifico = sum(l.saldato for l in lavori if l.saldo == "Bonifico")
    totale_finanziamento = sum(l.saldato for l in lavori if l.saldo == "Finanziamento")
    totale_sospeso = sum(l.saldato for l in lavori if l.saldo == "Sospeso")
    totale_negozio = sum(l.saldato for l in lavori if l.saldo == "Pag. Negozio")

    totale_saldato = totale_contanti + totale_assegni + totale_bonifico + totale_finanziamento

    return {
        "lavori": [
            {
                "id": l.id,
                "data": l.data.strftime("%Y-%m-%d"),
                "cliente": l.cliente,
                "contratto": l.contratto,
                "saldato": l.saldato,
                "commessa": l.commessa,
                "saldo": l.saldo,
                "extra_consegna": l.extra_consegna
            }
            for l in lavori
        ],
        "totali": {
            "contratto": totale_contratto,
            "saldato": totale_saldato,
            "percentuale_trasporto": percentuale_trasporto,
            "extra_su_consegne": extra_su_consegne,
            "totale_lordo": totale_lordo,
            "contanti": totale_contanti,
            "assegni": totale_assegni,
            "bonifico": totale_bonifico,
            "finanziamento": totale_finanziamento,
            "negozio": totale_negozio,
            "sospeso": totale_sospeso
        }
    }


@router.get("/esportazione/timbrature")
def get_timbrature_utente(utente: int, mese: int, anno: int, db: Session = Depends(get_db)):
    """
    Recupera tutte le timbrature di un utente per il mese e anno selezionati.
    """
    timbrature = db.query(Timbratura).filter(
        Timbratura.id_utente == utente,
        extract("month", Timbratura.data) == mese,
        extract("year", Timbratura.data) == anno
    ).order_by(Timbratura.data.asc()).all()

    return [
        {
            "id": t.id,
            "data": t.data.strftime("%Y-%m-%d"),
            "orario_ingresso": t.orario_ingresso.strftime("%H:%M"),
            "orario_uscita": t.orario_uscita.strftime("%H:%M"),
            "tempo_lavorativo": t.tempo_lavorativo
        }
        for t in timbrature
    ]


# 📌 Esporta Timbrature in PDF
@router.get("/esporta/timbrature")
def esporta_timbrature(utente: int, mese: int, anno: int, db: Session = Depends(get_db)):
    import datetime
    timbrature = db.query(Timbratura).join(User).filter(
        Timbratura.id_utente == utente,
        Timbratura.data >= datetime.date(anno, mese, 1),
        Timbratura.data < datetime.date(anno, mese + 1, 1)
    ).order_by(Timbratura.data).all()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, f"Timbrature - {anno}-{mese:02d}", ln=True, align="C")

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Utente: {timbrature[0].utente.full_name if timbrature else 'Nessun dato'}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", style="B", size=10)
    pdf.cell(40, 10, "Data", 1)
    pdf.cell(40, 10, "Ingresso", 1)
    pdf.cell(40, 10, "Uscita", 1)
    pdf.cell(40, 10, "Ore Lavorate", 1)
    pdf.ln()

    pdf.set_font("Arial", size=10)
    totale_ore = 0
    for t in timbrature:
        ore_lavorate = t.tempo_lavorativo / 60
        totale_ore += ore_lavorate
        pdf.cell(40, 10, str(t.data), 1)
        pdf.cell(40, 10, str(t.orario_ingresso), 1)
        pdf.cell(40, 10, str(t.orario_uscita), 1)
        pdf.cell(40, 10, f"{ore_lavorate:.2f}", 1)
        pdf.ln()

    pdf.cell(120, 10, "Totale Ore", 1)
    pdf.cell(40, 10, f"{totale_ore:.2f}", 1)

    response = Response(content=pdf.output(dest="S").encode("latin1"), media_type="application/pdf")
    response.headers["Content-Disposition"] = "attachment; filename=timbrature.pdf"
    return response


# 📌 Esporta Attività in PDF
@router.get("/esporta/attivita")
def esporta_attivita(
    data_da: str,
    data_a: str,
    commessa: Optional[str] = Query(None, description="Filtro opzionale per commessa"),
    db: Session = Depends(get_db)
):
    # import datetime

    try:
        # Converte le stringhe in oggetti datetime
        data_da = datetime.strptime(data_da, "%Y-%m-%d").date()
        data_a = datetime.strptime(data_a, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato data non valido. Usa YYYY-MM-DD.")

    query = db.query(Lavoro).filter(Lavoro.data.between(data_da, data_a))

    if commessa:
        query = query.filter(Lavoro.commessa == commessa)

    lavori = query.order_by(Lavoro.data).all()

    if not lavori:
        raise HTTPException(status_code=404, detail="Nessuna attività trovata per il periodo selezionato.")

    # Calcolo Totali
    totale_contratto = sum(l.contratto for l in lavori)
    totale_saldato = sum(l.saldato for l in lavori)
    extra_su_consegne = sum(l.extra_consegna or 0 for l in lavori)
    percentuale_trasporto = totale_contratto * 0.06
    totale_lordo = percentuale_trasporto + extra_su_consegne

    # Totali per tipo di saldo
    totale_contanti = sum(l.saldato for l in lavori if l.saldo == "Contanti")
    totale_assegni = sum(l.saldato for l in lavori if l.saldo == "Assegno")
    totale_bonifico = sum(l.saldato for l in lavori if l.saldo == "Bonifico")
    totale_sospeso = sum(l.saldato for l in lavori if l.saldo == "Sospeso")
    totale_negozio = sum(l.saldato for l in lavori if l.saldo == "Pag. Negozio")

    # Creazione PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, f"Attività | {data_da} - {data_a}", ln=True, align="C")

    pdf.ln(10)
    pdf.set_font("Arial", style="B", size=10)

    # Intestazione Tabella
    pdf.cell(20, 10, "Commessa", 1)
    pdf.cell(25, 10, "Data", 1)
    pdf.cell(40, 10, "Cliente", 1)
    pdf.cell(25, 10, "Pagamento", 1)
    pdf.cell(25, 10, "Contratto", 1)
    pdf.cell(25, 10, "Saldo", 1)
    pdf.cell(20, 10, "Extra", 1)
    pdf.ln()

    pdf.set_font("Arial", size=10)

    for l in lavori:
        pdf.cell(20, 10, safe_text(l.commessa), 1)
        pdf.cell(25, 10, safe_text(str(l.data)), 1)
        pdf.cell(40, 10, safe_text(l.cliente), 1)
        pdf.cell(25, 10, safe_text(l.saldo), 1)
        pdf.cell(25, 10, safe_text(f"{l.contratto:.2f} {chr(128)}"), 1)
        pdf.cell(25, 10, safe_text(f"{l.saldato:.2f} {chr(128)}"), 1)
        pdf.cell(20, 10, safe_text(f"{l.extra_consegna:.2f} {chr(128)}"), 1)
        pdf.ln()

    # Totali nella tabella
    pdf.set_font("Arial", style="B", size=10)  # Imposta il font in grassetto per la riga del totale
    pdf.cell(110, 10, "Totale", 1, align="R")  # Colonne fino a saldo
    pdf.cell(25, 10, safe_text(f"{totale_contratto:.2f} {chr(128)}"), 1)
    pdf.cell(25, 10, safe_text(f"{totale_saldato:.2f} {chr(128)}"), 1)
    pdf.cell(20, 10, safe_text(f"{extra_su_consegne:.2f} {chr(128)}"), 1)
    pdf.ln()
    pdf.set_font("Arial", size=10)  # Torna al font normale

    # Riepilogo Totali
    pdf.ln(10)
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, "Riepilogo Totali", ln=True)

    pdf.set_font("Arial", size=10)
    pdf.cell(80, 10, "Totale Contratto:", 1)
    pdf.cell(40, 10, safe_text(f"{totale_contratto:.2f} {chr(128)}"), 1)
    pdf.ln()

    pdf.cell(80, 10, "Percentuale trasporto (6%):", 1)
    pdf.cell(40, 10, safe_text(f"{percentuale_trasporto:.2f} {chr(128)}"), 1)
    pdf.ln()

    pdf.cell(80, 10, "Extra su consegne:", 1)
    pdf.cell(40, 10, safe_text(f"{extra_su_consegne:.2f} {chr(128)}"), 1)
    pdf.ln()

    pdf.set_font("Arial", style="B", size=10)
    pdf.cell(80, 10, "Totale Lordo:", 1)
    pdf.cell(40, 10, safe_text(f"{totale_lordo:.2f} {chr(128)}"), 1)
    pdf.ln()

    # Dettaglio Pagamenti
    pdf.ln(5)
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, "Dettaglio Saldi", ln=True)

    pdf.set_font("Arial", size=10)
    pdf.cell(80, 10, "Totale Contanti:", 1)
    pdf.cell(40, 10, safe_text(f"{totale_contanti:.2f} {chr(128)}"), 1)
    pdf.ln()

    pdf.cell(80, 10, "Totale Assegni:", 1)
    pdf.cell(40, 10, safe_text(f"{totale_assegni:.2f} {chr(128)}"), 1)
    pdf.ln()

    pdf.cell(80, 10, "Totale Bonifico:", 1)
    pdf.cell(40, 10, safe_text(f"{totale_bonifico:.2f} {chr(128)}"), 1)
    pdf.ln()

    pdf.cell(80, 10, "Totale Negozio:", 1)
    pdf.cell(40, 10, safe_text(f"{totale_negozio:.2f} {chr(128)}"), 1)
    pdf.ln()

    pdf.set_font("Arial", style="B", size=10)
    pdf.cell(80, 10, "Totale:", 1)
    pdf.cell(40, 10, safe_text(f"{(totale_contanti + totale_assegni + totale_bonifico + totale_negozio):.2f} {chr(128)}"), 1)
    pdf.ln()

    pdf.set_font("Arial", size=10)  # Rimuove il grassetto
    pdf.cell(80, 10, "Totale Sospeso:", 1)
    pdf.cell(40, 10, safe_text(f"{totale_sospeso:.2f} {chr(128)}"), 1)
    pdf.ln()

    # Salva PDF su disco e restituiscilo come risposta HTTP
    pdf_file = "attivita.pdf"
    pdf.output(pdf_file, "F")

    with open(pdf_file, "rb") as file:
        pdf_content = file.read()

    response = Response(content=pdf_content, media_type="application/pdf")
    response.headers["Content-Disposition"] = f"attachment; filename={pdf_file}"
    return response
