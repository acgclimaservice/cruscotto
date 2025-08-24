#!/usr/bin/env python3
# test_multi_ai.py
from app import app
from multi_ai_pdf_parser import MultiAIPDFParser

def test_multi_ai_parsing():
    """Test parsing con sistema Multi-AI"""
    with app.app_context():
        parser = MultiAIPDFParser()
        
        print("=== TEST MULTI-AI PARSING ===")
        
        # Verifica status AI
        status = parser.get_ai_status()
        print(f"Claude disponibile: {status['claude_available']}")
        print(f"Gemini disponibile: {status['gemini_available']}")
        print(f"Totale servizi AI: {status['total_ai_services']}/2")
        
        if status['total_ai_services'] == 0:
            print("AVVISO: Nessun servizio AI configurato, usando parsing locale")
        
        # Test con testo DDT simulato
        test_text = """
        DDT N. 2024/002
        Data: 20/01/2024
        
        Fornitore: TechnoMax S.p.A.
        P.IVA: 98765432109
        
        Destinazione: Magazzino Nord
        Via Milano 456, Torino
        
        Articoli:
        TM001    Notebook Dell XPS    1 PZ    € 1200,00
        TM002    Mouse Wireless       3 PZ    € 25,00
        TM003    Cuffie Bluetooth     2 PZ    € 80,00
        
        Totale documento: € 1355,00
        Note: Consegna urgente entro 3 giorni
        """
        
        print("\n=== TEST MODALITÀ DUAL AI ===")
        try:
            result_dual = parser.parse_ddt_with_ai(test_text, preferred_ai='dual')
            print(f"Parsing completato: {result_dual.get('source', 'N/A')}")
            print(f"AI Provider: {result_dual.get('ai_provider', 'N/A')}")
            print(f"Confidence: {result_dual.get('confidence', 'N/A')}")
            print(f"Fornitore: {result_dual.get('fornitore', 'N/A')}")
            print(f"Articoli estratti: {len(result_dual.get('articoli', []))}")
            
            if 'dual_ai_info' in result_dual:
                dual_info = result_dual['dual_ai_info']
                print(f"AI Primario: {dual_info.get('primary', 'N/A')}")
                print(f"AI Secondario: {dual_info.get('secondary', 'N/A')}")
                print(f"Motivo selezione: {dual_info.get('reason', 'N/A')}")
                
        except Exception as e:
            print(f"Errore test dual: {e}")
        
        print("\n=== TEST MODALITÀ CLAUDE ===")
        try:
            result_claude = parser.parse_ddt_with_ai(test_text, preferred_ai='claude')
            print(f"Parsing completato: {result_claude.get('source', 'N/A')}")
            print(f"AI Provider: {result_claude.get('ai_provider', 'N/A')}")
            print(f"Confidence: {result_claude.get('confidence', 'N/A')}")
                
        except Exception as e:
            print(f"Errore test Claude: {e}")
        
        print("\n=== TEST MODALITÀ GEMINI ===")
        try:
            result_gemini = parser.parse_ddt_with_ai(test_text, preferred_ai='gemini')
            print(f"Parsing completato: {result_gemini.get('source', 'N/A')}")
            print(f"AI Provider: {result_gemini.get('ai_provider', 'N/A')}")
            print(f"Confidence: {result_gemini.get('confidence', 'N/A')}")
                
        except Exception as e:
            print(f"Errore test Gemini: {e}")
        
        print("\n=== RIEPILOGO ===")
        if status['claude_available'] and status['gemini_available']:
            print("OK: Sistema Multi-AI completamente operativo!")
            print("AI: Entrambi i servizi AI sono disponibili")
        elif status['total_ai_services'] > 0:
            print("WARN: Sistema Multi-AI parzialmente operativo")
            print(f"AI: {status['total_ai_services']} servizio/i AI disponibile/i")
        else:
            print("ERR: Nessun servizio AI configurato")
            print("FIX: Configurare almeno una API key per Claude o Gemini")

if __name__ == "__main__":
    test_multi_ai_parsing()