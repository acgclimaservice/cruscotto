#!/usr/bin/env python3
# Script per importare mastrini da Excel

import pandas as pd
import sqlite3
from datetime import datetime

def import_mastrini():
    print("=== IMPORT MASTRINI DA EXCEL ===")
    
    # Leggi il file Excel
    df = pd.read_excel('D:/CRUSCOTTO_1.2/Mastrini_RICAVI_ACQUISTI.xlsx')
    print(f"Trovati {len(df)} mastrini nel file Excel")
    
    # Connetti al database
    conn = sqlite3.connect('D:/CRUSCOTTO_1.2/ddt_database.db')
    cursor = conn.cursor()
    
    # Pulisci la tabella mastrini esistente
    cursor.execute("DELETE FROM mastrino")
    print("Tabella mastrini pulita")
    
    importati = 0
    errori = 0
    
    for index, row in df.iterrows():
        try:
            # Mappa i campi Excel ai campi database
            codice = str(row['Codice']).strip() if pd.notna(row['Codice']) else ''
            descrizione = str(row['Descrizione']).strip() if pd.notna(row['Descrizione']) else ''
            tipo = str(row['Tipo']).strip().upper() if pd.notna(row['Tipo']) else 'GENERICO'
            
            # Inserisci nel database
            cursor.execute("""
                INSERT INTO mastrino (codice, descrizione, tipo, attivo)
                VALUES (?, ?, ?, ?)
            """, (codice, descrizione, tipo, True))
            
            importati += 1
            
        except Exception as e:
            errori += 1
            print(f"Errore riga {index + 1}: {e}")
    
    # Commit e chiudi connessione
    conn.commit()
    conn.close()
    
    print(f"Import completato: {importati} mastrini importati, {errori} errori")
    return importati, errori

if __name__ == "__main__":
    import_mastrini()