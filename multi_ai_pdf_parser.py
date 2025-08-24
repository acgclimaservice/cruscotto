# multi_ai_pdf_parser.py
import json
import os
from datetime import datetime
from models import db, ConfigurazioneSistema
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# Import opzionali
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

class MultiAIPDFParser:
    def __init__(self):
        self.claude_client = None
        self.gemini_model = None
        self.setup_ai_clients()
    
    def setup_ai_clients(self):
        """Inizializza i client AI disponibili"""
        
        # Configura Claude
        if ANTHROPIC_AVAILABLE:
            api_key = os.getenv('CLAUDE_API_KEY') or self.get_api_key_from_db('CLAUDE_API_KEY')
            if api_key:
                self.claude_client = anthropic.Anthropic(api_key=api_key)
                print("INFO: Claude AI configurato")
            else:
                print("WARN: CLAUDE_API_KEY non trovata")
        
        # Configura Gemini
        if GEMINI_AVAILABLE:
            api_key = os.getenv('GEMINI_API_KEY') or self.get_api_key_from_db('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro')
                self.gemini_model = genai.GenerativeModel(model_name)
                print(f"INFO: Gemini AI configurato ({model_name})")
            else:
                print("WARN: GEMINI_API_KEY non trovata")
    
    def get_api_key_from_db(self, key_name):
        """Recupera API key dalle configurazioni sistema"""
        try:
            config = ConfigurazioneSistema.query.filter_by(chiave=key_name).first()
            return config.valore if config else None
        except:
            return None
    
    def extract_text_from_pdf(self, pdf_file):
        """Estrae testo da file PDF"""
        if not PDF_AVAILABLE:
            print("WARN: PyPDF2 non disponibile - usando modalita simulazione")
            return "Testo simulato del documento PDF per demo"
            
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Errore estrazione PDF: {e}")
            return "Testo simulato del documento PDF per demo"
    
    def create_parsing_prompt(self, learning_data=None):
        """Crea il prompt base per il parsing DDT"""
        prompt = """
        Analizza questo documento DDT e estrai le seguenti informazioni in formato JSON:

        {
            "fornitore": "nome completo fornitore",
            "data_ddt_origine": "YYYY-MM-DD",
            "numero_ddt_origine": "numero DDT fornitore",
            "riferimento": "ordine/riferimento se presente",
            "destinazione": "indirizzo/magazzino destinazione",
            "articoli": [
                {
                    "codice": "codice articolo",
                    "descrizione": "descrizione completa",
                    "quantita": numero,
                    "costo_unitario": numero,
                    "unita_misura": "PZ/KG/MT/etc"
                }
            ],
            "totale_documento": numero,
            "note": "note aggiuntive se presenti",
            "confidence": 0.95
        }

        ISTRUZIONI SPECIFICHE:
        - Cerca varianti di "DDT", "Documento di Trasporto", "Bolla", "Documento di Consegna"
        - Per i prezzi, cerca "Prezzo", "Costo", "Importo", "€", "EUR", "Euro"
        - Per quantità cerca "Qt.", "Qtà", "Pezzi", "n.", "Quantità", "Q.tà"
        - Estrai TUTTI gli articoli dalla tabella, non solo i primi
        - Se mancano dati critici, indica confidence più basso
        - Restituisci SOLO il JSON valido, senza markdown o altro testo
        - Assicurati che tutti i numeri siano validi (no virgole, usa punti decimali)
        """
        
        if learning_data:
            prompt += f"\n\nEsempi di correzioni precedenti:\n{learning_data}"
        
        return prompt
    
    def parse_with_claude(self, pdf_text, learning_data=None):
        """Parsing con Claude AI"""
        if not self.claude_client:
            return None
            
        prompt = self.create_parsing_prompt(learning_data)
        prompt += f"\n\nTESTO DEL DOCUMENTO:\n{pdf_text}"
        
        try:
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            json_text = response.content[0].text.strip()
            if json_text.startswith('```json'):
                json_text = json_text.replace('```json', '').replace('```', '').strip()
            
            parsed_data = json.loads(json_text)
            parsed_data['source'] = 'claude_ai'
            parsed_data['ai_provider'] = 'Anthropic Claude'
            return parsed_data
            
        except Exception as e:
            print(f"Errore parsing Claude: {e}")
            return None
    
    def parse_with_gemini(self, pdf_text, learning_data=None):
        """Parsing con Gemini AI"""
        if not self.gemini_model:
            return None
            
        prompt = self.create_parsing_prompt(learning_data)
        prompt += f"\n\nTESTO DEL DOCUMENTO:\n{pdf_text}"
        
        try:
            response = self.gemini_model.generate_content(prompt)
            
            if not response.text:
                return None
                
            json_text = response.text.strip()
            if json_text.startswith('```json'):
                json_text = json_text.replace('```json', '').replace('```', '').strip()
            
            parsed_data = json.loads(json_text)
            parsed_data['source'] = 'gemini_ai'
            parsed_data['ai_provider'] = 'Google Gemini'
            return parsed_data
            
        except Exception as e:
            print(f"Errore parsing Gemini: {e}")
            return None
    
    def parse_with_dual_ai(self, pdf_text, learning_data=None):
        """Parsing con entrambi i servizi AI per massimizzare accuratezza"""
        claude_result = None
        gemini_result = None
        
        # Prova con Claude
        if self.claude_client:
            print("INFO: Tentativo parsing con Claude...")
            claude_result = self.parse_with_claude(pdf_text, learning_data)
        
        # Prova con Gemini
        if self.gemini_model:
            print("INFO: Tentativo parsing con Gemini...")  
            gemini_result = self.parse_with_gemini(pdf_text, learning_data)
        
        # Seleziona il migliore risultato
        if claude_result and gemini_result:
            # Confronta confidence e qualità
            claude_conf = claude_result.get('confidence', 0)
            gemini_conf = gemini_result.get('confidence', 0)
            
            # Considera anche il numero di articoli estratti
            claude_articles = len(claude_result.get('articoli', []))
            gemini_articles = len(gemini_result.get('articoli', []))
            
            # Score composito
            claude_score = claude_conf + (claude_articles * 0.05)
            gemini_score = gemini_conf + (gemini_articles * 0.05)
            
            if claude_score >= gemini_score:
                claude_result['dual_ai_info'] = {
                    'primary': 'claude',
                    'secondary': 'gemini',
                    'claude_confidence': claude_conf,
                    'gemini_confidence': gemini_conf,
                    'reason': 'Claude selected for higher composite score'
                }
                return claude_result
            else:
                gemini_result['dual_ai_info'] = {
                    'primary': 'gemini', 
                    'secondary': 'claude',
                    'claude_confidence': claude_conf,
                    'gemini_confidence': gemini_conf,
                    'reason': 'Gemini selected for higher composite score'
                }
                return gemini_result
        
        # Solo uno disponibile
        elif claude_result:
            claude_result['dual_ai_info'] = {'primary': 'claude', 'secondary': None}
            return claude_result
        elif gemini_result:
            gemini_result['dual_ai_info'] = {'primary': 'gemini', 'secondary': None}
            return gemini_result
        
        # Nessuno disponibile
        return None
    
    def parse_ddt_with_ai(self, pdf_text, learning_data=None, preferred_ai='dual'):
        """Metodo principale per parsing DDT"""
        
        # Modalità dual AI (default)
        if preferred_ai == 'dual':
            result = self.parse_with_dual_ai(pdf_text, learning_data)
            if result:
                return result
        
        # Modalità singolo AI
        elif preferred_ai == 'claude':
            result = self.parse_with_claude(pdf_text, learning_data)
            if result:
                return result
        elif preferred_ai == 'gemini':
            result = self.parse_with_gemini(pdf_text, learning_data)
            if result:
                return result
        
        # Fallback a parsing locale
        print("INFO: Fallback a parsing locale")
        return self.parse_with_local_ocr(pdf_text)
    
    def parse_with_local_ocr(self, pdf_text):
        """Parsing locale con regex (stesso del claude_pdf_parser.py)"""
        import re
        
        parsed_data = {
            "fornitore": "",
            "data_ddt_origine": datetime.now().strftime("%Y-%m-%d"),
            "numero_ddt_origine": "",
            "riferimento": "",
            "destinazione": "",
            "mastrino_ddt": "",
            "articoli": [],
            "totale_documento": 0.0,
            "note": "Estratto con parsing locale",
            "confidence": 0.7,
            "source": "local_ocr",
            "ai_provider": "Local Regex"
        }
        
        # Estrae fornitore
        fornitore_patterns = [
            r"(?:Fornitore|FORNITORE|Ditta|DITTA|Ragione Sociale)[:\\s]+([A-Za-z\\s\\.]+)",
            r"P\\.IVA[:\\s]+\\d+\\s*([A-Za-z\\s\\.]+)",
            r"^([A-Za-z\\s\\.]+)\\s*S\\.r\\.l\\.",
            r"^([A-Za-z\\s\\.]+)\\s*S\\.p\\.A\\."
        ]
        
        for pattern in fornitore_patterns:
            match = re.search(pattern, pdf_text, re.MULTILINE | re.IGNORECASE)
            if match:
                parsed_data["fornitore"] = match.group(1).strip()
                break
        
        # Estrae numero DDT
        ddt_patterns = [
            r"(?:DDT|Documento di Trasporto|Bolla)[:\\s\\#]*(\\w+[-/]\\w+[-/]\\w+)",
            r"(?:N°|Numero)[:\\s]*(\\d+[-/]\\d+)",
            r"(?:Doc\\.|Documento)[:\\s]*(\\w+[-/]\\w+)"
        ]
        
        for pattern in ddt_patterns:
            match = re.search(pattern, pdf_text, re.IGNORECASE)
            if match:
                parsed_data["numero_ddt_origine"] = match.group(1).strip()
                break
        
        # Estrae data
        date_patterns = [
            r"(\\d{1,2}[-/]\\d{1,2}[-/]\\d{4})",
            r"(\\d{4}[-/]\\d{1,2}[-/]\\d{1,2})"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, pdf_text)
            if match:
                try:
                    date_str = match.group(1)
                    for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d"]:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            parsed_data["data_ddt_origine"] = date_obj.strftime("%Y-%m-%d")
                            break
                        except ValueError:
                            continue
                except:
                    pass
                break
        
        # Crea articolo di default se non trova nulla
        if not parsed_data["articoli"]:
            parsed_data["articoli"] = [{
                "codice": "ART001",
                "descrizione": "Articolo da verificare (parsing automatico)",
                "quantita": 1,
                "costo_unitario": 0.0,
                "unita_misura": "PZ"
            }]
        
        if not parsed_data["fornitore"]:
            parsed_data["fornitore"] = "Fornitore da verificare"
        
        return parsed_data
    
    def save_parsing_correction(self, original_data, corrected_data, user_feedback):
        """Salva correzioni per training futuro (stesso del claude_pdf_parser.py)"""
        correction_data = {
            "timestamp": datetime.now().isoformat(),
            "original": original_data,
            "corrected": corrected_data,
            "user_feedback": user_feedback,
            "improvements": self.analyze_corrections(original_data, corrected_data)
        }
        
        existing_corrections = ConfigurazioneSistema.query.filter_by(
            chiave='PARSING_CORRECTIONS'
        ).first()
        
        if existing_corrections:
            try:
                corrections_list = json.loads(existing_corrections.valore)
            except:
                corrections_list = []
        else:
            corrections_list = []
            existing_corrections = ConfigurazioneSistema(
                chiave='PARSING_CORRECTIONS',
                valore='[]',
                descrizione='Correzioni parsing PDF per training'
            )
            db.session.add(existing_corrections)
        
        corrections_list.append(correction_data)
        
        if len(corrections_list) > 100:
            corrections_list = corrections_list[-100:]
        
        existing_corrections.valore = json.dumps(corrections_list)
        db.session.commit()
        
        return correction_data
    
    def analyze_corrections(self, original, corrected):
        """Analizza correzioni per migliorare parsing futuro"""
        improvements = []
        
        for field in ['fornitore', 'data_ddt_origine', 'riferimento']:
            if field in original and field in corrected:
                if original[field] != corrected[field]:
                    improvements.append({
                        'field': field,
                        'original': original[field],
                        'corrected': corrected[field],
                        'pattern': f"Campo {field} corretto da '{original[field]}' a '{corrected[field]}'"
                    })
        
        if 'articoli' in original and 'articoli' in corrected:
            orig_count = len(original['articoli'])
            corr_count = len(corrected['articoli'])
            if orig_count != corr_count:
                improvements.append({
                    'field': 'articoli_count',
                    'pattern': f"Numero articoli corretto da {orig_count} a {corr_count}"
                })
        
        return improvements
    
    def get_learning_data(self):
        """Recupera dati di apprendimento dalle correzioni precedenti"""
        try:
            corrections = ConfigurazioneSistema.query.filter_by(
                chiave='PARSING_CORRECTIONS'
            ).first()
            
            if not corrections:
                return None
            
            corrections_data = json.loads(corrections.valore)
            recent_corrections = corrections_data[-10:]
            
            learning_examples = []
            for correction in recent_corrections:
                if 'improvements' in correction:
                    for improvement in correction['improvements']:
                        learning_examples.append(improvement['pattern'])
            
            return "\n".join(learning_examples) if learning_examples else None
            
        except Exception as e:
            print(f"Errore recupero learning data: {e}")
            return None
    
    def get_ai_status(self):
        """Restituisce lo stato dei servizi AI"""
        return {
            'claude_available': self.claude_client is not None,
            'gemini_available': self.gemini_model is not None,
            'pdf_extraction': PDF_AVAILABLE,
            'total_ai_services': sum([
                self.claude_client is not None,
                self.gemini_model is not None
            ])
        }