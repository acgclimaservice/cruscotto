#!/usr/bin/env python3
# Script per importare fornitori da Excel

import pandas as pd
import sqlite3
from datetime import datetime

def import_fornitori():
    print("=== IMPORT FORNITORI DA EXCEL ===")
    
    # Leggi il file Excel
    df = pd.read_excel('D:/CRUSCOTTO_1.2/lista fornitori 21-08-2025 15_09_21.xlsx')
    print(f"Trovati {len(df)} fornitori nel file Excel")
    
    # Connetti al database
    conn = sqlite3.connect('D:/CRUSCOTTO_1.2/ddt_database.db')
    cursor = conn.cursor()
    
    # Pulisci la tabella fornitori esistente
    cursor.execute("DELETE FROM fornitore")
    print("Tabella fornitori pulita")
    
    importati = 0
    errori = 0
    
    for index, row in df.iterrows():
        try:
            # Mappa i campi Excel ai campi database
            ragione_sociale = str(row['ragione_sociale']).strip() if pd.notna(row['ragione_sociale']) else 'Fornitore senza nome'
            partita_iva = str(row['partita_iva']).strip() if pd.notna(row['partita_iva']) else ''
            codice_fiscale = str(row['codice_fiscale']).strip() if pd.notna(row['codice_fiscale']) else ''
            indirizzo = str(row['indirizzo']).strip() if pd.notna(row['indirizzo']) else ''
            citta = str(row['citta']).strip() if pd.notna(row['citta']) else ''
            provincia = str(row['provincia']).strip() if pd.notna(row['provincia']) else ''
            cap = str(row['cap']).strip() if pd.notna(row['cap']) else ''
            email = str(row['email']).strip() if pd.notna(row['email']) and row['email'] != '-' else ''
            telefono = str(row['telefono']).strip() if pd.notna(row['telefono']) else ''
            
            # Inserisci nel database
            cursor.execute("""
                INSERT INTO fornitore (
                    ragione_sociale, partita_iva, codice_fiscale, indirizzo, 
                    citta, provincia, cap, email, telefono, pec, 
                    codice_sdi, condizioni_pagamento, lead_time_giorni, note, attivo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ragione_sociale, partita_iva, codice_fiscale, indirizzo,
                citta, provincia, cap, email, telefono, '',  # pec vuoto
                '', '', 0, '', True  # codice_sdi, condizioni_pagamento, lead_time, note, attivo
            ))
            
            importati += 1
            
        except Exception as e:
            errori += 1
            print(f"Errore riga {index + 1}: {e}")
    
    # Commit e chiudi connessione
    conn.commit()
    conn.close()
    
    print(f"Import completato: {importati} fornitori importati, {errori} errori")
    return importati, errori

if __name__ == "__main__":
    import_fornitori()