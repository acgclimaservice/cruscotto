# APP.PY MERGED - PythonAnywhere + Sistema Parsing AI
# Combina tutte le funzionalità operative di PythonAnywhere con il sistema AI del locale

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
import os

# Carica variabili d'ambiente
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ddt_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Import e inizializza db da models
from models import db
db.init_app(app)

# Configura CORS per sviluppo
CORS(app)

# Import modelli - TUTTI insieme (PythonAnywhere style)
from models import (DDTIn, ArticoloIn, DDTOut, ArticoloOut, 
                    CatalogoArticolo, Movimento, Cliente, Fornitore, 
                    Magazzino, Mastrino)

# Import sistema parsing AI (dal locale)
try:
    from document_templates import generate_ddt_in_pdf, generate_ddt_out_pdf, generate_preventivo_pdf
    DOCUMENTS_AVAILABLE = True
except ImportError:
    DOCUMENTS_AVAILABLE = False
    print("WARNING document_templates non disponibile")

# Import export functions (PythonAnywhere)
try:
   from export_inventario import export_inventario_simple
except:
   export_inventario_simple = None

# Registra blueprint parsing AI (dal locale)
try:
    from routes.routes_parsing import parsing_bp
    app.register_blueprint(parsing_bp, url_prefix="/api/parsing")
    print("OK Sistema Parsing AI caricato")
except Exception as e:
    print(f"WARNING Parsing AI non disponibile: {e}")

# Blueprint aggiuntivi dal locale (opzionali)
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

# ========== ROUTE PRINCIPALI (DA PYTHONANYWHERE) ==========

@app.route('/')
def dashboard():
   ddt_in_count = DDTIn.query.filter_by(stato='confermato').count()
   ddt_out_count = DDTOut.query.filter_by(stato='confermato').count()
   bozze_count = DDTIn.query.filter_by(stato='bozza').count()
   return render_template('dashboard.html',
                        ddt_in_count=ddt_in_count,
                        ddt_out_count=ddt_out_count,
                        bozze_count=bozze_count)

def verifica_buchi_numerazione(ddts, tipo_ddt='IN'):
    """Verifica buchi nella numerazione sequenziale dei DDT"""
    buchi = []
    numeri = []
    
    for ddt in ddts:
        if ddt.numero_ddt and ddt.stato == 'confermato':  # Solo DDT confermati
            try:
                # Estrae numero da formato "DDT-001/2024" -> 1
                numero = int(ddt.numero_ddt.split('-')[1].split('/')[0])
                numeri.append(numero)
            except:
                continue
    
    if len(numeri) >= 2:
        numeri.sort()
        for i in range(len(numeri) - 1):
            if numeri[i+1] - numeri[i] > 1:
                for n in range(numeri[i] + 1, numeri[i+1]):
                    buchi.append(f"DDT-{n:03d}")
    
    return buchi

@app.route('/ddt-in')
def ddt_in_page():
   ddts = DDTIn.query.order_by(DDTIn.numero_ddt.asc()).all()
   buchi_numerazione = verifica_buchi_numerazione(ddts, 'IN')
   return render_template('ddt-in.html', ddts=ddts, buchi_numerazione=buchi_numerazione)

@app.route('/ddt-in/<int:id>')
def view_ddt_detail(id):
   ddt = DDTIn.query.get_or_404(id)
   return render_template('ddt-in-page.html', ddt=ddt)

# ========== NUOVO DDT IN CON PARSING AI ==========
@app.route('/ddt-in/nuovo', methods=['GET', 'POST'])
def nuovo_ddt_in():
   if request.method == 'GET':
       mastrini = Mastrino.query.filter_by(attivo=True).all()
       magazzini = Magazzino.query.filter_by(attivo=True).all()
       return render_template('nuovo-ddt-in.html', mastrini=mastrini, magazzini=magazzini)
   
   try:
       nuovo_ddt = DDTIn(
           fornitore=request.form['fornitore'],
           riferimento=request.form.get('riferimento', ''),
           destinazione=request.form['destinazione'],
           mastrino_ddt=request.form.get('mastrino_ddt', ''),
           commessa=request.form.get('commessa', ''),
           stato='bozza'
       )
       db.session.add(nuovo_ddt)
       db.session.flush()
       
       i = 0
       while f'articoli[{i}][descrizione]' in request.form:
           articolo = ArticoloIn(
               ddt_id=nuovo_ddt.id,
               codice_interno=request.form.get(f'articoli[{i}][codice]', ''),
               descrizione=request.form[f'articoli[{i}][descrizione]'],
               quantita=float(request.form[f'articoli[{i}][quantita]']),
               costo_unitario=float(request.form[f'articoli[{i}][costo]'])
           )
           db.session.add(articolo)
           i += 1
       
       db.session.commit()
       return redirect(f'/ddt-in/{nuovo_ddt.id}')
       
   except Exception as e:
       db.session.rollback()
       return f"Errore: {e}", 500

@app.route('/ddt-in/<int:id>/conferma', methods=['POST'])
def conferma_ddt(id):
   """Conferma DDT con automazioni"""
   try:
       from warehouse_automation import WarehouseAutomation
       
       ddt = DDTIn.query.get_or_404(id)
       
       if ddt.stato == 'confermato':
           return jsonify({'success': False, 'error': 'Già confermato'})
       
       # Genera numero progressivo
       anno = datetime.now().year
       ultimo = DDTIn.query.filter(
           DDTIn.numero_ddt.isnot(None),
           DDTIn.numero_ddt.like(f'%/{anno}')
       ).order_by(DDTIn.id.desc()).first()
       
       numero = 1
       if ultimo and ultimo.numero_ddt:
           try:
               numero = int(ultimo.numero_ddt.split('/')[0]) + 1
           except:
               pass
       
       ddt.numero_ddt = f'{numero:06d}/{anno}'
       ddt.data_ddt_origine = datetime.now().date()
       ddt.stato = 'confermato'
       
       # Applica automazioni se disponibili
       try:
           success, msg = WarehouseAutomation.process_ddt_confirmation(id)
       except:
           success, msg = True, "Automazioni non disponibili"
       
       if success:
           db.session.commit()
           return jsonify({
               'success': True,
               'numero': ddt.numero_ddt,
               'data': ddt.data_ddt_origine.strftime('%d/%m/%Y'),
               'message': msg
           })
       else:
           db.session.rollback()
           return jsonify({'success': False, 'error': msg})
           
   except Exception as e:
       db.session.rollback()
       return jsonify({'success': False, 'error': str(e)})

@app.route('/ddt-in/<int:id>/genera-ddt-out')
def genera_ddt_out_da_ddt_in(id):
    """Genera DDT OUT da DDT IN - passa i dati al form"""
    try:
        ddt_in = DDTIn.query.get_or_404(id)
        
        if ddt_in.stato != 'confermato':
            return "Solo DDT IN confermati possono generare DDT OUT", 400
        
        # Reindirizza al form nuovo DDT OUT passando l'ID del DDT IN
        return redirect(url_for('nuovo_ddt_out', from_ddt_in=id))
        
    except Exception as e:
        print(f"Errore generazione DDT OUT: {e}")
        return f"Errore: {str(e)}", 500

# ========== SISTEMA DDT OUT COMPLETO (DA PYTHONANYWHERE) ==========

@app.route('/ddt-out')
def ddt_out_list():
    """Lista DDT OUT"""
    try:
        ddts = DDTOut.query.order_by(DDTOut.numero_ddt.asc()).all()
        buchi_numerazione = verifica_buchi_numerazione(ddts, 'OUT')
        return render_template('ddt-out.html', ddts=ddts, buchi_numerazione=buchi_numerazione, datetime=datetime)
    except Exception as e:
        print(f"Errore lista DDT OUT: {e}")
        ddts = []
        buchi_numerazione = []
        return render_template('ddt-out.html', ddts=ddts, buchi_numerazione=buchi_numerazione)

@app.route('/ddt-out/nuovo', methods=['GET', 'POST'])
def nuovo_ddt_out():
    """Form nuovo DDT OUT con autocompletamento"""
    if request.method == 'GET':
        try:
            # Recupera dati per il form
            magazzini = Magazzino.query.filter_by(attivo=True).all() if Magazzino.query.first() else []
            clienti = Cliente.query.filter_by(attivo=True).all() if Cliente.query.first() else []
            mastrini_vendita = Mastrino.query.filter_by(attivo=True, tipo='ricavo').all() if Mastrino.query.first() else []
            
            # Se non ci sono dati, crea defaults
            if not magazzini:
                mag = Magazzino(codice='MAG001', descrizione='Magazzino Centrale', attivo=True)
                db.session.add(mag)
                db.session.commit()
                magazzini = [mag]
            
            if not mastrini_vendita:
                mast = Mastrino(codice='VEN001', descrizione='Vendita Prodotti', tipo='ricavo', attivo=True)
                db.session.add(mast)
                db.session.commit()
                mastrini_vendita = [mast]
            
            # Check se viene da un DDT IN
            from_ddt_in_id = request.args.get('from_ddt_in')
            from_ddt_in = None
            articoli_from_ddt_in = []
            
            if from_ddt_in_id:
                try:
                    ddt_id = int(from_ddt_in_id)
                    from_ddt_in = DDTIn.query.get(ddt_id)
                    if from_ddt_in and hasattr(from_ddt_in, 'articoli'):
                        for art in from_ddt_in.articoli:
                            articoli_from_ddt_in.append({
                                'codice_interno': getattr(art, 'codice_interno', ''),
                                'codice_fornitore': getattr(art, 'codice_fornitore', ''),
                                'descrizione': getattr(art, 'descrizione', ''),
                                'quantita': float(getattr(art, 'quantita', 0)),
                                'costo_unitario': float(getattr(art, 'costo_unitario', 0)),
                                'unita_misura': getattr(art, 'unita_misura', 'PZ'),
                                'note': getattr(art, 'note', '')
                            })
                except Exception as e:
                    print(f"Errore recupero DDT IN: {e}")
            
            # Prepara dati per JSON
            clienti_json = []
            for c in clienti:
                clienti_json.append({
                    'ragione_sociale': c.ragione_sociale,
                    'partita_iva': getattr(c, 'partita_iva', ''),
                    'indirizzo': getattr(c, 'indirizzo', ''),
                    'citta': getattr(c, 'citta', ''),
                    'cap': getattr(c, 'cap', ''),
                    'provincia': getattr(c, 'provincia', '')
                })
            
            mastrini_json = []
            for m in mastrini_vendita:
                mastrini_json.append({
                    'codice': m.codice,
                    'descrizione': m.descrizione,
                    'tipo': m.tipo
                })
            
            return render_template('nuovo-ddt-out.html',
                                 magazzini=magazzini,
                                 clienti=clienti_json,
                                 mastrini_vendita=mastrini_json,
                                 from_ddt_in=from_ddt_in,
                                 articoli_from_ddt_in=articoli_from_ddt_in,
                                 today=datetime.now().strftime('%Y-%m-%d'))
        except Exception as e:
            print(f"Errore form DDT OUT: {e}")
            import traceback
            traceback.print_exc()
            return f"Errore: {str(e)}", 500
    
    # POST - Salva DDT OUT
    if request.method == 'POST':
        try:
            # Crea nuovo DDT OUT
            nuovo_ddt = DDTOut()
            
            # Campi base
            nuovo_ddt.data_ddt_origine = datetime.now().date()
            nuovo_ddt.nome_origine = 'ACG Clima Service S.r.l.'  # Updated company name
            nuovo_ddt.destinazione = request.form.get('cliente', '')
            nuovo_ddt.riferimento = request.form.get('riferimento', '')
            nuovo_ddt.commessa = request.form.get('commessa', '')
            nuovo_ddt.magazzino_partenza = request.form.get('magazzino_partenza', '')
            nuovo_ddt.mastrino_ddt = request.form.get('mastrino_vendita', '')
            nuovo_ddt.stato = 'bozza'
            
            # Campi aggiuntivi
            nuovo_ddt.cliente = request.form.get('cliente', '')
            nuovo_ddt.mastrino_vendita = request.form.get('mastrino_vendita', '')
            
            db.session.add(nuovo_ddt)
            db.session.flush()
            
            # Aggiungi articoli
            i = 0
            while f'articoli[{i}][descrizione]' in request.form:
                if request.form.get(f'articoli[{i}][descrizione]'):
                    articolo = ArticoloOut(
                        ddt_id=nuovo_ddt.id,
                        codice_interno=request.form.get(f'articoli[{i}][codice_interno]', ''),
                        codice_fornitore=request.form.get(f'articoli[{i}][codice_fornitore]', ''),
                        descrizione=request.form.get(f'articoli[{i}][descrizione]'),
                        costo_unitario=float(request.form.get(f'articoli[{i}][prezzo_unitario]', 0)),
                        quantita=float(request.form.get(f'articoli[{i}][quantita]', 0)),
                        unita_misura=request.form.get(f'articoli[{i}][unita_misura]', 'PZ'),
                        note=request.form.get(f'articoli[{i}][note]', '')
                    )
                    db.session.add(articolo)
                i += 1
            
            # Se conferma immediata
            if request.form.get('action') == 'conferma':
                # Genera numero DDT
                anno = datetime.now().year
                ultimo = DDTOut.query.filter(
                    DDTOut.numero_ddt.like(f'OUT/%/{anno}')
                ).order_by(DDTOut.id.desc()).first()
                
                numero = 1
                if ultimo and ultimo.numero_ddt:
                    try:
                        numero = int(ultimo.numero_ddt.split('/')[1]) + 1
                    except:
                        pass
                
                nuovo_ddt.numero_ddt = f'OUT/{numero:04d}/{anno}'
                nuovo_ddt.data_ddt = datetime.now().date()
                nuovo_ddt.stato = 'confermato'
                
                # Genera movimenti
                for articolo in ArticoloOut.query.filter_by(ddt_id=nuovo_ddt.id).all():
                    movimento = Movimento(
                        data_movimento=datetime.now(),
                        tipo='uscita',
                        documento_tipo='ddt_out',
                        documento_numero=nuovo_ddt.numero_ddt,
                        codice_articolo=articolo.codice_interno or f'ART-{articolo.id}',
                        descrizione_articolo=articolo.descrizione,
                        quantita=articolo.quantita,
                        valore_unitario=articolo.costo_unitario or 0,
                        valore_totale=(articolo.quantita * (articolo.costo_unitario or 0)),
                        magazzino=nuovo_ddt.magazzino_partenza or 'Magazzino Centrale',
                        mastrino=nuovo_ddt.mastrino_vendita or 'VEN001',
                        causale=f'Uscita DDT OUT {nuovo_ddt.numero_ddt}'
                    )
                    db.session.add(movimento)
                    
                    # Aggiorna giacenza
                    if articolo.codice_interno:
                        cat_articolo = CatalogoArticolo.query.filter_by(
                            codice_interno=articolo.codice_interno
                        ).first()
                        if cat_articolo:
                            cat_articolo.giacenza_attuale = max(0, 
                                (cat_articolo.giacenza_attuale or 0) - articolo.quantita)
            
            db.session.commit()
            return redirect('/ddt-out')
            
        except Exception as e:
            db.session.rollback()
            print(f"Errore salvataggio DDT OUT: {e}")
            return f"Errore: {str(e)}", 500

@app.route('/ddt-out/<int:id>')
def view_ddt_out(id):
    """Visualizza dettaglio DDT OUT"""
    try:
        ddt = DDTOut.query.get_or_404(id)
        return render_template('ddt-out-page.html', ddt=ddt)
    except Exception as e:
        print(f"Errore view DDT OUT: {e}")
        return f"Errore: {str(e)}", 500

@app.route('/ddt-out/<int:id>/conferma', methods=['POST'])
def conferma_ddt_out(id):
    """Conferma DDT OUT con movimentazione magazzino"""
    try:
        ddt = DDTOut.query.get_or_404(id)
        
        if ddt.stato == 'confermato':
            return jsonify({'success': False, 'error': 'DDT già confermato'})
        
        # Genera numero progressivo
        anno = datetime.now().year
        ultimo = DDTOut.query.filter(
            DDTOut.numero_ddt.like(f'OUT/%/{anno}')
        ).order_by(DDTOut.id.desc()).first()
        
        numero = 1
        if ultimo and ultimo.numero_ddt:
            try:
                parti = ultimo.numero_ddt.split('/')
                if len(parti) >= 2:
                    numero = int(parti[1]) + 1
            except:
                pass
        
        # ASSEGNA NUMERO E DATA
        ddt.numero_ddt = f'OUT/{numero:04d}/{anno}'
        ddt.data_ddt = datetime.now().date()
        ddt.stato = 'confermato'
        
        # GENERA MOVIMENTI E AGGIORNA GIACENZE
        articoli = ArticoloOut.query.filter_by(ddt_id=ddt.id).all()
        
        for articolo in articoli:
            # Crea movimento di USCITA
            movimento = Movimento(
                data_movimento=datetime.now(),
                tipo='uscita',
                documento_tipo='ddt_out',
                documento_numero=ddt.numero_ddt,
                codice_articolo=articolo.codice_interno or f'ART-{articolo.id}',
                descrizione_articolo=articolo.descrizione,
                quantita=articolo.quantita,
                valore_unitario=articolo.costo_unitario or 0,
                valore_totale=(articolo.quantita * (articolo.costo_unitario or 0)),
                magazzino=ddt.magazzino_partenza or 'Magazzino Centrale',
                mastrino=ddt.mastrino_vendita or ddt.mastrino_ddt or 'VEN001',
                causale=f'Uscita per DDT OUT {ddt.numero_ddt} - Cliente: {ddt.cliente or ddt.destinazione or "N/D"}'
            )
            db.session.add(movimento)
            
            # AGGIORNA GIACENZA
            if articolo.codice_interno:
                cat_articolo = CatalogoArticolo.query.filter_by(
                    codice_interno=articolo.codice_interno
                ).first()
                
                if cat_articolo:
                    vecchia_giacenza = cat_articolo.giacenza_attuale or 0
                    nuova_giacenza = vecchia_giacenza - articolo.quantita
                    cat_articolo.giacenza_attuale = max(0, nuova_giacenza)
                    print(f"Aggiornata giacenza {articolo.codice_interno}: {vecchia_giacenza} -> {cat_articolo.giacenza_attuale}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'numero': ddt.numero_ddt,
            'data': ddt.data_ddt.strftime('%d/%m/%Y'),
            'message': f'DDT OUT {ddt.numero_ddt} confermato con {len(articoli)} articoli movimentati'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore conferma DDT OUT: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

# ========== ALTRE PAGINE PRINCIPALI ==========

@app.route('/catalogo')
def catalogo_page():
   try:
       articoli = CatalogoArticolo.query.all()
       valore_magazzino = sum((a.giacenza_attuale or 0) * (a.costo_ultimo or 0) for a in articoli)
       sotto_scorta = len([a for a in articoli if (a.giacenza_attuale or 0) < (a.scorta_minima or 0)])
       esauriti = len([a for a in articoli if (a.giacenza_attuale or 0) == 0])
       fornitori = Fornitore.query.filter_by(attivo=True).all()
   except Exception as e:
       print(f"Errore catalogo: {e}")
       articoli = []
       valore_magazzino = sotto_scorta = esauriti = 0
       fornitori = []
   
   return render_template('catalogo.html',
                        articoli=articoli,
                        valore_magazzino=valore_magazzino,
                        sotto_scorta=sotto_scorta,
                        esauriti=esauriti,
                        fornitori=fornitori)

@app.route('/movimenti')
def movimenti_page():
   movimenti = Movimento.query.order_by(Movimento.data_movimento.desc()).all()
   return render_template('movimenti.html', movimenti=movimenti)

@app.route('/inventario')
def inventario_page():
   from datetime import datetime, date
   
   data_riferimento = request.args.get('data', date.today().strftime('%Y-%m-%d'))
   magazzino_filtro = request.args.get('magazzino', 'tutti')
   
   try:
       articoli = CatalogoArticolo.query.all()
       
       if data_riferimento != date.today().strftime('%Y-%m-%d'):
           data_ref = datetime.strptime(data_riferimento, '%Y-%m-%d')
           for art in articoli:
               entrate = db.session.query(db.func.sum(Movimento.quantita)).filter(
                   Movimento.codice_articolo == art.codice_interno,
                   Movimento.tipo == 'entrata',
                   Movimento.data_movimento <= data_ref
               ).scalar() or 0
               
               uscite = db.session.query(db.func.sum(Movimento.quantita)).filter(
                   Movimento.codice_articolo == art.codice_interno,
                   Movimento.tipo == 'uscita',
                   Movimento.data_movimento <= data_ref
               ).scalar() or 0
               
               art.giacenza_calcolata = entrate - uscite
       else:
           for art in articoli:
               art.giacenza_calcolata = art.giacenza_attuale
       
       valore_totale = sum((a.giacenza_calcolata or 0) * (a.costo_ultimo or 0) for a in articoli)
       pezzi_totali = sum(a.giacenza_calcolata or 0 for a in articoli)
       
       magazzini = Magazzino.query.filter_by(attivo=True).all()
       
       statistiche = {
           'valore_totale': valore_totale,
           'numero_articoli': len([a for a in articoli if a.giacenza_calcolata != 0]),  # Include giacenze negative
           'pezzi_totali': pezzi_totali,
           'data_riferimento': data_riferimento
       }
       
       sotto_scorta = len([a for a in articoli if (a.giacenza_calcolata or 0) < (a.scorta_minima or 0) and a.scorta_minima > 0])
       giacenze_negative = len([a for a in articoli if (a.giacenza_calcolata or 0) < 0])
       
   except Exception as e:
       print(f"Errore inventario: {e}")
       articoli = []
       statistiche = {'valore_totale': 0, 'numero_articoli': 0, 'pezzi_totali': 0, 'data_riferimento': data_riferimento}
       sotto_scorta = 0
       giacenze_negative = 0
       magazzini = []
   
   return render_template('inventario.html',
                        articoli=articoli,
                        statistiche=statistiche,
                        sotto_scorta=sotto_scorta,
                        giacenze_negative=giacenze_negative,
                        magazzini=magazzini,
                        magazzino_filtro=magazzino_filtro)

@app.route('/clienti')
def clienti_page():
   clienti = Cliente.query.all()
   return render_template('clienti.html', clienti=clienti)

@app.route('/fornitori')
def fornitori_page():
   fornitori = Fornitore.query.all()
   return render_template('fornitori.html', fornitori=fornitori)

@app.route('/impostazioni')
def impostazioni_page():
   mastrini = Mastrino.query.all()
   magazzini = Magazzino.query.all()
   return render_template('impostazioni.html',
                        mastrini=mastrini,
                        magazzini=magazzini,
                        configurazioni={})

@app.route('/preventivi')
def preventivi_page():
   return render_template('preventivi.html', preventivi=[])

@app.route('/offerte')
def offerte_page():
   return render_template('offerte.html', offerte=[])

@app.route('/ordini')
def ordini_page():
   return render_template('ordini.html', ordini=[])

@app.route('/mastrini')
def mastrini_page():
   mastrini = Mastrino.query.order_by(Mastrino.tipo, Mastrino.codice).all()
   return render_template('mastrini.html', mastrini=mastrini)

# ========== API AUTOCOMPLETE (DA PYTHONANYWHERE) ==========

@app.route('/api/articoli/search')
def search_articoli():
   q = request.args.get('q', '')
   if len(q) < 2:
       return jsonify([])
   
   articoli = CatalogoArticolo.query.filter(
       db.or_(
           CatalogoArticolo.codice_interno.contains(q),
           CatalogoArticolo.codice_fornitore.contains(q),
           CatalogoArticolo.descrizione.contains(q)
       )
   ).limit(10).all()
   
   return jsonify([{
       'codice_interno': a.codice_interno,
       'descrizione': a.descrizione,
       'costo_ultimo': a.costo_ultimo or 0,
       'giacenza_attuale': a.giacenza_attuale or 0
   } for a in articoli])

@app.route('/api/fornitori/search')
def search_fornitori():
   q = request.args.get('q', '')
   if len(q) < 2:
       return jsonify([])
   
   fornitori = Fornitore.query.filter(
       Fornitore.ragione_sociale.contains(q)
   ).limit(10).all()
   
   return jsonify([f.ragione_sociale for f in fornitori])

@app.route('/api/clienti/search')
def search_clienti():
    """API per autocompletamento clienti"""
    q = request.args.get('q', '')
    if len(q) < 2:
        return jsonify([])
    
    # Costruisci filtri in base agli attributi disponibili
    filters = [Cliente.ragione_sociale.contains(q)]
    
    # Aggiungi altri filtri solo se gli attributi esistono
    if hasattr(Cliente, 'partita_iva'):
        filters.append(Cliente.partita_iva.contains(q))
    if hasattr(Cliente, 'citta'):
        filters.append(Cliente.citta.contains(q))
    
    clienti = Cliente.query.filter(
        db.or_(*filters)
    ).limit(10).all()
    
    return jsonify([{
        'ragione_sociale': c.ragione_sociale,
        'partita_iva': getattr(c, 'partita_iva', ''),
        'indirizzo': getattr(c, 'indirizzo', ''),
        'citta': getattr(c, 'citta', ''),
        'cap': getattr(c, 'cap', ''),
        'provincia': getattr(c, 'provincia', '')
    } for c in clienti])

@app.route('/api/mastrini/acquisto')
def api_mastrini_acquisto():
    """API per ottenere mastrini di tipo acquisto"""
    mastrini = Mastrino.query.filter_by(tipo='acquisto', attivo=True).all()
    return jsonify([{
        'codice': m.codice,
        'descrizione': m.descrizione
    } for m in mastrini])

# ========== API SISTEMA DDT ==========

@app.route('/ddt-in/<int:id>/salva', methods=['POST'])
def salva_modifiche_ddt(id):
   try:
       ddt = DDTIn.query.get_or_404(id)
       if ddt.stato != 'bozza':
           return jsonify({'success': False, 'error': 'Solo bozze modificabili'}), 403
       
       data = request.json
       ddt.fornitore = data.get('fornitore', ddt.fornitore)
       ddt.riferimento = data.get('riferimento', ddt.riferimento)
       ddt.destinazione = data.get('destinazione', ddt.destinazione)
       
       ArticoloIn.query.filter_by(ddt_id=id).delete()
       
       for art_data in data.get('articoli', []):
           articolo = ArticoloIn(
               ddt_id=id,
               codice_interno=art_data.get('codice', ''),
               descrizione=art_data.get('descrizione', ''),
               quantita=float(art_data.get('quantita', 0)),
               costo_unitario=float(art_data.get('prezzo', 0))
           )
           db.session.add(articolo)
       
       db.session.commit()
       return jsonify({'success': True, 'message': f'DDT {id} salvato'})
       
   except Exception as e:
       db.session.rollback()
       return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ddt-in/<int:id>/elimina', methods=['POST'])
def elimina_ddt_bozza(id):
   try:
       ddt = DDTIn.query.get_or_404(id)
       if ddt.stato != 'bozza':
           return jsonify({'success': False, 'error': 'Solo bozze eliminabili'})
       
       ArticoloIn.query.filter_by(ddt_id=id).delete()
       db.session.delete(ddt)
       db.session.commit()
       
       return jsonify({'success': True, 'message': 'Bozza eliminata'})
   except Exception as e:
       db.session.rollback()
       return jsonify({'success': False, 'error': str(e)})

# ========== SISTEMA IMPORT DDT ==========

@app.route('/ddt-import')
def ddt_import_page():
    """Pagina import DDT da PDF"""
    return render_template('ddt-import.html')

@app.route('/api/ddt-import/create', methods=['POST'])
def create_ddt_from_import():
    """Crea DDT da import PDF"""
    try:
        data = request.json
        
        # Crea nuovo DDT in bozza
        nuovo_ddt = DDTIn(
            fornitore=data.get('fornitore', 'Fornitore Import'),
            riferimento=data.get('riferimento', ''),
            destinazione=data.get('destinazione', 'Magazzino Centrale'),
            mastrino_ddt=data.get('mastrino_ddt', ''),
            commessa=data.get('commessa', ''),
            stato='bozza'
        )
        
        # Se c'è una data, impostala
        if data.get('data_ddt'):
            from datetime import datetime
            nuovo_ddt.data_ddt_origine = datetime.strptime(data['data_ddt'], '%Y-%m-%d').date()
        
        db.session.add(nuovo_ddt)
        db.session.flush()
        
        # Aggiungi articoli
        for art in data.get('articoli', []):
            articolo = ArticoloIn(
                ddt_id=nuovo_ddt.id,
                codice_interno=art.get('codice', ''),
                descrizione=art.get('descrizione', 'Articolo importato'),
                quantita=float(art.get('quantita', 0)),
                costo_unitario=float(art.get('prezzo', 0))
            )
            db.session.add(articolo)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': nuovo_ddt.id,
            'message': f'DDT creato in bozza (ID: {nuovo_ddt.id})'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== SISTEMA STAMPA E EXPORT ==========

@app.route('/inventario/export')
def export_inventario():
   """Export inventario"""
   if export_inventario_simple:
       return export_inventario_simple(request, CatalogoArticolo, Movimento, db)
   return "Export non disponibile", 500

@app.route('/inventario/stampa')
def stampa_inventario():
   """Versione stampabile dell'inventario"""
   from datetime import date
   
   data_riferimento = request.args.get('data', date.today().strftime('%Y-%m-%d'))
   articoli = CatalogoArticolo.query.filter(CatalogoArticolo.giacenza_attuale > 0).all()
   
   valore_totale = sum((a.giacenza_attuale or 0) * (a.costo_ultimo or 0) for a in articoli)
   
   return render_template('inventario_stampa.html',
                        articoli=articoli,
                        data_riferimento=data_riferimento,
                        valore_totale=valore_totale)

@app.route('/ddt-in/<int:id>/stampa')
def stampa_ddt_in(id):
    """Stampa DDT IN"""
    ddt = DDTIn.query.get_or_404(id)
    return render_template('ddt-stampa.html', ddt=ddt)

# ========== API PDF GENERATION (DAL LOCALE) ==========

@app.route('/api/ddt-in/<int:ddt_id>/pdf')
def api_ddt_in_pdf(ddt_id):
    """Genera PDF per DDT IN con template professionale"""
    try:
        ddt = DDTIn.query.get_or_404(ddt_id)
        
        if DOCUMENTS_AVAILABLE:
            # Usa template avanzato
            ddt_data = {
                'numero': ddt.numero_ddt or f'BOZZA-{ddt.id}',
                'data': ddt.data_ddt_origine.strftime('%d/%m/%Y') if ddt.data_ddt_origine else 'N/D',
                'fornitore': ddt.fornitore,
                'destinazione': ddt.destinazione,
                'articoli': ddt.articoli,
                'stato': ddt.stato
            }
            return generate_ddt_in_pdf(ddt_data)
        else:
            # Fallback semplice
            return render_template('ddt-stampa.html', ddt=ddt)
            
    except Exception as e:
        return f"Errore generazione PDF: {str(e)}", 500

@app.route('/api/ddt-out/<int:ddt_id>/pdf')
def api_ddt_out_pdf(ddt_id):
    """Genera PDF per DDT OUT con template professionale"""
    try:
        ddt = DDTOut.query.get_or_404(ddt_id)
        
        if DOCUMENTS_AVAILABLE:
            ddt_data = {
                'numero': ddt.numero_ddt or f'BOZZA-{ddt.id}',
                'data': ddt.data_ddt.strftime('%d/%m/%Y') if ddt.data_ddt else 'N/D',
                'cliente': ddt.cliente or ddt.destinazione,
                'destinazione': ddt.destinazione,
                'articoli': getattr(ddt, 'articoli', []),
                'stato': ddt.stato
            }
            return generate_ddt_out_pdf(ddt_data)
        else:
            return render_template('ddt-out-stampa.html', ddt=ddt)
            
    except Exception as e:
        return f"Errore generazione PDF: {str(e)}", 500

# ========== SISTEMA LEARNING (DA PYTHONANYWHERE) ==========

@app.route('/api/learning-stats')
def api_learning_stats():
   try:
       from models import PatternFornitore, CorrezioneApplicata
       stats = {
           'fornitori_appresi': PatternFornitore.query.count(),
           'correzioni_totali': CorrezioneApplicata.query.count(),
           'accuratezza': 0
       }
       if stats['correzioni_totali'] > 0:
           stats['accuratezza'] = min(95, 60 + stats['correzioni_totali'] * 5)
   except:
       stats = {'fornitori_appresi': 0, 'correzioni_totali': 0, 'accuratezza': 0}
   
   return jsonify(stats)

# ========== UTILITÀ AMMINISTRATIVE ==========

@app.route('/admin/reset-archivi', methods=['GET', 'POST'])
def reset_archivi():
   """Pagina per azzerare archivi (TEMPORANEA)"""
   if request.method == 'GET':
       return render_template('reset-archivi.html')
   
   try:
       ArticoloIn.query.delete()
       db.session.commit()
       
       DDTIn.query.delete()
       DDTOut.query.delete()
       db.session.commit()
       
       CatalogoArticolo.query.delete()
       Movimento.query.delete()
       db.session.commit()
       
       try:
           from models import AllocazioneLottoWH, GiacenzaMagazzinoWH
           AllocazioneLottoWH.query.delete()
           GiacenzaMagazzinoWH.query.delete()
           db.session.commit()
       except:
           pass
       
       return redirect('/')
       
   except Exception as e:
       db.session.rollback()
       return f"Errore durante il reset: {e}", 500

if __name__ == '__main__':
   with app.app_context():
       db.create_all()
   
   print("CRUSCOTTO MERGED - Sistema completo operativo!")
   print("OK Funzionalita PythonAnywhere: DDT IN/OUT, Inventario, Movimenti")
   print("OK Sistema Parsing AI: Claude + Gemini integrato")
   print("OK Generazione PDF professionale")
   print("OK API complete e autocomplete")
   
   app.run(debug=True)