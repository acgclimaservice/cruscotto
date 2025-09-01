#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per importare dati da file Excel nel database
Importa: clienti, fornitori, mastrini ricavi/acquisti
"""

import pandas as pd
import sqlite3
from datetime import datetime
import sys
import os

# Aggiungi la directory corrente al path per importare i modelli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def connect_db():
    """Connessione al database"""
    return sqlite3.connect('D:/CRUSCOTTO_1.2/ddt_database.db')

def import_clienti():
    """Importa clienti da Excel"""
    print("=== IMPORTAZIONE CLIENTI ===")
    
    try:
        # Leggi Excel
        df = pd.read_excel('lista clienti 21-08-2025 15_10_09.xlsx')
        print(f"Trovati {len(df)} clienti nel file Excel")
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # Controlla clienti già presenti
        cursor.execute("SELECT COUNT(*) FROM cliente")
        clienti_esistenti = cursor.fetchone()[0]
        print(f"Clienti già presenti nel DB: {clienti_esistenti}")
        
        importati = 0
        saltati = 0
        
        for _, row in df.iterrows():
            try:
                denominazione = str(row['Denominazione']) if pd.notna(row['Denominazione']) else None
                if not denominazione or denominazione.lower() in ['nan', 'none', '']:
                    saltati += 1
                    continue
                
                # Estrai dati con gestione NaN
                partita_iva = str(row['P.IVA/TAX ID']) if pd.notna(row['P.IVA/TAX ID']) else ''
                codice_fiscale = str(row['Codice Fiscale']) if pd.notna(row['Codice Fiscale']) else ''
                indirizzo = str(row['Indirizzo']) if pd.notna(row['Indirizzo']) else ''
                citta = str(row['Comune']) if pd.notna(row['Comune']) else ''
                provincia = str(row['Provincia']) if pd.notna(row['Provincia']) else ''
                cap = str(row['CAP']) if pd.notna(row['CAP']) else ''
                telefono = str(row['Telefono']) if pd.notna(row['Telefono']) else ''
                email = str(row['Indirizzo e-mail']) if pd.notna(row['Indirizzo e-mail']) else ''
                note = str(row['Note']) if pd.notna(row['Note']) else ''
                codice_interno = str(row['Codice interno']) if pd.notna(row['Codice interno']) else ''
                
                # Pulisci i dati
                if partita_iva in ['nan', 'None', '0.0']:
                    partita_iva = ''
                if cap in ['nan', 'None', '0.0']:
                    cap = ''
                if telefono in ['nan', 'None', '0.0']:
                    telefono = ''
                
                # Controlla se esiste già
                cursor.execute("SELECT id FROM cliente WHERE ragione_sociale = ?", (denominazione,))
                if cursor.fetchone():
                    print(f"Cliente già esistente: {denominazione}")
                    saltati += 1
                    continue
                
                # Inserisci
                cursor.execute("""
                    INSERT INTO cliente (
                        ragione_sociale, partita_iva, codice_fiscale, indirizzo, 
                        citta, provincia, cap, telefono, email, note, attivo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    denominazione, partita_iva, codice_fiscale, indirizzo,
                    citta, provincia, cap, telefono, email, note
                ))
                
                importati += 1
                if importati % 10 == 0:
                    print(f"Importati {importati} clienti...")
                    
            except Exception as e:
                print(f"Errore importando cliente {row.get('Denominazione', 'N/A')}: {e}")
                saltati += 1
        
        conn.commit()
        conn.close()
        
        print(f"OK Importazione clienti completata: {importati} importati, {saltati} saltati")
        
    except Exception as e:
        print(f"ERRORE importazione clienti: {e}")

def import_fornitori():
    """Importa fornitori da Excel"""
    print("\n=== IMPORTAZIONE FORNITORI ===")
    
    try:
        # Leggi Excel
        df = pd.read_excel('lista fornitori 21-08-2025 15_09_21.xlsx')
        print(f"Trovati {len(df)} fornitori nel file Excel")
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # Controlla fornitori già presenti
        cursor.execute("SELECT COUNT(*) FROM fornitore")
        fornitori_esistenti = cursor.fetchone()[0]
        print(f"Fornitori già presenti nel DB: {fornitori_esistenti}")
        
        importati = 0
        saltati = 0
        
        for _, row in df.iterrows():
            try:
                ragione_sociale = str(row['ragione_sociale']) if pd.notna(row['ragione_sociale']) else None
                if not ragione_sociale or ragione_sociale.lower() in ['nan', 'none', '', '-']:
                    saltati += 1
                    continue
                
                # Estrai dati con gestione NaN
                partita_iva = str(row['partita_iva']) if pd.notna(row['partita_iva']) else ''
                codice_fiscale = str(row['codice_fiscale']) if pd.notna(row['codice_fiscale']) else ''
                indirizzo = str(row['indirizzo']) if pd.notna(row['indirizzo']) else ''
                citta = str(row['citta']) if pd.notna(row['citta']) else ''
                provincia = str(row['provincia']) if pd.notna(row['provincia']) else ''
                cap = str(row['cap']) if pd.notna(row['cap']) else ''
                telefono = str(row['telefono']) if pd.notna(row['telefono']) else ''
                email = str(row['email']) if pd.notna(row['email']) else ''
                
                # Pulisci i dati
                if partita_iva in ['nan', 'None', '-', '0.0']:
                    partita_iva = ''
                if codice_fiscale in ['nan', 'None', '-', '0.0']:
                    codice_fiscale = ''
                if indirizzo in ['nan', 'None', '-']:
                    indirizzo = ''
                if telefono in ['nan', 'None', '-', '0.0']:
                    telefono = ''
                if email in ['nan', 'None', '-']:
                    email = ''
                
                # Controlla se esiste già
                cursor.execute("SELECT id FROM fornitore WHERE ragione_sociale = ?", (ragione_sociale,))
                if cursor.fetchone():
                    print(f"Fornitore già esistente: {ragione_sociale}")
                    saltati += 1
                    continue
                
                # Inserisci
                cursor.execute("""
                    INSERT INTO fornitore (
                        ragione_sociale, partita_iva, codice_fiscale, indirizzo, 
                        citta, provincia, cap, telefono, email, attivo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    ragione_sociale, partita_iva, codice_fiscale, indirizzo,
                    citta, provincia, cap, telefono, email
                ))
                
                importati += 1
                if importati % 10 == 0:
                    print(f"Importati {importati} fornitori...")
                    
            except Exception as e:
                print(f"Errore importando fornitore {row.get('ragione_sociale', 'N/A')}: {e}")
                saltati += 1
        
        conn.commit()
        conn.close()
        
        print(f"OK Importazione fornitori completata: {importati} importati, {saltati} saltati")
        
    except Exception as e:
        print(f"ERRORE importazione fornitori: {e}")

def import_mastrini():
    """Importa mastrini ricavi e acquisti da Excel"""
    print("\n=== IMPORTAZIONE MASTRINI ===")
    
    try:
        # Leggi tutti i fogli
        xls = pd.ExcelFile('Mastrini_RICAVI_ACQUISTI.xlsx')
        print(f"Fogli disponibili: {xls.sheet_names}")
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # Controlla mastrini già presenti
        cursor.execute("SELECT COUNT(*) FROM mastrino")
        mastrini_esistenti = cursor.fetchone()[0]
        print(f"Mastrini già presenti nel DB: {mastrini_esistenti}")
        
        importati = 0
        saltati = 0
        
        # Importa RICAVI
        if 'RICAVI' in xls.sheet_names:
            df_ricavi = pd.read_excel('Mastrini_RICAVI_ACQUISTI.xlsx', sheet_name='RICAVI')
            print(f"Trovati {len(df_ricavi)} mastrini RICAVI")
            
            for _, row in df_ricavi.iterrows():
                try:
                    codice = str(row['Codice']) if pd.notna(row['Codice']) else None
                    descrizione = str(row['Descrizione']) if pd.notna(row['Descrizione']) else None
                    
                    if not codice or not descrizione:
                        saltati += 1
                        continue
                    
                    # Controlla se esiste già
                    cursor.execute("SELECT id FROM mastrino WHERE codice = ?", (codice,))
                    if cursor.fetchone():
                        saltati += 1
                        continue
                    
                    # Inserisci
                    cursor.execute("""
                        INSERT INTO mastrino (codice, descrizione, tipo, attivo)
                        VALUES (?, ?, 'RICAVO', 1)
                    """, (codice, descrizione))
                    
                    importati += 1
                    
                except Exception as e:
                    print(f"Errore importando mastrino ricavo {row.get('Codice', 'N/A')}: {e}")
                    saltati += 1
        
        # Importa ACQUISTI
        if 'ACQUISTI' in xls.sheet_names:
            df_acquisti = pd.read_excel('Mastrini_RICAVI_ACQUISTI.xlsx', sheet_name='ACQUISTI')
            print(f"Trovati {len(df_acquisti)} mastrini ACQUISTI")
            
            for _, row in df_acquisti.iterrows():
                try:
                    codice = str(row['Codice']) if pd.notna(row['Codice']) else None
                    descrizione = str(row['Descrizione']) if pd.notna(row['Descrizione']) else None
                    
                    if not codice or not descrizione:
                        saltati += 1
                        continue
                    
                    # Controlla se esiste già
                    cursor.execute("SELECT id FROM mastrino WHERE codice = ?", (codice,))
                    if cursor.fetchone():
                        saltati += 1
                        continue
                    
                    # Inserisci
                    cursor.execute("""
                        INSERT INTO mastrino (codice, descrizione, tipo, attivo)
                        VALUES (?, ?, 'ACQUISTO', 1)
                    """, (codice, descrizione))
                    
                    importati += 1
                    
                except Exception as e:
                    print(f"Errore importando mastrino acquisto {row.get('Codice', 'N/A')}: {e}")
                    saltati += 1
        
        conn.commit()
        conn.close()
        
        print(f"OK Importazione mastrini completata: {importati} importati, {saltati} saltati")
        
    except Exception as e:
        print(f"ERRORE importazione mastrini: {e}")

def main():
    """Esegui tutte le importazioni"""
    print("AVVIO IMPORTAZIONE DATI DA EXCEL")
    print("=" * 50)
    
    # Verifica file
    files_to_check = [
        'lista clienti 21-08-2025 15_10_09.xlsx',
        'lista fornitori 21-08-2025 15_09_21.xlsx', 
        'Mastrini_RICAVI_ACQUISTI.xlsx'
    ]
    
    missing_files = []
    for file in files_to_check:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"ERRORE - File mancanti: {missing_files}")
        return
    
    # Esegui importazioni
    import_clienti()
    import_fornitori()
    import_mastrini()
    
    print("\n" + "=" * 50)
    print("IMPORTAZIONE COMPLETATA!")

if __name__ == "__main__":
    main()