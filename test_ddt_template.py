#!/usr/bin/env python3
"""
Test per verificare il DDT nel template
"""

from app import app, db
from models import DDTIn

def test_ddt_template():
    with app.app_context():
        print("=== TEST DDT TEMPLATE ===")

        ddt = DDTIn.query.get(1)
        if ddt:
            print(f"DDT trovato: {ddt.id}")
            print(f"pdf_allegato type: {type(ddt.pdf_allegato)}")
            print(f"pdf_allegato value: {ddt.pdf_allegato[:50] if ddt.pdf_allegato else 'None'}...")
            print(f"pdf_allegato bool: {bool(ddt.pdf_allegato)}")
            print(f"pdf_filename: {ddt.pdf_filename}")

            # Test template render
            from flask import render_template_string

            test_template = """
            DDT ID: {{ ddt.id }}
            Ha PDF: {{ 'SI' if ddt.pdf_allegato else 'NO' }}
            Filename: {{ ddt.pdf_filename or 'N/A' }}
            Condizione: {% if ddt.pdf_allegato %}VERO{% else %}FALSO{% endif %}
            """

            try:
                result = render_template_string(test_template, ddt=ddt)
                print("Template render SUCCESS:")
                print(result)
            except Exception as e:
                print(f"Template render ERROR: {e}")

        else:
            print("DDT 1 non trovato")

if __name__ == '__main__':
    test_ddt_template()