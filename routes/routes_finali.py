# routes_impostazioni.py
from flask import Blueprint, render_template, request, jsonify
from models import db, Mastrino, Magazzino, ConfigurazioneSistema

impostazioni_bp = Blueprint('impostazioni', __name__)

@impostazioni_bp.route('/')
def impostazioni_home():
    """Pagina principale impostazioni"""
    mastrini = Mastrino.query.order_by(Mastrino.tipo, Mastrino.codice).all()
    magazzini = Magazzino.query.order_by(Magazzino.codice).all()
    configurazioni = ConfigurazioneSistema.query.all()
    
    return render_template('impostazioni.html',
                         mastrini=mastrini,
                         magazzini=magazzini,
                         configurazioni=configurazioni)

@impostazioni_bp.route('/mastrino/nuovo', methods=['POST'])
def nuovo_mastrino():
    """Crea nuovo mastrino"""
    data = request.json
    
    # Verifica codice univoco
    if Mastrino.query.filter_by(codice=data['codice']).first():
        return jsonify({'error': 'Codice mastrino già esistente'}), 400
    
    mastrino = Mastrino(
        codice=data['codice'],
        descrizione=data['descrizione'],
        tipo=data['tipo'],  # acquisto/ricavo
        attivo=True
    )
    
    db.session.add(mastrino)
    db.session.commit()
    
    return jsonify({'success': True, 'id': mastrino.id})

@impostazioni_bp.route('/mastrino/<int:id>/toggle', methods=['POST'])
def toggle_mastrino(id):
    """Attiva/disattiva mastrino"""
    mastrino = Mastrino.query.get_or_404(id)
    mastrino.attivo = not mastrino.attivo
    db.session.commit()
    
    return jsonify({'success': True, 'attivo': mastrino.attivo})

@impostazioni_bp.route('/magazzino/nuovo', methods=['POST'])
def nuovo_magazzino():
    """Crea nuovo magazzino"""
    data = request.json
    
    # Verifica codice univoco
    if Magazzino.query.filter_by(codice=data['codice']).first():
        return jsonify({'error': 'Codice magazzino già esistente'}), 400
    
    magazzino = Magazzino(
        codice=data['codice'],
        descrizione=data['descrizione'],
        indirizzo=data.get('indirizzo'),
        responsabile=data.get('responsabile'),
        attivo=True
    )
    
    db.session.add(magazzino)
    db.session.commit()
    
    return jsonify({'success': True, 'id': magazzino.id})

@impostazioni_bp.route('/magazzino/<int:id>/toggle', methods=['POST'])
def toggle_magazzino(id):
    """Attiva/disattiva magazzino"""
    magazzino = Magazzino.query.get_or_404(id)
    magazzino.attivo = not magazzino.attivo
    db.session.commit()
    
    return jsonify({'success': True, 'attivo': magazzino.attivo})

@impostazioni_bp.route('/configurazione/salva', methods=['POST'])
def salva_configurazioni():
    """Salva configurazioni sistema"""
    data = request.json
    
    for chiave, valore in data.items():
        config = ConfigurazioneSistema.query.filter_by(chiave=chiave).first()
        if config:
            config.valore = valore
            config.data_modifica = datetime.now()
        else:
            config = ConfigurazioneSistema(
                chiave=chiave,
                valore=valore,
                descrizione=f"Configurazione {chiave}"
            )
            db.session.add(config)
    
    db.session.commit()
    return jsonify({'success': True})

# routes_inventario.py
from flask import Blueprint, render_template, request, jsonify, send_file
from models import db, CatalogoArticolo, Movimento
from utils_automation import calcola_valore_magazzino, verifica_scorte_minime
from datetime import datetime

inventario_bp = Blueprint('inventario', __name__)

@inventario_bp.route('/')
def inventario_home():
    """Dashboard inventario"""
    articoli = CatalogoArticolo.query.filter_by(attivo=True).order_by(CatalogoArticolo.codice_interno).all()
    sotto_scorta = len(verifica_scorte_minime())
    
    statistiche = {
        'numero_articoli': len(articoli),
        'valore_totale': calcola_valore_magazzino(),
        'pezzi_totali': sum(a.giacenza_attuale for a in articoli),
        'sotto_scorta': sotto_scorta
    }
    
    return render_template('inventario.html',
                         articoli=articoli,
                         statistiche=statistiche,
                         sotto_scorta=sotto_scorta)

@inventario_bp.route('/valorizzazione')
def valorizzazione():
    """Report valorizzazione magazzino"""
    articoli = CatalogoArticolo.query.filter(
        CatalogoArticolo.attivo == True,
        CatalogoArticolo.giacenza_attuale > 0
    ).order_by(CatalogoArticolo.categoria, CatalogoArticolo.codice_interno).all()
    
    # Raggruppa per categoria
    per_categoria = {}
    for articolo in articoli:
        categoria = articolo.categoria or 'Senza Categoria'
        if categoria not in per_categoria:
            per_categoria[categoria] = {
                'articoli': [],
                'valore_totale': 0,
                'pezzi_totali': 0
            }
        
        valore = articolo.giacenza_attuale * articolo.costo_medio
        per_categoria[categoria]['articoli'].append({
            'codice': articolo.codice_interno,
            'descrizione': articolo.descrizione,
            'giacenza': articolo.giacenza_attuale,
            'costo_medio': articolo.costo_medio,
            'valore': valore
        })
        per_categoria[categoria]['valore_totale'] += valore
        per_categoria[categoria]['pezzi_totali'] += articolo.giacenza_attuale
    
    return render_template('valorizzazione.html', per_categoria=per_categoria)

@inventario_bp.route('/inventario-fisico', methods=['GET', 'POST'])
def inventario_fisico():
    """Gestione inventario fisico"""
    if request.method == 'GET':
        articoli = CatalogoArticolo.query.filter_by(attivo=True).order_by(CatalogoArticolo.codice_interno).all()
        return render_template('inventario-fisico.html', articoli=articoli)
    
    if request.method == 'POST':
        data = request.json
        numero_inventario = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        movimenti_creati = 0
        
        for item in data['inventario']:
            articolo = CatalogoArticolo.query.get(item['articolo_id'])
            if not articolo:
                continue
            
            giacenza_teorica = articolo.giacenza_attuale
            giacenza_fisica = float(item['giacenza_fisica'])
            differenza = giacenza_fisica - giacenza_teorica
            
            if differenza != 0:
                # Crea movimento di inventario
                movimento = Movimento(
                    tipo='inventario',
                    documento_tipo='inventario',
                    documento_numero=numero_inventario,
                    codice_articolo=articolo.codice_interno,
                    descrizione_articolo=articolo.descrizione,
                    quantita=abs(differenza),
                    valore_unitario=articolo.costo_medio,
                    valore_totale=abs(differenza) * articolo.costo_medio,
                    magazzino=item.get('magazzino', 'Magazzino Centrale'),
                    causale=f"Inventario fisico: {giacenza_teorica} → {giacenza_fisica}",
                    note=item.get('note', '')
                )
                
                # Aggiorna giacenza
                articolo.giacenza_attuale = giacenza_fisica
                
                db.session.add(movimento)
                movimenti_creati += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'numero_inventario': numero_inventario,
            'movimenti_creati': movimenti_creati
        })

@inventario_bp.route('/export-excel')
def export_inventario_excel():
    """Esporta inventario in Excel"""
    articoli = CatalogoArticolo.query.filter_by(attivo=True).order_by(CatalogoArticolo.codice_interno).all()
    
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Inventario')
    
    headers = [
        'Codice', 'Descrizione', 'Categoria', 'Fornitore', 'U.M.',
        'Giacenza', 'Costo Medio', 'Valore Giacenza', 'Scorta Min.',
        'Stato', 'Ubicazione'
    ]
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    for row, articolo in enumerate(articoli, 1):
        valore_giacenza = articolo.giacenza_attuale * articolo.costo_medio
        stato = 'RIORDINARE' if articolo.giacenza_attuale < articolo.scorta_minima else 'OK'
        
        data = [
            articolo.codice_interno,
            articolo.descrizione,
            articolo.categoria or '',
            articolo.fornitore_principale or '',
            articolo.unita_misura,
            articolo.giacenza_attuale,
            articolo.costo_medio,
            valore_giacenza,
            articolo.scorta_minima,
            stato,
            articolo.ubicazione or ''
        ]
        
        for col, value in enumerate(data):
            worksheet.write(row, col, value)
    
    workbook.close()
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f'inventario_{datetime.now().strftime("%Y%m%d")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# routes_preventivi.py
from flask import Blueprint, render_template, request, jsonify
from models import db, Preventivo, ArticoloPreventivo, Cliente, CatalogoArticolo
from utils_automation import calcola_margine_preventivo

preventivi_bp = Blueprint('preventivi', __name__)

@preventivi_bp.route('/')
def preventivi_list():
    """Lista preventivi"""
    preventivi = Preventivo.query.order_by(Preventivo.data_preventivo.desc()).all()
    return render_template('preventivi.html', preventivi=preventivi)

@preventivi_bp.route('/nuovo', methods=['GET', 'POST'])
def nuovo_preventivo():
    """Crea nuovo preventivo"""
    if request.method == 'GET':
        clienti = Cliente.query.filter_by(attivo=True).all()
        return render_template('nuovo-preventivo.html', clienti=clienti)
    
    if request.method == 'POST':
        data = request.json
        
        # Genera numero progressivo
        anno = datetime.now().year
        ultimo = Preventivo.query.filter(
            Preventivo.numero_preventivo.like(f'PREV/%/{anno}')
        ).order_by(Preventivo.id.desc()).first()
        
        if ultimo and ultimo.numero_preventivo:
            numero = int(ultimo.numero_preventivo.split('/')[1]) + 1
        else:
            numero = 1
        
        preventivo = Preventivo(
            numero_preventivo=f'PREV/{numero:04d}/{anno}',
            data_preventivo=datetime.now().date(),
            cliente=data['cliente'],
            contatto_cliente=data.get('contatto_cliente'),
            validita_giorni=int(data.get('validita_giorni', 30)),
            condizioni_pagamento=data.get('condizioni_pagamento'),
            note=data.get('note'),
            stato='bozza'
        )
        
        db.session.add(preventivo)
        db.session.flush()
        
        # Aggiungi articoli
        for art_data in data.get('articoli', []):
            articolo = ArticoloPreventivo(
                preventivo_id=preventivo.id,
                codice_interno=art_data.get('codice_interno'),
                descrizione=art_data['descrizione'],
                costo_unitario=float(art_data.get('costo_unitario', 0)),
                prezzo_unitario=float(art_data.get('prezzo_unitario', 0)),
                unita_misura=art_data.get('unita_misura', 'PZ'),
                quantita=float(art_data.get('quantita', 0)),
                sconto_percentuale=float(art_data.get('sconto_percentuale', 0)),
                note=art_data.get('note', '')
            )
            db.session.add(articolo)
        
        # Calcola totali
        costi, ricavi, margine = calcola_margine_preventivo(preventivo)
        preventivo.totale = ricavi
        preventivo.margine = margine
        
        db.session.commit()
        return jsonify({'success': True, 'id': preventivo.id})

# routes_offerte.py
from flask import Blueprint, render_template, request, jsonify
from models import db, OffertaFornitore, ArticoloOfferta, Fornitore
from utils_automation import aggiorna_prezzi_catalogo_da_offerta

offerte_bp = Blueprint('offerte', __name__)

@offerte_bp.route('/')
def offerte_list():
    """Lista offerte fornitori"""
    offerte = OffertaFornitore.query.order_by(OffertaFornitore.data_offerta.desc()).all()
    return render_template('offerte.html', offerte=offerte)

@offerte_bp.route('/nuova', methods=['GET', 'POST'])
def nuova_offerta():
    """Crea nuova offerta fornitore"""
    if request.method == 'GET':
        fornitori = Fornitore.query.filter_by(attivo=True).all()
        return render_template('nuova-offerta.html', fornitori=fornitori)
    
    if request.method == 'POST':
        data = request.json
        
        offerta = OffertaFornitore(
            numero_offerta=data['numero_offerta'],
            data_offerta=datetime.strptime(data['data_offerta'], '%Y-%m-%d').date(),
            fornitore=data['fornitore'],
            validita_giorni=int(data.get('validita_giorni', 30)),
            condizioni_pagamento=data.get('condizioni_pagamento'),
            note=data.get('note'),
            stato='ricevuta'
        )
        
        db.session.add(offerta)
        db.session.flush()
        
        # Aggiungi articoli
        for art_data in data.get('articoli', []):
            articolo = ArticoloOfferta(
                offerta_id=offerta.id,
                codice_interno=art_data.get('codice_interno'),
                codice_fornitore=art_data.get('codice_fornitore'),
                descrizione=art_data['descrizione'],
                codice_produttore=art_data.get('codice_produttore'),
                nome_produttore=art_data.get('nome_produttore'),
                prezzo_unitario=float(art_data.get('prezzo_unitario', 0)),
                unita_misura=art_data.get('unita_misura', 'PZ'),
                quantita_minima=float(art_data.get('quantita_minima', 0)),
                lead_time_giorni=int(art_data.get('lead_time_giorni', 7)),
                note=art_data.get('note', '')
            )
            db.session.add(articolo)
        
        db.session.commit()
        return jsonify({'success': True, 'id': offerta.id})

@offerte_bp.route('/<int:id>/accetta', methods=['POST'])
def accetta_offerta(id):
    """Accetta offerta e aggiorna prezzi catalogo"""
    offerta = OffertaFornitore.query.get_or_404(id)
    offerta.stato = 'accettata'
    
    # Aggiorna prezzi nel catalogo
    aggiorna_prezzi_catalogo_da_offerta(offerta)
    
    db.session.commit()
    return jsonify({'success': True})