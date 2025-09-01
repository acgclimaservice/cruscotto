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
    pdf_allegato = db.Column(db.Text)  # Base64 encoded PDF
    pdf_filename = db.Column(db.String(255))  # Nome file originale
    
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
    __tablename__ = 'catalogo_articolo'
    __table_args__ = (db.UniqueConstraint('codice_interno', 'ubicazione', name='uq_codice_ubicazione'),)
    
    id = db.Column(db.Integer, primary_key=True)
    codice_interno = db.Column(db.String(50))
    codice_fornitore = db.Column(db.String(50))
    descrizione = db.Column(db.String(500))
    fornitore_principale = db.Column(db.String(200))
    codice_produttore = db.Column(db.String(50))
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
    
    def get_ddt_in(self):
        if self.documento_tipo == 'ddt_in' and self.documento_id:
            return DDTIn.query.get(self.documento_id)
        return None
    
    def get_ddt_out(self):
        if self.documento_tipo == 'ddt_out' and self.documento_id:
            return DDTOut.query.get(self.documento_id)
        return None

class MovimentoInterno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_movimento = db.Column(db.Date, default=datetime.now().date)
    numero_documento = db.Column(db.String(50))
    magazzino_partenza = db.Column(db.String(100))
    magazzino_destinazione = db.Column(db.String(100))
    causale = db.Column(db.String(200))
    stato = db.Column(db.String(20), default='bozza')
    note = db.Column(db.Text)

class ArticoloMovimentoInterno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movimento_id = db.Column(db.Integer, db.ForeignKey('movimento_interno.id'))
    codice_articolo = db.Column(db.String(50))
    descrizione_articolo = db.Column(db.String(500))
    quantita = db.Column(db.Float)
    unita_misura = db.Column(db.String(10))

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
    data_preventivo = db.Column(db.Date, default=datetime.now().date)
    data_scadenza = db.Column(db.Date)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    cliente_nome = db.Column(db.String(200))
    oggetto = db.Column(db.String(300))
    stato = db.Column(db.String(20), default='bozza')  # bozza, inviato, accettato, rifiutato, scaduto
    totale_netto = db.Column(db.Float, default=0)
    iva = db.Column(db.Float, default=22)
    totale_lordo = db.Column(db.Float, default=0)
    margine_percentuale = db.Column(db.Float, default=0)
    margine_valore = db.Column(db.Float, default=0)
    note = db.Column(db.Text)
    data_invio = db.Column(db.Date)
    data_accettazione = db.Column(db.Date)
    riferimento_cliente = db.Column(db.String(100))
    commessa = db.Column(db.String(50))
    
    # Relazioni
    cliente = db.relationship('Cliente', backref='preventivi')

class OrdineFornitore(db.Model):
    __tablename__ = 'ordine_fornitore'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_ordine = db.Column(db.String(50), unique=True)
    data_ordine = db.Column(db.Date, default=datetime.now().date)
    data_richiesta = db.Column(db.Date)
    data_scadenza = db.Column(db.Date)
    fornitore_id = db.Column(db.Integer, db.ForeignKey('fornitore.id'))
    fornitore_nome = db.Column(db.String(200))
    oggetto = db.Column(db.String(300))
    stato = db.Column(db.String(20), default='bozza')  # bozza, inviato, confermato, ricevuto, completato
    totale_netto = db.Column(db.Float, default=0)
    iva = db.Column(db.Float, default=22)
    totale_lordo = db.Column(db.Float, default=0)
    note = db.Column(db.Text)
    data_invio = db.Column(db.Date)
    data_conferma = db.Column(db.Date)
    riferimento_fornitore = db.Column(db.String(100))
    priorita = db.Column(db.String(10), default='media')  # bassa, media, alta
    commessa = db.Column(db.String(50))
    pdf_allegato = db.Column(db.Text)  # Base64 encoded PDF
    pdf_filename = db.Column(db.String(255))  # Nome file originale
    
    # Relazioni
    fornitore = db.relationship('Fornitore', backref='ordini')

class DettaglioPreventivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    preventivo_id = db.Column(db.Integer, db.ForeignKey('preventivo.id'))
    codice_articolo = db.Column(db.String(50))
    descrizione = db.Column(db.String(500))
    quantita = db.Column(db.Float)
    unita_misura = db.Column(db.String(10), default='PZ')
    prezzo_unitario = db.Column(db.Float)
    costo_unitario = db.Column(db.Float)
    sconto_percentuale = db.Column(db.Float, default=0)
    totale_riga = db.Column(db.Float)
    note = db.Column(db.Text)
    
    # Relazioni
    preventivo = db.relationship('Preventivo', backref='dettagli')

class DettaglioOrdine(db.Model):
    __tablename__ = 'dettaglio_ordine'
    
    id = db.Column(db.Integer, primary_key=True)
    ordine_id = db.Column(db.Integer, db.ForeignKey('ordine_fornitore.id'))
    codice_articolo = db.Column(db.String(50))
    codice_fornitore = db.Column(db.String(50))
    descrizione = db.Column(db.String(500))
    quantita = db.Column(db.Float)
    unita_misura = db.Column(db.String(10), default='PZ')
    prezzo_unitario = db.Column(db.Float)
    sconto_percentuale = db.Column(db.Float, default=0)
    totale_riga = db.Column(db.Float)
    note = db.Column(db.Text)
    disponibilita = db.Column(db.String(50))
    tempo_consegna = db.Column(db.String(50))
    
    # Relazioni
    ordine = db.relationship('OrdineFornitore', backref='dettagli')

class ArticoloIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ddt_id = db.Column(db.Integer, db.ForeignKey('ddt_in.id'))
    codice_interno = db.Column(db.String(50))
    codice_fornitore = db.Column(db.String(50))
    descrizione = db.Column(db.String(500))
    fornitore = db.Column(db.String(200))
    codice_produttore = db.Column(db.String(50))
    nome_produttore = db.Column(db.String(200))
    unita_misura = db.Column(db.String(10), default='PZ')
    quantita = db.Column(db.Float)
    costo_unitario = db.Column(db.Float)
    mastrino_riga = db.Column(db.String(50))  # Mastrino specifico per questa riga

class ArticoloOut(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ddt_id = db.Column(db.Integer, db.ForeignKey('ddt_out.id'))
    codice_interno = db.Column(db.String(50))
    codice_fornitore = db.Column(db.String(50))
    descrizione = db.Column(db.String(500))
    fornitore = db.Column(db.String(200))
    codice_produttore = db.Column(db.String(50))
    nome_produttore = db.Column(db.String(200))
    unita_misura = db.Column(db.String(10), default='PZ')
    quantita = db.Column(db.Float)
    prezzo_unitario = db.Column(db.Float)
    mastrino_riga = db.Column(db.String(50))  # Mastrino specifico per questa riga

class CollegamentoMastrini(db.Model):
    __tablename__ = 'collegamento_mastrini'
    
    id = db.Column(db.Integer, primary_key=True)
    mastrino_acquisto_id = db.Column(db.Integer, db.ForeignKey('mastrino.id'))
    mastrino_ricavo_id = db.Column(db.Integer, db.ForeignKey('mastrino.id'))
    descrizione_collegamento = db.Column(db.String(500))
    attivo = db.Column(db.Boolean, default=True)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relazioni
    mastrino_acquisto = db.relationship('Mastrino', foreign_keys=[mastrino_acquisto_id])
    mastrino_ricavo = db.relationship('Mastrino', foreign_keys=[mastrino_ricavo_id])
    costo_unitario = db.Column(db.Float)

class ConfigurazioneSistema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chiave = db.Column(db.String(100), unique=True)
    valore = db.Column(db.Text)
    descrizione = db.Column(db.String(300))

# Bug #46 - Modello Commesse
class Commessa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_progressivo = db.Column(db.String(50), unique=True)
    data_apertura = db.Column(db.Date, default=datetime.now().date)
    data_scadenza = db.Column(db.Date)
    stato = db.Column(db.String(20), default='aperta')  # aperta, chiusa
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    cliente_nome = db.Column(db.String(200))  # Denormalizzato per performance
    tipologia = db.Column(db.String(50))  # Riqualificazione, Manutenzione Ordinaria, Manutenzione Straordinaria
    descrizione = db.Column(db.Text)
    note = db.Column(db.Text)
    
    # Relazioni
    cliente = db.relationship('Cliente', backref='commesse')
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero_progressivo': self.numero_progressivo,
            'data_apertura': self.data_apertura.strftime('%Y-%m-%d') if self.data_apertura else None,
            'data_scadenza': self.data_scadenza.strftime('%Y-%m-%d') if self.data_scadenza else None,
            'stato': self.stato,
            'cliente_id': self.cliente_id,
            'cliente_nome': self.cliente_nome,
            'tipologia': self.tipologia,
            'descrizione': self.descrizione,
            'note': self.note
        }

class OffertaFornitore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_offerta = db.Column(db.String(50), unique=True)
    data_offerta = db.Column(db.Date)
    data_ricevuta = db.Column(db.Date, default=datetime.now().date)
    data_scadenza = db.Column(db.Date)
    fornitore_nome = db.Column(db.String(200))
    fornitore_id = db.Column(db.Integer, db.ForeignKey('fornitore.id'))
    oggetto = db.Column(db.String(500))
    stato = db.Column(db.String(20), default='ricevuta')  # ricevuta, valutata, accettata, rifiutata
    priorita = db.Column(db.String(20), default='media')  # alta, media, bassa
    totale_netto = db.Column(db.Float, default=0)
    totale_lordo = db.Column(db.Float, default=0)
    iva = db.Column(db.Float, default=22)
    valutazione = db.Column(db.Text)
    data_valutazione = db.Column(db.Date)
    data_accettazione = db.Column(db.Date)
    note = db.Column(db.Text)
    commessa = db.Column(db.String(50))
    
    # Relazioni
    fornitore = db.relationship('Fornitore', backref='offerte')
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero_offerta': self.numero_offerta,
            'data_ricevuta': self.data_ricevuta.strftime('%Y-%m-%d') if self.data_ricevuta else None,
            'fornitore_nome': self.fornitore_nome,
            'oggetto': self.oggetto,
            'stato': self.stato,
            'totale_netto': self.totale_netto,
            'totale_lordo': self.totale_lordo
        }

class DettaglioOfferta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offerta_id = db.Column(db.Integer, db.ForeignKey('offerta_fornitore.id'))
    codice_articolo = db.Column(db.String(50))
    codice_fornitore = db.Column(db.String(50))
    descrizione = db.Column(db.String(500))
    quantita = db.Column(db.Float)
    unita_misura = db.Column(db.String(10), default='PZ')
    prezzo_unitario = db.Column(db.Float)
    sconto_percentuale = db.Column(db.Float, default=0)
    totale_riga = db.Column(db.Float)
    note = db.Column(db.Text)
    
    # Relazioni
    offerta = db.relationship('OffertaFornitore', backref='dettagli')

class BatchImportJob(db.Model):
    __tablename__ = 'batch_import_job'
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    total_files = db.Column(db.Integer)
    processed_files = db.Column(db.Integer, default=0)
    successful_files = db.Column(db.Integer, default=0)
    failed_files = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)

class BatchImportFile(db.Model):
    __tablename__ = 'batch_import_file'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('batch_import_job.id'))
    filename = db.Column(db.String(255))
    original_filename = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    ddt_in_id = db.Column(db.Integer, db.ForeignKey('ddt_in.id'))
    error_message = db.Column(db.Text)
    processed_at = db.Column(db.DateTime)
    
    # Relazioni
    job = db.relationship('BatchImportJob', backref='files')
    ddt_in = db.relationship('DDTIn', backref='batch_imports')
