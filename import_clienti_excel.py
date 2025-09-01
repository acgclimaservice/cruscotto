#!/usr/bin/env python3
# Script per importare clienti da Excel

import pandas as pd
import sqlite3
from datetime import datetime

def import_clienti():
    print("=== IMPORT CLIENTI DA EXCEL ===")
    
    # Leggi il file Excel
    df = pd.read_excel('D:/CRUSCOTTO_1.2/lista clienti 21-08-2025 15_10_09.xlsx')
    print(f"Trovati {len(df)} clienti nel file Excel")
    
    # Connetti al database
    conn = sqlite3.connect('D:/CRUSCOTTO_1.2/ddt_database.db')
    cursor = conn.cursor()
    
    # Pulisci la tabella clienti esistente
    cursor.execute("DELETE FROM cliente")
    print("Tabella clienti pulita")
    
    importati = 0
    errori = 0
    
    for index, row in df.iterrows():
        try:
            # Mappa i campi Excel ai campi database
            ragione_sociale = str(row['Denominazione']).strip() if pd.notna(row['Denominazione']) else 'Cliente senza nome'
            partita_iva = str(row['P.IVA/TAX ID']).strip() if pd.notna(row['P.IVA/TAX ID']) else ''
            codice_fiscale = str(row['Codice Fiscale']).strip() if pd.notna(row['Codice Fiscale']) else ''
            indirizzo = str(row['Indirizzo']).strip() if pd.notna(row['Indirizzo']) else ''
            citta = str(row['Comune']).strip() if pd.notna(row['Comune']) else ''
            provincia = str(row['Provincia']).strip() if pd.notna(row['Provincia']) else ''
            cap = str(row['CAP']).strip() if pd.notna(row['CAP']) else ''
            email = str(row['Indirizzo e-mail']).strip() if pd.notna(row['Indirizzo e-mail']) else ''
            telefono = str(row['Telefono']).strip() if pd.notna(row['Telefono']) else ''
            pec = str(row['Indirizzo PEC']).strip() if pd.notna(row['Indirizzo PEC']) else ''
            codice_sdi = str(row['Codice SDI']).strip() if pd.notna(row['Codice SDI']) else ''
            condizioni_pagamento = str(row['Termini di pagamento']).strip() if pd.notna(row['Termini di pagamento']) else ''
            note = str(row['Note']).strip() if pd.notna(row['Note']) else ''
            
            # Inserisci nel database
            cursor.execute("""
                INSERT INTO cliente (
                    ragione_sociale, partita_iva, codice_fiscale, indirizzo, 
                    citta, provincia, cap, email, telefono, pec, 
                    codice_sdi, condizioni_pagamento, note, attivo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ragione_sociale, partita_iva, codice_fiscale, indirizzo,
                citta, provincia, cap, email, telefono, pec,
                codice_sdi, condizioni_pagamento, note, True
            ))
            
            importati += 1
            
        except Exception as e:
            errori += 1
            print(f"Errore riga {index + 1}: {e}")
    
    # Commit e chiudi connessione
    conn.commit()
    conn.close()
    
    print(f"Import completato: {importati} clienti importati, {errori} errori")
    return importati, errori

if __name__ == "__main__":
    import_clienti()