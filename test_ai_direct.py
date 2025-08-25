#!/usr/bin/env python3
"""
Test diretto delle API AI per isolare il problema proxies
"""

import os
from dotenv import load_dotenv

def test_claude():
    """Test Claude API diretto"""
    print("🧪 Test Claude API...")
    try:
        import anthropic
        print(f"✅ anthropic importato - versione: {anthropic.__version__}")
        
        api_key = os.getenv('CLAUDE_API_KEY')
        if not api_key:
            print("❌ CLAUDE_API_KEY non trovata")
            return False
            
        print(f"✅ API key trovata (lunghezza: {len(api_key)})")
        
        # Test inizializzazione semplice
        client = anthropic.Anthropic(api_key=api_key)
        print("✅ Client Claude inizializzato correttamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore Claude: {type(e).__name__}: {e}")
        return False

def test_gemini():
    """Test Gemini API diretto"""
    print("\n🧪 Test Gemini API...")
    try:
        import google.generativeai as genai
        print(f"✅ google.generativeai importato")
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY non trovata")
            return False
            
        print(f"✅ API key trovata (lunghezza: {len(api_key)})")
        
        # Test configurazione
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        print("✅ Client Gemini inizializzato correttamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore Gemini: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("🔍 TEST DIRETTO API AI")
    print("=" * 50)
    
    # Carica environment
    load_dotenv()
    print("✅ Environment variables caricato")
    
    # Test singoli
    claude_ok = test_claude()
    gemini_ok = test_gemini()
    
    # Riepilogo
    print("\n" + "=" * 50)
    print("📋 RISULTATI:")
    print(f"Claude: {'✅ OK' if claude_ok else '❌ ERRORE'}")
    print(f"Gemini: {'✅ OK' if gemini_ok else '❌ ERRORE'}")
    
    if claude_ok and gemini_ok:
        print("🎯 ENTRAMBI I SERVIZI AI FUNZIONANO!")
    else:
        print("⚠️ Uno o più servizi hanno problemi")