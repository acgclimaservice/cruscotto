#!/usr/bin/env python3
"""
Script per inizializzare il database su PythonAnywhere
Esegui questo script UNA SOLA VOLTA dopo il deploy
"""

from app import app, db
from models import *

def init_database():
    """Inizializza il database creando tutte le tabelle"""
    try:
        with app.app_context():
            print("Creazione tabelle database...")
            db.create_all()
            print("✅ Database inizializzato correttamente!")
            
            # Verifica tabelle create
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tabelle create: {tables}")
            
    except Exception as e:
        print(f"❌ Errore inizializzazione database: {e}")
        return False
    return True

if __name__ == "__main__":
    init_database()