#!/usr/bin/env python3
"""
Crea tabelle per sistema AI Learning
"""

from app import app, db
from models_parsing_training import ParsingTrainingExample, ParsingRule

def create_training_tables():
    """Crea le tabelle per il training AI"""

    with app.app_context():
        try:
            # Crea le tabelle
            db.create_all()
            print("✅ Tabelle AI Learning create con successo!")

            # Verifica tabelle create
            tables = db.engine.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            training_tables = [t[0] for t in tables if 'parsing' in t[0] or 'training' in t[0]]

            if training_tables:
                print(f"📊 Tabelle training trovate: {training_tables}")
            else:
                print("⚠️ Nessuna tabella training trovata")

        except Exception as e:
            print(f"❌ Errore creazione tabelle: {e}")

if __name__ == "__main__":
    create_training_tables()