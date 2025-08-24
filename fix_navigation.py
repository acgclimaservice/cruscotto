#!/usr/bin/env python3
# fix_navigation.py - Script per modificare la navigazione dei template
import os
import re

# Template da modificare (tutti tranne dashboard)
templates_to_fix = [
    'catalogo.html',
    'clienti.html', 
    'fornitori.html',
    'impostazioni.html',
    'inventario.html',
    'movimenti.html',
    'ordini.html',
    'preventivi.html',
    'offerte.html',
    'reports.html',
    'mastrini.html',
    'nuovo-ddt-in.html',
    'nuovo-ddt-out.html'
]

templates_dir = 'templates'

def fix_navigation(filename):
    """Modifica la navigazione per avere solo il link alla dashboard"""
    filepath = os.path.join(templates_dir, filename)
    
    if not os.path.exists(filepath):
        print(f"File non trovato: {filepath}")
        return False
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern per trovare l'intera sezione nav
        nav_pattern = r'<nav>\s*<ul>.*?</ul>\s*</nav>'
        
        # Sostituzione con navigazione semplificata
        new_nav = """<nav>
            <ul>
                <li><a href="/">🏠 Dashboard</a></li>
            </ul>
        </nav>"""
        
        # Applica la sostituzione
        content_modified = re.sub(nav_pattern, new_nav, content, flags=re.DOTALL)
        
        # Verifica che la modifica sia stata applicata
        if content != content_modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content_modified)
            print(f"OK: Aggiornato {filename}")
            return True
        else:
            print(f"SKIP: Nessuna modifica necessaria {filename}")
            return False
            
    except Exception as e:
        print(f"ERR: Errore con {filename}: {e}")
        return False

def main():
    print("=== AGGIORNAMENTO NAVIGAZIONE TEMPLATE ===")
    print("Modifica navigazione per avere solo link alla dashboard\n")
    
    updated_count = 0
    
    for template in templates_to_fix:
        if fix_navigation(template):
            updated_count += 1
    
    print(f"\n=== RISULTATO ===")
    print(f"Template aggiornati: {updated_count}/{len(templates_to_fix)}")
    print("La dashboard mantiene la navigazione completa come richiesto.")

if __name__ == "__main__":
    main()