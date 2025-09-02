#!/usr/bin/env python
"""
Script di migrazione database per aggiungere nuove colonne
"""
from app import app, db
from sqlalchemy import text
import sys

def migrate_database():
    """Aggiunge le nuove colonne al database se non esistono già"""
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Verifica colonne esistenti
                result = conn.execute(text('PRAGMA table_info(dettaglio_offerta)'))
                columns = [row[1] for row in result.fetchall()]
                print(f"Colonne attuali in dettaglio_offerta: {columns}")
                
                migrations_needed = []
                
                if 'disponibilita' not in columns:
                    migrations_needed.append('ALTER TABLE dettaglio_offerta ADD COLUMN disponibilita VARCHAR(50)')
                    
                if 'tempo_consegna' not in columns:
                    migrations_needed.append('ALTER TABLE dettaglio_offerta ADD COLUMN tempo_consegna VARCHAR(50)')
                
                if migrations_needed:
                    print(f"Eseguendo {len(migrations_needed)} migrazione/i...")
                    for migration in migrations_needed:
                        print(f"  Eseguendo: {migration}")
                        conn.execute(text(migration))
                    
                    conn.commit()
                    print("Migrazioni completate con successo!")
                else:
                    print("Database già aggiornato, nessuna migrazione necessaria.")
                    
                # Verifica finale
                result = conn.execute(text('PRAGMA table_info(dettaglio_offerta)'))
                columns_after = [row[1] for row in result.fetchall()]
                print(f"Colonne dopo migrazione: {columns_after}")
                
        except Exception as e:
            print(f"Errore durante la migrazione: {e}")
            return False
            
    return True

if __name__ == '__main__':
    print("=== Script di Migrazione Database ===")
    print("Sistema Parsing AI caricato...")
    
    success = migrate_database()
    if success:
        print("Migrazione completata con successo!")
        sys.exit(0)
    else:
        print("Errore durante la migrazione!")
        sys.exit(1)