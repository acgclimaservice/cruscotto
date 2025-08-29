from flask import Blueprint, render_template, request, jsonify, current_app
from models import db, Mastrino, Magazzino, ConfigurazioneSistema
from auth import login_required, validate_input
from datetime import datetime

impostazioni_bp = Blueprint('impostazioni', __name__)

@impostazioni_bp.route('/')
@login_required
def impostazioni_home():
    try:
        mastrini = Mastrino.query.order_by(Mastrino.tipo, Mastrino.codice).all()
        magazzini = Magazzino.query.order_by(Magazzino.codice).all()
        configurazioni = {c.chiave: c.valore for c in ConfigurazioneSistema.query.all()}
        
        return render_template('impostazioni.html',
                             mastrini=mastrini,
                             magazzini=magazzini,
                             configurazioni=configurazioni)
    except Exception as e:
        current_app.logger.error(f"Errore impostazioni: {e}")
        return render_template('impostazioni.html', mastrini=[], magazzini=[], configurazioni={})

@impostazioni_bp.route('/mastrino/nuovo', methods=['POST'])
@login_required
@validate_input(['codice', 'descrizione', 'tipo'])
def nuovo_mastrino():
    try:
        data = request.json
        
        if Mastrino.query.filter_by(codice=data['codice']).first():
            return jsonify({'error': 'Codice già esistente'}), 400
        
        if data['tipo'] not in ['acquisto', 'ricavo']:
            return jsonify({'error': 'Tipo non valido'}), 400
        
        mastrino = Mastrino(
            codice=data['codice'][:50],
            descrizione=data['descrizione'][:200],
            tipo=data['tipo'],
            attivo=True
        )
        
        db.session.add(mastrino)
        db.session.commit()
        
        return jsonify({'success': True, 'id': mastrino.id})
        
    except Exception as e:
        current_app.logger.error(f"Errore creazione mastrino: {e}")
        return jsonify({'error': 'Errore interno'}), 500

@impostazioni_bp.route('/magazzino/nuovo', methods=['POST'])
@login_required
@validate_input(['codice', 'descrizione'])
def nuovo_magazzino():
    try:
        data = request.json
        
        if Magazzino.query.filter_by(codice=data['codice']).first():
            return jsonify({'error': 'Codice già esistente'}), 400
        
        magazzino = Magazzino(
            codice=data['codice'][:50],
            descrizione=data['descrizione'][:200],
            indirizzo=data.get('indirizzo', '')[:300],
            responsabile=data.get('responsabile', '')[:100],
            attivo=True
        )
        
        db.session.add(magazzino)
        db.session.commit()
        
        return jsonify({'success': True, 'id': magazzino.id})
        
    except Exception as e:
        current_app.logger.error(f"Errore creazione magazzino: {e}")
        return jsonify({'error': 'Errore interno'}), 500

@impostazioni_bp.route('/configurazione/salva', methods=['POST'])
@login_required
def salva_configurazioni():
    try:
        data = request.json
        aggiornate = 0
        
        for chiave, valore in data.items():
            if len(chiave) > 100 or len(str(valore)) > 1000:
                continue
                
            config = ConfigurazioneSistema.query.filter_by(chiave=chiave).first()
            if config:
                config.valore = str(valore)
                config.data_modifica = datetime.now()
            else:
                config = ConfigurazioneSistema(
                    chiave=chiave,
                    valore=str(valore),
                    descrizione=f"Config {chiave}"
                )
                db.session.add(config)
            aggiornate += 1
        
        db.session.commit()
        return jsonify({'success': True, 'aggiornate': aggiornate})
        
    except Exception as e:
        current_app.logger.error(f"Errore salvataggio config: {e}")
        return jsonify({'error': 'Errore interno'}), 500