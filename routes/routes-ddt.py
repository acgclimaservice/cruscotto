from flask import Blueprint, render_template, request, jsonify, current_app
from models import db, DDTIn, DDTOut, ArticoloIn, ArticoloOut
from auth import login_required, validate_input
from sqlalchemy import desc
from datetime import datetime

ddt_bp = Blueprint('ddt', __name__)

def paginate_query(query, page=1, per_page=None):
    """Helper per paginazione"""
    per_page = per_page or current_app.config.get('ITEMS_PER_PAGE', 50)
    page = max(1, page)
    return query.paginate(page=page, per_page=per_page, error_out=False)

@ddt_bp.route('/in')
@login_required
def ddt_in_list():
    """Lista DDT IN ottimizzata con paginazione"""
    try:
        page = request.args.get('page', 1, type=int)
        
        # Query ottimizzata: prima bozze, poi confermati
        query = DDTIn.query.order_by(
            DDTIn.stato.desc(),  # bozza > confermato
            desc(DDTIn.id)       # più recenti primi
        )
        
        pagination = paginate_query(query, page)
        return render_template('ddt-in.html', 
                             ddts=pagination.items,
                             pagination=pagination)
        
    except Exception as e:
        current_app.logger.error(f"Errore lista DDT IN: {e}")
        return render_template('ddt-in.html', ddts=[], pagination=None)

@ddt_bp.route('/in/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_ddt_in():
    """Crea DDT IN con validazione"""
    if request.method == 'GET':
        return render_template('nuovo-ddt-in.html')
    
    @validate_input(['data_ddt_origine', 'fornitore', 'destinazione'])
    def create_ddt():
        try:
            data = request.form if request.form else request.json
            
            nuovo_ddt = DDTIn(
                data_ddt_origine=datetime.strptime(data['data_ddt_origine'], '%Y-%m-%d').date(),
                fornitore=data['fornitore'][:200],  # Limit length
                riferimento=data.get('riferimento', '')[:100],
                destinazione=data['destinazione'][:200],
                mastrino_ddt=data.get('mastrino_ddt', '')[:50],
                commessa=data.get('commessa', '')[:50],
                stato='bozza'
            )
            
            db.session.add(nuovo_ddt)
            db.session.commit()
            
            return jsonify({'success': True, 'id': nuovo_ddt.id})
            
        except ValueError as e:
            return jsonify({'error': 'Data non valida'}), 400
        except Exception as e:
            current_app.logger.error(f"Errore creazione DDT: {e}")
            return jsonify({'error': 'Errore interno'}), 500
    
    return create_ddt()

@ddt_bp.route('/in/<int:id>/conferma', methods=['POST'])
@login_required
def conferma_ddt_in(id):
    """Conferma DDT con transazione"""
    try:
        ddt = DDTIn.query.get_or_404(id)
        
        if ddt.stato == 'confermato':
            return jsonify({'error': 'DDT già confermato'}), 400
        
        # Transazione atomica
        with db.session.begin():
            # Genera numero progressivo
            anno = datetime.now().year
            ultimo = DDTIn.query.filter(
                DDTIn.numero_ddt.like(f'IN/%/{anno}')
            ).order_by(desc(DDTIn.id)).first()
            
            numero = 1
            if ultimo and ultimo.numero_ddt:
                try:
                    numero = int(ultimo.numero_ddt.split('/')[1]) + 1
                except (IndexError, ValueError):
                    numero = 1
            
            ddt.numero_ddt = f'IN/{numero:04d}/{anno}'
            ddt.data_ddt = datetime.now().date()
            ddt.stato = 'confermato'
        
        return jsonify({'success': True, 'numero': ddt.numero_ddt})
        
    except Exception as e:
        current_app.logger.error(f"Errore conferma DDT {id}: {e}")
        return jsonify({'error': 'Errore conferma'}), 500

@ddt_bp.route('/out')
@login_required 
def ddt_out_list():
    """Lista DDT OUT ottimizzata"""
    try:
        page = request.args.get('page', 1, type=int)
        
        query = DDTOut.query.order_by(
            DDTOut.stato.desc(),
            desc(DDTOut.id)
        )
        
        pagination = paginate_query(query, page)
        return render_template('ddt-out.html',
                             ddts=pagination.items,
                             pagination=pagination)
        
    except Exception as e:
        current_app.logger.error(f"Errore lista DDT OUT: {e}")
        return render_template('ddt-out.html', ddts=[], pagination=None)