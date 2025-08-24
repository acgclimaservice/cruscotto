from flask import Blueprint, render_template, request, jsonify
from models import db, DDTIn, DDTOut
from datetime import datetime

ddt_bp = Blueprint('ddt', __name__)

@ddt_bp.route('/in/nuovo', methods=['GET', 'POST'])
def nuovo_ddt_in():
    if request.method == 'GET':
        return render_template('nuovo-ddt-in.html', fornitori=[], magazzini=[], mastrini=[])
    
    data = request.json or request.form
    nuovo_ddt = DDTIn(
        data_ddt_origine=datetime.strptime(data['data_ddt_origine'], '%Y-%m-%d').date(),
        fornitore=data['fornitore'],
        riferimento=data.get('riferimento', ''),
        destinazione=data['destinazione'],
        mastrino_ddt=data.get('mastrino_ddt', ''),
        commessa=data.get('commessa', ''),
        stato='bozza'
    )
    db.session.add(nuovo_ddt)
    db.session.commit()
    return jsonify({'success': True, 'id': nuovo_ddt.id})

@ddt_bp.route('/in/<int:id>/conferma', methods=['POST'])
def conferma_ddt_in(id):
    ddt = DDTIn.query.get_or_404(id)
    if ddt.stato == 'confermato':
        return jsonify({'error': 'DDT già confermato'}), 400
    
    anno = datetime.now().year
    ultimo = DDTIn.query.filter(
        DDTIn.numero_ddt.like(f'IN/%/{anno}')
    ).order_by(DDTIn.id.desc()).first()
    
    numero = 1
    if ultimo and ultimo.numero_ddt:
        try:
            numero = int(ultimo.numero_ddt.split('/')[1]) + 1
        except:
            numero = 1
    
    ddt.numero_ddt = f'IN/{numero:04d}/{anno}'
    ddt.data_ddt = datetime.now().date()
    ddt.stato = 'confermato'
    db.session.commit()
    
    return jsonify({'success': True, 'numero': ddt.numero_ddt})

@ddt_bp.route('/out/nuovo', methods=['GET', 'POST'])
def nuovo_ddt_out():
    if request.method == 'GET':
        return render_template('nuovo-ddt-out.html', clienti=[], magazzini=[], mastrini=[])
    
    data = request.json or request.form
    nuovo_ddt = DDTOut(
        data_ddt_origine=datetime.strptime(data['data_ddt_origine'], '%Y-%m-%d').date(),
        nome_origine=data['nome_origine'],
        riferimento=data.get('riferimento', ''),
        destinazione=data['destinazione'],
        mastrino_ddt=data.get('mastrino_ddt', ''),
        commessa=data.get('commessa', ''),
        magazzino_partenza=data.get('magazzino_partenza', ''),
        stato='bozza'
    )
    db.session.add(nuovo_ddt)
    db.session.commit()
    return jsonify({'success': True, 'id': nuovo_ddt.id})

@ddt_bp.route('/out/<int:id>/conferma', methods=['POST'])
def conferma_ddt_out(id):
    ddt = DDTOut.query.get_or_404(id)
    if ddt.stato == 'confermato':
        return jsonify({'error': 'DDT già confermato'}), 400
    
    anno = datetime.now().year
    ultimo = DDTOut.query.filter(
        DDTOut.numero_ddt.like(f'OUT/%/{anno}')
    ).order_by(DDTOut.id.desc()).first()
    
    numero = 1
    if ultimo and ultimo.numero_ddt:
        try:
            numero = int(ultimo.numero_ddt.split('/')[1]) + 1
        except:
            numero = 1
    
    ddt.numero_ddt = f'OUT/{numero:04d}/{anno}'
    ddt.data_ddt = datetime.now().date()
    ddt.stato = 'confermato'
    db.session.commit()
    
    return jsonify({'success': True, 'numero': ddt.numero_ddt})
