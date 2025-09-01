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
        self.claude_api_key = os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        
        if self.claude_api_key:
            try:
                import anthropic
                self.claude_client = anthropic.Anthropic(api_key=self.claude_api_key)
                print("INFO: Claude AI configurato")
            except Exception as e:
                print(f"WARN: Errore init Claude: {e}")
                self.claude_client = None
        
        # Gemini API
        self.gemini_model = None
        self.gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        
        if self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
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
        """Parser con Claude AI usando text extraction"""
        print(f"DEBUG Claude: Inizio parsing, file_obj type: {type(file_obj)}")
        if not self.claude_client:
            print("DEBUG Claude: Client non disponibile")
            return {'success': False, 'error': 'Claude non disponibile'}
        
        try:
            print("DEBUG Claude: Tentativo parsing con Claude AI")
            # Estrai testo dal PDF invece di inviare il PDF direttamente
            file_obj.seek(0)
            pdf_text = self._extract_pdf_text(file_obj)
            
            if not pdf_text or len(pdf_text.strip()) < 10:
                print("DEBUG Claude: Testo estratto insufficiente dal PDF")
                return {'success': False, 'error': 'Impossibile estrarre testo dal PDF'}
            
            print(f"DEBUG Claude: Testo estratto: {len(pdf_text)} caratteri")
            
            prompt = f"""Analizza questo testo estratto da un DDT italiano e restituisci SOLO il JSON in questo formato:

{{
  "numero_ddt": "numero del documento",
  "data_ddt": "YYYY-MM-DD",
  "fornitore": {{
    "ragione_sociale": "nome azienda fornitore",
    "partita_iva": "partita iva se presente"
  }},
  "articoli": [
    {{
      "codice": "codice articolo",
      "descrizione": "descrizione completa",
      "quantita": numero_quantita,
      "prezzo_unitario": prezzo_numerico
    }}
  ]
}}

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
- Rispondi SOLO con JSON valido, nessun altro testo

TESTO DEL DDT:
{pdf_text}"""

            message = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            content = message.content[0].text.strip()
            content = content.replace('```json', '').replace('```', '').strip()
            
            parsed_data = json.loads(content)
            parsed_data['ai_used'] = 'claude'
            parsed_data['ai_reason'] = 'Claude AI selezionato dall\'utente e completato con successo'
            return {'success': True, 'data': parsed_data}
            
        except Exception as e:
            return {'success': False, 'error': f'Claude error: {str(e)}'}
    
    def _extract_pdf_text(self, file_obj):
        """Estrai testo dal PDF usando PyPDF2"""
        try:
            import PyPDF2
            file_obj.seek(0)
            pdf_reader = PyPDF2.PdfReader(file_obj)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except ImportError:
            print("PyPDF2 non installato, tentativo con pdfplumber...")
            try:
                import pdfplumber
                file_obj.seek(0)
                
                text = ""
                with pdfplumber.open(file_obj) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                
                return text.strip()
            except ImportError:
                print("Nessun modulo PDF disponibile")
                return None
        except Exception as e:
            print(f"Errore estrazione testo PDF: {e}")
            return None
    
    def parse_ddt_with_gemini(self, file_obj):
        """Parser con Gemini AI usando API diretta"""
        print(f"DEBUG Gemini: Inizio parsing, file_obj type: {type(file_obj)}")
        gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not gemini_key:
            print("DEBUG Gemini: Key non disponibile")
            return {'success': False, 'error': 'Gemini key non disponibile'}
        
        try:
            print("DEBUG Gemini: Tentativo parsing con Gemini AI")
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

            # API diretta - usa modello funzionante
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            
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
                    parsed_data['ai_used'] = 'gemini'
                    parsed_data['ai_reason'] = 'Gemini AI selezionato dall\'utente e completato con successo'
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
        print(f"PARSING AVVIATO: AI preferita = {preferred_ai.upper()}")
        print(f"Tentativo parsing con {preferred_ai}")
        
        # Prova con AI preferito
        if preferred_ai == 'claude':
            result = self.parse_ddt_with_claude(file_obj)
            if result['success']:
                print("Parsing Claude completato")
                return result
            
            print(f"Claude fallito: {result.get('error')}")
            # Fallback a Gemini
            print("DEBUG: Tentativo fallback a Gemini...")
            result = self.parse_ddt_with_gemini(file_obj)
            print(f"DEBUG: Risultato Gemini: success={result.get('success')}, error={result.get('error')}")
            if result['success']:
                print("Parsing Gemini completato (fallback)")
                # Aggiorna il motivo della selezione
                if 'data' in result:
                    result['data']['ai_reason'] = f"Gemini AI usato come fallback (Claude fallito: {result.get('error', 'errore sconosciuto')[:50]})"
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
                # Aggiorna il motivo della selezione
                if 'data' in result:
                    result['data']['ai_reason'] = f"Claude AI usato come fallback (Gemini fallito: {result.get('error', 'errore sconosciuto')[:50]})"
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
            
            template_data['ai_used'] = 'fallback'
            template_data['ai_reason'] = 'Parser basico usato: entrambe le AI (Claude e Gemini) non sono riuscite ad elaborare il documento'
            return {
                'success': True, 
                'data': template_data,
                'warning': 'Dati generati automaticamente - completare manualmente'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Anche parser basico fallito: {str(e)}'}

    def parse_ordine_pdf(self, file_path, ai_service='claude'):
        """
        Parse PDF di offerta fornitore per creare ordine
        """
        print(f"Parsing offerta fornitore con {ai_service}")
        
        if ai_service == 'claude':
            return self.parse_ordine_with_claude(file_path)
        elif ai_service == 'gemini':
            return self.parse_ordine_with_gemini(file_path)
        else:
            return {'success': False, 'error': 'Servizio AI non supportato'}
    
    def parse_ordine_with_claude(self, file_path):
        """Parse offerta fornitore utilizzando Claude AI"""
        if not self.claude_client:
            print("DEBUG Claude: Client non disponibile")
            return {'success': False, 'error': 'Claude non disponibile'}
        
        try:
            print("DEBUG Claude: Tentativo parsing ordine con Claude AI")
            
            # Estrai testo dal PDF
            with open(file_path, 'rb') as pdf_file:
                pdf_text = self._extract_pdf_text(pdf_file)
            
            if not pdf_text or len(pdf_text.strip()) < 10:
                print("DEBUG Claude: Testo estratto insufficiente dal PDF")
                return {'success': False, 'error': 'Impossibile estrarre testo dal PDF'}
            
            print(f"DEBUG Claude: Testo estratto: {len(pdf_text)} caratteri")
            
            prompt = f"""Analizza questo testo estratto da un'offerta fornitore e restituisci SOLO il JSON in questo formato:
{{
  "fornitore": "Nome del fornitore",
  "data_offerta": "YYYY-MM-DD",
  "numero_offerta": "Numero offerta",
  "validita_offerta": "YYYY-MM-DD",
  "oggetto": "Oggetto/descrizione dell'offerta",
  "note": "Note aggiuntive",
  "articoli": [
    {{
      "descrizione": "Descrizione articolo",
      "quantita": 1.0,
      "prezzo_unitario": 100.00
    }}
  ]
}}

REGOLE IMPORTANTI:
- Estrai TUTTI gli articoli/prodotti presenti nell'offerta
- Se le date non sono chiare, lascia il campo vuoto ""
- I prezzi devono essere numerici (rimuovi €, virgole, etc.)
- Le quantità devono essere numeriche
- Mantieni descrizioni complete
- Rispondi SOLO con il JSON, niente altro

TESTO DA ANALIZZARE:
{pdf_text[:3000]}"""

            message = self.claude_client.messages.create(
                model='claude-3-haiku-20240307',
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = message.content[0].text.strip()
            print(f"DEBUG Claude: Risposta ricevuta: {len(content)} caratteri")
            
            # Pulisci JSON
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '')
            content = content.strip()
            
            try:
                data = json.loads(content)
                data['ai_used'] = 'claude'
                return {'success': True, 'data': data}
            except json.JSONDecodeError as e:
                print(f"Errore parsing JSON Claude ordine: {e}")
                print(f"Contenuto ricevuto: {content}")
                return {'success': False, 'error': f'JSON non valido da Claude: {str(e)}'}
                
        except Exception as e:
            print(f"Errore Claude parsing ordine: {e}")
            return {'success': False, 'error': str(e)}
    
    def parse_ordine_with_gemini(self, file_path):
        """Parse offerta fornitore utilizzando Gemini AI"""
        try:
            import base64
            
            # Leggi PDF
            with open(file_path, 'rb') as pdf_file:
                pdf_data = pdf_file.read()
                pdf_base64 = base64.b64encode(pdf_data).decode()
            
            url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self.gemini_api_key}'
            
            prompt = """Analizza questo PDF di un'offerta fornitore e restituisci i dati in formato JSON con questa struttura:

{
  "fornitore": "Nome del fornitore",
  "data_offerta": "YYYY-MM-DD",
  "numero_offerta": "Numero offerta", 
  "validita_offerta": "YYYY-MM-DD (scadenza offerta)",
  "oggetto": "Oggetto/descrizione dell'offerta",
  "note": "Note aggiuntive",
  "articoli": [
    {
      "descrizione": "Descrizione articolo",
      "quantita": 1.0,
      "prezzo_unitario": 100.00
    }
  ]
}

ISTRUZIONI:
- Estrai tutti gli articoli presenti nell'offerta
- Se le date non sono chiare, NON inventarle
- I prezzi devono essere numerici (senza €)
- Le quantità devono essere numeriche
- Rispondi SOLO con il JSON"""

            payload = {
                'contents': [{
                    'parts': [
                        {'text': prompt},
                        {
                            'inlineData': {
                                'mimeType': 'application/pdf',
                                'data': pdf_base64
                            }
                        }
                    ]
                }]
            }
            
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # Pulisci JSON
                    content = content.strip()
                    if content.startswith('```json'):
                        content = content.replace('```json', '').replace('```', '')
                    content = content.strip()
                    
                    try:
                        data = json.loads(content)
                        data['ai_used'] = 'gemini'
                        return {'success': True, 'data': data}
                    except json.JSONDecodeError as e:
                        print(f"Errore parsing JSON Gemini: {e}")
                        return {'success': False, 'error': f'JSON non valido da Gemini: {str(e)}'}
                else:
                    return {'success': False, 'error': 'Nessuna risposta da Gemini'}
            else:
                print(f"Errore Gemini API: {response.status_code} - {response.text}")
                return {'success': False, 'error': f'Errore API Gemini: {response.status_code}'}
                
        except Exception as e:
            print(f"Errore Gemini parsing ordine: {e}")
            return {'success': False, 'error': f'Errore Gemini: {str(e)}'}
