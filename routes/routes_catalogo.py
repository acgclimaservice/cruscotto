from flask import Blueprint, render_template, request, jsonify, current_app
from models import db, CatalogoArticolo, Fornitore, Movimento
from auth import login_required, validate_input
from utils_automation import calcola_valore_magazzino, verifica_scorte_minime
from sqlalchemy import desc, or_
from datetime import datetime

catalogo_bp = Blueprint('catalogo', __name__)

def paginate_query(query, page=1, per_page=None):
    per_page = per_page or current_app.config.get('ITEMS_PER_PAGE', 50)
    return query.paginate(page=page, per_page=per_page, error_out=False)

@catalogo_bp.route('/')
@login_required
def catalogo_list():
    """Lista articoli ottimizzata con paginazione"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '').strip()
        
        query = CatalogoArticolo.query.filter_by(attivo=True)
        
        # Ricerca unificata
        if search:
            query = query.filter(or_(
                CatalogoArticolo.codice_interno.contains(search),
                CatalogoArticolo.descrizione.contains(search),
                CatalogoArticolo.fornitore_principale.contains(search)
            ))
        
        query = query.order_by(CatalogoArticolo.codice_interno)
        pagination = paginate_query(query, page)
        
        # Statistiche in query separate
        stats = {
            'valore_magazzino': calcola_valore_magazzino(),
            'sotto_scorta': len(verifica_scorte_minime()),
            'esauriti': CatalogoArticolo.query.filter_by(giacenza_attuale=0, attivo=True).count()
        }
        
        return render_template('catalogo.html', 
                             articoli=pagination.items,
                             pagination=pagination,
                             search=search,
                             **stats)
        
    except Exception as e:
        current_app.logger.error(f"Errore catalogo: {e}")
        return render_template('catalogo.html', articoli=[], pagination=None)

@catalogo_bp.route('/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_articolo():
    if request.method == 'GET':
        return render_template('nuovo-articolo.html')
    
    @validate_input(['codice_interno', 'descrizione'])
    def create_articolo():
        try:
            data = request.form if request.form else request.json
            
            # Verifica duplicati
            if CatalogoArticolo.query.filter_by(codice_interno=data['codice_interno']).first():
                return jsonify({'error': 'Codice già esistente'}), 400
            
            articolo = CatalogoArticolo(
                codice_interno=data['codice_interno'][:50],
                descrizione=data['descrizione'][:500],
                fornitore_principale=data.get('fornitore_principale', '')[:200],
                costo_ultimo=max(0, float(data.get('costo_ultimo', 0))),
                prezzo_vendita=max(0, float(data.get('prezzo_vendita', 0))),
                giacenza_attuale=max(0, float(data.get('giacenza_attuale', 0))),
                scorta_minima=max(0, float(data.get('scorta_minima', 0))),
                unita_misura=data.get('unita_misura', 'PZ')[:10],
                attivo=True
            )
            
            db.session.add(articolo)
            db.session.commit()
            
            return jsonify({'success': True, 'id': articolo.id})
            
        except ValueError:
            return jsonify({'error': 'Valori numerici non validi'}), 400
        except Exception as e:
            current_app.logger.error(f"Errore creazione articolo: {e}")
            return jsonify({'error': 'Errore interno'}), 500
    
    return create_articolo()

@catalogo_bp.route('/<int:id>')
@login_required
def dettaglio_articolo(id):
    try:
        articolo = CatalogoArticolo.query.get_or_404(id)
        
        # Movimenti recenti paginati
        movimenti = Movimento.query.filter_by(
            codice_articolo=articolo.codice_interno
        ).order_by(desc(Movimento.data_movimento)).limit(20).all()
        
        return render_template('dettaglio-articolo.html', 
                             articolo=articolo, movimenti=movimenti)
    except Exception as e:
        current_app.logger.error(f"Errore dettaglio articolo {id}: {e}")
        return "Articolo non trovato", 404

@catalogo_bp.route('/api/search')
@login_required
def api_search():
    """API ricerca veloce per autocomplete"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    try:
        limit = current_app.config.get('MAX_SEARCH_RESULTS', 10)
        
        articoli = CatalogoArticolo.query.filter(
            or_(
                CatalogoArticolo.codice_interno.contains(query),
                CatalogoArticolo.descrizione.contains(query)
            ),
            CatalogoArticolo.attivo == True
        ).limit(limit).all()
        
        results = [{
            'id': art.id,
            'codice': art.codice_interno,
            'descrizione': art.descrizione,
            'giacenza': art.giacenza_attuale,
            'prezzo': art.prezzo_vendita
        } for art in articoli]
        
        return jsonify(results)
        
    except Exception as e:
        current_app.logger.error(f"Errore ricerca: {e}")
        return jsonify([])

@catalogo_bp.route('/bulk-update', methods=['POST'])
@login_required
def bulk_update():
    """Aggiornamento di massa prezzi/giacenze"""
    try:
        data = request.json
        updated = 0
        
        for item in data.get('updates', []):
            articolo = CatalogoArticolo.query.get(item.get('id'))
            if not articolo:
                continue
                
            if 'prezzo_vendita' in item:
                articolo.prezzo_vendita = max(0, float(item['prezzo_vendita']))
            if 'scorta_minima' in item:
                articolo.scorta_minima = max(0, float(item['scorta_minima']))
                
            updated += 1
        
        db.session.commit()
        return jsonify({'success': True, 'updated': updated})
        
    except Exception as e:
        current_app.logger.error(f"Errore bulk update: {e}")
        return jsonify({'error': 'Errore aggiornamento'}), 500