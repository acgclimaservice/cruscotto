# routes_clienti.py
from flask import Blueprint, render_template, request, jsonify, send_file
from models import db, Cliente
import pandas as pd
from io import BytesIO
import xlsxwriter

clienti_bp = Blueprint('clienti', __name__)

@clienti_bp.route('/')
def clienti_list():
    """Lista clienti con filtri"""
    filtri = {
        'ragione_sociale': request.args.get('ragione_sociale', ''),
        'partita_iva': request.args.get('partita_iva', ''),
        'citta': request.args.get('citta', ''),
        'attivo': request.args.get('attivo', 'true')
    }
    
    query = Cliente.query
    
    if filtri['ragione_sociale']:
        query = query.filter(Cliente.ragione_sociale.contains(filtri['ragione_sociale']))
    if filtri['partita_iva']:
        query = query.filter(Cliente.partita_iva.contains(filtri['partita_iva']))
    if filtri['citta']:
        query = query.filter(Cliente.citta.contains(filtri['citta']))
    if filtri['attivo'] == 'true':
        query = query.filter_by(attivo=True)
    
    clienti = query.order_by(Cliente.ragione_sociale).all()
    
    return render_template('clienti.html', clienti=clienti, filtri=filtri)

@clienti_bp.route('/nuovo', methods=['GET', 'POST'])
def nuovo_cliente():
    """Crea nuovo cliente"""
    if request.method == 'GET':
        return render_template('nuovo-cliente.html')
    
    if request.method == 'POST':
        data = request.json
        
        nuovo_cliente = Cliente(
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
            codice_sdi=data.get('codice_sdi'),
            condizioni_pagamento=data.get('condizioni_pagamento'),
            note=data.get('note'),
            attivo=True
        )
        
        db.session.add(nuovo_cliente)
        db.session.commit()
        
        return jsonify({'success': True, 'id': nuovo_cliente.id})

@clienti_bp.route('/<int:id>/modifica', methods=['GET', 'POST'])
def modifica_cliente(id):
    """Modifica cliente esistente"""
    cliente = Cliente.query.get_or_404(id)
    
    if request.method == 'GET':
        return render_template('modifica-cliente.html', cliente=cliente)
    
    if request.method == 'POST':
        data = request.json
        
        cliente.ragione_sociale = data.get('ragione_sociale', cliente.ragione_sociale)
        cliente.partita_iva = data.get('partita_iva')
        cliente.codice_fiscale = data.get('codice_fiscale')
        cliente.indirizzo = data.get('indirizzo')
        cliente.citta = data.get('citta')
        cliente.provincia = data.get('provincia')
        cliente.cap = data.get('cap')
        cliente.telefono = data.get('telefono')
        cliente.email = data.get('email')
        cliente.pec = data.get('pec')
        cliente.codice_sdi = data.get('codice_sdi')
        cliente.condizioni_pagamento = data.get('condizioni_pagamento')
        cliente.note = data.get('note')
        
        db.session.commit()
        return jsonify({'success': True})

@clienti_bp.route('/importa-excel', methods=['POST'])
def importa_excel():
    """Importa clienti da file Excel"""
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
                # Mapping colonne Excel → Database
                ragione_sociale = row.get('Denominazione', row.get('ragione_sociale', ''))
                
                # Verifica se il cliente esiste già
                if Cliente.query.filter_by(ragione_sociale=ragione_sociale).first():
                    errori.append(f"Riga {index + 1}: Cliente {ragione_sociale} già esistente")
                    continue
                
                # Gestione valori NaN e conversioni
                def safe_str(value):
                    if pd.isna(value) or value == '-':
                        return ''
                    return str(value).strip()
                
                cliente = Cliente(
                    ragione_sociale=safe_str(ragione_sociale),
                    partita_iva=safe_str(row.get('P.IVA/TAX ID', row.get('partita_iva', ''))),
                    codice_fiscale=safe_str(row.get('Codice Fiscale', row.get('codice_fiscale', ''))),
                    indirizzo=safe_str(row.get('Indirizzo', row.get('indirizzo', ''))),
                    citta=safe_str(row.get('Comune', row.get('citta', ''))),
                    provincia=safe_str(row.get('Provincia', row.get('provincia', ''))),
                    cap=safe_str(row.get('CAP', row.get('cap', ''))),
                    telefono=safe_str(row.get('Telefono', row.get('telefono', ''))),
                    email=safe_str(row.get('Indirizzo e-mail', row.get('email', ''))),
                    pec=safe_str(row.get('Indirizzo PEC', row.get('pec', ''))),
                    codice_sdi=safe_str(row.get('Codice SDI', row.get('codice_sdi', ''))),
                    condizioni_pagamento=safe_str(row.get('Termini di pagamento', row.get('condizioni_pagamento', ''))),
                    note=safe_str(row.get('Note', '')),
                    attivo=True
                )
                
                db.session.add(cliente)
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

@clienti_bp.route('/template-excel')
def template_excel():
    """Genera template Excel per importazione clienti"""
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Clienti')
    
    headers = [
        'ragione_sociale', 'partita_iva', 'codice_fiscale', 'indirizzo',
        'citta', 'provincia', 'cap', 'telefono', 'email', 'pec',
        'codice_sdi', 'condizioni_pagamento'
    ]
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    # Esempio
    esempio = [
        'Cliente Esempio S.r.l.', '12345678901', 'CLNEXM80A01H501Z', 'Via Roma 123',
        'Milano', 'MI', '20100', '02-1234567', 'info@clienteesempio.it', 'pec@clienteesempio.it',
        'ABC123', 'Pagamento a 30 giorni'
    ]
    
    for col, value in enumerate(esempio):
        worksheet.write(1, col, value)
    
    workbook.close()
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='template_clienti.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )