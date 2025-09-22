#!/usr/bin/env python3
"""
Script per verificare la configurazione del magazzino
"""

from app import app, db
from models import Magazzino, ConfigurazioneSistema

def check_warehouse_config():
    with app.app_context():
        print("=== VERIFICA CONFIGURAZIONE MAGAZZINO ===")

        # Controlla tutti i magazzini
        magazzini = Magazzino.query.all()
        print(f"Magazzini trovati: {len(magazzini)}")
        for mag in magazzini:
            print(f"  - {mag.codice}: {mag.descrizione} (attivo: {mag.attivo})")

        # Controlla configurazione sistema
        config = ConfigurazioneSistema.query.filter_by(chiave='magazzino_predefinito').first()
        if config:
            print(f"Configurazione trovata: {config.chiave} = '{config.valore}'")

            # Verifica che il magazzino configurato esiste
            mag_predefinito = Magazzino.query.filter_by(codice=config.valore).first()
            if mag_predefinito:
                print(f"Magazzino predefinito: {mag_predefinito.codice} - {mag_predefinito.descrizione}")
            else:
                print(f"ERRORE: Magazzino {config.valore} non trovato!")
        else:
            print("ERRORE: Configurazione 'magazzino_predefinito' non trovata!")

        print("=== FINE VERIFICA ===")

if __name__ == '__main__':
    check_warehouse_config()