#!/usr/bin/env python3
"""
Script per aggiornare il database con la nuova struttura MPLS Enhanced v4.92
"""

from app import app, db

def update_database():
    """Aggiorna il database con i nuovi campi Enhanced"""
    try:
        with app.app_context():
            print("🔄 Aggiornamento database in corso...")
            
            # Ricrea tutte le tabelle con la struttura Enhanced
            db.drop_all()
            db.create_all()
            
            print("✅ Database ricreato con struttura Enhanced v4.92!")
            print("🚀 Ora puoi fare il reload della web app su PythonAnywhere")
            return True
            
    except Exception as e:
        print(f"❌ Errore durante l'aggiornamento: {e}")
        return False

if __name__ == "__main__":
    success = update_database()
    exit(0 if success else 1)