#!/usr/bin/env python3
# test_claude_parsing.py
from app import app
from claude_pdf_parser import ClaudePDFParser

def test_claude_parsing():
    """Test parsing with Claude API"""
    with app.app_context():
        parser = ClaudePDFParser()
        
        print("=== TEST PARSING CLAUDE ===")
        print(f"Cliente Claude inizializzato: {parser.client is not None}")
        
        if parser.client:
            print("OK: API Claude configurata correttamente")
            
            # Test con testo simulato DDT
            test_text = """
            DDT N. 2024/001
            Data: 15/01/2024
            
            Fornitore: ACME S.r.l.
            P.IVA: 12345678901
            
            Destinazione: Magazzino Centrale
            Via Roma 123, Milano
            
            Articoli:
            ART001    Monitor LED 27"     2 PZ    € 150,00
            ART002    Tastiera Gaming     1 PZ    € 89,00
            
            Totale: € 389,00
            """
            
            print("\n=== INIZIO PARSING ===")
            try:
                result = parser.parse_ddt_with_claude(test_text)
                
                print(f"Sorgente parsing: {result.get('source', 'N/A')}")
                print(f"Confidence: {result.get('confidence', 'N/A')}")
                print(f"Fornitore: {result.get('fornitore', 'N/A')}")
                print(f"Data DDT: {result.get('data_ddt_origine', 'N/A')}")
                print(f"Numero DDT: {result.get('numero_ddt_origine', 'N/A')}")
                print(f"Articoli: {len(result.get('articoli', []))}")
                print(f"Totale: {result.get('totale_documento', 'N/A')}")
                
                if result.get('source') == 'claude_ai':
                    print("\nSUCCESSO: Parsing con Claude AI attivo!")
                else:
                    print(f"\nFALLBACK: Usando {result.get('source', 'unknown')}")
                    
            except Exception as e:
                print(f"ERRORE durante parsing: {e}")
                
        else:
            print("ERRORE: API Claude NON configurata")
            print("Verrà utilizzato parsing locale")

if __name__ == "__main__":
    test_claude_parsing()