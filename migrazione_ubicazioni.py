#!/usr/bin/env python3
"""
Migrazione per supportare ubicazioni multiple per lo stesso articolo
- Rimuove il constraint UNIQUE su codice_interno
- Aggiunge constraint UNIQUE su (codice_interno, ubicazione)
"""

import sqlite3
import os
from datetime import datetime

def migrazione_ubicazioni():
    db_path = 'ddt_database.db'
    backup_path = f'ddt_database_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    print(f"=== MIGRAZIONE UBICAZIONI MULTIPLE ===")
    print(f"Database: {db_path}")
    print(f"Backup: {backup_path}")
    
    if not os.path.exists(db_path):
        print("ERRORE: Database non trovato")
        return False
    
    # Crea backup
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"OK Backup creato: {backup_path}")
    except Exception as e:
        print(f"ERRORE durante backup: {e}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n1. Controllo struttura attuale...")
        
        # Verifica se il constraint esiste
        cursor.execute("PRAGMA table_info(catalogo_articolo)")
        columns = cursor.fetchall()
        print(f"OK Trovate {len(columns)} colonne nella tabella catalogo_articolo")
        
        # Verifica indici esistenti
        cursor.execute("PRAGMA index_list(catalogo_articolo)")
        indexes = cursor.fetchall()
        print(f"OK Trovati {len(indexes)} indici esistenti")
        
        print("\n2. Creazione nuova struttura tabella...")
        
        # Crea una tabella temporanea con la nuova struttura
        cursor.execute("""
            CREATE TABLE catalogo_articolo_new (
                id INTEGER PRIMARY KEY,
                codice_interno VARCHAR(50),
                codice_fornitore VARCHAR(50),
                descrizione VARCHAR(500),
                fornitore_principale VARCHAR(200),
                codice_produttore VARCHAR(50),
                costo_ultimo FLOAT,
                costo_medio FLOAT,
                prezzo_vendita FLOAT,
                unita_misura VARCHAR(10),
                giacenza_attuale FLOAT DEFAULT 0,
                scorta_minima FLOAT DEFAULT 0,
                ubicazione VARCHAR(100),
                attivo BOOLEAN DEFAULT 1,
                UNIQUE(codice_interno, ubicazione)
            )
        """)
        print("OK Tabella temporanea creata")
        
        print("\n3. Copia dati esistenti...")
        
        # Copia tutti i dati dalla tabella originale
        cursor.execute("""
            INSERT INTO catalogo_articolo_new 
            SELECT * FROM catalogo_articolo
        """)
        
        rows_copied = cursor.rowcount
        print(f"OK Copiati {rows_copied} record")
        
        print("\n4. Sostituzione tabella...")
        
        # Elimina la tabella originale e rinomina quella nuova
        cursor.execute("DROP TABLE catalogo_articolo")
        cursor.execute("ALTER TABLE catalogo_articolo_new RENAME TO catalogo_articolo")
        print("OK Tabella sostituita")
        
        print("\n5. Verifica finale...")
        
        # Verifica che tutto sia ok
        cursor.execute("SELECT COUNT(*) FROM catalogo_articolo")
        final_count = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA table_info(catalogo_articolo)")
        final_columns = cursor.fetchall()
        
        print(f"OK Record finali: {final_count}")
        print(f"OK Colonne finali: {len(final_columns)}")
        
        # Commit delle modifiche
        conn.commit()
        print("\nSUCCESSO: MIGRAZIONE COMPLETATA CON SUCCESSO!")
        print("Ora e' possibile avere lo stesso articolo in ubicazioni diverse")
        
        return True
        
    except Exception as e:
        print(f"\nERRORE durante la migrazione: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrazione_ubicazioni()