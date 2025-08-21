from flask import Blueprint, render_template, request, jsonify, current_app
from models import db, CatalogoArticolo, Movimento
from auth import login_required, validate_input
from utils_automation import calcola_valore_magazzino, verifica_scorte_minime
from datetime import datetime

inventario_bp = Blueprint('inventario', __name__)

def paginate_query(query, page=1, per_page=None):
    per_page = per_page or current_app.config.get('ITEMS_PER_PAGE', 50)
    return query.paginate(page=page, per_page=per_page, error_out=False)

@inventario_bp.route('/')
@login_required
def inventario_home():
    try:
        page = request.args.get('page', 1, type=int)
        filtro = request.args.get('filtro', 'tutti')
        
        query = CatalogoArticolo.query.filter_by(attivo=True)
        
        # Filtri ottimizzati
        if filtro == 'sotto_scorta':
            query = query.filter(CatalogoArticolo.giacenza_attuale < CatalogoArticolo.scorta_minima)
        elif filtro == 'esauriti':
            query = query.filter(CatalogoArticolo.giacenza_attuale == 0)
        elif filtro == 'disponibili':
            query = query.filter(CatalogoArticolo.giacenza_attuale > CatalogoArticolo.scorta_minima)
        
        pagination = paginate_query(query.order_by(CatalogoArticolo.codice_interno), page)
        
        # Statistiche con query separate
        stats = {
            'valore_totale': calcola_valore_magazzino(),
            'numero_articoli': CatalogoArticolo.query.filter_by(attivo=True).count(),
            'sotto_scorta': len(verifica_scorte_minime()),
            'pezzi_totali': db.session.query(
                db.func.sum(CatalogoArticolo.giacenza_attuale)
            ).filter_by(attivo=True).scalar() or 0
        }
        
        return render_template('inventario.html',
                             articoli=pagination.items,
                             pagination=pagination,
                             filtro=filtro,
                             statistiche=stats)
        
    except Exception as e:
        current_app.logger.error(f"Errore inventario: {e}")
        return render_template('inventario.html', articoli=[], pagination=None)

@inventario_bp.route('/valorizzazione')
@login_required
def valorizzazione():
    try:
        # Query ottimizzata con aggregazione
        articoli = db.session.query(
            CatalogoArticolo.categoria,
            db.func.count(CatalogoArticolo.id).label('count'),
            db.func.sum(CatalogoArticolo.giacenza_attuale * CatalogoArticolo.costo_medio).label('valore'),
            db.func.sum(CatalogoArticolo.giacenza_attuale).label('pezzi')
        ).filter(
            CatalogoArticolo.attivo == True,
            CatalogoArticolo.giacenza_attuale > 0
        ).group_by(CatalogoArticolo.categoria).all()
        
        per_categoria = {}
        for row in articoli:
            categoria = row.categoria or 'Senza Categoria'
            per_categoria[categoria] = {
                'count': row.count,
                'valore_totale': row.valore or 0,
                'pezzi_totali': row.pezzi or 0
            }
        
        return render_template('valorizzazione.html', per_categoria=per_categoria)
        
    except Exception as e:
        current_app.logger.error(f"Errore valorizzazione: {e}")
        return render_template('valorizzazione.html', per_categoria={})

@inventario_bp.route('/inventario-fisico', methods=['GET', 'POST'])
@login_required
def inventario_fisico():
    if request.method == 'GET':
        try:
            page = request.args.get('page', 1, type=int)
            query = CatalogoArticolo.query.filter_by(attivo=True).order_by(
                CatalogoArticolo.codice_interno
            )
            pagination = paginate_query(query, page)
            
            return render_template('inventario-fisico.html', 
                                 articoli=pagination.items,
                                 pagination=pagination)
        except Exception as e:
            current_app.logger.error(f"Errore inventario fisico: {e}")
            return render_template('inventario-fisico.html', articoli=[])
    
    @validate_input(['inventario'])
    def process_inventario():
        try:
            data = request.json
            numero = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            movimenti_creati = 0
            
            # Transazione atomica per inventario
            with db.session.begin():
                for item in data['inventario']:
                    articolo = CatalogoArticolo.query.get(item['articolo_id'])
                    if not articolo:
                        continue
                    
                    giacenza_fisica = float(item['giacenza_fisica'])
                    differenza = giacenza_fisica - articolo.giacenza_attuale
                    
                    if abs(differenza) > 0.001:
                        movimento = Movimento(
                            tipo='inventario',
                            documento_tipo='inventario',
                            documento_numero=numero,
                            codice_articolo=articolo.codice_interno,
                            descrizione_articolo=articolo.descrizione,
                            quantita=abs(differenza),
                            valore_unitario=articolo.costo_medio or 0,
                            valore_totale=abs(differenza) * (articolo.costo_medio or 0),
                            magazzino='Inventario Fisico',
                            causale=f"Inventario: {articolo.giacenza_attuale} → {giacenza_fisica}"
                        )
                        
                        articolo.giacenza_attuale = giacenza_fisica
                        db.session.add(movimento)
                        movimenti_creati += 1
            
            return jsonify({
                'success': True,
                'numero_inventario': numero,
                'movimenti_creati': movimenti_creati
            })
            
        except ValueError:
            return jsonify({'error': 'Giacenze non valide'}), 400
        except Exception as e:
            current_app.logger.error(f"Errore inventario fisico: {e}")
            return jsonify({'error': 'Errore interno'}), 500
    
    return process_inventario()