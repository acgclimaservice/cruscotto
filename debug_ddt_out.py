#!/usr/bin/env python3
"""
Script per diagnosticare problemi con DDT OUT
"""

from app import app, db
from models import DDTOut, ArticoloOut

def debug_ddt_out():
    with app.app_context():
        print("=== DEBUG DDT OUT ===")

        try:
            # Test query base
            print("1. Testando query base DDTOut...")
            count = DDTOut.query.count()
            print(f"   Totale DDT OUT nel database: {count}")

            # Test query con order by
            print("2. Testando query con ordinamento...")
            ddts = DDTOut.query.order_by(DDTOut.id.desc()).limit(5).all()
            print(f"   Primi 5 DDT OUT trovati: {len(ddts)}")

            for ddt in ddts:
                print(f"   - ID: {ddt.id}, Numero: {ddt.numero_ddt}, Stato: {ddt.stato}")

            # Test query complessa (quella dell'endpoint)
            print("3. Testando query complessa dell'endpoint...")
            query = DDTOut.query.order_by(
                DDTOut.stato.asc(),
                DDTOut.numero_ddt.desc().nulls_last(),
                DDTOut.id.desc()
            )
            ddts_full = query.all()
            print(f"   Query complessa completata: {len(ddts_full)} risultati")

            # Test verifica buchi numerazione
            print("4. Testando verifica_buchi_numerazione...")
            from app import verifica_buchi_numerazione
            buchi = verifica_buchi_numerazione(ddts_full, 'OUT')
            print(f"   Buchi numerazione: {len(buchi)}")

            # Test render template
            print("5. Testando template ddt-out.html...")
            import os
            template_path = os.path.join('templates', 'ddt-out.html')
            if os.path.exists(template_path):
                print(f"   Template esiste: {template_path}")
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"   Template size: {len(content)} caratteri")
            else:
                print(f"   ERRORE: Template non trovato: {template_path}")

        except Exception as e:
            print(f"ERRORE durante debug: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

        print("=== FINE DEBUG ===")

if __name__ == '__main__':
    debug_ddt_out()