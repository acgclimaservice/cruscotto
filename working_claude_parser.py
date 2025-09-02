"""
Working Claude Parser - Parser di fallback semplificato per MPLS
Utilizzato quando Multi-AI Parser non è disponibile
"""

import os
import json
import base64
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

class WorkingClaudeParser:
    def __init__(self):
        """Inizializza il parser Claude semplificato"""
        load_dotenv()
        
        # Claude API
        self.claude_client = None
        self.claude_api_key = os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        
        if self.claude_api_key:
            try:
                import anthropic
                self.claude_client = anthropic.Anthropic(api_key=self.claude_api_key)
                print("INFO: Working Claude Parser configurato")
            except Exception as e:
                print(f"WARN: Errore init Working Claude: {e}")
                self.claude_client = None

    def _extract_pdf_text(self, file_obj) -> str:
        """Estrae testo dal PDF usando PyMuPDF"""
        try:
            import fitz  # PyMuPDF
            file_obj.seek(0)
            pdf_data = file_obj.read()
            
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            return text.strip()
        except ImportError:
            print("WARN: PyMuPDF non disponibile, usando fallback")
            return ""
        except Exception as e:
            print(f"WARN: Errore estrazione testo PDF: {e}")
            return ""

    def parse_pdf_with_claude(self, file_obj) -> Dict[str, Any]:
        """Parser PDF con Claude AI per formato DDT/preventivo"""
        if not self.claude_client:
            return {'error': 'Claude non disponibile'}
        
        try:
            # Estrai testo dal PDF
            file_obj.seek(0)
            pdf_text = self._extract_pdf_text(file_obj)
            
            if not pdf_text or len(pdf_text.strip()) < 10:
                return {'error': 'Impossibile estrarre testo dal PDF'}
            
            print(f"DEBUG Working Claude: Testo estratto: {len(pdf_text)} caratteri")
            
            # Prompt ottimizzato per preventivi/offerte/DDT
            prompt = f"""Analizza questo testo estratto da un documento italiano (preventivo, offerta o DDT) e restituisci SOLO il JSON in questo formato:

{{
  "numero_ddt": "numero del documento",
  "data_ddt": "YYYY-MM-DD", 
  "destinatario": {{
    "ragione_sociale": "nome cliente/destinatario",
    "indirizzo": "indirizzo completo se presente",
    "cap": "codice postale",
    "citta": "città"
  }},
  "fornitore": {{
    "ragione_sociale": "nome azienda fornitore", 
    "partita_iva": "partita iva se presente"
  }},
  "articoli": [
    {{
      "codice": "codice articolo o vuoto",
      "descrizione": "descrizione completa",
      "quantita": numero_quantita,
      "prezzo_unitario": prezzo_numerico,
      "totale": prezzo_totale_riga
    }}
  ],
  "totale_fattura": importo_totale_documento,
  "oggetto": "oggetto/descrizione lavoro se presente",
  "note": "note aggiuntive se presenti"
}}

IMPORTANTE per DESTINATARIO vs FORNITORE:
- Il DESTINATARIO è il CLIENTE (chi riceve preventivo/merce)
- Il FORNITORE è chi EMETTE il documento (chi invia)
- Se vedi "ACGCLIMA SERVICE", probabilmente è il fornitore che emette
- Cerca "Cliente:", "Destinatario:", "Spett.le" per il cliente
- Cerca "Mittente:", "Da:" o intestazione per il fornitore

REGOLE ESTRAZIONE:
- Estrai TUTTI gli articoli/servizi presenti
- Per le quantità usa formato numerico (es. 2, non "2,000")
- Per i prezzi usa formato numerico (es. 150.50, non "150,50") 
- Se manca un campo, usa stringa vuota "" o 0 per numeri
- Rispondi SOLO con JSON valido, nessun altro testo

TESTO DEL DOCUMENTO:
{pdf_text[:4000]}"""

            # Chiamata a Claude
            message = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            print(f"DEBUG Working Claude: Risposta ricevuta: {len(response_text)} caratteri")
            
            # Parse JSON response
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            try:
                result = json.loads(response_text)
                print("DEBUG Working Claude: JSON parsed successfully")
                
                # Valida e normalizza il risultato
                result = self._validate_and_normalize_result(result)
                return result
                
            except json.JSONDecodeError as e:
                print(f"WARN Working Claude: Errore parsing JSON: {e}")
                print(f"Risposta raw: {response_text[:200]}")
                return {'error': 'Risposta JSON non valida da Claude'}
                
        except Exception as e:
            print(f"ERROR Working Claude: {e}")
            return {'error': f'Errore nel parsing: {str(e)}'}

    def _validate_and_normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Valida e normalizza il risultato del parsing"""
        try:
            # Assicura campi obbligatori
            if 'numero_ddt' not in result:
                result['numero_ddt'] = ''
            if 'data_ddt' not in result:
                result['data_ddt'] = datetime.now().strftime('%Y-%m-%d')
            if 'destinatario' not in result:
                result['destinatario'] = {}
            if 'fornitore' not in result:
                result['fornitore'] = {}
            if 'articoli' not in result:
                result['articoli'] = []
                
            # Normalizza destinatario
            dest = result['destinatario']
            if 'ragione_sociale' not in dest:
                dest['ragione_sociale'] = ''
            if 'indirizzo' not in dest:
                dest['indirizzo'] = ''
            if 'cap' not in dest:
                dest['cap'] = ''
            if 'citta' not in dest:
                dest['citta'] = ''
                
            # Normalizza fornitore  
            forn = result['fornitore']
            if 'ragione_sociale' not in forn:
                forn['ragione_sociale'] = ''
            if 'partita_iva' not in forn:
                forn['partita_iva'] = ''
                
            # Normalizza articoli
            articoli_normalizzati = []
            for art in result['articoli']:
                art_norm = {
                    'codice': art.get('codice', ''),
                    'descrizione': art.get('descrizione', ''),
                    'quantita': float(art.get('quantita', 1)),
                    'prezzo_unitario': float(art.get('prezzo_unitario', 0)),
                    'totale': float(art.get('totale', 0))
                }
                # Se il totale non è specificato, calcolalo
                if art_norm['totale'] == 0:
                    art_norm['totale'] = art_norm['quantita'] * art_norm['prezzo_unitario']
                    
                articoli_normalizzati.append(art_norm)
                
            result['articoli'] = articoli_normalizzati
            
            # Campi opzionali
            if 'totale_fattura' not in result:
                result['totale_fattura'] = ''
            if 'oggetto' not in result:
                result['oggetto'] = ''
            if 'note' not in result:
                result['note'] = ''
                
            print(f"DEBUG Working Claude: Risultato normalizzato - {len(result['articoli'])} articoli")
            return result
            
        except Exception as e:
            print(f"WARN Working Claude: Errore normalizzazione: {e}")
            return result