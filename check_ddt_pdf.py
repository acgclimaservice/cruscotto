#!/usr/bin/env python3
"""
Script per verificare se i DDT IN hanno PDF allegati
"""

from app import app, db
from models import DDTIn

def check_ddt_pdf():
    with app.app_context():
        print("=== VERIFICA PDF DDT IN ===")

        # Controlla tutti i DDT IN
        ddts = DDTIn.query.all()
        print(f"Totale DDT IN trovati: {len(ddts)}")

        for ddt in ddts:
            has_pdf = bool(ddt.pdf_allegato)
            pdf_filename = ddt.pdf_filename or "N/A"
            pdf_size = len(ddt.pdf_allegato) if ddt.pdf_allegato else 0

            print(f"DDT {ddt.id} - Numero: {ddt.numero_ddt or 'BOZZA'}")
            print(f"  - Ha PDF: {has_pdf}")
            print(f"  - Filename: {pdf_filename}")
            print(f"  - Size: {pdf_size} bytes")
            print(f"  - Fornitore: {ddt.fornitore}")
            print()

        # Test specifico DDT 1
        ddt1 = DDTIn.query.get(1)
        if ddt1:
            print("=== TEST DDT 1 ===")
            print(f"Numero: {ddt1.numero_ddt}")
            print(f"Fornitore: {ddt1.fornitore}")
            print(f"Ha PDF: {bool(ddt1.pdf_allegato)}")
            print(f"PDF filename: {ddt1.pdf_filename}")
            if ddt1.pdf_allegato:
                print(f"PDF size: {len(ddt1.pdf_allegato)} bytes")
                print("Endpoint da testare: /ddt-in/1/pdf")
            else:
                print("❌ Nessun PDF allegato per DDT 1")
        else:
            print("❌ DDT 1 non trovato")

        print("=== FINE VERIFICA ===")

if __name__ == '__main__':
    check_ddt_pdf()