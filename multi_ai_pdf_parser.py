import os
import json
import base64
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime
from dotenv import load_dotenv

class MultiAIPDFParser:
    def __init__(self):
        """Inizializza il parser multi-AI con le API keys dall'ambiente"""
        # Carica variabili d'ambiente dal file .env
        load_dotenv()
        
        # Claude API
        self.claude_client = None
        claude_key = os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        
        if claude_key:
            try:
                import anthropic
                self.claude_client = anthropic.Anthropic(api_key=claude_key)
                print("INFO: Claude AI configurato")
            except Exception as e:
                print(f"WARN: Errore init Claude: {e}")
                self.claude_client = None
        
        # Gemini API
        self.gemini_model = None
        gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
                self.gemini_model = genai.GenerativeModel(model_name)
                print(f"INFO: Gemini AI configurato ({model_name})")
            except Exception as e:
                print(f"WARN: Errore init Gemini: {e}")
                self.gemini_model = None
    
    def get_ai_status(self):
        """Restituisce lo status dei servizi AI disponibili"""
        return {
            'claude': self.claude_client is not None,
            'gemini': self.gemini_model is not None
        }
    
    def parse_ddt_with_claude(self, file_obj):
        """Parser con Claude AI"""
        if not self.claude_client:
            return {'success': False, 'error': 'Claude non disponibile'}
        
        try:
            # Converti file in base64
            file_obj.seek(0)
            pdf_base64 = base64.b64encode(file_obj.read()).decode()
            
            prompt = """Analizza questo DDT italiano e restituisci SOLO il JSON in questo formato:

{
  "numero_ddt": "numero del documento",
  "data_ddt": "YYYY-MM-DD",
  "fornitore": {
    "ragione_sociale": "nome azienda fornitore",
    "partita_iva": "partita iva se presente"
  },
  "articoli": [
    {
      "codice": "codice articolo",
      "descrizione": "descrizione completa",
      "quantita": numero_quantita,
      "prezzo_unitario": prezzo_numerico
    }
  ]
}

CRITICO - DISTINZIONE FORNITORE/DESTINATARIO:
- Il FORNITORE è chi INVIA la merce (mittente, chi emette il DDT)
- Il DESTINATARIO è chi RICEVE la merce (cliente finale)
- Se vedi "ACGCLIMA SERVICE" come destinatario, NON è il fornitore
- Cerca nella sezione "Mittente", "Fornitore", "Da:" o intestazione del documento
- Il fornitore ha solitamente P.IVA e indirizzo nella parte superiore del DDT

IMPORTANTE: 
- Estrai TUTTI gli articoli presenti
- Per le quantità usa il formato numerico (es. 2, non "2,000")  
- Per i prezzi usa il formato numerico (es. 150.50)
- Rispondi SOLO con JSON valido, nessun altro testo"""

            message = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_base64
                            }
                        },
                        {
                            "type": "text", 
                            "text": prompt
                        }
                    ]
                }]
            )
            
            content = message.content[0].text.strip()
            content = content.replace('```json', '').replace('```', '').strip()
            
            parsed_data = json.loads(content)
            return {'success': True, 'data': parsed_data}
            
        except Exception as e:
            return {'success': False, 'error': f'Claude error: {str(e)}'}
    
    def parse_ddt_with_gemini(self, file_obj):
        """Parser con Gemini AI usando API diretta"""
        gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not gemini_key:
            return {'success': False, 'error': 'Gemini key non disponibile'}
        
        try:
            file_obj.seek(0)
            pdf_data = file_obj.read()
            pdf_base64 = base64.b64encode(pdf_data).decode()
            
            prompt = """Analizza questo DDT italiano. Restituisci SOLO JSON valido nel formato:
{
  "numero_ddt": "numero documento",
  "data_ddt": "YYYY-MM-DD", 
  "fornitore": {"ragione_sociale": "nome", "partita_iva": "piva"},
  "articoli": [{"codice": "cod", "descrizione": "desc", "quantita": num, "prezzo_unitario": num}]
}

CRITICO - DISTINZIONE FORNITORE/DESTINATARIO:
- Il FORNITORE è chi INVIA la merce (mittente, emittente del DDT)
- Il DESTINATARIO è chi RICEVE la merce (cliente, "A:", "Spett.le")
- Se vedi "ACGCLIMA SERVICE" come destinatario, NON è il fornitore
- Cerca il fornitore nella sezione intestazione, "Mittente", "Da:" del documento
- Il fornitore è l'azienda che emette il DDT (di solito in alto)

IMPORTANTE: quantità come numero puro (2 non 2,000), prezzi come decimali."""

            # API diretta come in Agenda Trello
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={gemini_key}"
            
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "application/pdf",
                                "data": pdf_base64
                            }
                        }
                    ]
                }]
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    content = content.replace('```json', '').replace('```', '').strip()
                    
                    parsed_data = json.loads(content)
                    return {'success': True, 'data': parsed_data}
                else:
                    return {'success': False, 'error': 'Gemini: risposta vuota'}
            else:
                error_msg = f"Gemini API error {response.status_code}"
                if response.status_code == 429:
                    error_msg += " - quota exhausted"
                return {'success': False, 'error': error_msg}
            
        except Exception as e:
            return {'success': False, 'error': f'Gemini error: {str(e)}'}
    
    def parse_ddt_with_ai(self, file_obj, preferred_ai='claude'):
        """Parser principale con fallback automatico"""
        print(f"Tentativo parsing con {preferred_ai}")
        
        # Prova con AI preferito
        if preferred_ai == 'claude':
            result = self.parse_ddt_with_claude(file_obj)
            if result['success']:
                print("Parsing Claude completato")
                return result
            
            print(f"Claude fallito: {result.get('error')}")
            # Fallback a Gemini
            result = self.parse_ddt_with_gemini(file_obj)
            if result['success']:
                print("Parsing Gemini completato (fallback)")
                return result
        
        elif preferred_ai == 'gemini':
            result = self.parse_ddt_with_gemini(file_obj)
            if result['success']:
                print("Parsing Gemini completato")
                return result
                
            print(f"Gemini fallito: {result.get('error')}")
            # Fallback a Claude
            result = self.parse_ddt_with_claude(file_obj)
            if result['success']:
                print("Parsing Claude completato (fallback)")
                return result
        
        # Fallback a parser basico se tutte le AI falliscono
        print("Tutte le AI fallite, uso parser basico")
        return self.parse_with_basic_fallback(file_obj)
    
    def parse_with_both_ai(self, file_obj):
        """Parse con entrambe le AI e confronta i risultati"""
        print("Parsing con entrambe le AI simultaneamente...")
        
        results = {}
        
        # Prova Claude
        claude_result = self.parse_ddt_with_claude(file_obj)
        if claude_result.get('success'):
            results['claude'] = claude_result
            print("Claude parsing: SUCCESS")
        else:
            print(f"Claude parsing: FAILED - {claude_result.get('error')}")
        
        # Prova Gemini
        gemini_result = self.parse_ddt_with_gemini(file_obj)
        if gemini_result.get('success'):
            results['gemini'] = gemini_result
            print("Gemini parsing: SUCCESS")
        else:
            print(f"Gemini parsing: FAILED - {gemini_result.get('error')}")
        
        # Se abbiamo risultati, scegli il migliore o combina
        if results:
            if len(results) == 1:
                # Solo una AI ha funzionato
                ai_name = list(results.keys())[0]
                print(f"Usato risultato di {ai_name}")
                return results[ai_name]
            
            elif len(results) == 2:
                # Entrambe hanno funzionato - confronta e scegli il migliore
                claude_data = results['claude']
                gemini_data = results['gemini']
                
                # Logica per scegliere il migliore (più articoli, più dati)
                claude_articles = len(claude_data.get('articoli', []))
                gemini_articles = len(gemini_data.get('articoli', []))
                
                if claude_articles >= gemini_articles:
                    print(f"Scelto Claude ({claude_articles} vs {gemini_articles} articoli)")
                    result = claude_data.copy()
                    result['ai_used'] = 'claude'
                    result['comparison'] = {'claude_articles': claude_articles, 'gemini_articles': gemini_articles}
                    return result
                else:
                    print(f"Scelto Gemini ({gemini_articles} vs {claude_articles} articoli)")
                    result = gemini_data.copy()
                    result['ai_used'] = 'gemini'
                    result['comparison'] = {'claude_articles': claude_articles, 'gemini_articles': gemini_articles}
                    return result
        
        # Fallback a parser basico se tutte le AI falliscono  
        print("Entrambe le AI hanno fallito, uso parser basico")
        return self.parse_with_basic_fallback(file_obj)
    
    def parse_with_basic_fallback(self, file_obj):
        """Parser basico di fallback quando le AI non funzionano"""
        try:
            # Simulazione parsing basico con dati template
            print("Parser basico: creazione dati template")
            
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            template_data = {
                "numero_ddt": f"TEMP-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "data_ddt": current_date,
                "fornitore": {
                    "ragione_sociale": "Fornitore da completare manualmente",
                    "partita_iva": ""
                },
                "articoli": [{
                    "codice": "ART001",
                    "descrizione": "Articolo da completare manualmente", 
                    "quantita": 1,
                    "prezzo_unitario": 0.0
                }]
            }
            
            return {
                'success': True, 
                'data': template_data,
                'warning': 'Dati generati automaticamente - completare manualmente'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Anche parser basico fallito: {str(e)}'}
