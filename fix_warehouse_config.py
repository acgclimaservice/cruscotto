#!/usr/bin/env python3
"""
Script per correggere la configurazione del magazzino
"""

from app import app, db
from models import Magazzino, ConfigurazioneSistema

def fix_warehouse_config():
    with app.app_context():
        print("=== CORREZIONE CONFIGURAZIONE MAGAZZINO ===")

        # Trova la configurazione errata
        config = ConfigurazioneSistema.query.filter_by(chiave='magazzino_predefinito').first()
        if config:
            print(f"Configurazione corrente: {config.chiave} = '{config.valore}'")

            # Aggiorna con MAG001
            config.valore = 'MAG001'
            db.session.commit()
            print("Configurazione aggiornata a 'MAG001'")

            # Verifica
            mag_predefinito = Magazzino.query.filter_by(codice='MAG001').first()
            if mag_predefinito:
                print(f"Magazzino predefinito ora: {mag_predefinito.codice} - {mag_predefinito.descrizione}")
            else:
                print("ERRORE: MAG001 non trovato!")
        else:
            print("ERRORE: Configurazione non trovata!")

        print("=== CORREZIONE COMPLETATA ===")

if __name__ == '__main__':
    fix_warehouse_config()