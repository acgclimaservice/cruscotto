from models import db, Movimento, CatalogoArticolo, DDTIn, DDTOut
from datetime import datetime, timedelta
from sqlalchemy import func

def genera_movimento(tipo, documento_tipo, documento_id, documento_numero, articolo, magazzino, mastrino):
    movimento = Movimento(
        data_movimento=datetime.now(),
        tipo=tipo,
        documento_tipo=documento_tipo,
        documento_id=documento_id,
        documento_numero=documento_numero,
        codice_articolo=articolo.codice_interno,
        descrizione_articolo=articolo.descrizione,
        quantita=articolo.quantita,
        valore_unitario=articolo.costo_unitario,
        valore_totale=articolo.quantita * articolo.costo_unitario,
        magazzino=magazzino,
        mastrino=mastrino,
        causale=f"Movimento da {documento_tipo.upper()} {documento_numero}",
        note=articolo.note
    )
    db.session.add(movimento)

def get_dashboard_stats():
    stats = {
        'ddt_in_confermati': DDTIn.query.filter_by(stato='confermato').count(),
        'ddt_out_confermati': DDTOut.query.filter_by(stato='confermato').count(),
        'ddt_in_bozze': DDTIn.query.filter_by(stato='bozza').count(),
        'ddt_out_bozze': DDTOut.query.filter_by(stato='bozza').count(),
        'valore_magazzino': calcola_valore_magazzino(),
        'movimenti_oggi': Movimento.query.filter(
            func.date(Movimento.data_movimento) == datetime.now().date()
        ).count()
    }
    return stats

def aggiorna_catalogo(articolo, tipo_movimento):
    if not articolo.codice_interno:
        return
    
    catalogo_art = CatalogoArticolo.query.filter_by(
        codice_interno=articolo.codice_interno
    ).first()
    
    if not catalogo_art:
        catalogo_art = CatalogoArticolo(
            codice_interno=articolo.codice_interno,
            codice_fornitore=articolo.codice_fornitore,
            descrizione=articolo.descrizione,
            fornitore_principale=articolo.fornitore,
            codice_produttore=articolo.codice_produttore,
            nome_produttore=articolo.nome_produttore,
            costo_ultimo=articolo.costo_unitario,
            costo_medio=articolo.costo_unitario,
            prezzo_vendita=articolo.costo_unitario * 1.4,
            unita_misura=articolo.unita_misura,
            giacenza_attuale=0,
            scorta_minima=10,
            attivo=True
        )
        db.session.add(catalogo_art)
    
    catalogo_art.costo_ultimo = articolo.costo_unitario
    
    if tipo_movimento == 'entrata':
        catalogo_art.giacenza_attuale += articolo.quantita
    elif tipo_movimento == 'uscita':
        catalogo_art.giacenza_attuale -= articolo.quantita
    
    catalogo_art.costo_medio = calcola_costo_medio(articolo.codice_interno)

def calcola_costo_medio(codice_articolo):
    movimenti_entrata = Movimento.query.filter(
        Movimento.codice_articolo == codice_articolo,
        Movimento.tipo == 'entrata'
    ).all()
    
    if not movimenti_entrata:
        return 0
    
    totale_valore = sum(m.valore_totale for m in movimenti_entrata)
    totale_quantita = sum(m.quantita for m in movimenti_entrata)
    
    if totale_quantita == 0:
        return 0
    
    return totale_valore / totale_quantita

def verifica_scorte_minime():
    return CatalogoArticolo.query.filter(
        CatalogoArticolo.giacenza_attuale < CatalogoArticolo.scorta_minima,
        CatalogoArticolo.attivo == True
    ).all()

def calcola_valore_magazzino():
    articoli = CatalogoArticolo.query.filter(
        CatalogoArticolo.attivo == True,
        CatalogoArticolo.giacenza_attuale > 0
    ).all()
    
    return sum(
        a.giacenza_attuale * a.costo_medio 
        for a in articoli if a.costo_medio
    )