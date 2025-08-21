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
                # Verifica se il cliente esiste già
                if Cliente.query.filter_by(ragione_sociale=row['ragione_sociale']).first():
                    errori.append(f"Riga {index + 1}: Cliente {row['ragione_sociale']} già esistente")
                    continue
                
                cliente = Cliente(
                    ragione_sociale=row['ragione_sociale'],
                    partita_iva=row.get('partita_iva', ''),
                    codice_fiscale=row.get('codice_fiscale', ''),
                    indirizzo=row.get('indirizzo', ''),
                    citta=row.get('citta', ''),
                    provincia=row.get('provincia', ''),
                    cap=row.get('cap', ''),
                    telefono=row.get('telefono', ''),
                    email=row.get('email', ''),
                    pec=row.get('pec', ''),
                    codice_sdi=row.get('codice_sdi', ''),
                    condizioni_pagamento=row.get('condizioni_pagamento', ''),
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

# routes_fornitori.py
from flask import Blueprint, render_template, request, jsonify, send_file
from models import db, Fornitore

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
                # Verifica se il fornitore esiste già
                if Fornitore.query.filter_by(ragione_sociale=row['ragione_sociale']).first():
                    errori.append(f"Riga {index + 1}: Fornitore {row['ragione_sociale']} già esistente")
                    continue
                
                fornitore = Fornitore(
                    ragione_sociale=row['ragione_sociale'],
                    partita_iva=row.get('partita_iva', ''),
                    codice_fiscale=row.get('codice_fiscale', ''),
                    indirizzo=row.get('indirizzo', ''),
                    citta=row.get('citta', ''),
                    provincia=row.get('provincia', ''),
                    cap=row.get('cap', ''),
                    telefono=row.get('telefono', ''),
                    email=row.get('email', ''),
                    pec=row.get('pec', ''),
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