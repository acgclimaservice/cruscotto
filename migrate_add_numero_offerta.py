#!/usr/bin/env python3
"""
Migrazione Database: Aggiunge campo numero_offerta_fornitore
"""

from app import app, db
from sqlalchemy import text

def migrate_add_numero_offerta_field():
    """Aggiunge il campo numero_offerta_fornitore alla tabella ordine_fornitore"""

    with app.app_context():
        try:
            # Verifica se il campo esiste già
            result = db.engine.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('ordine_fornitore') WHERE name='numero_offerta_fornitore'"
            )).fetchone()

            if result[0] == 0:
                # Campo non esiste, aggiungilo
                db.engine.execute(text(
                    "ALTER TABLE ordine_fornitore ADD COLUMN numero_offerta_fornitore VARCHAR(100)"
                ))
                print("✅ Campo 'numero_offerta_fornitore' aggiunto con successo!")
            else:
                print("ℹ️ Campo 'numero_offerta_fornitore' già presente")

        except Exception as e:
            print(f"❌ Errore durante migrazione: {e}")

if __name__ == "__main__":
    migrate_add_numero_offerta_field()