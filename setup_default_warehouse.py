#!/usr/bin/env python3
"""
Script per configurare MAG001 come magazzino predefinito per DDT In
"""

from app import app, db
from models import Magazzino, ConfigurazioneSistema

def setup_default_warehouse():
    with app.app_context():
        # Verifica se MAG001 esiste
        mag001 = Magazzino.query.filter_by(codice='MAG001').first()

        if not mag001:
            # Crea MAG001 se non esiste
            print("Creazione magazzino MAG001...")
            mag001 = Magazzino(
                codice='MAG001',
                descrizione='Magazzino Principale',
                responsabile='Sistema',
                attivo=True
            )
            db.session.add(mag001)
            db.session.commit()
            print("✓ Magazzino MAG001 creato")
        else:
            print("✓ Magazzino MAG001 già esistente")

        # Configura come magazzino predefinito
        config = ConfigurazioneSistema.query.filter_by(chiave='magazzino_predefinito').first()

        if not config:
            # Crea configurazione
            print("Creazione configurazione magazzino predefinito...")
            config = ConfigurazioneSistema(
                chiave='magazzino_predefinito',
                valore='MAG001',
                descrizione='Magazzino predefinito per DDT In'
            )
            db.session.add(config)
        else:
            # Aggiorna configurazione esistente
            print("Aggiornamento configurazione magazzino predefinito...")
            config.valore = 'MAG001'

        db.session.commit()
        print("✓ MAG001 configurato come magazzino predefinito")

        # Verifica configurazione
        test_config = ConfigurazioneSistema.query.filter_by(chiave='magazzino_predefinito').first()
        test_mag = Magazzino.query.filter_by(codice=test_config.valore).first()

        print(f"✓ Configurazione verificata: {test_mag.codice} - {test_mag.descrizione}")

if __name__ == '__main__':
    setup_default_warehouse()