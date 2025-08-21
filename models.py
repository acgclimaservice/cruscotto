from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ==================== DDT MODELS ====================

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

# ==================== OFFERTE MODELS ====================

class OffertaFornitore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_offerta = db.Column(db.String(50), unique=True)
    data_offerta = db.Column(db.Date)
    fornitore = db.Column(db.String(200))
    validita_giorni = db.Column(db.Integer, default=30)
    condizioni_pagamento = db.Column(db.String(100))
    stato = db.Column(db.String(20), default='ricevuta')  # ricevuta/valutata/accettata/rifiutata
    note = db.Column(db.Text)
    articoli = db.relationship('ArticoloOfferta', backref='offerta', lazy=True, cascade='all, delete-orphan')

class ArticoloOfferta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offerta_id = db.Column(db.Integer, db.ForeignKey('offerta_fornitore.id'), nullable=False)
    codice_interno = db.Column(db.String(50))
    codice_fornitore = db.Column(db.String(50))
    descrizione = db.Column(db.String(500))
    codice_produttore = db.Column(db.String(50))
    nome_produttore = db.Column(db.String(200))
    prezzo_unitario = db.Column(db.Float)
    unita_misura = db.Column(db.String(10))
    quantita_minima = db.Column(db.Float)
    lead_time_giorni = db.Column(db.Integer)
    note = db.Column(db.Text)

# ==================== PREVENTIVI MODELS ====================

class Preventivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_preventivo = db.Column(db.String(50), unique=True)
    data_preventivo = db.Column(db.Date)
    cliente = db.Column(db.String(200))
    contatto_cliente = db.Column(db.String(200))
    validita_giorni = db.Column(db.Integer, default=30)
    condizioni_pagamento = db.Column(db.String(100))
    stato = db.Column(db.String(20), default='bozza')  # bozza/inviato/accettato/rifiutato
    note = db.Column(db.Text)
    totale = db.Column(db.Float, default=0)
    margine = db.Column(db.Float, default=0)
    articoli = db.relationship('ArticoloPreventivo', backref='preventivo', lazy=True, cascade='all, delete-orphan')

class ArticoloPreventivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    preventivo_id = db.Column(db.Integer, db.ForeignKey('preventivo.id'), nullable=False)
    codice_interno = db.Column(db.String(50))
    descrizione = db.Column(db.String(500))
    costo_unitario = db.Column(db.Float)
    prezzo_unitario = db.Column(db.Float)
    unita_misura = db.Column(db.String(10))
    quantita = db.Column(db.Float)
    sconto_percentuale = db.Column(db.Float, default=0)
    note = db.Column(db.Text)

# ==================== CATALOGO MODELS ====================

class CatalogoArticolo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codice_interno = db.Column(db.String(50), unique=True)
    codice_fornitore = db.Column(db.String(50))
    descrizione = db.Column(db.String(500))
    fornitore_principale = db.Column(db.String(200))
    codice_produttore = db.Column(db.String(50))
    nome_produttore = db.Column(db.String(200))
    categoria = db.Column(db.String(100))
    sottocategoria = db.Column(db.String(100))
    costo_ultimo = db.Column(db.Float)
    costo_medio = db.Column(db.Float)
    prezzo_vendita = db.Column(db.Float)
    unita_misura = db.Column(db.String(10))
    giacenza_attuale = db.Column(db.Float, default=0)
    scorta_minima = db.Column(db.Float, default=0)
    ubicazione = db.Column(db.String(100))
    attivo = db.Column(db.Boolean, default=True)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.Text)

# ==================== MOVIMENTI MODELS ====================

class Movimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_movimento = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20))  # entrata/uscita
    documento_tipo = db.Column(db.String(20))  # ddt_in/ddt_out/rettifica
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
    note = db.Column(db.Text)

# ==================== ANAGRAFICHE MODELS ====================

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ragione_sociale = db.Column(db.String(200), nullable=False)
    partita_iva = db.Column(db.String(20))
    codice_fiscale = db.Column(db.String(20))
    indirizzo = db.Column(db.String(300))
    citta = db.Column(db.String(100))
    provincia = db.Column(db.String(5))
    cap = db.Column(db.String(10))
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(100))
    pec = db.Column(db.String(100))
    codice_sdi = db.Column(db.String(20))
    condizioni_pagamento = db.Column(db.String(100))
    attivo = db.Column(db.Boolean, default=True)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.Text)

class Fornitore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ragione_sociale = db.Column(db.String(200), nullable=False)
    partita_iva = db.Column(db.String(20))
    codice_fiscale = db.Column(db.String(20))
    indirizzo = db.Column(db.String(300))
    citta = db.Column(db.String(100))
    provincia = db.Column(db.String(5))
    cap = db.Column(db.String(10))
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(100))
    pec = db.Column(db.String(100))
    condizioni_pagamento = db.Column(db.String(100))
    lead_time_giorni = db.Column(db.Integer, default=7)
    attivo = db.Column(db.Boolean, default=True)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.Text)

# ==================== CONFIGURAZIONE MODELS ====================

class Mastrino(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codice = db.Column(db.String(50), unique=True)
    descrizione = db.Column(db.String(200))
    tipo = db.Column(db.String(20))  # acquisto/ricavo
    attivo = db.Column(db.Boolean, default=True)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)

class Magazzino(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codice = db.Column(db.String(50), unique=True)
    descrizione = db.Column(db.String(200))
    indirizzo = db.Column(db.String(300))
    responsabile = db.Column(db.String(100))
    attivo = db.Column(db.Boolean, default=True)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.Text)

# ==================== CONFIGURAZIONE SISTEMA ====================

class ConfigurazioneSistema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chiave = db.Column(db.String(100), unique=True)
    valore = db.Column(db.Text)
    descrizione = db.Column(db.String(300))
    data_modifica = db.Column(db.DateTime, default=datetime.utcnow)