#!/usr/bin/env python3
"""
Script di diagnosi per PythonAnywhere
Controlla tutti i componenti del sistema AI e database
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Controlla variabili ambiente"""
    print("=== CONTROLLO VARIABILI AMBIENTE ===")
    
    required_vars = [
        'CLAUDE_API_KEY', 'ANTHROPIC_API_KEY', 
        'GEMINI_API_KEY', 'GOOGLE_API_KEY', 'SECRET_KEY'
    ]
    
    # Carica .env se esiste
    env_path = Path('.env')
    if env_path.exists():
        print(f"✓ File .env trovato: {env_path.absolute()}")
        with open('.env', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if '=' in line and not line.startswith('#'):
                    key = line.split('=')[0].strip()
                    if key in required_vars:
                        print(f"✓ {key}: configurata")
    else:
        print("❌ File .env NON trovato!")
        return False
    
    return True

def check_packages():
    """Controlla installazione pacchetti Python"""
    print("\n=== CONTROLLO PACCHETTI PYTHON ===")
    
    required_packages = [
        'flask', 'anthropic', 'google.generativeai', 
        'PyMuPDF', 'pdfplumber', 'PyPDF2', 'dotenv'
    ]
    
    for package in required_packages:
        try:
            if package == 'google.generativeai':
                import google.generativeai
                print(f"✓ google-generativeai: {google.generativeai.__version__}")
            elif package == 'PyMuPDF':
                import fitz
                print(f"✓ PyMuPDF: {fitz.version}")
            elif package == 'dotenv':
                from dotenv import load_dotenv
                print(f"✓ python-dotenv: installato")
            else:
                module = __import__(package)
                version = getattr(module, '__version__', 'unknown')
                print(f"✓ {package}: {version}")
        except ImportError as e:
            print(f"❌ {package}: NON installato - {e}")
            return False
    
    return True

def check_ai_apis():
    """Testa connessione API AI"""
    print("\n=== TEST CONNESSIONE API AI ===")
    
    # Carica environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass
    
    # Test Claude
    try:
        import anthropic
        claude_key = os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        if claude_key:
            client = anthropic.Anthropic(api_key=claude_key)
            print(f"✓ Claude API: Chiave configurata (lunghezza: {len(claude_key)})")
        else:
            print("❌ Claude API: Chiave mancante")
    except Exception as e:
        print(f"❌ Claude API: Errore - {e}")
    
    # Test Gemini
    try:
        import google.generativeai as genai
        gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if gemini_key:
            genai.configure(api_key=gemini_key)
            print(f"✓ Gemini API: Chiave configurata (lunghezza: {len(gemini_key)})")
        else:
            print("❌ Gemini API: Chiave mancante")
    except Exception as e:
        print(f"❌ Gemini API: Errore - {e}")

def check_database():
    """Controlla database e tabelle"""
    print("\n=== CONTROLLO DATABASE ===")
    
    db_paths = [
        'ddt_database.db', 
        'instance/ddt_database.db',
        '/home/acgclimaservice/mysite/ddt_database.db'
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"✓ Database trovato: {os.path.abspath(db_path)}")
            
            # Controlla tabelle
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"✓ Tabelle trovate: {len(tables)}")
                for table in tables:
                    print(f"  - {table[0]}")
                conn.close()
                return True
            except Exception as e:
                print(f"❌ Errore lettura database: {e}")
        else:
            print(f"⚠ Database non trovato in: {db_path}")
    
    return False

def check_files():
    """Controlla file essenziali"""
    print("\n=== CONTROLLO FILE ESSENZIALI ===")
    
    required_files = [
        'app.py', 'models.py', 'requirements.txt',
        'routes/routes_parsing.py', 'multi_ai_pdf_parser.py'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✓ {file_path}: {size} bytes")
        else:
            print(f"❌ {file_path}: NON trovato")
            return False
    
    return True

def main():
    """Esegue tutti i controlli"""
    print("🔍 DIAGNOSI PYTHONANYWHERE - Sistema AI Parsing")
    print("=" * 50)
    
    checks = [
        ("File essenziali", check_files),
        ("Variabili ambiente", check_environment),
        ("Pacchetti Python", check_packages),
        ("Database", check_database),
        ("API AI", check_ai_apis),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ Errore in {name}: {e}")
            results[name] = False
    
    # Riepilogo
    print("\n" + "=" * 50)
    print("📋 RIEPILOGO DIAGNOSI:")
    for name, success in results.items():
        status = "✅ OK" if success else "❌ ERRORE"
        print(f"{status} {name}")
    
    all_ok = all(results.values())
    print(f"\n🎯 STATO GENERALE: {'✅ TUTTO OK' if all_ok else '❌ PROBLEMI RILEVATI'}")
    
    if not all_ok:
        print("\n💡 SUGGERIMENTI:")
        print("1. Esegui: pip3.11 install --user -r requirements.txt")
        print("2. Crea/controlla file .env con chiavi API")
        print("3. Esegui: python3.11 init_db_pythonanywhere.py")
        print("4. Riavvia webapp: touch /var/www/acgclimaservice_pythonanywhere_com_wsgi.py")

if __name__ == "__main__":
    main()