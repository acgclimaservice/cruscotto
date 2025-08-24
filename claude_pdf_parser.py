# claude_pdf_parser.py
import json
import os
from datetime import datetime
from models import db, ConfigurazioneSistema

# Import opzionali
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

class ClaudePDFParser:
    def __init__(self):
        self.client = None
        self.setup_claude_client()
    
    def setup_claude_client(self):
        """Inizializza il client Claude con API key"""
        if not ANTHROPIC_AVAILABLE:
            print("WARN: Libreria anthropic non disponibile. Usa modalita simulazione.")
            return
            
        api_key = os.environ.get('CLAUDE_API_KEY') or self.get_claude_api_key()
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            print("WARN: CLAUDE_API_KEY non configurata. Usa modalita simulazione.")
    
    def get_claude_api_key(self):
        """Recupera API key dalle configurazioni sistema"""
        config = ConfigurazioneSistema.query.filter_by(chiave='CLAUDE_API_KEY').first()
        return config.valore if config else None
    
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
    
    def parse_ddt_with_claude(self, pdf_text, learning_data=None):
        """Parsing PDF con Claude AI + dati di apprendimento"""
        if not self.client or not ANTHROPIC_AVAILABLE:
            print("INFO: Usando parsing OCR locale invece di simulazione")
            return self.parse_with_local_ocr(pdf_text)
        
        # Prompt base con schema DDT
        base_prompt = """
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

        IMPORTANTE:
        - Cerca varianti di "DDT", "Documento di Trasporto", "Bolla"
        - Per i prezzi, cerca "Prezzo", "Costo", "Importo", "€", "EUR"
        - Per quantità cerca "Qt.", "Qtà", "Pezzi", "n."
        - Se mancano dati, indica confidence più basso
        - Restituisci SOLO il JSON, senza altro testo
        """
        
        # Aggiunge esempi di apprendimento se disponibili
        if learning_data:
            base_prompt += f"\n\nEsempi di correzioni precedenti per migliorare l'accuratezza:\n{learning_data}"
        
        base_prompt += f"\n\nTESTO DEL DOCUMENTO:\n{pdf_text}"
        
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": base_prompt}]
            )
            
            # Estrae JSON dalla risposta
            json_text = response.content[0].text.strip()
            if json_text.startswith('```json'):
                json_text = json_text.replace('```json', '').replace('```', '').strip()
            
            parsed_data = json.loads(json_text)
            parsed_data['source'] = 'claude_ai'
            return parsed_data
            
        except Exception as e:
            print(f"Errore parsing Claude: {e}")
            return self.parse_with_local_ocr(pdf_text)
    
    def parse_with_local_ocr(self, pdf_text):
        """Parsing locale con regex e pattern matching"""
        import re
        from datetime import datetime
        
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
            "source": "local_ocr"
        }
        
        # Estrae fornitore (cerca pattern comuni)
        fornitore_patterns = [
            r"(?:Fornitore|FORNITORE|Ditta|DITTA|Ragione Sociale)[:\s]+([A-Za-z\s\.]+)",
            r"P\.IVA[:\s]+\d+\s*([A-Za-z\s\.]+)",
            r"^([A-Za-z\s\.]+)\s*S\.r\.l\.",
            r"^([A-Za-z\s\.]+)\s*S\.p\.A\."
        ]
        
        for pattern in fornitore_patterns:
            match = re.search(pattern, pdf_text, re.MULTILINE | re.IGNORECASE)
            if match:
                parsed_data["fornitore"] = match.group(1).strip()
                break
        
        # Estrae numero DDT
        ddt_patterns = [
            r"(?:DDT|Documento di Trasporto|Bolla)[:\s\#]*(\w+[-/]\w+[-/]\w+)",
            r"(?:N°|Numero)[:\s]*(\d+[-/]\d+)",
            r"(?:Doc\.|Documento)[:\s]*(\w+[-/]\w+)"
        ]
        
        for pattern in ddt_patterns:
            match = re.search(pattern, pdf_text, re.IGNORECASE)
            if match:
                parsed_data["numero_ddt_origine"] = match.group(1).strip()
                break
        
        # Estrae data
        date_patterns = [
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
            r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, pdf_text)
            if match:
                try:
                    date_str = match.group(1)
                    # Prova diversi formati
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
        
        # Estrae articoli (pattern tabellare)
        lines = pdf_text.split('\n')
        in_table = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Cerca inizio tabella articoli
            if re.search(r"(?:codice|descrizione|quantita|prezzo|costo)", line, re.IGNORECASE):
                in_table = True
                continue
                
            if in_table:
                # Pattern per riga articolo: codice, descrizione, quantità, prezzo
                parts = re.split(r'\s{2,}|\t', line)
                if len(parts) >= 3:
                    try:
                        articolo = {
                            "codice": parts[0].strip() if parts[0] else f"ART{len(parsed_data['articoli'])+1:03d}",
                            "descrizione": parts[1].strip() if len(parts) > 1 else "Articolo estratto",
                            "quantita": 1,
                            "costo_unitario": 0.0,
                            "unita_misura": "PZ"
                        }
                        
                        # Cerca quantità e prezzo negli altri campi
                        for part in parts[2:]:
                            part = part.replace(',', '.')
                            # Se contiene solo numeri, potrebbe essere quantità o prezzo
                            if re.match(r'^\d+\.?\d*$', part):
                                num = float(part)
                                if num < 100:  # Probabilmente quantità
                                    articolo["quantita"] = num
                                else:  # Probabilmente prezzo
                                    articolo["costo_unitario"] = num
                        
                        parsed_data["articoli"].append(articolo)
                        
                        # Limita a 10 articoli per evitare parsing errato
                        if len(parsed_data["articoli"]) >= 10:
                            break
                            
                    except Exception as e:
                        continue
        
        # Se non ha trovato articoli, crea uno di default
        if not parsed_data["articoli"]:
            parsed_data["articoli"] = [{
                "codice": "ART001",
                "descrizione": "Articolo da verificare (parsing automatico)",
                "quantita": 1,
                "costo_unitario": 0.0,
                "unita_misura": "PZ"
            }]
        
        # Calcola totale documento
        parsed_data["totale_documento"] = sum(
            art["quantita"] * art["costo_unitario"] 
            for art in parsed_data["articoli"]
        )
        
        # Se non ha trovato fornitore, usa placeholder
        if not parsed_data["fornitore"]:
            parsed_data["fornitore"] = "Fornitore da verificare"
        
        return parsed_data
    
    def simulate_parsing(self):
        """Parsing simulato per demo senza API key"""
        return {
            "fornitore": "Fornitore Estratto da Demo",
            "data_ddt_origine": "2024-01-20",
            "numero_ddt_origine": "DDT-DEMO-001",
            "riferimento": "ORD-2024-001",
            "destinazione": "Magazzino Centrale",
            "articoli": [
                {
                    "codice": "ART001",
                    "descrizione": "Monitor LED 27 Full HD",
                    "quantita": 2,
                    "costo_unitario": 150.00,
                    "unita_misura": "PZ"
                },
                {
                    "codice": "ART002", 
                    "descrizione": "Tastiera Meccanica Gaming",
                    "quantita": 1,
                    "costo_unitario": 89.00,
                    "unita_misura": "PZ"
                }
            ],
            "totale_documento": 389.00,
            "note": "Parsed con modalita demo",
            "confidence": 0.85,
            "source": "simulation"
        }
    
    def save_parsing_correction(self, original_data, corrected_data, user_feedback):
        """Salva correzioni per training futuro"""
        correction_data = {
            "timestamp": datetime.now().isoformat(),
            "original": original_data,
            "corrected": corrected_data,
            "user_feedback": user_feedback,
            "improvements": self.analyze_corrections(original_data, corrected_data)
        }
        
        # Salva in configurazioni sistema per training
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
        
        # Mantieni solo ultime 100 correzioni
        if len(corrections_list) > 100:
            corrections_list = corrections_list[-100:]
        
        existing_corrections.valore = json.dumps(corrections_list)
        db.session.commit()
        
        return correction_data
    
    def analyze_corrections(self, original, corrected):
        """Analizza le correzioni per migliorare parsing futuro"""
        improvements = []
        
        # Controlla campi principali
        for field in ['fornitore', 'data_ddt_origine', 'riferimento']:
            if field in original and field in corrected:
                if original[field] != corrected[field]:
                    improvements.append({
                        'field': field,
                        'original': original[field],
                        'corrected': corrected[field],
                        'pattern': f"Campo {field} corretto da '{original[field]}' a '{corrected[field]}'"
                    })
        
        # Controlla articoli
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
        corrections = ConfigurazioneSistema.query.filter_by(
            chiave='PARSING_CORRECTIONS'
        ).first()
        
        if not corrections:
            return None
        
        try:
            corrections_data = json.loads(corrections.valore)
            # Prende le ultime 10 correzioni più significative
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