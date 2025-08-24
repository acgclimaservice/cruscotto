#!/usr/bin/env python3
# create_test_data.py - Crea dati di test per verificare le funzionalità
from app import app
from models import db, DDTIn, DDTOut
from datetime import datetime, date

def create_test_data():
    """Crea dati di test per DDT IN e OUT"""
    
    with app.app_context():
        # Crea database se non esiste
        db.create_all()
        
        # Controlla se esistono già dati
        existing_ddt_in = DDTIn.query.first()
        if existing_ddt_in:
            print("Dati di test già presenti")
            print(f"DDT IN esistenti: {DDTIn.query.count()}")
            print(f"DDT OUT esistenti: {DDTOut.query.count()}")
            return
        
        print("Creazione dati di test...")
        
        # DDT IN di test
        test_ddt_in = [
            {
                'data_ddt_origine': date(2024, 1, 15),
                'numero_ddt_origine': 'DDT-FOR-001/2024',
                'fornitore': 'TechSupply Italia S.r.l.',
                'riferimento': 'OrdineAcquisto-2024-001',
                'destinazione': 'Magazzino Centrale - Via Roma 123, Milano',
                'stato': 'confermato'
            },
            {
                'data_ddt_origine': date(2024, 1, 20), 
                'numero_ddt_origine': 'DDT-FOR-002/2024',
                'fornitore': 'ElettroForniture S.p.A.',
                'riferimento': 'OrdineAcquisto-2024-002',
                'destinazione': 'Magazzino Nord - Via Torino 456, Torino',
                'stato': 'confermato'
            },
            {
                'data_ddt_origine': date(2024, 1, 25),
                'numero_ddt_origine': 'DDT-FOR-003/2024',
                'fornitore': 'Clima Pro Service',
                'riferimento': '',
                'destinazione': 'Cantiere Cliente - Via Napoli 789, Roma',
                'stato': 'bozza'
            }
        ]
        
        for ddt_data in test_ddt_in:
            ddt = DDTIn(**ddt_data)
            db.session.add(ddt)
        
        # DDT OUT di test
        test_ddt_out = [
            {
                'data_ddt_origine': date(2024, 1, 16),
                'numero_ddt_origine': 'OUT-001/2024',
                'nome_origine': 'Cliente ABC S.r.l.',
                'riferimento': 'Ordine-Cliente-001',
                'destinazione': 'Sede Cliente - Via Milano 321, Milano',
                'magazzino_partenza': 'Magazzino Centrale',
                'stato': 'confermato'
            },
            {
                'data_ddt_origine': date(2024, 1, 22),
                'numero_ddt_origine': 'OUT-002/2024', 
                'nome_origine': 'Impresa Edile XYZ',
                'riferimento': 'Cantiere-B2024',
                'destinazione': 'Cantiere Edile - Via Venezia 654, Venezia',
                'magazzino_partenza': 'Magazzino Nord',
                'stato': 'confermato'
            },
            {
                'data_ddt_origine': date(2024, 1, 28),
                'numero_ddt_origine': 'OUT-003/2024',
                'nome_origine': 'Hotel Resort Marina',
                'riferimento': 'Manutenzione-Gennaio',
                'destinazione': 'Hotel Marina - Viale Mare 123, Rimini',
                'magazzino_partenza': 'Magazzino Centrale',
                'stato': 'bozza'
            }
        ]
        
        for ddt_data in test_ddt_out:
            ddt = DDTOut(**ddt_data)
            db.session.add(ddt)
        
        # Salva tutto
        db.session.commit()
        
        print("✓ Dati di test creati con successo!")
        print(f"- {len(test_ddt_in)} DDT IN creati")
        print(f"- {len(test_ddt_out)} DDT OUT creati")
        print()
        print("Ora puoi testare:")
        print("1. http://127.0.0.1:5000/ddt-in (lista DDT IN)")
        print("2. Clicca 'Visualizza' su qualsiasi DDT")
        print("3. http://127.0.0.1:5000/ddt-out (lista DDT OUT)")
        print("4. http://127.0.0.1:5000/ddt/in/nuovo (nuovo DDT con PDF highlighting)")

if __name__ == "__main__":
    create_test_data()