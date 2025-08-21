from flask import Blueprint, render_template, request, jsonify, send_file
from models import db, Movimento, CatalogoArticolo, Magazzino, Mastrino
from utils_automation import genera_report_mastrini, calcola_valore_magazzino
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import pandas as pd
from io import BytesIO
import xlsxwriter

movimenti_bp = Blueprint('movimenti', __name__)

@movimenti_bp.route('/')
def movimenti_list():
    """Lista movimenti con filtri"""
    # Parametri filtro
    filtri = {
        'data_da': request.args.get('data_da'),
        'data_a': request.args.get('data_a'),
        'tipo': request.args.get('tipo'),
        'magazzino': request.args.get('magazzino'),
        'articolo': request.args.get('articolo'),
        'mastrino': request.args.get('mastrino')
    }
    
    # Query base
    query = Movimento.query
    
    # Applica filtri
    if filtri['data_da']:
        data_da = datetime.strptime(filtri['data_da'], '%Y-%m-%d')
        query = query.filter(Movimento.data_movimento >= data_da)
    
    if filtri['data_a']:
        data_a = datetime.strptime(filtri['data_a'], '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Movimento.data_movimento < data_a)
    
    if filtri['tipo']:
        query = query.filter_by(tipo=filtri['tipo'])
    
    if filtri['magazzino']:
        query = query.filter_by(magazzino=filtri['magazzino'])
    
    if filtri['articolo']:
        query = query.filter(Movimento.descrizione_articolo.contains(filtri['articolo']))
    
    if filtri['mastrino']:
        query = query.filter_by(mastrino=filtri['mastrino'])
    
    # Ordina per data più recente
    movimenti = query.order_by(Movimento.data_movimento.desc()).limit(500).all()
    
    # Dati per filtri
    magazzini = Magazzino.query.filter_by(attivo=True).all()
    mastrini = Mastrino.query.filter_by(attivo=True).all()
    
    return render_template('movimenti.html',
                         movimenti=movimenti,
                         filtri=filtri,
                         magazzini=magazzini,
                         mastrini=mastrini)

@movimenti_bp.route('/report-mastrini')
def report_mastrini():
    """Report movimenti per mastrino"""
    # Parametri periodo (default ultimo mese)
    data_a = request.args.get('data_a') or datetime.now().strftime('%Y-%m-%d')
    data_da = request.args.get('data_da') or (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    data_da_obj = datetime.strptime(data_da, '%Y-%m-%d')
    data_a_obj = datetime.strptime(data_a, '%Y-%m-%d') + timedelta(days=1)
    
    # Genera report
    report = genera_report_mastrini(data_da_obj, data_a_obj)
    
    return render_template('report-mastrini.html',
                         report=report,
                         data_da=data_da,
                         data_a=data_a)

@movimenti_bp.route('/analisi-articolo/<codice>')
def analisi_articolo(codice):
    """Analisi dettagliata movimenti di un articolo"""
    articolo = CatalogoArticolo.query.filter_by(codice_interno=codice).first_or_404()
    
    # Movimenti ultimi 6 mesi
    data_limite = datetime.now() - timedelta(days=180)
    movimenti = Movimento.query.filter(
        Movimento.codice_articolo == codice,
        Movimento.data_movimento >= data_limite
    ).order_by(Movimento.data_movimento.desc()).all()
    
    # Statistiche
    totale_entrate = sum(m.quantita for m in movimenti if m.tipo == 'entrata')
    totale_uscite = sum(m.quantita for m in movimenti if m.tipo == 'uscita')
    
    # Consumo medio mensile
    movimenti_uscita = [m for m in movimenti if m.tipo == 'uscita']
    consumo_mensile = sum(m.quantita for m in movimenti_uscita) / 6 if movimenti_uscita else 0
    
    # Previsione esaurimento
    giorni_autonomia = 0
    if consumo_mensile > 0:
        consumo_giornaliero = consumo_mensile / 30
        giorni_autonomia = articolo.giacenza_attuale / consumo_giornaliero
    
    statistiche = {
        'totale_entrate': totale_entrate,
        'totale_uscite': totale_uscite,
        'saldo': totale_entrate - totale_uscite,
        'consumo_mensile': consumo_mensile,
        'giorni_autonomia': giorni_autonomia,
        'num_movimenti': len(movimenti)
    }
    
    return render_template('analisi-articolo.html',
                         articolo=articolo,
                         movimenti=movimenti,
                         statistiche=statistiche)

@movimenti_bp.route('/rettifica', methods=['GET', 'POST'])
def rettifica_inventario():
    """Gestione rettifiche manuali"""
    if request.method == 'GET':
        articoli = CatalogoArticolo.query.filter_by(attivo=True).order_by(CatalogoArticolo.codice_interno).all()
        return render_template('rettifica-inventario.html', articoli=articoli)
    
    if request.method == 'POST':
        data = request.json
        
        for rettifica in data['rettifiche']:
            articolo = CatalogoArticolo.query.get(rettifica['articolo_id'])
            if not articolo:
                continue
            
            nuova_giacenza = float(rettifica['nuova_giacenza'])
            differenza = nuova_giacenza - articolo.giacenza_attuale
            
            if differenza != 0:
                # Crea movimento di rettifica
                movimento = Movimento(
                    tipo='rettifica',
                    documento_tipo='rettifica',
                    documento_numero=f"RETT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    codice_articolo=articolo.codice_interno,
                    descrizione_articolo=articolo.descrizione,
                    quantita=abs(differenza),
                    valore_unitario=articolo.costo_medio,
                    valore_totale=abs(differenza) * articolo.costo_medio,
                    magazzino=rettifica.get('magazzino', 'Magazzino Centrale'),
                    causale=f"Rettifica inventario: {articolo.giacenza_attuale} → {nuova_giacenza}",
                    note=rettifica.get('note', '')
                )
                
                # Se differenza positiva = entrata, se negativa = uscita per il movimento
                movimento.tipo = 'entrata' if differenza > 0 else 'uscita'
                
                # Aggiorna giacenza
                articolo.giacenza_attuale = nuova_giacenza
                
                db.session.add(movimento)
        
        db.session.commit()
        return jsonify({'success': True})

@movimenti_bp.route('/dashboard-movimenti')
def dashboard_movimenti():
    """Dashboard riepilogativo movimenti"""
    oggi = datetime.now().date()
    settimana_fa = oggi - timedelta(days=7)
    mese_fa = oggi - timedelta(days=30)
    
    # Statistiche periodo
    movimenti_oggi = Movimento.query.filter(
        func.date(Movimento.data_movimento) == oggi
    ).count()
    
    movimenti_settimana = Movimento.query.filter(
        Movimento.data_movimento >= settimana_fa
    ).count()
    
    movimenti_mese = Movimento.query.filter(
        Movimento.data_movimento >= mese_fa
    ).count()
    
    # Valore movimentato questo mese
    valore_entrate_mese = db.session.query(func.sum(Movimento.valore_totale)).filter(
        Movimento.tipo == 'entrata',
        Movimento.data_movimento >= mese_fa
    ).scalar() or 0
    
    valore_uscite_mese = db.session.query(func.sum(Movimento.valore_totale)).filter(
        Movimento.tipo == 'uscita',
        Movimento.data_movimento >= mese_fa
    ).scalar() or 0
    
    # Top articoli movimentati
    top_articoli = db.session.query(
        Movimento.codice_articolo,
        Movimento.descrizione_articolo,
        func.sum(Movimento.quantita).label('totale_quantita'),
        func.count(Movimento.id).label('num_movimenti')
    ).filter(
        Movimento.data_movimento >= mese_fa
    ).group_by(
        Movimento.codice_articolo
    ).order_by(
        func.sum(Movimento.quantita).desc()
    ).limit(10).all()
    
    statistiche = {
        'movimenti_oggi': movimenti_oggi,
        'movimenti_settimana': movimenti_settimana,
        'movimenti_mese': movimenti_mese,
        'valore_entrate_mese': valore_entrate_mese,
        'valore_uscite_mese': valore_uscite_mese,
        'saldo_mese': valore_entrate_mese - valore_uscite_mese,
        'valore_magazzino': calcola_valore_magazzino()
    }
    
    return render_template('dashboard-movimenti.html',
                         statistiche=statistiche,
                         top_articoli=top_articoli)

@movimenti_bp.route('/export-excel')
def export_movimenti_excel():
    """Esporta movimenti in Excel"""
    # Parametri filtro dalla query string
    data_da = request.args.get('data_da')
    data_a = request.args.get('data_a')
    tipo = request.args.get('tipo')
    
    query = Movimento.query
    
    if data_da:
        query = query.filter(Movimento.data_movimento >= datetime.strptime(data_da, '%Y-%m-%d'))
    if data_a:
        query = query.filter(Movimento.data_movimento <= datetime.strptime(data_a, '%Y-%m-%d'))
    if tipo:
        query = query.filter_by(tipo=tipo)
    
    movimenti = query.order_by(Movimento.data_movimento.desc()).all()
    
    # Crea Excel
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Movimenti')
    
    # Headers
    headers = [
        'Data/Ora', 'Tipo', 'Documento', 'N° Documento', 'Codice Articolo',
        'Descrizione', 'Quantità', 'Valore Unit.', 'Valore Tot.', 'Magazzino',
        'Mastrino', 'Causale', 'Note'
    ]
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    # Dati
    for row, movimento in enumerate(movimenti, 1):
        data = [
            movimento.data_movimento.strftime('%d/%m/%Y %H:%M'),
            movimento.tipo.upper(),
            movimento.documento_tipo.upper(),
            movimento.documento_numero or '',
            movimento.codice_articolo,
            movimento.descrizione_articolo,
            movimento.quantita,
            movimento.valore_unitario,
            movimento.valore_totale,
            movimento.magazzino or '',
            movimento.mastrino or '',
            movimento.causale or '',
            movimento.note or ''
        ]
        
        for col, value in enumerate(data):
            worksheet.write(row, col, value)
    
    workbook.close()
    output.seek(0)
    
    filename = f'movimenti_{datetime.now().strftime("%Y%m%d")}.xlsx'
    if data_da and data_a:
        filename = f'movimenti_{data_da}_{data_a}.xlsx'
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@movimenti_bp.route('/api/statistiche-articolo/<codice>')
def api_statistiche_articolo(codice):
    """API per statistiche movimento articolo"""
    giorni = int(request.args.get('giorni', 30))
    data_limite = datetime.now() - timedelta(days=giorni)
    
    movimenti = Movimento.query.filter(
        Movimento.codice_articolo == codice,
        Movimento.data_movimento >= data_limite
    ).all()
    
    entrate = sum(m.quantita for m in movimenti if m.tipo == 'entrata')
    uscite = sum(m.quantita for m in movimenti if m.tipo == 'uscita')
    
    # Trend giornaliero
    trend = {}
    for movimento in movimenti:
        data_str = movimento.data_movimento.strftime('%Y-%m-%d')
        if data_str not in trend:
            trend[data_str] = {'entrate': 0, 'uscite': 0}
        
        if movimento.tipo == 'entrata':
            trend[data_str]['entrate'] += movimento.quantita
        else:
            trend[data_str]['uscite'] += movimento.quantita
    
    return jsonify({
        'entrate': entrate,
        'uscite': uscite,
        'saldo': entrate - uscite,
        'num_movimenti': len(movimenti),
        'trend': trend
    })