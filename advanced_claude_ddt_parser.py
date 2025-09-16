# Advanced Claude DDT Parser - Sistema di Parsing Evoluto
import os
import json
import base64
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import fitz  # PyMuPDF per PDF
from PIL import Image
import io

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

class AdvancedClaudeDDTParser:
    """
    Parser DDT ultra-evoluto con Claude API che supporta:
    - Parsing multi-step con ragionamento
    - Validazione schema automatica
    - OCR su documenti scansionati
    - Estrazione intelligente con context awareness
    - Recovery automatico da errori
    - Supporto multiple formati
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
        Entry point principale per parsing DDT evoluto

        Args:
            file_obj: File object del PDF
            document_type: Tipo documento ('ddt_in', 'ddt_out', 'fattura', 'ordine')

        Returns:
            Dict con risultati parsing e metadati
        """
        if not self.claude_client:
            return {
                'success': False,
                'error': 'Claude API non disponibile',
                'fallback_suggested': True
            }

        try:
            print(f"🚀 ADVANCED CLAUDE DDT: Inizio parsing {document_type}")

            # Step 1: Estrazione contenuto multi-format
            content_data = self._extract_document_content(file_obj)
            if not content_data['success']:
                return content_data

            # Step 2: Analisi preliminare del documento
            doc_analysis = self._analyze_document_structure(content_data)

            # Step 3: Parsing multi-step intelligente
            parsing_result = self._intelligent_multi_step_parsing(
                content_data, doc_analysis, document_type
            )

            # Step 4: Validazione e correzione automatica
            validated_result = self._validate_and_correct(parsing_result, document_type)

            # Step 5: Post-processing e normalizzazione
            final_result = self._post_process_data(validated_result, document_type)

            print(f"✅ ADVANCED CLAUDE: Parsing completato con successo")
            return {
                'success': True,
                'data': final_result,
                'metadata': {
                    'parser_version': 'advanced_claude_v2',
                    'confidence_score': self._calculate_confidence(final_result),
                    'document_analysis': doc_analysis,
                    'processing_time': datetime.now().isoformat()
                }
            }

        except Exception as e:
            print(f"❌ ADVANCED CLAUDE ERROR: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_suggested': True
            }

    def _extract_document_content(self, file_obj) -> Dict[str, Any]:
        """Estrae contenuto da PDF con supporto testo e immagini"""
        try:
            file_obj.seek(0)
            pdf_doc = fitz.open(stream=file_obj.read(), filetype="pdf")

            extracted_content = {
                'text_content': '',
                'images': [],
                'pages': [],
                'metadata': {}
            }

            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]

                # Estrai testo con posizioni
                text_dict = page.get_text("dict")
                page_text = page.get_text()

                # Estrai immagini se il testo è scarso (documento scansionato)
                page_images = []
                if len(page_text.strip()) < 100:  # Probabile scansione
                    print(f"📸 Pagina {page_num + 1}: Testo scarso, estraendo immagini...")
                    image_list = page.get_images()

                    for img_index, img in enumerate(image_list):
                        try:
                            xref = img[0]
                            pix = fitz.Pixmap(pdf_doc, xref)

                            if pix.n - pix.alpha < 4:  # Evita CMYK
                                img_data = pix.tobytes("png")
                                img_base64 = base64.b64encode(img_data).decode()
                                page_images.append({
                                    'index': img_index,
                                    'data': img_base64,
                                    'format': 'png'
                                })
                            pix = None
                        except Exception as e:
                            print(f"⚠️ Errore estrazione immagine {img_index}: {e}")

                extracted_content['pages'].append({
                    'page_number': page_num + 1,
                    'text': page_text,
                    'text_blocks': text_dict.get('blocks', []),
                    'images': page_images,
                    'bbox': page.rect
                })

                extracted_content['text_content'] += page_text + "\\n"
                extracted_content['images'].extend(page_images)

            pdf_doc.close()

            return {
                'success': True,
                'content': extracted_content,
                'type': 'hybrid' if extracted_content['images'] else 'text'
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
            'is_scanned': len(content['images']) > 0,
            'page_count': len(content['pages']),
            'language': 'italian',  # Assumiamo italiano
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
        elif len(content['images']) > 0:
            analysis['layout_type'] = 'scanned'

        return analysis

    def _intelligent_multi_step_parsing(self, content_data: Dict, analysis: Dict, doc_type: str) -> Dict[str, Any]:
        """Parsing multi-step con ragionamento intelligente"""

        # Step 1: Schema-guided extraction
        schema_prompt = self._build_schema_prompt(doc_type)

        # Step 2: Context-aware prompting basato sull'analisi
        context_prompt = self._build_context_prompt(analysis)

        # Step 3: Layout-specific instructions
        layout_prompt = self._build_layout_prompt(analysis['layout_type'])

        # Step 4: Semantic reasoning instructions
        reasoning_prompt = self._build_reasoning_prompt()

        # Combina tutti i prompt
        full_prompt = f"""
{schema_prompt}

{context_prompt}

{layout_prompt}

{reasoning_prompt}

IMPORTANTE:
- Rispondi SOLO con JSON valido, nessun altro testo
- Se un campo non è trovato, usa null
- Date in formato YYYY-MM-DD
- Numeri con punto decimale
- Stringhe senza caratteri speciali problematici

METODO DI LAVORO:
1. Analizza tutto il testo per capire la struttura
2. Identifica sezioni chiave (intestazione, articoli, totali)
3. Estrai i dati seguendo la logica del documento
4. RAGIONA su ogni campo: ha senso logico?
5. Valida semanticamente i dati estratti
6. Restituisci JSON finale
"""

        # Chiamata Claude con contenuto ottimizzato
        if content_data['type'] == 'hybrid' and content_data['content']['images']:
            # Usa vision per documenti con immagini
            result = self._parse_with_vision(full_prompt, content_data['content'])
        else:
            # Usa solo testo per documenti di qualità alta
            result = self._parse_with_text(full_prompt, content_data['content']['text_content'])

        return result

    def _build_schema_prompt(self, doc_type: str) -> str:
        """Costruisce prompt con schema specifico per tipo documento"""

        if doc_type == 'ddt_in':
            return '''
SCHEMA JSON RICHIESTO per DDT IN (documento di trasporto ricevuto):
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
    "note": "eventuali note o condizioni"
}
'''
        else:
            return '''
SCHEMA JSON RICHIESTO per documento generico:
{
    "numero_documento": "numero documento",
    "data_documento": "data in formato YYYY-MM-DD",
    "mittente": "chi invia",
    "destinatario": "chi riceve",
    "totale": 0.00,
    "articoli": [],
    "note": "note varie"
}
'''

    def _build_context_prompt(self, analysis: Dict) -> str:
        """Costruisce prompt contestuale basato sull'analisi"""

        quality = analysis['document_quality']
        is_scanned = analysis['is_scanned']
        suspected_fields = analysis['suspected_fields']

        prompt = f"CONTESTO DOCUMENTO:\\n"
        prompt += f"- Qualità: {'Alta' if quality == 'high' else 'Bassa (possibile scansione)'} \\n"

        if is_scanned:
            prompt += "- DOCUMENTO SCANSIONATO: Fai particolare attenzione a OCR errors\\n"

        if suspected_fields:
            prompt += f"- Campi probabilmente presenti: {', '.join(suspected_fields)}\\n"

        prompt += """
REGOLE SPECIFICHE:
- Il FORNITORE/MITTENTE è chi invia la merce (nella parte alta del documento)
- Il DESTINATARIO è chi riceve la merce (ACG CLIMA SERVICE se è un DDT IN)
- Se vedi "ACG CLIMA SERVICE" come destinazione, NON è il fornitore
- Articoli di solito in tabella al centro del documento
- Totali nella parte bassa
- Date possono essere in formato DD/MM/YYYY o DD-MM-YYYY
"""
        return prompt

    def _build_layout_prompt(self, layout_type: str) -> str:
        """Costruisce prompt specifico per layout documento"""

        if layout_type == 'cambielli':
            return """
LAYOUT SPECIFICO CAMBIELLI:
- Fornitore: sempre "0000000030 - CAMBIELLI SPA"
- Numero offerta: formato "XC/STD/xxxxxxx"
- Oggetto: vicino a parola "riferimento"
- Note: nel fondo del PDF vicino a "NOTE" - cerca condizioni commerciali
"""
        elif layout_type == 'scanned':
            return """
LAYOUT SCANSIONATO:
- Testo potrebbe avere errori OCR
- Cerca pattern numerici anche se il formato non è perfetto
- Date potrebbero essere scritte male (0 vs O, 1 vs l)
- Controlla logica dei valori estratti
"""
        else:
            return """
LAYOUT STANDARD:
- Segui la struttura logica del documento
- Intestazione -> Articoli -> Totali
- Attenzione a tabelle multi-colonna
"""

    def _build_reasoning_prompt(self) -> str:
        """Costruisce prompt per ragionamento semantico sui campi"""
        return """
🧠 RAGIONAMENTO SEMANTICO - VALIDA SEMPRE LA LOGICA:

CAMPO NOTE - USA IL BUON SENSO:
❌ NON sono note: "Firma Per Accettazione", "Importo I.V.A.", "Totale offerta", firme, intestazioni
✅ SONO note: condizioni di pagamento, modalità consegna, validità offerta, clausole contrattuali

Esempi di VERE note:
- "EVENTUALE CONSEGNA AL MARCIAPIEDE SALDO ALLA CONSEGNA SALVO DIVERSI ACCORDI"
- "VALIDA 10 GG DATA OFFERTA - SALVO APPROVAZIONE DELL'AZIENDA"
- "Pagamento a 30 giorni data fattura"
- "Consegna franco magazzino"
- "Prezzi IVA esclusa"

CAMPO FORNITORE - LOGICA:
✅ È il fornitore: chi INVIA la merce, emette il documento, ha P.IVA in alto
❌ NON è il fornitore: "ACG CLIMA SERVICE" (è quasi sempre il destinatario)

CAMPO NUMERO_DDT/OFFERTA - LOGICA:
✅ Formato tipico: numeri, lettere, slash, trattini (es: "2024/001", "XC/STD/123")
❌ NON è numero: date, importi, descrizioni

CAMPO ARTICOLI - RAGIONA:
✅ Devono avere: descrizione prodotto, quantità, prezzo
❌ Ignora: intestazioni tabella, totali, righe vuote

REGOLA D'ORO: Se un dato estratto non ha senso logico nel contesto, cerca altrove!
"""

    def _parse_with_vision(self, prompt: str, content: Dict) -> Dict[str, Any]:
        """Parsing con Claude Vision per documenti con immagini"""
        try:
            # Usa prima immagine disponibile per vision
            if not content['images']:
                return self._parse_with_text(prompt, content['text_content'])

            image_data = content['images'][0]['data']

            message = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        }
                    ]
                }]
            )

            response_text = message.content[0].text.strip()
            return self._parse_claude_response(response_text)

        except Exception as e:
            print(f"❌ Vision parsing failed: {e}")
            # Fallback a parsing testuale
            return self._parse_with_text(prompt, content['text_content'])

    def _parse_with_text(self, prompt: str, text_content: str) -> Dict[str, Any]:
        """Parsing con Claude usando solo testo"""
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
        """Valida risultati e corregge errori comuni"""
        if not parsing_result.get('success'):
            return parsing_result

        data = parsing_result['data']

        # Validazioni specifiche
        self._validate_dates(data)
        self._validate_numbers(data)
        self._validate_required_fields(data, doc_type)

        # Validazione semantica intelligente
        self._validate_semantic_logic(data)

        return {'success': True, 'data': data}

    def _validate_dates(self, data: Dict):
        """Valida e corregge formato date"""
        date_fields = ['data_ddt', 'data_documento', 'data_offerta']

        for field in date_fields:
            if field in data and data[field]:
                date_value = str(data[field])

                # Prova vari formati
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                    try:
                        parsed_date = datetime.strptime(date_value, fmt)
                        data[field] = parsed_date.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue

    def _validate_numbers(self, data: Dict):
        """Valida e corregge formato numeri"""
        number_fields = ['totale_fattura', 'totale', 'prezzo_unitario', 'quantita', 'totale_riga']

        def fix_number(value):
            if value is None or value == '':
                return 0.0
            try:
                # Gestisci virgole come separatori decimali
                str_val = str(value).replace(',', '.')
                return float(str_val)
            except:
                return 0.0

        # Correggi numeri top-level
        for field in number_fields:
            if field in data:
                data[field] = fix_number(data[field])

        # Correggi numeri negli articoli
        if 'articoli' in data and data['articoli']:
            for articolo in data['articoli']:
                for field in number_fields:
                    if field in articolo:
                        articolo[field] = fix_number(articolo[field])

    def _validate_required_fields(self, data: Dict, doc_type: str):
        """Verifica campi obbligatori"""
        required_fields = ['numero_ddt', 'data_ddt', 'fornitore'] if doc_type == 'ddt_in' else []

        for field in required_fields:
            if field not in data or not data[field]:
                print(f"⚠️ Campo obbligatorio mancante: {field}")

    def _validate_semantic_logic(self, data: Dict):
        """Validazione semantica intelligente dei campi estratti"""

        # Validazione NOTE - il campo più problematico
        if 'note' in data and data['note']:
            note_text = str(data['note']).upper()

            # Pattern che NON dovrebbero essere note
            invalid_note_patterns = [
                'FIRMA.*ACCETTAZIONE',
                'IMPORTO.*IVA',
                'TOTALE.*OFFERTA',
                'CLIENTE',
                r'^[A-Z\s]{1,20}$',  # Troppo breve/generico
                'PREVENTIVO',
                'FATTURA',
                'DOCUMENTO'
            ]

            # Pattern che DOVREBBERO essere note
            valid_note_patterns = [
                'EVENTUALE.*CONSEGNA',
                'SALDO.*CONSEGNA',
                'VALIDA.*GG',
                'ACCORDI',
                'APPROVAZIONE',
                'PAGAMENTO',
                'CONSEGNA.*FRANCO',
                'GIORNI.*DATA',
                'PREZZI.*IVA'
            ]

            import re

            # Check se le note sembrano non valide
            is_invalid = any(re.search(pattern, note_text) for pattern in invalid_note_patterns)
            is_valid = any(re.search(pattern, note_text) for pattern in valid_note_patterns)

            if is_invalid and not is_valid:
                print(f"🤔 Note sembrano non valide: '{data['note'][:50]}...'")
                print("🔍 Suggerimento: cerca condizioni commerciali nel documento")
                # Potresti anche azzerare il campo se proprio non ha senso
                # data['note'] = None
            elif is_valid:
                print(f"✅ Note sembrano valide: condizioni commerciali rilevate")

        # Validazione FORNITORE
        if 'fornitore' in data and data['fornitore']:
            fornitore = str(data['fornitore']).upper()
            if 'ACG CLIMA SERVICE' in fornitore:
                print(f"⚠️ Fornitore sospetto: '{data['fornitore']}' (ACG è di solito il destinatario)")

        # Validazione NUMERO_DDT
        if 'numero_ddt' in data and data['numero_ddt']:
            numero = str(data['numero_ddt'])
            # Check se sembra una data invece di un numero
            if re.match(r'^\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}$', numero):
                print(f"⚠️ Numero DDT sembra una data: '{numero}'")

        # Validazione ARTICOLI
        if 'articoli' in data and data['articoli']:
            valid_articles = []
            for art in data['articoli']:
                if isinstance(art, dict):
                    # Check se ha campi sensati
                    has_description = art.get('descrizione') and len(str(art['descrizione'])) > 5
                    has_quantity = art.get('quantita') and float(art['quantita']) > 0

                    if has_description and has_quantity:
                        valid_articles.append(art)
                    else:
                        print(f"🗑️ Articolo scartato (non valido): {art}")

            original_count = len(data['articoli'])
            data['articoli'] = valid_articles
            print(f"📦 Articoli validati: {len(valid_articles)} validi su {original_count} totali")

    def _post_process_data(self, validated_result: Dict, doc_type: str) -> Dict[str, Any]:
        """Post-processing finale dei dati"""
        if not validated_result.get('success'):
            return validated_result

        data = validated_result['data']

        # Aggiungi metadati processing
        data['ai_used'] = 'claude_advanced_v2'
        data['ai_reason'] = 'Advanced Claude multi-step parsing with vision support'
        data['processing_timestamp'] = datetime.now().isoformat()

        return data

    def _calculate_confidence(self, data: Dict) -> float:
        """Calcola score di confidenza del parsing"""
        score = 0.0
        total_checks = 0

        # Check presenza campi critici
        critical_fields = ['numero_ddt', 'data_ddt', 'fornitore']
        for field in critical_fields:
            total_checks += 1
            if field in data and data[field]:
                score += 1

        # Check formato date
        if 'data_ddt' in data and data['data_ddt']:
            total_checks += 1
            try:
                datetime.strptime(data['data_ddt'], '%Y-%m-%d')
                score += 1
            except:
                pass

        # Check presenza articoli
        total_checks += 1
        if 'articoli' in data and data['articoli']:
            score += 1

        return score / total_checks if total_checks > 0 else 0.0

# Funzione di utilità per integrazione facile
def parse_ddt_with_advanced_claude(file_obj, document_type='ddt_in'):
    """
    Funzione wrapper per parsing DDT con sistema evoluto

    Args:
        file_obj: File object del PDF
        document_type: Tipo documento ('ddt_in', 'ddt_out', etc.)

    Returns:
        Dict con risultati parsing
    """
    parser = AdvancedClaudeDDTParser()
    return parser.parse_ddt_advanced(file_obj, document_type)

if __name__ == "__main__":
    print("Advanced Claude DDT Parser - Sistema evoluto per parsing documenti")
    print("Supporta: Vision API, Multi-step reasoning, Schema validation, Error recovery")