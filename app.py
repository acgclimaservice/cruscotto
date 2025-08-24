from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
import os
from models import db, DDTIn, DDTOut, CatalogoArticolo, Movimento, Cliente, Fornitore, Mastrino, Magazzino, Preventivo, OffertaFornitore
from document_templates import generate_ddt_in_pdf, generate_ddt_out_pdf, generate_preventivo_pdf, generate_ordine_fornitore_pdf

# Carica variabili d'ambiente
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ddt_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db.init_app(app)
CORS(app)

# Import e registra routes
try:
    from routes.routes_ddt import ddt_bp
    app.register_blueprint(ddt_bp, url_prefix='/ddt')
except:
    pass

try:
    from routes.routes_clienti import clienti_bp
    app.register_blueprint(clienti_bp, url_prefix='/api/clienti')
except:
    pass

try:
    from routes.routes_fornitori import fornitori_bp
    app.register_blueprint(fornitori_bp, url_prefix='/api/fornitori')
except:
    pass

try:
    from routes.routes_catalogo import catalogo_bp
    app.register_blueprint(catalogo_bp, url_prefix='/api/catalogo')
except:
    pass

try:
    from routes.routes_parsing import parsing_bp
    app.register_blueprint(parsing_bp, url_prefix='/api/parsing')
except:
    pass

# Routes base
@app.route('/')
def dashboard():
    try:
        ddt_in_count = DDTIn.query.filter_by(stato='confermato').count()
        ddt_out_count = DDTOut.query.filter_by(stato='confermato').count()
        bozze_count = DDTIn.query.filter_by(stato='bozza').count() + DDTOut.query.filter_by(stato='bozza').count()
    except:
        ddt_in_count = 0
        ddt_out_count = 0
        bozze_count = 0
    
    return render_template('dashboard.html', 
                         ddt_in_count=ddt_in_count,
                         ddt_out_count=ddt_out_count,
                         bozze_count=bozze_count)

@app.route('/ddt-in')
def ddt_in():
    try:
        ddts = DDTIn.query.all()
    except:
        ddts = []
    return render_template('ddt-in.html', ddts=ddts)

@app.route('/ddt/in/<int:ddt_id>')
def ddt_in_dettaglio(ddt_id):
    """Visualizza dettaglio DDT IN"""
    try:
        ddt = DDTIn.query.get_or_404(ddt_id)
        
        # TODO: Implementare relazione con articoli
        articoli = []  # Placeholder per articoli del DDT
        
        return render_template('ddt-in-page.html', ddt=ddt, articoli=articoli)
    except:
        from flask import abort
        abort(404)

@app.route('/ddt-out')
def ddt_out():
    try:
        ddts = DDTOut.query.all()
    except:
        ddts = []
    return render_template('ddt-out.html', ddts=ddts)

@app.route('/ddt/out/<int:ddt_id>')
def ddt_out_dettaglio(ddt_id):
    """Visualizza dettaglio DDT OUT"""
    try:
        ddt = DDTOut.query.get_or_404(ddt_id)
        
        # TODO: Implementare relazione con articoli
        articoli = []  # Placeholder per articoli del DDT
        
        return render_template('ddt-out-page.html', ddt=ddt, articoli=articoli)
    except:
        from flask import abort
        abort(404)

@app.route('/ddt/in/nuovo')
def nuovo_ddt_in():
    """Pagina creazione nuovo DDT IN"""
    return render_template('nuovo-ddt-in.html')

@app.route('/ddt/out/nuovo') 
def nuovo_ddt_out():
    """Pagina creazione nuovo DDT OUT"""
    return render_template('nuovo-ddt-out.html')

@app.route('/offerte')
def offerte():
    try:
        offerte = OffertaFornitore.query.all()
    except:
        offerte = []
    return render_template('offerte.html', offerte=offerte)

@app.route('/preventivi')
def preventivi():
    try:
        preventivi = Preventivo.query.all()
    except:
        preventivi = []
    return render_template('preventivi.html', preventivi=preventivi)

@app.route('/ordini')
def ordini():
    # Per ora restituiamo una pagina vuota - da implementare il model Ordine
    return render_template('ordini.html', ordini=[])

@app.route('/reports')
def reports():
    # Pagina reports mancante - da implementare
    return render_template('reports.html', reports=[], report={})

@app.route('/parsing-management')
def parsing_management():
    # Pagina gestione parsing e training AI
    return render_template('parsing-management.html')

@app.route('/mastrini')
def mastrini():
    try:
        mastrini = Mastrino.query.order_by(Mastrino.codice).all()
        # Aggiungi conteggio utilizzi se necessario
        for mastrino in mastrini:
            mastrino.utilizzi = 0  # TODO: implementare conteggio reale
    except:
        mastrini = []
    return render_template('mastrini.html', mastrini=mastrini)

@app.route('/catalogo')
def catalogo():
    try:
        articoli = CatalogoArticolo.query.filter_by(attivo=True).all()
        valore_magazzino = sum(a.giacenza_attuale * (a.costo_medio or 0) for a in articoli)
        sotto_scorta = len([a for a in articoli if a.giacenza_attuale < a.scorta_minima])
        esauriti = len([a for a in articoli if a.giacenza_attuale == 0])
    except:
        articoli = []
        valore_magazzino = 0
        sotto_scorta = 0
        esauriti = 0
    return render_template('catalogo.html', articoli=articoli, 
                          valore_magazzino=valore_magazzino,
                          sotto_scorta=sotto_scorta, esauriti=esauriti)

@app.route('/movimenti')
def movimenti():
    try:
        movimenti = Movimento.query.order_by(Movimento.data_movimento.desc()).limit(100).all()
    except:
        movimenti = []
    return render_template('movimenti.html', movimenti=movimenti, filtri={})

@app.route('/inventario')
def inventario():
    try:
        articoli = CatalogoArticolo.query.filter_by(attivo=True).all()
        valore_totale = sum(a.giacenza_attuale * (a.costo_medio or 0) for a in articoli)
        pezzi_totali = sum(a.giacenza_attuale for a in articoli)
        sotto_scorta = len([a for a in articoli if a.giacenza_attuale < a.scorta_minima])
        statistiche = {
            'valore_totale': valore_totale,
            'numero_articoli': len(articoli),
            'pezzi_totali': pezzi_totali
        }
    except:
        articoli = []
        statistiche = {'valore_totale': 0, 'numero_articoli': 0, 'pezzi_totali': 0}
        sotto_scorta = 0
    return render_template('inventario.html', articoli=articoli, 
                          statistiche=statistiche, sotto_scorta=sotto_scorta)

@app.route('/clienti')
def clienti():
    try:
        clienti = Cliente.query.filter_by(attivo=True).all()
    except:
        clienti = []
    return render_template('clienti.html', clienti=clienti)

@app.route('/fornitori')
def fornitori():
    try:
        fornitori = Fornitore.query.filter_by(attivo=True).all()
    except:
        fornitori = []
    return render_template('fornitori.html', fornitori=fornitori)

@app.route('/impostazioni')
def impostazioni():
    try:
        mastrini = Mastrino.query.all()
        magazzini = Magazzino.query.all()
    except:
        mastrini = []
        magazzini = []
    return render_template('impostazioni.html', mastrini=mastrini, 
                          magazzini=magazzini, configurazioni={})

# API endpoints
@app.route('/api/articolo/cerca/<codice>')
def cerca_articolo(codice):
    articolo = CatalogoArticolo.query.filter_by(codice_interno=codice).first()
    if articolo:
        return jsonify({
            'found': True,
            'descrizione': articolo.descrizione,
            'costo_ultimo': articolo.costo_ultimo,
            'prezzo_vendita': articolo.prezzo_vendita,
            'unita_misura': articolo.unita_misura
        })
    return jsonify({'found': False})

@app.route('/api/ddt-in', methods=['POST'])
def api_nuovo_ddt_in():
    try:
        data = request.json
        nuovo_ddt = DDTIn(
            data_ddt_origine=datetime.strptime(data['data_ddt_origine'], '%Y-%m-%d').date(),
            fornitore=data['fornitore'],
            riferimento=data.get('riferimento', ''),
            destinazione=data['destinazione'],
            stato='bozza'
        )
        db.session.add(nuovo_ddt)
        db.session.commit()
        return jsonify({'success': True, 'id': nuovo_ddt.id, 'message': 'DDT creato'}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/ddt-out', methods=['POST'])
def api_nuovo_ddt_out():
    try:
        data = request.json
        nuovo_ddt = DDTOut(
            data_ddt_origine=datetime.strptime(data['data_ddt_origine'], '%Y-%m-%d').date(),
            nome_origine=data['nome_origine'],
            riferimento=data.get('riferimento', ''),
            destinazione=data['destinazione'],
            magazzino_partenza=data.get('magazzino_partenza', ''),
            stato='bozza'
        )
        db.session.add(nuovo_ddt)
        db.session.commit()
        return jsonify({'success': True, 'id': nuovo_ddt.id, 'message': 'DDT creato'}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# Routes per generazione PDF documenti
@app.route('/api/ddt-in/<int:ddt_id>/pdf')
def api_ddt_in_pdf(ddt_id):
    """Genera PDF per DDT IN"""
    try:
        ddt = DDTIn.query.get_or_404(ddt_id)
        
        # Converti l'oggetto DDT in dict per il template
        ddt_data = {
            'numero_ddt': f"IN-{ddt.id:06d}",
            'fornitore': ddt.fornitore,
            'data_ddt_origine': ddt.data_ddt_origine.strftime('%d/%m/%Y') if ddt.data_ddt_origine else '',
            'numero_ddt_origine': ddt.numero_ddt_origine or '',
            'riferimento': ddt.riferimento or '',
            'destinazione': ddt.destinazione or '',
            'stato': ddt.stato or 'bozza',
            'articoli': []  # TODO: implementare relazione con articoli
        }
        
        html_content = generate_ddt_in_pdf(ddt_data)
        
        from flask import Response
        return Response(
            html_content,
            mimetype='text/html',
            headers={"Content-disposition": f"attachment; filename=DDT_IN_{ddt.id}.html"}
        )
        
    except Exception as e:
        return jsonify({'error': f'Errore generazione PDF: {str(e)}'}), 500

@app.route('/api/ddt-out/<int:ddt_id>/pdf')
def api_ddt_out_pdf(ddt_id):
    """Genera PDF per DDT OUT"""
    try:
        ddt = DDTOut.query.get_or_404(ddt_id)
        
        ddt_data = {
            'numero_ddt': f"OUT-{ddt.id:06d}",
            'nome_origine': ddt.nome_origine,
            'data_ddt_origine': ddt.data_ddt_origine.strftime('%d/%m/%Y') if ddt.data_ddt_origine else '',
            'riferimento': ddt.riferimento or '',
            'destinazione': ddt.destinazione or '',
            'magazzino_partenza': ddt.magazzino_partenza or '',
            'stato': ddt.stato or 'bozza'
        }
        
        html_content = generate_ddt_out_pdf(ddt_data)
        
        from flask import Response
        return Response(
            html_content,
            mimetype='text/html',
            headers={"Content-disposition": f"attachment; filename=DDT_OUT_{ddt.id}.html"}
        )
        
    except Exception as e:
        return jsonify({'error': f'Errore generazione PDF: {str(e)}'}), 500

@app.route('/api/preventivi/<int:preventivo_id>/pdf')
def api_preventivo_pdf(preventivo_id):
    """Genera PDF per Preventivo"""
    try:
        preventivo = Preventivo.query.get_or_404(preventivo_id)
        
        preventivo_data = {
            'numero': f"PREV-{preventivo.id:06d}",
            'cliente': preventivo.cliente_nome or 'N/A',
            'data_creazione': preventivo.data_creazione.strftime('%d/%m/%Y') if preventivo.data_creazione else '',
            'oggetto': preventivo.oggetto or '',
            'validita_giorni': 30,
            'stato': preventivo.stato or 'bozza'
        }
        
        html_content = generate_preventivo_pdf(preventivo_data)
        
        from flask import Response
        return Response(
            html_content,
            mimetype='text/html',
            headers={"Content-disposition": f"attachment; filename=Preventivo_{preventivo.id}.html"}
        )
        
    except Exception as e:
        return jsonify({'error': f'Errore generazione PDF: {str(e)}'}), 500

@app.route('/api/ordini/<int:ordine_id>/pdf')
def api_ordine_pdf(ordine_id):
    """Genera PDF per Ordine (placeholder per futura implementazione)"""
    try:
        # TODO: Implementare model Ordine
        ordine_data = {
            'numero': f"ORD-{ordine_id:06d}",
            'fornitore': 'Fornitore da implementare',
            'data_ordine': datetime.now().strftime('%d/%m/%Y'),
            'riferimento': '',
            'data_consegna': 'Da concordare',
            'stato': 'emesso',
            'condizioni_pagamento': '30 gg fm'
        }
        
        html_content = generate_ordine_fornitore_pdf(ordine_data)
        
        from flask import Response
        return Response(
            html_content,
            mimetype='text/html',
            headers={"Content-disposition": f"attachment; filename=Ordine_{ordine_id}.html"}
        )
        
    except Exception as e:
        return jsonify({'error': f'Errore generazione PDF: {str(e)}'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
