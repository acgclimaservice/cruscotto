from models import db, Movimento, CatalogoArticolo, DDTIn, DDTOut
from datetime import datetime
from sqlalchemy import func

def genera_movimento(tipo, documento_tipo, documento_id, documento_numero, articolo, magazzino, mastrino):
    """
    Genera movimento automatico da DDT confermato
    
    Args:
        tipo: 'entrata' o 'uscita'
        documento_tipo: 'ddt_in' o 'ddt_out'
        documento_id: ID del documento
        documento_numero: Numero del documento
        articolo: Oggetto ArticoloIn o ArticoloOut
        magazzino: Nome del magazzino
        mastrino: Codice mastrino
    """
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
    print(f"Movimento creato: {tipo} {articolo.codice_interno} - {articolo.quantita} pz")

def aggiorna_catalogo(articolo, tipo_movimento):
    """
    Aggiorna o crea articolo nel catalogo automaticamente dai DDT
    
    Args:
        articolo: Oggetto ArticoloIn o ArticoloOut
        tipo_movimento: 'entrata' o 'uscita'
    """
    if not articolo.codice_interno:
        return
    
    # Cerca articolo esistente nel catalogo
    catalogo_art = CatalogoArticolo.query.filter_by(
        codice_interno=articolo.codice_interno
    ).first()
    
    if not catalogo_art:
        # Crea nuovo articolo nel catalogo
        catalogo_art = CatalogoArticolo(
            codice_interno=articolo.codice_interno,
            codice_fornitore=articolo.codice_fornitore,
            descrizione=articolo.descrizione,
            fornitore_principale=articolo.fornitore,
            codice_produttore=articolo.codice_produttore,
            nome_produttore=articolo.nome_produttore,
            costo_ultimo=articolo.costo_unitario,
            costo_medio=articolo.costo_unitario,
            prezzo_vendita=articolo.costo_unitario * 1.4,  # Margine 40% di default
            unita_misura=articolo.unita_misura,
            giacenza_attuale=0,
            scorta_minima=10,  # Default
            attivo=True
        )
        db.session.add(catalogo_art)
        print(f"Nuovo articolo creato nel catalogo: {articolo.codice_interno}")
    
    # Aggiorna dati articolo
    catalogo_art.costo_ultimo = articolo.costo_unitario
    
    # Aggiorna giacenza
    if tipo_movimento == 'entrata':
        catalogo_art.giacenza_attuale += articolo.quantita
        print(f"Giacenza aggiornata +{articolo.quantita}: {catalogo_art.giacenza_attuale}")
    elif tipo_movimento == 'uscita':
        catalogo_art.giacenza_attuale -= articolo.quantita
        print(f"Giacenza aggiornata -{articolo.quantita}: {catalogo_art.giacenza_attuale}")
    
    # Ricalcola costo medio ponderato
    catalogo_art.costo_medio = calcola_costo_medio(articolo.codice_interno)

def calcola_costo_medio(codice_articolo):
    """
    Calcola il costo medio ponderato di un articolo basato sui movimenti di entrata
    
    Args:
        codice_articolo: Codice interno dell'articolo
        
    Returns:
        float: Costo medio ponderato
    """
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
    
    costo_medio = totale_valore / totale_quantita
    print(f"Costo medio calcolato per {codice_articolo}: €{costo_medio:.2f}")
    return costo_medio

def verifica_scorte_minime():
    """
    Verifica articoli sotto scorta minima
    
    Returns:
        list: Lista di articoli sotto scorta
    """
    articoli_sotto_scorta = CatalogoArticolo.query.filter(
        CatalogoArticolo.giacenza_attuale < CatalogoArticolo.scorta_minima,
        CatalogoArticolo.attivo == True
    ).all()
    
    return articoli_sotto_scorta

def calcola_valore_magazzino():
    """
    Calcola il valore totale del magazzino
    
    Returns:
        float: Valore totale magazzino
    """
    articoli = CatalogoArticolo.query.filter(
        CatalogoArticolo.attivo == True,
        CatalogoArticolo.giacenza_attuale > 0
    ).all()
    
    valore_totale = sum(
        a.giacenza_attuale * a.costo_medio 
        for a in articoli if a.costo_medio
    )
    
    return valore_totale

def genera_report_mastrini(data_da, data_a):
    """
    Genera report movimenti per mastrino in un periodo
    
    Args:
        data_da: Data inizio periodo
        data_a: Data fine periodo
        
    Returns:
        dict: Report per mastrino con totali
    """
    movimenti = Movimento.query.filter(
        Movimento.data_movimento >= data_da,
        Movimento.data_movimento <= data_a,
        Movimento.mastrino.isnot(None)
    ).all()
    
    report = {}
    
    for movimento in movimenti:
        mastrino = movimento.mastrino
        if mastrino not in report:
            report[mastrino] = {
                'movimenti': 0,
                'entrate': 0,
                'uscite': 0,
                'saldo': 0
            }
        
        report[mastrino]['movimenti'] += 1
        
        if movimento.tipo == 'entrata':
            report[mastrino]['entrate'] += movimento.valore_totale
        elif movimento.tipo == 'uscita':
            report[mastrino]['uscite'] += movimento.valore_totale
        
        report[mastrino]['saldo'] = (
            report[mastrino]['entrate'] - report[mastrino]['uscite']
        )
    
    return report

def aggiorna_prezzi_catalogo_da_offerta(offerta):
    """
    Aggiorna prezzi nel catalogo da offerta fornitore accettata
    
    Args:
        offerta: Oggetto OffertaFornitore
    """
    if offerta.stato != 'accettata':
        return
    
    for articolo_offerta in offerta.articoli:
        if articolo_offerta.codice_interno:
            catalogo_art = CatalogoArticolo.query.filter_by(
                codice_interno=articolo_offerta.codice_interno
            ).first()
            
            if catalogo_art:
                # Aggiorna prezzo se migliore
                if (articolo_offerta.prezzo_unitario < catalogo_art.costo_ultimo or 
                    catalogo_art.costo_ultimo == 0):
                    catalogo_art.costo_ultimo = articolo_offerta.prezzo_unitario
                    print(f"Prezzo aggiornato da offerta: {articolo_offerta.codice_interno}")

def calcola_margine_preventivo(preventivo):
    """
    Calcola il margine totale di un preventivo
    
    Args:
        preventivo: Oggetto Preventivo
        
    Returns:
        tuple: (totale_costi, totale_ricavi, margine_percentuale)
    """
    totale_costi = 0
    totale_ricavi = 0
    
    for articolo in preventivo.articoli:
        # Trova costo dal catalogo
        catalogo_art = CatalogoArticolo.query.filter_by(
            codice_interno=articolo.codice_interno
        ).first()
        
        costo_unitario = catalogo_art.costo_medio if catalogo_art else articolo.costo_unitario
        prezzo_unitario = articolo.prezzo_unitario * (1 - articolo.sconto_percentuale / 100)
        
        totale_costi += costo_unitario * articolo.quantita
        totale_ricavi += prezzo_unitario * articolo.quantita
    
    margine_percentuale = 0
    if totale_ricavi > 0:
        margine_percentuale = ((totale_ricavi - totale_costi) / totale_ricavi) * 100
    
    return totale_costi, totale_ricavi, margine_percentuale

def ottimizza_riordini():
    """
    Suggerisce riordini basati su scorte minime e leadtime
    
    Returns:
        list: Lista di suggerimenti riordino
    """
    articoli_da_riordinare = verifica_scorte_minime()
    suggerimenti = []
    
    for articolo in articoli_da_riordinare:
        # Calcola consumo medio degli ultimi 30 giorni
        data_limite = datetime.now() - timedelta(days=30)
        movimenti_uscita = Movimento.query.filter(
            Movimento.codice_articolo == articolo.codice_interno,
            Movimento.tipo == 'uscita',
            Movimento.data_movimento >= data_limite
        ).all()
        
        consumo_mensile = sum(m.quantita for m in movimenti_uscita)
        consumo_giornaliero = consumo_mensile / 30 if consumo_mensile > 0 else 1
        
        # Quantità suggerita = scorta_minima + (consumo_giornaliero * leadtime)
        leadtime = 7  # Default leadtime
        quantita_suggerita = articolo.scorta_minima + (consumo_giornaliero * leadtime)
        
        suggerimenti.append({
            'codice': articolo.codice_interno,
            'descrizione': articolo.descrizione,
            'giacenza_attuale': articolo.giacenza_attuale,
            'scorta_minima': articolo.scorta_minima,
            'quantita_suggerita': quantita_suggerita,
            'fornitore': articolo.fornitore_principale,
            'costo_unitario': articolo.costo_ultimo
        })
    
    return suggerimenti

def genera_codice_automatico(prefisso='ART'):
    """
    Genera codice articolo automatico
    
    Args:
        prefisso: Prefisso del codice
        
    Returns:
        str: Nuovo codice generato
    """
    ultimo_articolo = CatalogoArticolo.query.filter(
        CatalogoArticolo.codice_interno.like(f'{prefisso}-%')
    ).order_by(CatalogoArticolo.id.desc()).first()
    
    if ultimo_articolo and ultimo_articolo.codice_interno:
        try:
            ultimo_numero = int(ultimo_articolo.codice_interno.split('-')[1])
            nuovo_numero = ultimo_numero + 1
        except (IndexError, ValueError):
            nuovo_numero = 1
    else:
        nuovo_numero = 1
    
    return f'{prefisso}-{nuovo_numero:03d}'

def backup_database():
    """
    Esegue backup del database
    
    Returns:
        str: Path del file di backup
    """
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'backup_ddt_{timestamp}.db'
    
    try:
        shutil.copy2('ddt_database.db', backup_path)
        print(f"Backup creato: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Errore durante il backup: {e}")
        return None
