from app import app, db
from models import *

with app.app_context():
    # Crea tabelle
    db.create_all()
    
    # Dati iniziali
    if not Mastrino.query.first():
        mastrini = [
            Mastrino(codice='ACQ001', descrizione='Acquisto Materiali', tipo='acquisto', attivo=True),
            Mastrino(codice='ACQ002', descrizione='Acquisto Servizi', tipo='acquisto', attivo=True),
            Mastrino(codice='VEN001', descrizione='Vendita Prodotti', tipo='ricavo', attivo=True),
            Mastrino(codice='VEN002', descrizione='Vendita Servizi', tipo='ricavo', attivo=True)
        ]
        for m in mastrini:
            db.session.add(m)
    
    if not Magazzino.query.first():
        magazzini = [
            Magazzino(codice='MAG001', descrizione='Magazzino Centrale', responsabile='Admin', attivo=True),
            Magazzino(codice='MAG002', descrizione='Deposito Nord', responsabile='Admin', attivo=True),
            Magazzino(codice='MAG003', descrizione='Deposito Sud', responsabile='Admin', attivo=True)
        ]
        for m in magazzini:
            db.session.add(m)
    
    # Articoli esempio
    if not CatalogoArticolo.query.first():
        articoli = [
            CatalogoArticolo(
                codice_interno='ART001',
                descrizione='Monitor LED 27"',
                fornitore_principale='Tech Supplies',
                costo_ultimo=150.00,
                costo_medio=148.50,
                prezzo_vendita=250.00,
                unita_misura='PZ',
                giacenza_attuale=15,
                scorta_minima=5,
                attivo=True
            ),
            CatalogoArticolo(
                codice_interno='ART002',
                descrizione='Tastiera Meccanica',
                fornitore_principale='Gaming Store',
                costo_ultimo=89.00,
                costo_medio=85.50,
                prezzo_vendita=149.00,
                unita_misura='PZ',
                giacenza_attuale=25,
                scorta_minima=10,
                attivo=True
            )
        ]
        for a in articoli:
            db.session.add(a)
    
    db.session.commit()
    print("Database inizializzato con dati esempio - OK!")
