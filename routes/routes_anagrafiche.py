from flask import Blueprint, render_template, request, jsonify, current_app
from models import db, Cliente, Fornitore
from auth import login_required, validate_input
from sqlalchemy import or_

anagrafiche_bp = Blueprint('anagrafiche', __name__)

def paginate_query(query, page=1, per_page=None):
    per_page = per_page or current_app.config.get('ITEMS_PER_PAGE', 50)
    return query.paginate(page=page, per_page=per_page, error_out=False)

# CLIENTI
@anagrafiche_bp.route('/clienti')
@login_required
def clienti_list():
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '').strip()
        
        query = Cliente.query.filter_by(attivo=True)
        
        if search:
            query = query.filter(or_(
                Cliente.ragione_sociale.contains(search),
                Cliente.partita_iva.contains(search),
                Cliente.citta.contains(search)
            ))
        
        pagination = paginate_query(query.order_by(Cliente.ragione_sociale), page)
        
        return render_template('clienti.html', 
                             clienti=pagination.items,
                             pagination=pagination, search=search)
    except Exception as e:
        current_app.logger.error(f"Errore clienti: {e}")
        return render_template('clienti.html', clienti=[], pagination=None)

@anagrafiche_bp.route('/clienti/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_cliente():
    if request.method == 'GET':
        return render_template('nuovo-cliente.html')
    
    @validate_input(['ragione_sociale'])
    def create_cliente():
        try:
            data = request.form if request.form else request.json
            
            cliente = Cliente(
                ragione_sociale=data['ragione_sociale'][:200],
                partita_iva=data.get('partita_iva', '')[:20],
                email=data.get('email', '')[:100],
                telefono=data.get('telefono', '')[:50],
                citta=data.get('citta', '')[:100],
                attivo=True
            )
            
            db.session.add(cliente)
            db.session.commit()
            
            return jsonify({'success': True, 'id': cliente.id})
            
        except Exception as e:
            current_app.logger.error(f"Errore creazione cliente: {e}")
            return jsonify({'error': 'Errore interno'}), 500
    
    return create_cliente()

# FORNITORI  
@anagrafiche_bp.route('/fornitori')
@login_required
def fornitori_list():
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '').strip()
        
        query = Fornitore.query.filter_by(attivo=True)
        
        if search:
            query = query.filter(or_(
                Fornitore.ragione_sociale.contains(search),
                Fornitore.partita_iva.contains(search),
                Fornitore.citta.contains(search)
            ))
        
        pagination = paginate_query(query.order_by(Fornitore.ragione_sociale), page)
        
        return render_template('fornitori.html',
                             fornitori=pagination.items,
                             pagination=pagination, search=search)
    except Exception as e:
        current_app.logger.error(f"Errore fornitori: {e}")
        return render_template('fornitori.html', fornitori=[], pagination=None)

@anagrafiche_bp.route('/fornitori/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_fornitore():
    if request.method == 'GET':
        return render_template('nuovo-fornitore.html')
    
    @validate_input(['ragione_sociale'])
    def create_fornitore():
        try:
            data = request.form if request.form else request.json
            
            fornitore = Fornitore(
                ragione_sociale=data['ragione_sociale'][:200],
                partita_iva=data.get('partita_iva', '')[:20],
                email=data.get('email', '')[:100],
                telefono=data.get('telefono', '')[:50],
                citta=data.get('citta', '')[:100],
                lead_time_giorni=max(1, int(data.get('lead_time_giorni', 7))),
                attivo=True
            )
            
            db.session.add(fornitore)
            db.session.commit()
            
            return jsonify({'success': True, 'id': fornitore.id})
            
        except ValueError:
            return jsonify({'error': 'Lead time non valido'}), 400
        except Exception as e:
            current_app.logger.error(f"Errore creazione fornitore: {e}")
            return jsonify({'error': 'Errore interno'}), 500
    
    return create_fornitore()

# API COMUNI
@anagrafiche_bp.route('/api/<tipo>/search')
@login_required  
def api_search(tipo):
    """Ricerca unificata clienti/fornitori"""
    if tipo not in ['clienti', 'fornitori']:
        return jsonify([])
        
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    try:
        Model = Cliente if tipo == 'clienti' else Fornitore
        limit = current_app.config.get('MAX_SEARCH_RESULTS', 10)
        
        results = Model.query.filter(
            or_(
                Model.ragione_sociale.contains(query),
                Model.partita_iva.contains(query)
            ),
            Model.attivo == True
        ).limit(limit).all()
        
        data = [{
            'id': r.id,
            'ragione_sociale': r.ragione_sociale,
            'partita_iva': r.partita_iva,
            'citta': r.citta
        } for r in results]
        
        return jsonify(data)
        
    except Exception as e:
        current_app.logger.error(f"Errore ricerca {tipo}: {e}")
        return jsonify([])