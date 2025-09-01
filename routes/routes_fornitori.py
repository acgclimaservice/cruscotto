# routes_fornitori.py
from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for
from models import db, Fornitore
import pandas as pd
from io import BytesIO
import xlsxwriter

fornitori_bp = Blueprint('fornitori', __name__)

@fornitori_bp.route('/')
def fornitori_list():
    """Lista fornitori con filtri"""
    filtri = {
        'ragione_sociale': request.args.get('ragione_sociale', ''),
        'partita_iva': request.args.get('partita_iva', ''),
        'citta': request.args.get('citta', ''),
        'attivo': request.args.get('attivo', 'true')
    }
    
    query = Fornitore.query
    
    if filtri['ragione_sociale']:
        query = query.filter(Fornitore.ragione_sociale.contains(filtri['ragione_sociale']))
    if filtri['partita_iva']:
        query = query.filter(Fornitore.partita_iva.contains(filtri['partita_iva']))
    if filtri['citta']:
        query = query.filter(Fornitore.citta.contains(filtri['citta']))
    if filtri['attivo'] == 'true':
        query = query.filter_by(attivo=True)
    
    fornitori = query.order_by(Fornitore.ragione_sociale).all()
    
    return render_template('fornitori.html', fornitori=fornitori, filtri=filtri)

@fornitori_bp.route('/nuovo', methods=['GET', 'POST'])
def nuovo_fornitore():
    """Crea nuovo fornitore"""
    if request.method == 'GET':
        return render_template('nuovo-fornitore.html')
    
    if request.method == 'POST':
        try:
            # Handle both form data and JSON
            if request.is_json:
                data = request.json
                def get_data(key, default=''):
                    return data.get(key, default)
            else:
                def get_data(key, default=''):
                    return request.form.get(key, default).strip()
            
            # Validation
            ragione_sociale = get_data('ragione_sociale')
            if not ragione_sociale:
                if request.is_json:
                    return jsonify({'success': False, 'error': 'Ragione sociale obbligatoria'}), 400
                else:
                    flash('Ragione sociale obbligatoria', 'error')
                    return redirect(url_for('fornitori.nuovo_fornitore'))
            
            # Check for duplicates
            partita_iva = get_data('partita_iva')
            if partita_iva:
                esistente = Fornitore.query.filter_by(partita_iva=partita_iva, attivo=True).first()
                if esistente:
                    if request.is_json:
                        return jsonify({'success': False, 'error': f'Fornitore con P.IVA {partita_iva} già esistente'}), 400
                    else:
                        flash(f'Fornitore con P.IVA {partita_iva} già esistente', 'error')
                        return redirect(url_for('fornitori.nuovo_fornitore'))
            
            # Convert lead time
            lead_time_str = get_data('lead_time_giorni', '7')
            try:
                lead_time_giorni = int(lead_time_str) if lead_time_str else 7
            except ValueError:
                lead_time_giorni = 7
            
            nuovo_fornitore = Fornitore(
                ragione_sociale=ragione_sociale,
                partita_iva=partita_iva,
                codice_fiscale=get_data('codice_fiscale'),
                indirizzo=get_data('indirizzo'),
                citta=get_data('citta'),
                provincia=get_data('provincia'),
                cap=get_data('cap'),
                telefono=get_data('telefono'),
                email=get_data('email'),
                pec=get_data('pec'),
                condizioni_pagamento=get_data('condizioni_pagamento'),
                lead_time_giorni=lead_time_giorni,
                note=get_data('note'),
                attivo=True
            )
            
            db.session.add(nuovo_fornitore)
            db.session.commit()
            
            if request.is_json:
                return jsonify({'success': True, 'id': nuovo_fornitore.id})
            else:
                flash('Fornitore creato con successo!', 'success')
                return redirect(url_for('fornitori_page'))
        
        except Exception as e:
            db.session.rollback()
            print(f"Errore creazione fornitore: {e}")
            if request.is_json:
                return jsonify({'success': False, 'error': f'Errore durante creazione: {str(e)}'}), 500
            else:
                flash(f'Errore durante creazione: {str(e)}', 'error')
                return redirect(url_for('fornitori.nuovo_fornitore'))

@fornitori_bp.route('/<int:id>/modifica', methods=['GET', 'POST'])
def modifica_fornitore(id):
    """Modifica fornitore esistente"""
    fornitore = Fornitore.query.get_or_404(id)
    
    if request.method == 'GET':
        return render_template('modifica-fornitore.html', fornitore=fornitore)
    
    if request.method == 'POST':
        data = request.json
        
        fornitore.ragione_sociale = data.get('ragione_sociale', fornitore.ragione_sociale)
        fornitore.partita_iva = data.get('partita_iva')
        fornitore.codice_fiscale = data.get('codice_fiscale')
        fornitore.indirizzo = data.get('indirizzo')
        fornitore.citta = data.get('citta')
        fornitore.provincia = data.get('provincia')
        fornitore.cap = data.get('cap')
        fornitore.telefono = data.get('telefono')
        fornitore.email = data.get('email')
        fornitore.pec = data.get('pec')
        fornitore.condizioni_pagamento = data.get('condizioni_pagamento')
        fornitore.lead_time_giorni = int(data.get('lead_time_giorni', 7))
        fornitore.note = data.get('note')
        
        db.session.commit()
        return jsonify({'success': True})

@fornitori_bp.route('/<int:id>/elimina', methods=['POST'])
def elimina_fornitore(id):
    """Elimina fornitore"""
    try:
        fornitore = Fornitore.query.get_or_404(id)
        
        # Verifica se il fornitore è utilizzato in DDT IN
        from models import DDTIn
        ddt_collegati = DDTIn.query.filter_by(fornitore=fornitore.ragione_sociale).count()
        
        if ddt_collegati > 0:
            return jsonify({
                'success': False,
                'error': f'Impossibile eliminare. Il fornitore è utilizzato in {ddt_collegati} DDT IN'
            })
        
        db.session.delete(fornitore)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@fornitori_bp.route('/importa-excel', methods=['POST'])
def importa_excel_fornitori():
    """Importa fornitori da file Excel"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nessun file caricato'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nessun file selezionato'}), 400
    
    try:
        df = pd.read_excel(file)
        
        importati = 0
        errori = []
        
        for index, row in df.iterrows():
            try:
                # Gestione valori NaN e conversioni
                def safe_str(value):
                    if pd.isna(value) or value == '-':
                        return ''
                    return str(value).strip()
                
                ragione_sociale = safe_str(row.get('ragione_sociale', ''))
                
                # Verifica se il fornitore esiste già
                if Fornitore.query.filter_by(ragione_sociale=ragione_sociale).first():
                    errori.append(f"Riga {index + 1}: Fornitore {ragione_sociale} già esistente")
                    continue
                
                fornitore = Fornitore(
                    ragione_sociale=ragione_sociale,
                    partita_iva=safe_str(row.get('partita_iva', '')),
                    codice_fiscale=safe_str(row.get('codice_fiscale', '')),
                    indirizzo=safe_str(row.get('indirizzo', '')),
                    citta=safe_str(row.get('citta', '')),
                    provincia=safe_str(row.get('provincia', '')),
                    cap=safe_str(row.get('cap', '')),
                    telefono=safe_str(row.get('telefono', '')),
                    email=safe_str(row.get('email', '')),
                    pec=safe_str(row.get('pec', '')),
                    condizioni_pagamento=row.get('condizioni_pagamento', ''),
                    lead_time_giorni=int(row.get('lead_time_giorni', 7)),
                    attivo=True
                )
                
                db.session.add(fornitore)
                importati += 1
                
            except Exception as e:
                errori.append(f"Riga {index + 1}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'importati': importati,
            'errori': errori
        })
        
    except Exception as e:
        return jsonify({'error': f'Errore durante l\'importazione: {str(e)}'}), 500

@fornitori_bp.route('/template-excel')
def template_excel_fornitori():
    """Genera template Excel per importazione fornitori"""
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Fornitori')
    
    headers = [
        'ragione_sociale', 'partita_iva', 'codice_fiscale', 'indirizzo',
        'citta', 'provincia', 'cap', 'telefono', 'email', 'pec',
        'condizioni_pagamento', 'lead_time_giorni'
    ]
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    # Esempio
    esempio = [
        'Fornitore Esempio S.r.l.', '09876543210', 'FRNEXM80A01H501Z', 'Via Milano 456',
        'Roma', 'RM', '00100', '06-7654321', 'info@fornitoreesempio.it', 'pec@fornitoreesempio.it',
        'Pagamento a 60 giorni', 14
    ]
    
    for col, value in enumerate(esempio):
        worksheet.write(1, col, value)
    
    workbook.close()
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='template_fornitori.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )