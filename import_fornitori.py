import pandas as pd
from app import app, db, Fornitore

def importa_fornitori_da_excel(file_path):
    """Importa fornitori da file Excel"""
    try:
        # Leggi Excel
        df = pd.read_excel(file_path)
        
        # Mappa colonne (adatta questi nomi alle tue colonne)
        colonne_mapping = {
            'Ragione Sociale': 'ragione_sociale',
            'P.IVA': 'partita_iva', 
            'Codice Fiscale': 'codice_fiscale',
            'Indirizzo': 'indirizzo',
            'Città': 'citta',
            'Provincia': 'provincia',
            'CAP': 'cap',
            'Telefono': 'telefono',
            'Email': 'email',
            'PEC': 'pec'
        }
        
        df = df.rename(columns=colonne_mapping)
        
        importati = 0
        errori = []
        
        with app.app_context():
            for index, row in df.iterrows():
                try:
                    # Verifica se esiste già
                    esistente = Fornitore.query.filter_by(
                        ragione_sociale=row['ragione_sociale']
                    ).first()
                    
                    if esistente:
                        errori.append(f"Riga {index+2}: {row['ragione_sociale']} già esistente")
                        continue
                    
                    # Crea nuovo fornitore
                    fornitore = Fornitore(
                        ragione_sociale=str(row['ragione_sociale'])[:200],
                        partita_iva=str(row.get('partita_iva', ''))[:20],
                        codice_fiscale=str(row.get('codice_fiscale', ''))[:20],
                        indirizzo=str(row.get('indirizzo', ''))[:300],
                        citta=str(row.get('citta', ''))[:100],
                        provincia=str(row.get('provincia', ''))[:5],
                        cap=str(row.get('cap', ''))[:10],
                        telefono=str(row.get('telefono', ''))[:50],
                        email=str(row.get('email', ''))[:100],
                        pec=str(row.get('pec', ''))[:100],
                        attivo=True
                    )
                    
                    db.session.add(fornitore)
                    importati += 1
                    
                except Exception as e:
                    errori.append(f"Riga {index+2}: {str(e)}")
            
            db.session.commit()
        
        return {
            'success': True,
            'importati': importati,
            'errori': errori
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == '__main__':
    # Test diretto
    file_path = 'lista fornitori 21082025 15_09_21.xlsx'
    risultato = importa_fornitori_da_excel(file_path)
    print(f"Importati: {risultato.get('importati', 0)}")
    print(f"Errori: {len(risultato.get('errori', []))}")
