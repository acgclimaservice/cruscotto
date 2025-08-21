from flask import Blueprint, render_template, request, jsonify, current_app
from models import db, Movimento, CatalogoArticolo, Magazzino, Mastrino
from auth import login_required, validate_input
from datetime import datetime, timedelta
from sqlalchemy import func, desc

movimenti_bp = Blueprint('movimenti', __name__)

def paginate_query(query, page=1, per_page=None):
    per_page = per_page or current_app.config.get('ITEMS_PER_PAGE', 50)
    return query.paginate(page=page, per_page=per_page, error_out=False)

@movimenti_bp.route('/')
@login_required
def movimenti_list():
    """Lista movimenti ottimizzata con paginazione"""
    try:
        page = request.args.get('page', 1, type=int)
        filtri = {
            'data_da': request.args.get('data_da'),
            'data_a': request.args.get('data_a'),
            'tipo': request.args.get('tipo'),
            'articolo': request.args.get('articolo')
        }
        
        query = Movimento.query
        
        # Applica filtri
        if filtri['data_da']:
            query = query.filter(Movimento.data_movimento >= 
                               datetime.strptime(filtri['data_da'], '%Y-%m-%d'))
        if filtri['data_a']:
            query = query.filter(Movimento.data_movimento <= 
                               datetime.strptime(filtri['data_a'], '%Y-%m-%d'))
        if filtri['tipo']:
            query = query.filter_by(tipo=filtri['tipo'])
        if filtri['articolo']:
            query = query.filter(Movimento.descrizione_articolo.contains(filtri['articolo']))
        
        query = query.order_by(desc(Movimento.data_movimento))
        pagination = paginate_query(query, page)
        
        return render_template('movimenti.html',
                             movimenti=pagination.items,
                             pagination=pagination,
                             filtri=filtri)
        
    except Exception as e:
        current_app.logger.error(f"Errore movimenti: {e}")
        return render_template('movimenti.html', movimenti=[], pagination=None)

@movimenti_bp.route('/dashboard')
@login_required
def dashboard_movimenti():
    """Dashboard con query ottimizzate"""
    try:
        oggi = datetime.now().date()
        mese_fa = oggi - timedelta(days=30)
        
        # Query aggregate ottimizzate
        stats = {
            'movimenti_oggi': Movimento.query.filter(
                func.date(Movimento.data_movimento) == oggi
            ).count(),
            
            'valore_entrate_mese': db.session.query(
                func.coalesce(func.sum(Movimento.valore_totale), 0)
            ).filter(
                Movimento.tipo == 'entrata',
                Movimento.data_movimento >= mese_fa
            ).scalar(),
            
            'valore_uscite_mese': db.session.query(
                func.coalesce(func.sum(Movimento.valore_totale), 0)
            ).filter(
                Movimento.tipo == 'uscita',
                Movimento.data_movimento >= mese_fa
            ).scalar()
        }
        
        stats['saldo_mese'] = stats['valore_entrate_mese'] - stats['valore_uscite_mese']
        
        return render_template('dashboard-movimenti.html', statistiche=stats)
        
    except Exception as e:
        current_app.logger.error(f"Errore dashboard movimenti: {e}")
        stats = {'movimenti_oggi': 0, 'valore_entrate_mese': 0, 
                'valore_uscite_mese': 0, 'saldo_mese': 0}
        return render_template('dashboard-movimenti.html', statistiche=stats)

@movimenti_bp.route('/rettifica', methods=['GET', 'POST'])
@login_required
def rettifica_inventario():
    if request.method == 'GET':
        try:
            page = request.args.get('page', 1, type=int)
            query = CatalogoArticolo.query.filter_by(attivo=True).order_by(
                CatalogoArticolo.codice_interno
            )
            pagination = paginate_query(query, page)
            
            return render_template('rettifica-inventario.html', 
                                 articoli=pagination.items,
                                 pagination=pagination)
        except Exception as e:
            current_app.logger.error(f"Errore rettifica: {e}")
            return render_template('rettifica-inventario.html', articoli=[])
    
    @validate_input(['rettifiche'])
    def process_rettifica():
        try:
            data = request.json
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            movimenti_creati = 0
            
            for rettifica in data['rettifiche']:
                articolo = CatalogoArticolo.query.get(rettifica['articolo_id'])
                if not articolo:
                    continue
                
                nuova_giacenza = float(rettifica['nuova_giacenza'])
                differenza = nuova_giacenza - articolo.giacenza_attuale
                
                if abs(differenza) > 0.001:  # Evita differenze float trascurabili
                    movimento = Movimento(
                        tipo='entrata' if differenza > 0 else 'uscita',
                        documento_tipo='rettifica',
                        documento_numero=f"RETT-{timestamp}",
                        codice_articolo=articolo.codice_interno,
                        descrizione_articolo=articolo.descrizione,
                        quantita=abs(differenza),
                        valore_unitario=articolo.costo_medio or 0,
                        valore_totale=abs(differenza) * (articolo.costo_medio or 0),
                        magazzino='Magazzino Centrale',
                        causale=f"Rettifica: {articolo.giacenza_attuale:.2f} → {nuova_giacenza:.2f}"
                    )
                    
                    articolo.giacenza_attuale = nuova_giacenza
                    db.session.add(movimento)
                    movimenti_creati += 1
            
            db.session.commit()
            return jsonify({'success': True, 'movimenti_creati': movimenti_creati})
            
        except ValueError:
            return jsonify({'error': 'Valori numerici non validi'}), 400
        except Exception as e:
            current_app.logger.error(f"Errore rettifica: {e}")
            return jsonify({'error': 'Errore interno'}), 500
    
    return process_rettifica()