from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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
    stato = db.Column(db.String(20), default='bozza')
    
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

class CatalogoArticolo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codice_interno = db.Column(db.String(50), unique=True)
    codice_fornitore = db.Column(db.String(50))
    descrizione = db.Column(db.String(500))
    fornitore_principale = db.Column(db.String(200))
    costo_ultimo = db.Column(db.Float)
    costo_medio = db.Column(db.Float)
    prezzo_vendita = db.Column(db.Float)
    unita_misura = db.Column(db.String(10))
    giacenza_attuale = db.Column(db.Float, default=0)
    scorta_minima = db.Column(db.Float, default=0)
    ubicazione = db.Column(db.String(100))
    attivo = db.Column(db.Boolean, default=True)

class Movimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_movimento = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20))
    documento_tipo = db.Column(db.String(20))
    documento_id = db.Column(db.Integer)
    documento_numero = db.Column(db.String(50))
    codice_articolo = db.Column(db.String(50))
    descrizione_articolo = db.Column(db.String(500))
    quantita = db.Column(db.Float)
    valore_unitario = db.Column(db.Float)
    valore_totale = db.Column(db.Float)
    magazzino = db.Column(db.String(100))
    mastrino = db.Column(db.String(50))
    causale = db.Column(db.String(200))

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ragione_sociale = db.Column(db.String(200), nullable=False)
    partita_iva = db.Column(db.String(20))
    codice_fiscale = db.Column(db.String(20))
    indirizzo = db.Column(db.String(200))
    citta = db.Column(db.String(100))
    provincia = db.Column(db.String(2))
    cap = db.Column(db.String(10))
    email = db.Column(db.String(100))
    telefono = db.Column(db.String(50))
    pec = db.Column(db.String(100))
    codice_sdi = db.Column(db.String(10))
    condizioni_pagamento = db.Column(db.String(100))
    note = db.Column(db.Text)
    attivo = db.Column(db.Boolean, default=True)

class Fornitore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ragione_sociale = db.Column(db.String(200), nullable=False)
    partita_iva = db.Column(db.String(20))
    codice_fiscale = db.Column(db.String(20))
    indirizzo = db.Column(db.String(200))
    citta = db.Column(db.String(100))
    provincia = db.Column(db.String(2))
    cap = db.Column(db.String(10))
    email = db.Column(db.String(100))
    telefono = db.Column(db.String(50))
    pec = db.Column(db.String(100))
    codice_sdi = db.Column(db.String(10))
    condizioni_pagamento = db.Column(db.String(100))
    lead_time_giorni = db.Column(db.Integer, default=7)
    note = db.Column(db.Text)
    attivo = db.Column(db.Boolean, default=True)

class Mastrino(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codice = db.Column(db.String(50), unique=True)
    descrizione = db.Column(db.String(200))
    tipo = db.Column(db.String(20))
    attivo = db.Column(db.Boolean, default=True)

class Magazzino(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codice = db.Column(db.String(50), unique=True)
    descrizione = db.Column(db.String(200))
    responsabile = db.Column(db.String(100))
    attivo = db.Column(db.Boolean, default=True)

class Preventivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_preventivo = db.Column(db.String(50), unique=True)
    data_preventivo = db.Column(db.Date)
    cliente = db.Column(db.String(200))
    stato = db.Column(db.String(20), default='bozza')
    totale = db.Column(db.Float, default=0)
    margine = db.Column(db.Float, default=0)

class OffertaFornitore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_offerta = db.Column(db.String(50), unique=True)
    data_offerta = db.Column(db.Date)
    fornitore = db.Column(db.String(200))
    stato = db.Column(db.String(20), default='ricevuta')
    totale = db.Column(db.Float, default=0)

class ArticoloIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ddt_id = db.Column(db.Integer, db.ForeignKey('ddt_in.id'))
    codice_interno = db.Column(db.String(50))
    descrizione = db.Column(db.String(500))
    quantita = db.Column(db.Float)
    costo_unitario = db.Column(db.Float)

class ArticoloOut(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ddt_id = db.Column(db.Integer, db.ForeignKey('ddt_out.id'))
    codice_interno = db.Column(db.String(50))
    descrizione = db.Column(db.String(500))
    quantita = db.Column(db.Float)
    costo_unitario = db.Column(db.Float)

class ConfigurazioneSistema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chiave = db.Column(db.String(100), unique=True)
    valore = db.Column(db.Text)
    descrizione = db.Column(db.String(300))
