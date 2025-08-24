from models import db, Movimento, CatalogoArticolo, DDTIn, DDTOut
from datetime import datetime, timedelta
from sqlalchemy import func

def genera_movimento(tipo, documento_tipo, documento_numero, articolo, quantita, magazzino):
    movimento = Movimento(
        data_movimento=datetime.now(),
        tipo=tipo,
        documento_tipo=documento_tipo,
        documento_numero=documento_numero,
        codice_articolo=articolo.get('codice_interno'),
        descrizione_articolo=articolo.get('descrizione'),
        quantita=quantita,
        valore_unitario=articolo.get('costo_unitario', 0),
        valore_totale=quantita * articolo.get('costo_unitario', 0),
        magazzino=magazzino
    )
    db.session.add(movimento)
    return movimento

def aggiorna_giacenze(codice_articolo, quantita, tipo_movimento):
    articolo = CatalogoArticolo.query.filter_by(codice_interno=codice_articolo).first()
    if articolo:
        if tipo_movimento == 'entrata':
            articolo.giacenza_attuale += quantita
        elif tipo_movimento == 'uscita':
            articolo.giacenza_attuale = max(0, articolo.giacenza_attuale - quantita)
        db.session.commit()

def calcola_valore_magazzino():
    articoli = CatalogoArticolo.query.filter(
        CatalogoArticolo.attivo == True,
        CatalogoArticolo.giacenza_attuale > 0
    ).all()
    return sum(a.giacenza_attuale * (a.costo_medio or 0) for a in articoli)

def verifica_scorte_minime():
    return CatalogoArticolo.query.filter(
        CatalogoArticolo.giacenza_attuale < CatalogoArticolo.scorta_minima,
        CatalogoArticolo.attivo == True
    ).all()
