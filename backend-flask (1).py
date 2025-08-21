from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ddt_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db = SQLAlchemy(app)
CORS(app)

# Models
class DDTIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_ddt = db.Column(db.String(50), unique=True)
    data_ddt = db.Column(db.Date)
    data_ddt_origine = db.Column(db.Date)
    fornitore = db.Column(db.String(200))
    riferimento = db.Column(db.String(100))
    destinazione = db.Column(db.String(200))
    mastrino_ddt = db.Column(db.String(50))
    commessa = db.Column(db.String(50))
    stato = db.Column(db.String(20), default='bozza')  # bozza/confermato
    articoli = db.relationship('ArticoloIn', backref='ddt', lazy=True, cascade='all, delete-orphan')
    
class DDTOut(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_ddt = db.Column(db.String(50), unique=True)
    data_ddt = db.Column(db.Date)
    data_ddt_origine = db.Column(db.Date)
    nome_origine = db.Column(db.String(200))
    riferimento = db.Column(db.String(100))
    destinazione = db.Column(db.String(200))
    mastrino_ddt = db.Column(db.String(50))
    commessa = db.Column(db.String(50))
    magazzino_partenza = db.Column(db.String(100))
    stato = db.Column(db.String(20), default='bozza')
    articoli = db.relationship('ArticoloOut', backref='ddt', lazy=True, cascade='all, delete-orphan')

class ArticoloIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ddt_id = db.Column(db.Integer, db.ForeignKey('ddt_in.id'), nullable=False)
    codice_interno = db.Column(db.String(50))
    codice_fornitore = db.Column(db.String(50))
    descrizione = db.Column(db.String(500))
    fornitore = db.Column(db.String(200))
    codice_produttore = db.Column(db.String(50))
    nome_produttore = db.Column(db.String(200))
    costo_unitario = db.Column(db.Float)
    unita_misura = db.Column(db.String(10))
    quantita = db.Column(db.Float)
    note = db.Column(db.Text)

class ArticoloOut(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ddt_id = db.Column(db.Integer, db.ForeignKey('ddt_out.id'), nullable=False)
    codice_interno = db.Column(db.String(50))
    codice_fornitore = db.Column(db.String(50))
    descrizione = db.Column(db.String(500))
    fornitore = db.Column(db.String(200))
    codice_produttore = db.Column(db.String(50))
    nome_produttore = db.Column(db.String(200))
    costo_unitario = db.Column(db.Float)
    unita_misura = db.Column(db.String(10))
    quantita = db.Column(db.Float)
    note = db.Column(db.Text)

# Routes per pagine HTML
@app.route('/')
def dashboard():
    ddt_in_count = DDTIn.query.filter_by(stato='confermato').count()
    ddt_out_count = DDTOut.query.filter_by(stato='confermato').count()
    return render_template('dashboard.html', 
                         ddt_in_count=ddt_in_count, 
                         ddt_out_count=ddt_out_count)

@app.route('/ddt-in')
def ddt_in_list():
    ddts = DDTIn.query.order_by(DDTIn.stato.desc(), DDTIn.numero_ddt).all()
    return render_template('ddt-in.html', ddts=ddts)

@app.route('/ddt-out')
def ddt_out_list():
    ddts = DDTOut.query.order_by(DDTOut.stato.desc(), DDTOut.numero_ddt).all()
    return render_template('ddt-out.html', ddts=ddts)

# API Endpoints
@app.route('/api/ddt-in', methods=['GET', 'POST'])
def api_ddt_in():
    if request.method == 'POST':
        data = request.json
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
        return jsonify({'id': nuovo_ddt.id, 'message': 'DDT creato'}), 201
    
    # GET
    ddts = DDTIn.query.all()
    return jsonify([{
        'id': d.id,
        'numero_ddt': d.numero_ddt,
        'data_ddt': d.data_ddt.isoformat() if d.data_ddt else None,
        'data_ddt_origine': d.data_ddt_origine.isoformat() if d.data_ddt_origine else None,
        'fornitore': d.fornitore,
        'stato': d.stato
    } for d in ddts])

@app.route('/api/ddt-in/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_ddt_in_detail(id):
    ddt = DDTIn.query.get_or_404(id)
    
    if request.method == 'GET':
        return jsonify({
            'id': ddt.id,
            'numero_ddt': ddt.numero_ddt,
            'data_ddt': ddt.data_ddt.isoformat() if ddt.data_ddt else None,
            'data_ddt_origine': ddt.data_ddt_origine.isoformat() if ddt.data_ddt_origine else None,
            'fornitore': ddt.fornitore,
            'riferimento': ddt.riferimento,
            'destinazione': ddt.destinazione,
            'mastrino_ddt': ddt.mastrino_ddt,
            'commessa': ddt.commessa,
            'stato': ddt.stato,
            'articoli': [{
                'id': a.id,
                'codice_interno': a.codice_interno,
                'descrizione': a.descrizione,
                'quantita': a.quantita,
                'costo_unitario': a.costo_unitario
            } for a in ddt.articoli]
        })
    
    elif request.method == 'PUT':
        data = request.json
        for key, value in data.items():
            if hasattr(ddt, key) and key != 'id':
                setattr(ddt, key, value)
        db.session.commit()
        return jsonify({'message': 'DDT aggiornato'})
    
    elif request.method == 'DELETE':
        if ddt.stato == 'confermato':
            return jsonify({'error': 'Non puoi eliminare un DDT confermato'}), 400
        db.session.delete(ddt)
        db.session.commit()
        return jsonify({'message': 'DDT eliminato'})

@app.route('/api/ddt-in/<int:id>/conferma', methods=['POST'])
def conferma_ddt_in(id):
    ddt = DDTIn.query.get_or_404(id)
    if ddt.stato == 'confermato':
        return jsonify({'error': 'DDT già confermato'}), 400
    
    # Genera numero progressivo
    anno = datetime.now().year
    ultimo = DDTIn.query.filter(
        DDTIn.numero_ddt.like(f'IN/%/{anno}')
    ).order_by(DDTIn.id.desc()).first()
    
    if ultimo and ultimo.numero_ddt:
        numero = int(ultimo.numero_ddt.split('/')[1]) + 1
    else:
        numero = 1
    
    ddt.numero_ddt = f'IN/{numero:04d}/{anno}'
    ddt.data_ddt = datetime.now().date()
    ddt.stato = 'confermato'
    db.session.commit()
    
    return jsonify({'message': 'DDT confermato', 'numero': ddt.numero_ddt})

@app.route('/api/ddt-in/<int:id>/duplica-out', methods=['POST'])
def duplica_ddt_out(id):
    ddt_in = DDTIn.query.get_or_404(id)
    if ddt_in.stato != 'confermato':
        return jsonify({'error': 'Solo DDT confermati possono essere duplicati'}), 400
    
    nuovo_ddt_out = DDTOut(
        data_ddt_origine=ddt_in.data_ddt_origine,
        nome_origine='Azienda S.r.l.',  # Da configurare
        riferimento=ddt_in.riferimento,
        destinazione=ddt_in.fornitore,  # Inverti fornitore->destinazione
        mastrino_ddt=ddt_in.mastrino_ddt,
        commessa=ddt_in.commessa,
        magazzino_partenza='Magazzino Centrale',  # Default
        stato='bozza'
    )
    
    db.session.add(nuovo_ddt_out)
    db.session.flush()
    
    # Copia articoli
    for art_in in ddt_in.articoli:
        art_out = ArticoloOut(
            ddt_id=nuovo_ddt_out.id,
            codice_interno=art_in.codice_interno,
            codice_fornitore=art_in.codice_fornitore,
            descrizione=art_in.descrizione,
            fornitore=art_in.fornitore,
            codice_produttore=art_in.codice_produttore,
            nome_produttore=art_in.nome_produttore,
            costo_unitario=art_in.costo_unitario,
            unita_misura=art_in.unita_misura,
            quantita=art_in.quantita,
            note=art_in.note
        )
        db.session.add(art_out)
    
    db.session.commit()
    return jsonify({'message': 'DDT OUT creato', 'id': nuovo_ddt_out.id})

# Inizializza database
@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)