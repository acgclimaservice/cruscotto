# Advanced Claude DDT Parser LITE - Senza dipendenze problematiche
import os
import json
import base64
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import PyPDF2  # Usa PyPDF2 invece di PyMuPDF

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

class AdvancedClaudeDDTParserLite:
    """
    Parser DDT evoluto COMPATIBILE con PythonAnywhere
    - Niente PyMuPDF (causa libcrypt.so.2 error)
    - Usa PyPDF2 per estrazione testo
    - Mantiene ragionamento semantico avanzato
    - Compatibile con tutti gli ambienti Python
    """

    def __init__(self):
        self.claude_client = None
        if CLAUDE_AVAILABLE:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.claude_client = anthropic.Anthropic(api_key=api_key)

        self.max_retries = 3
        self.confidence_threshold = 0.8

    def parse_ddt_advanced(self, file_obj, document_type='ddt_in') -> Dict[str, Any]:
        """
        Entry point principale per parsing DDT evoluto LITE
        """
        if not self.claude_client:
            return {
                'success': False,
                'error': 'Claude API non disponibile',
                'fallback_suggested': True
            }

        try:
            print(f"🚀 ADVANCED CLAUDE DDT LITE: Inizio parsing {document_type}")

            # Step 1: Estrazione contenuto con PyPDF2 (compatibile)
            content_data = self._extract_document_content_lite(file_obj)
            if not content_data['success']:
                return content_data

            # Step 2: Analisi preliminare del documento
            doc_analysis = self._analyze_document_structure(content_data)

            # Step 3: Parsing intelligente con ragionamento semantico
            parsing_result = self._intelligent_parsing_with_reasoning(
                content_data, doc_analysis, document_type
            )

            # Step 4: Validazione e correzione automatica
            validated_result = self._validate_and_correct(parsing_result, document_type)

            # Step 5: Post-processing e normalizzazione
            final_result = self._post_process_data(validated_result, document_type)

            print(f"✅ ADVANCED CLAUDE LITE: Parsing completato con successo")
            return {
                'success': True,
                'data': final_result,
                'metadata': {
                    'parser_version': 'advanced_claude_lite_v1',
                    'confidence_score': self._calculate_confidence(final_result),
                    'document_analysis': doc_analysis,
                    'processing_time': datetime.now().isoformat()
                }
            }

        except Exception as e:
            print(f"❌ ADVANCED CLAUDE LITE ERROR: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_suggested': True
            }

    def _extract_document_content_lite(self, file_obj) -> Dict[str, Any]:
        """Estrae contenuto da PDF usando PyPDF2 (compatibile PythonAnywhere)"""
        try:
            file_obj.seek(0)
            pdf_reader = PyPDF2.PdfReader(file_obj)

            extracted_content = {
                'text_content': '',
                'pages': [],
                'page_count': len(pdf_reader.pages),
                'metadata': {}
            }

            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()

                    extracted_content['pages'].append({
                        'page_number': page_num + 1,
                        'text': page_text,
                        'char_count': len(page_text)
                    })

                    extracted_content['text_content'] += page_text + "\\n"

                except Exception as e:
                    print(f"⚠️ Errore estrazione pagina {page_num + 1}: {e}")
                    # Continua con le altre pagine

            return {
                'success': True,
                'content': extracted_content,
                'type': 'text_only'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Errore estrazione contenuto: {e}"
            }

    def _analyze_document_structure(self, content_data: Dict) -> Dict[str, Any]:
        """Analizza struttura del documento per orientare il parsing"""
        content = content_data['content']
        text = content['text_content']

        analysis = {
            'document_quality': 'high' if len(text) > 500 else 'low',
            'page_count': content['page_count'],
            'language': 'italian',
            'suspected_fields': [],
            'layout_type': 'standard'
        }

        # Analisi pattern comuni nei DDT
        patterns = {
            'numero_ddt': [r'ddt[:\s#]*([a-zA-Z0-9\-/]{3,20})', r'doc[:\s#]*([a-zA-Z0-9\-/]{3,20})'],
            'data': [r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})', r'(\d{2,4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})'],
            'fornitore': [r'mittente[:\s]*(.*?)(?=\n|destinatario)', r'da[:\s]*(.*?)(?=\n|a[:\s])'],
            'destinatario': [r'destinatario[:\s]*(.*?)(?=\n)', r'a[:\s]*(.*?)(?=\n)'],
            'totale': [r'totale[:\s]*€?\s*(\d+[,\.]\d{2})', r'€\s*(\d+[,\.]\d{2})']
        }

        text_upper = text.upper()
        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, text_upper, re.IGNORECASE):
                    analysis['suspected_fields'].append(field)
                    break

        # Determina layout type
        if 'CAMBIELLI' in text_upper:
            analysis['layout_type'] = 'cambielli'
        elif 'RIELLO' in text_upper:
            analysis['layout_type'] = 'riello'

        return analysis

    def _intelligent_parsing_with_reasoning(self, content_data: Dict, analysis: Dict, doc_type: str) -> Dict[str, Any]:
        """Parsing intelligente con ragionamento semantico forte"""

        # Costruisci prompt con ragionamento semantico incorporato
        full_prompt = f"""
{self._build_schema_prompt(doc_type)}

🧠 RAGIONAMENTO SEMANTICO OBBLIGATORIO:

CAMPO NOTE - RAGIONA PRIMA DI ESTRARRE:
❌ NON sono note commerciali:
- "Firma Per Accettazione"
- "Importo I.V.A."
- "Totale offerta"
- "Cliente"
- Intestazioni di tabelle
- Firme e formule standard

✅ SONO note commerciali valide:
- "EVENTUALE CONSEGNA AL MARCIAPIEDE SALDO ALLA CONSEGNA SALVO DIVERSI ACCORDI"
- "VALIDA 10 GG DATA OFFERTA - SALVO APPROVAZIONE DELL'AZIENDA"
- Condizioni di pagamento
- Modalità di consegna
- Validità dell'offerta
- Clausole contrattuali

REGOLA FONDAMENTALE PER LE NOTE:
Cerca nel fondo del documento, vicino alla parola "NOTE" o "CONDIZIONI",
testo che contiene informazioni commerciali come:
- CONSEGNA, SALDO, PAGAMENTO
- VALIDITÀ, ACCORDI, APPROVAZIONE
- Giorni, date, condizioni

CAMPO FORNITORE - LOGICA:
✅ È il fornitore: chi INVIA la merce, emette il documento
❌ NON è il fornitore: "ACG CLIMA SERVICE" (è il destinatario)

METODO DI LAVORO OBBLIGATORIO:
1. Leggi tutto il documento
2. Per ogni campo, RAGIONA: "Ha senso logico?"
3. Se un dato non ha senso, cerca altrove
4. Valida semanticamente prima di estrarre

{self._build_layout_specific_rules(analysis['layout_type'])}

IMPORTANTE:
- Rispondi SOLO con JSON valido
- Se non trovi un campo logicamente valido, usa null
- Date in formato YYYY-MM-DD
- Numeri con punto decimale
"""

        # Chiamata Claude
        result = self._parse_with_text_reasoning(full_prompt, content_data['content']['text_content'])
        return result

    def _build_schema_prompt(self, doc_type: str) -> str:
        """Schema JSON con focus su campi problematici"""
        if doc_type == 'ddt_in':
            return '''
SCHEMA JSON RICHIESTO per DDT IN:
{
    "numero_ddt": "numero documento trasporto",
    "data_ddt": "data in formato YYYY-MM-DD",
    "fornitore": "nome fornitore/mittente che invia la merce",
    "destinatario": "nome destinatario che riceve la merce",
    "causale_trasporto": "causale del trasporto",
    "aspetto_beni": "aspetto dei beni",
    "trasportatore": "nome trasportatore",
    "totale_fattura": 0.00,
    "articoli": [
        {
            "codice": "codice articolo/prodotto",
            "descrizione": "descrizione completa",
            "quantita": 0.0,
            "unita_misura": "PZ/MT/KG etc",
            "prezzo_unitario": 0.00,
            "totale_riga": 0.00
        }
    ],
    "note": "SOLO condizioni commerciali vere - non firme o totali"
}
'''
        else:
            return '''Schema generico per altri documenti'''

    def _build_layout_specific_rules(self, layout_type: str) -> str:
        """Regole specifiche per layout"""
        if layout_type == 'cambielli':
            return """
REGOLE SPECIFICHE CAMBIELLI:
- Fornitore: sempre "0000000030 - CAMBIELLI SPA"
- Numero offerta: formato "XC/STD/xxxxxxx"
- Note: cerca nel FONDO del documento condizioni come "EVENTUALE CONSEGNA AL MARCIAPIEDE"
"""
        else:
            return "Applica regole standard di ragionamento semantico"

    def _parse_with_text_reasoning(self, prompt: str, text_content: str) -> Dict[str, Any]:
        """Parsing con Claude + ragionamento semantico"""
        try:
            full_prompt = f"{prompt}\\n\\nTESTO DEL DOCUMENTO:\\n{text_content[:12000]}"

            message = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": full_prompt
                }]
            )

            response_text = message.content[0].text.strip()
            return self._parse_claude_response(response_text)

        except Exception as e:
            print(f"❌ Text parsing failed: {e}")
            return {'success': False, 'error': str(e)}

    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """Parsifica risposta Claude estraendo JSON"""
        try:
            # Pulisci risposta da markdown
            response_text = response_text.replace('```json', '').replace('```', '').strip()

            # Trova JSON nella risposta
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("JSON non trovato nella risposta")

            json_text = response_text[json_start:json_end]
            parsed_data = json.loads(json_text)

            return {'success': True, 'data': parsed_data}

        except Exception as e:
            print(f"❌ Errore parsing risposta Claude: {e}")
            print(f"Risposta raw: {response_text[:500]}...")
            return {'success': False, 'error': f'Errore parsing risposta: {e}'}

    def _validate_and_correct(self, parsing_result: Dict, doc_type: str) -> Dict[str, Any]:
        """Validazione post-parsing"""
        if not parsing_result.get('success'):
            return parsing_result

        data = parsing_result['data']

        # Validazioni base
        self._validate_dates(data)
        self._validate_numbers(data)
        self._validate_semantic_logic(data)

        return {'success': True, 'data': data}

    def _validate_dates(self, data: Dict):
        """Valida formato date"""
        date_fields = ['data_ddt', 'data_documento', 'data_offerta']
        for field in date_fields:
            if field in data and data[field]:
                date_value = str(data[field])
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                    try:
                        parsed_date = datetime.strptime(date_value, fmt)
                        data[field] = parsed_date.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue

    def _validate_numbers(self, data: Dict):
        """Valida formato numeri"""
        def fix_number(value):
            if value is None or value == '':
                return 0.0
            try:
                str_val = str(value).replace(',', '.')
                return float(str_val)
            except:
                return 0.0

        number_fields = ['totale_fattura', 'totale', 'prezzo_unitario', 'quantita', 'totale_riga']

        for field in number_fields:
            if field in data:
                data[field] = fix_number(data[field])

        if 'articoli' in data and data['articoli']:
            for articolo in data['articoli']:
                for field in number_fields:
                    if field in articolo:
                        articolo[field] = fix_number(articolo[field])

    def _validate_semantic_logic(self, data: Dict):
        """Validazione semantica intelligente"""

        # Validazione NOTE critiche
        if 'note' in data and data['note']:
            note_text = str(data['note']).upper()

            # Pattern INVALIDI per le note
            invalid_patterns = [
                'FIRMA.*ACCETTAZIONE',
                'IMPORTO.*IVA',
                'TOTALE.*OFFERTA',
                'TOTALEOFFERTA',  # Caso specifico dell'utente
                'CLIENTE$',
                r'^[A-Z\s]{1,15}$'  # Troppo generiche
            ]

            # Pattern VALIDI per le note
            valid_patterns = [
                'EVENTUALE.*CONSEGNA',
                'CONSEGNA.*MARCIAPIEDE',
                'SALDO.*CONSEGNA',
                'VALIDA.*GG',
                'ACCORDI',
                'APPROVAZIONE',
                'PAGAMENTO.*GIORNI',
                'FRANCO.*MAGAZZINO'
            ]

            is_invalid = any(re.search(pattern, note_text) for pattern in invalid_patterns)
            is_valid = any(re.search(pattern, note_text) for pattern in valid_patterns)

            if is_invalid and not is_valid:
                print(f"🚫 Note INVALIDE rilevate: '{data['note'][:50]}...'")
                print(f"💡 Suggerimento: cerca condizioni commerciali nel documento")
                # Azzera campo note invalido
                data['note'] = None
            elif is_valid:
                print(f"✅ Note VALIDE: condizioni commerciali riconosciute")

        # Validazione FORNITORE
        if 'fornitore' in data and data['fornitore']:
            fornitore = str(data['fornitore']).upper()
            if 'ACG CLIMA SERVICE' in fornitore:
                print(f"⚠️ Fornitore sospetto: ACG è di solito il destinatario, non il fornitore")

    def _post_process_data(self, validated_result: Dict, doc_type: str) -> Dict[str, Any]:
        """Post-processing finale"""
        if not validated_result.get('success'):
            return validated_result

        data = validated_result['data']

        data['ai_used'] = 'claude_advanced_lite'
        data['ai_reason'] = 'Advanced Claude LITE con ragionamento semantico (compatibile PythonAnywhere)'
        data['processing_timestamp'] = datetime.now().isoformat()

        return data

    def _calculate_confidence(self, data: Dict) -> float:
        """Calcola confidence score"""
        score = 0.0
        total_checks = 0

        critical_fields = ['numero_ddt', 'data_ddt', 'fornitore']
        for field in critical_fields:
            total_checks += 1
            if field in data and data[field]:
                score += 1

        return score / total_checks if total_checks > 0 else 0.0

# Funzione wrapper per integrazione
def parse_ddt_with_advanced_claude_lite(file_obj, document_type='ddt_in'):
    """
    Funzione wrapper per parsing DDT con sistema evoluto LITE
    COMPATIBILE con PythonAnywhere (no PyMuPDF/libcrypt issues)
    """
    parser = AdvancedClaudeDDTParserLite()
    return parser.parse_ddt_advanced(file_obj, document_type)

if __name__ == "__main__":
    print("Advanced Claude DDT Parser LITE - Compatibile PythonAnywhere")
    print("Nessuna dipendenza PyMuPDF - Solo PyPDF2 + ragionamento semantico avanzato")