from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

# Inizializzazione Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ddt_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'ddt-system-2024-secure-key'

# Inizializzazione estensioni
CORS(app)

# Import modelli (DEVE essere dopo app ma prima di db.init_app)
from models import db, DDTIn, DDTOut, CatalogoArticolo, Movimento, Cliente, Fornitore, Magazzino, Mastrino

# Inizializza database
db.init_app(app)

# Import utilities automatiche
from utils_automation import get_dashboard_stats, verifica_scorte_minime, calcola_valore_magazzino

# Import routes modulari
from routes_ddt import ddt_bp

# Registrazione blueprints
app.register_blueprint(ddt_bp, url_prefix='/ddt')

# ==================== ROUTES PRINCIPALI ====================
@app.route('/')
def dashboard():
    """Dashboard principale con statistiche real-time"""
    try:
        stats = get_dashboard_stats()
        articoli_sotto_scorta = len(verifica_scorte_minime())
        
        return render_template('dashboard.html',
                             ddt_in_count=stats['ddt_in_confermati'],
                             ddt_out_count=stats['ddt_out_confermati'],
                             bozze_count=stats['ddt_in_bozze'] + stats['ddt_out_bozze'],
                             valore_magazzino=stats['valore_magazzino'],
                             articoli_sotto_scorta=articoli_sotto_scorta,
                             movimenti_oggi=stats['movimenti_oggi'])
    except Exception as e:
        print(f"Errore dashboard: {e}")
        # Fallback values
        return render_template('dashboard.html',
                             ddt_in_count=0, ddt_out_count=0, bozze_count=0,
                             valore_magazzino=0, articoli_sotto_scorta=0, movimenti_oggi=0)

# ==================== CATALOGO ROUTES ====================
@app.route('/catalogo')
def catalogo_list():
    """Lista articoli catalogo"""
    search = request.args.get('search', '').strip()
    
    query = CatalogoArticolo.query.filter_by(attivo=True)
    if search:
        query = query.filter(
            db.or_(
                CatalogoArticolo.codice_interno.contains(search),
                CatalogoArticolo.descrizione.contains(search)
            )
        )
    
    articoli = query.order_by(CatalogoArticolo.codice_interno).all()
    sotto_scorta = len(verifica_scorte_minime())
    
    return render_template('catalogo.html', 
                         articoli=articoli, 
                         search=search,
                         sotto_scorta=sotto_scorta,
                         valore_magazzino=calcola_valore_magazzino())

@app.route('/catalogo/<int:id>')
def dettaglio_articolo(id):
    """Dettaglio articolo catalogo"""
    articolo = CatalogoArticolo.query.get_or_404(id)
    
    # Movimenti recenti
    movimenti = Movimento.query.filter_by(
        codice_articolo=articolo.codice_interno
    ).order_by(Movimento.data_movimento.desc()).limit(20).all()
    
    return render_template('dettaglio-articolo.html', 
                         articolo=articolo, 
                         movimenti=movimenti)

# ==================== MOVIMENTI ROUTES ====================
@app.route('/movimenti')
def movimenti_list():
    """Lista movimenti con filtri"""
    filtri = {
        'data_da': request.args.get('data_da'),
        'data_a': request.args.get('data_a'),
        'tipo': request.args.get('tipo'),
        'articolo': request.args.get('articolo')
    }
    
    query = Movimento.query
    
    # Applica filtri
    if filtri['data_da']:
        query = query.filter(Movimento.data_movimento >= datetime.strptime(filtri['data_da'], '%Y-%m-%d'))
    if filtri['data_a']:
        query = query.filter(Movimento.data_movimento <= datetime.strptime(filtri['data_a'], '%Y-%m-%d'))
    if filtri['tipo']:
        query = query.filter_by(tipo=filtri['tipo'])
    if filtri['articolo']:
        query = query.filter(Movimento.descrizione_articolo.contains(filtri['articolo']))
    
    movimenti = query.order_by(Movimento.data_movimento.desc()).limit(200).all()
    
    return render_template('movimenti.html', 
                         movimenti=movimenti, 
                         filtri=filtri)

# ==================== INVENTARIO ROUTES ====================
@app.route('/inventario')
def inventario_home():
    """Dashboard inventario"""
    articoli = CatalogoArticolo.query.filter_by(attivo=True).order_by(CatalogoArticolo.codice_interno).all()
    sotto_scorta = verifica_scorte_minime()
    
    statistiche = {
        'numero_articoli': len(articoli),
        'valore_totale': calcola_valore_magazzino(),
        'pezzi_totali': sum(a.giacenza_attuale for a in articoli),
        'sotto_scorta': len(sotto_scorta)
    }
    
    return render_template('inventario.html',
                         articoli=articoli,
                         statistiche=statistiche,
                         sotto_scorta=len(sotto_scorta))

# ==================== ANAGRAFICHE ROUTES ====================
@app.route('/clienti')
def clienti_list():
    """Lista clienti"""
    search = request.args.get('search', '').strip()
    
    query = Cliente.query.filter_by(attivo=True)
    if search:
        query = query.filter(Cliente.ragione_sociale.contains(search))
    
    clienti = query.order_by(Cliente.ragione_sociale).all()
    return render_template('clienti.html', clienti=clienti, search=search)

@app.route('/fornitori')
def fornitori_list():
    """Lista fornitori"""
    search = request.args.get('search', '').strip()
    
    query = Fornitore.query.filter_by(attivo=True)
    if search:
        query = query.filter(Fornitore.ragione_sociale.contains(search))
    
    fornitori = query.order_by(Fornitore.ragione_sociale).all()
    return render_template('fornitori.html', fornitori=fornitori, search=search)

# ==================== IMPOSTAZIONI ROUTES ====================
@app.route('/impostazioni')
def impostazioni_home():
    """Pagina impostazioni"""
    mastrini = Mastrino.query.order_by(Mastrino.tipo, Mastrino.codice).all()
    magazzini = Magazzino.query.order_by(Magazzino.codice).all()
    
    return render_template('impostazioni.html',
                         mastrini=mastrini,
                         magazzini=magazzini)

# ==================== API GLOBALI ====================
@app.route('/api/search')
def api_search():
    """Ricerca globale nel sistema"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({'results': []})
    
    results = []
    
    # Cerca articoli
    articoli = CatalogoArticolo.query.filter(
        db.or_(
            CatalogoArticolo.codice_interno.contains(query),
            CatalogoArticolo.descrizione.contains(query)
        ),
        CatalogoArticolo.attivo == True
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
            'subtitle': f"{ddt.fornitore}"
        })
    
    return jsonify({'results': results[:10]})

@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    """API statistiche dashboard real-time"""
    try:
        stats = get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== INIZIALIZZAZIONE DATABASE ====================
def init_database():
    """Inizializza database con dati base"""
    with app.app_context():
        db.create_all()
        
        # Verifica se è già inizializzato
        if Magazzino.query.first():
            return
        
        print("🔧 Inizializzazione database...")
        
        # Magazzini base
        magazzini = [
            Magazzino(codice='MAG001', descrizione='Magazzino Centrale', responsabile='Admin', attivo=True),
            Magazzino(codice='MAG002', descrizione='Deposito Nord', responsabile='Admin', attivo=True),
            Magazzino(codice='MAG003', descrizione='Deposito Sud', responsabile='Admin', attivo=True)
        ]
        
        # Mastrini base
        mastrini = [
            Mastrino(codice='ACQ001', descrizione='Acquisto Materiali', tipo='acquisto', attivo=True),
            Mastrino(codice='ACQ002', descrizione='Acquisto Attrezzature', tipo='acquisto', attivo=True),
            Mastrino(codice='VEN001', descrizione='Vendita Prodotti', tipo='ricavo', attivo=True),
            Mastrino(codice='VEN002', descrizione='Vendita Servizi', tipo='ricavo', attivo=True)
        ]
        
        # Fornitori/clienti esempio
        fornitore = Fornitore(
            ragione_sociale='Fornitore Esempio S.r.l.',
            partita_iva='12345678901',
            email='info@fornitore.it',
            citta='Milano',
            attivo=True
        )
        
        cliente = Cliente(
            ragione_sociale='Cliente Esempio S.r.l.',
            partita_iva='10987654321',
            email='info@cliente.it',
            citta='Roma',
            attivo=True
        )
        
        # Salva tutto
        for item in magazzini + mastrini + [fornitore, cliente]:
            db.session.add(item)
        
        db.session.commit()
        print("✅ Database inizializzato con successo")

# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ==================== AVVIO APPLICAZIONE ====================
if __name__ == '__main__':
    init_database()
    print("🚀 Sistema DDT avviato!")
    print("📊 Automatismi attivi:")
    print("   ✅ Numerazione progressiva DDT")
    print("   ✅ Popolamento automatico catalogo")
    print("   ✅ Calcolo costo medio ponderato")
    print("   ✅ Aggiornamento giacenze automatico")
    print("   ✅ Generazione movimenti")
    print("   ✅ Alert scorte minime")
    app.run(debug=True, host='0.0.0.0', port=5000)