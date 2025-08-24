#!/usr/bin/env python3
"""
Script per installare pacchetti AI nel sistema PythonAnywhere
"""

import subprocess
import sys
import os

def install_system_packages():
    """Installa pacchetti necessari per il sistema"""
    
    packages = [
        "anthropic==0.25.0",
        "google-generativeai==0.5.0", 
        "PyMuPDF==1.23.0",
        "pdfplumber==0.10.0",
        "PyPDF2==3.0.1"
    ]
    
    print("🔧 Installazione pacchetti sistema per PythonAnywhere...")
    
    for package in packages:
        print(f"\n📦 Installando {package}...")
        try:
            # Prova installazione globale
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ {package} installato")
            else:
                print(f"❌ Errore {package}: {result.stderr}")
                
                # Se fallisce, prova con --user
                print(f"🔄 Retry con --user...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "--user", package
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"✅ {package} installato con --user")
                else:
                    print(f"❌ Errore definitivo {package}: {result.stderr}")
                    
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout installazione {package}")
        except Exception as e:
            print(f"❌ Eccezione {package}: {e}")

def verify_installation():
    """Verifica installazione pacchetti"""
    print("\n🧪 Verifica installazione...")
    
    try:
        import anthropic
        print("✅ anthropic OK")
    except ImportError as e:
        print(f"❌ anthropic: {e}")
    
    try:
        import google.generativeai
        print("✅ google-generativeai OK") 
    except ImportError as e:
        print(f"❌ google-generativeai: {e}")
        
    try:
        import fitz  # PyMuPDF
        print("✅ PyMuPDF OK")
    except ImportError as e:
        print(f"❌ PyMuPDF: {e}")

if __name__ == "__main__":
    install_system_packages()
    verify_installation()
    print("\n🎯 Riavvia la webapp dopo questo script!")