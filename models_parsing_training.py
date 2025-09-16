# Sistema di Training per AI Parsing
from models import db
from datetime import datetime
import json

class ParsingTrainingExample(db.Model):
    """Esempi di training per migliorare il parsing AI"""
    __tablename__ = 'parsing_training_examples'

    id = db.Column(db.Integer, primary_key=True)
    fornitore_nome = db.Column(db.String(200))  # Nome fornitore per pattern specifici
    documento_tipo = db.Column(db.String(50))   # 'offerta', 'ddt_in', 'fattura'
    pdf_hash = db.Column(db.String(64))         # Hash MD5 del PDF per identificazione

    # Dati parsing originale (quello che ha sbagliato)
    parsing_originale = db.Column(db.Text)      # JSON del parsing automatico

    # Correzioni manuali (quello che era giusto)
    parsing_corretto = db.Column(db.Text)       # JSON delle correzioni
    campo_corretto = db.Column(db.String(100))  # Campo specifico corretto
    valore_sbagliato = db.Column(db.Text)       # Valore che aveva sbagliato
    valore_corretto = db.Column(db.Text)        # Valore corretto

    # Pattern per future correzioni
    pattern_riconoscimento = db.Column(db.Text) # Regole per riconoscere il pattern

    # Metadati
    data_creazione = db.Column(db.DateTime, default=datetime.now)
    creato_da = db.Column(db.String(100))       # Utente che ha fatto la correzione
    validato = db.Column(db.Boolean, default=False)
    note = db.Column(db.Text)

class ParsingRule(db.Model):
    """Regole di parsing specifiche per fornitore/documento"""
    __tablename__ = 'parsing_rules'

    id = db.Column(db.Integer, primary_key=True)
    fornitore_pattern = db.Column(db.String(200))  # Pattern nome fornitore (regex)
    documento_tipo = db.Column(db.String(50))
    campo_target = db.Column(db.String(100))       # Campo da correggere

    # Regole specifiche
    xpath_selector = db.Column(db.Text)            # Selettore XPath per PDF
    regex_pattern = db.Column(db.Text)             # Pattern regex
    posizione_testo = db.Column(db.Text)           # "dopo 'Codice:'", "prima di 'Descrizione'"

    # Istruzioni AI specifiche
    prompt_aggiuntivo = db.Column(db.Text)         # Prompt specifico da aggiungere

    # Priorità e validazione
    priorita = db.Column(db.Integer, default=0)    # 0=bassa, 10=alta
    attiva = db.Column(db.Boolean, default=True)
    data_creazione = db.Column(db.DateTime, default=datetime.now)
    successi = db.Column(db.Integer, default=0)    # Contatore successi
    fallimenti = db.Column(db.Integer, default=0)  # Contatore fallimenti