# routes_fornitori.py
from flask import Blueprint, render_template, request, jsonify, send_file
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
        data = request.json
        
        nuovo_fornitore = Fornitore(
            ragione_sociale=data['ragione_sociale'],
            partita_iva=data.get('partita_iva'),
            codice_fiscale=data.get('codice_fiscale'),
            indirizzo=data.get('indirizzo'),
            citta=data.get('citta'),
            provincia=data.get('provincia'),
            cap=data.get('cap'),
            telefono=data.get('telefono'),
            email=data.get('email'),
            pec=data.get('pec'),
            condizioni_pagamento=data.get('condizioni_pagamento'),
            lead_time_giorni=int(data.get('lead_time_giorni', 7)),
            note=data.get('note'),
            attivo=True
        )
        
        db.session.add(nuovo_fornitore)
        db.session.commit()
        
        return jsonify({'success': True, 'id': nuovo_fornitore.id})

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