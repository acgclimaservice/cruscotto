from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import os

# Inizializzazione app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ddt_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Inizializza estensioni
db = SQLAlchemy(app)
CORS(app)

# Import modelli dopo inizializzazione db
from models import *

# Import routes
from routes.routes_ddt import ddt_bp
from routes.routes_offerte import offerte_bp
from routes.routes_preventivi import preventivi_bp
from routes.routes_catalogo import catalogo_bp
from routes.routes_movimenti import movimenti_bp
from routes.routes_clienti import clienti_bp
from routes.routes_fornitori import fornitori_bp
from routes.routes_impostazioni import impostazioni_bp
from routes.routes_inventario import inventario_bp
from routes.routes_reports import reports_bp
from routes.routes_api import api_bp

# Registrazione blueprints
app.register_blueprint(ddt_bp, url_prefix='/ddt')
app.register_blueprint(offerte_bp, url_prefix='/offerte')
app.register_blueprint(preventivi_bp, url_prefix='/preventivi')
app.register_blueprint(catalogo_bp, url_prefix='/catalogo')
app.register_blueprint(movimenti_bp, url_prefix='/movimenti')
app.register_blueprint(clienti_bp, url_prefix='/clienti')
app.register_blueprint(fornitori_bp, url_prefix='/fornitori')
app.register_blueprint(impostazioni_bp, url_prefix='/impostazioni')
app.register_blueprint(inventario_bp, url_prefix='/inventario')
app.register_blueprint(reports_bp, url_prefix='/reports')
app.register_blueprint(api_bp, url_prefix='/api')

# Routes principali
@app.route('/')
def dashboard():
    """Dashboard principale con statistiche"""
    try:
        # Statistiche DDT
        ddt_in_count = DDTIn.query.filter_by(stato='confermato').count()
        ddt_out_count = DDTOut.query.filter_by(stato='confermato').count()
        
        # Bozze in attesa
        bozze_in = DDTIn.query.filter_by(stato='bozza').count()
        bozze_out = DDTOut.query.filter_by(stato='bozza').count()
        bozze_count = bozze_in + bozze_out
        
        # Statistiche magazzino
        from utils_automation import calcola_valore_magazzino, verifica_scorte_minime
        valore_magazzino = calcola_valore_magazzino()
        articoli_sotto_scorta = len(verifica_scorte_minime())
        
        # Movimenti ultimo mese
        data_limite = datetime.now() - timedelta(days=30)
        movimenti_mese = Movimento.query.filter(
            Movimento.data_movimento >= data_limite
        ).count()
        
        # Valore movimenti ultimo mese
        valore_entrate = db.session.query(db.func.sum(Movimento.valore_totale)).filter(
            Movimento.tipo == 'entrata',
            Movimento.data_movimento >= data_limite
        ).scalar() or 0
        
        valore_uscite = db.session.query(db.func.sum(Movimento.valore_totale)).filter(
            Movimento.tipo == 'uscita',
            Movimento.data_movimento >= data_limite
        ).scalar() or 0
        
        # Preventivi in corso
        preventivi_attivi = Preventivo.query.filter(
            Preventivo.stato.in_(['bozza', 'inviato'])
        ).count()
        
        # Offerte da valutare
        offerte_da_valutare = OffertaFornitore.query.filter_by(stato='ricevuta').count()
        
        statistiche = {
            'ddt_in_count': ddt_in_count,
            'ddt_out_count': ddt_out_count,
            'bozze_count': bozze_count,
            'valore_magazzino': valore_magazzino,
            'articoli_sotto_scorta': articoli_sotto_scorta,
            'movimenti_mese': movimenti_mese,
            'valore_entrate': valore_entrate,
            'valore_uscite': valore_uscite,
            'preventivi_attivi': preventivi_attivi,
            'offerte_da_valutare': offerte_da_valutare
        }
        
        return render_template('dashboard.html', **statistiche)
        
    except Exception as e:
        print(f"Errore dashboard: {e}")
        # Valori di fallback se ci sono errori
        return render_template('dashboard.html', 
                             ddt_in_count=0, ddt_out_count=0, bozze_count=0)

@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    """API per statistiche dashboard aggiornate"""
    try:
        oggi = datetime.now().date()
        ieri = oggi - timedelta(days=1)
        settimana_fa = oggi - timedelta(days=7)
        
        stats = {
            'movimenti_oggi': Movimento.query.filter(
                db.func.date(Movimento.data_movimento) == oggi
            ).count(),
            'movimenti_ieri': Movimento.query.filter(
                db.func.date(Movimento.data_movimento) == ieri
            ).count(),
            'valore_entrate_settimana': db.session.query(
                db.func.sum(Movimento.valore_totale)
            ).filter(
                Movimento.tipo == 'entrata',
                Movimento.data_movimento >= settimana_fa
            ).scalar() or 0,
            'valore_uscite_settimana': db.session.query(
                db.func.sum(Movimento.valore_totale)
            ).filter(
                Movimento.tipo == 'uscita', 
                Movimento.data_movimento >= settimana_fa
            ).scalar() or 0,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search')
def search_global():
    """Ricerca globale nel sistema"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': []})
    
    results = []
    
    try:
        # Cerca articoli
        articoli = CatalogoArticolo.query.filter(
            db.or_(
                CatalogoArticolo.codice_interno.contains(query),
                CatalogoArticolo.descrizione.contains(query)
            )
        ).limit(5).all()
        
        for art in articoli:
            results.append({
                'type': 'articolo',
                'title': f"{art.codice_interno} - {art.descrizione}",
                'url': f"/catalogo/{art.id}",
                'subtitle': f"Giacenza: {art.giacenza_attuale}"
            })
        
        # Cerca DDT
        ddts_in = DDTIn.query.filter(
            db.or_(
                DDTIn.numero_ddt.contains(query),
                DDTIn.fornitore.contains(query)
            )
        ).limit(3).all()
        
        for ddt in ddts_in:
            results.append({
                'type': 'ddt_in',
                'title': f"DDT IN {ddt.numero_ddt or 'Bozza'}",
                'url': f"/ddt/in/{ddt.id}",
                'subtitle': f"{ddt.fornitore} - {ddt.data_ddt_origine}"
            })
        
        # Cerca clienti
        clienti = Cliente.query.filter(
            Cliente.ragione_sociale.contains(query)
        ).limit(3).all()
        
        for cliente in clienti:
            results.append({
                'type': 'cliente',
                'title': cliente.ragione_sociale,
                'url': f"/clienti/{cliente.id}",
                'subtitle': cliente.citta or ''
            })
        
        return jsonify({'results': results[:10]})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# Inizializzazione database - CORRETTO per Flask 2.3+
def create_tables():
    """Crea le tabelle del database se non esistono"""
    try:
        with app.app_context():
            db.create_all()
            
            # Inizializzazione dati di base se il database è vuoto
            if not Magazzino.query.first():
                init_base_data()
                
    except Exception as e:
        print(f"Errore inizializzazione database: {e}")

def init_base_data():
    """Inizializza dati di base del sistema"""
    try:
        # Magazzini di default
        magazzini_default = [
            {'codice': 'MAG001', 'descrizione': 'Magazzino Centrale', 'responsabile': 'Admin'},
            {'codice': 'MAG002', 'descrizione': 'Deposito Nord', 'responsabile': 'Admin'},
            {'codice': 'MAG003', 'descrizione': 'Deposito Sud', 'responsabile': 'Admin'}
        ]
        
        for mag_data in magazzini_default:
            magazzino = Magazzino(**mag_data, attivo=True)
            db.session.add(magazzino)
        
        # Mastrini di default
        mastrini_default = [
            {'codice': 'ACQ001', 'descrizione': 'Acquisto Materiali', 'tipo': 'acquisto'},
            {'codice': 'ACQ002', 'descrizione': 'Acquisto Attrezzature', 'tipo': 'acquisto'},
            {'codice': 'VEN001', 'descrizione': 'Vendita Prodotti', 'tipo': 'ricavo'},
            {'codice': 'VEN002', 'descrizione': 'Vendita Servizi', 'tipo': 'ricavo'}
        ]
        
        for mast_data in mastrini_default:
            mastrino = Mastrino(**mast_data, attivo=True)
            db.session.add(mastrino)
        
        # Configurazioni sistema
        configurazioni_default = [
            {'chiave': 'azienda_nome', 'valore': 'Azienda S.r.l.', 'descrizione': 'Nome azienda'},
            {'chiave': 'azienda_piva', 'valore': '12345678901', 'descrizione': 'Partita IVA'},
            {'chiave': 'backup_automatico', 'valore': 'giornaliero', 'descrizione': 'Frequenza backup'},
            {'chiave': 'margine_default', 'valore': '40', 'descrizione': 'Margine % default'}
        ]
        
        for conf_data in configurazioni_default:
            config = ConfigurazioneSistema(**conf_data)
            db.session.add(config)
        
        db.session.commit()
        print("Dati di base inizializzati con successo")
        
    except Exception as e:
        print(f"Errore inizializzazione dati base: {e}")
        db.session.rollback()

# Context processor per template
@app.context_processor
def inject_global_vars():
    """Variabili globali disponibili in tutti i template"""
    return {
        'app_name': 'Sistema Gestione DDT',
        'current_year': datetime.now().year,
        'version': '2.0.0'
    }

if __name__ == '__main__':
    create_tables()  # Chiamata diretta invece del decorator deprecato
    app.run(debug=True, host='0.0.0.0', port=5000)