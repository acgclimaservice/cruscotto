#!/usr/bin/env python3
"""
Script per verificare le configurazioni email
"""

from app import app, db
from models import ConfigurazioneSistema

def check_email_config():
    with app.app_context():
        print("=== VERIFICA CONFIGURAZIONI EMAIL ===")

        # Configurazioni email da controllare
        email_configs = [
            'email_address',
            'email_password',
            'email_imap_server',
            'email_imap_port',
            'email_monitor_active',
            'email_check_interval',
            'email_max_attachments'
        ]

        for config_key in email_configs:
            config = ConfigurazioneSistema.query.filter_by(chiave=config_key).first()
            if config:
                # Nasconde password per sicurezza
                if 'password' in config_key:
                    value_display = f"[{len(config.valore)} caratteri]: {config.valore[:4]}...{config.valore[-4:]}"
                else:
                    value_display = config.valore
                print(f"✓ {config_key}: {value_display}")
            else:
                print(f"✗ {config_key}: NON CONFIGURATO")

        print("\n=== CONTROLLO PASSWORD ===")
        password_config = ConfigurazioneSistema.query.filter_by(chiave='email_password').first()
        if password_config:
            password = password_config.valore
            print(f"Password completa: '{password}'")
            print(f"Lunghezza: {len(password)}")
            print(f"Caratteri nascosti? {repr(password)}")
            # Controlla se ci sono spazi
            if ' ' in password:
                print("⚠️  PROBLEMA: La password contiene spazi!")
                print("Password senza spazi:", password.replace(' ', ''))
                print("Lunghezza senza spazi:", len(password.replace(' ', '')))

        print("=== FINE VERIFICA ===")

if __name__ == '__main__':
    check_email_config()