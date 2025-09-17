# Enhanced AI Parser con Regole Specifiche Fornitori
import os
import json
import hashlib
import re
from multi_ai_pdf_parser import MultiAIPDFParser

class EnhancedAIParser(MultiAIPDFParser):
    """Parser AI con regole specifiche per fornitori"""

    def __init__(self):
        super().__init__()

    def detect_supplier_from_text(self, pdf_text):
        """Rileva il fornitore dal testo"""
        if not pdf_text:
            return None

        # Lista di fornitori con regole specifiche
        known_suppliers = [
            'CAMBIELLI', 'RIELLO', 'SIME', 'IMMERGAS',
            'BERETTA', 'FERROLI', 'VAILLANT', 'JUNKERS'
        ]

        text_upper = pdf_text.upper()
        for supplier in known_suppliers:
            if supplier in text_upper:
                return supplier

        return None

    def extract_cambielli_oggetto(self, pdf_text):
        """Estrae oggetto ordine CAMBIELLI dalla zona vicino a 'riferimento'"""
        if not pdf_text:
            return None

        text = pdf_text.upper()

        # Pattern per trovare testo vicino a "RIFERIMENTO"
        riferimento_patterns = [
            r'RIFERIMENTO[:\s-]*([A-Z\s\w\d\.,\-/()]{10,80})',
            r'RIF[:\s.-]*([A-Z\s\w\d\.,\-/()]{10,80})',
            r'RIFERIMENTO[:\s]*(.+?)(?=\n|OGGETTO|DESCRIZIONE|$)',
            r'VS[:\s]*RIF[:\s]*([A-Z\s\w\d\.,\-/()]{10,80})'
        ]

        for pattern in riferimento_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                oggetto = match.strip()

                # Pulisci il testo estratto
                oggetto = re.sub(r'^[:\s\-\.]+', '', oggetto)  # Rimuovi caratteri iniziali
                oggetto = re.sub(r'[:\s\-\.]+$', '', oggetto)  # Rimuovi caratteri finali

                # Verifica che sia un oggetto valido (contiene parole significative)
                if any(keyword in oggetto.upper() for keyword in [
                    'CONDOMINIO', 'RSA', 'RESIDENZA', 'CASA', 'VILLA', 'PALAZZO',
                    'CENTRO', 'ISTITUTO', 'OSPEDALE', 'SCUOLA', 'UFFICIO'
                ]) and len(oggetto) > 5:
                    print(f"🔍 Oggetto CAMBIELLI trovato con pattern: {pattern}")
                    return oggetto.title()  # Capitalizza per estetica

        # Fallback: cerca pattern più generici
        fallback_patterns = [
            r'(?:LAVORI|FORNITURA|INSTALLAZIONE)[:\s]*([A-Z\s\w\d\.,\-/()]{15,60})',
            r'(?:PRESSO|PER)[:\s]*([A-Z\s\w\d\.,\-/()]{15,60})'
        ]

        for pattern in fallback_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                oggetto = match.strip()
                if len(oggetto) > 10:
                    print(f"🔍 Oggetto CAMBIELLI trovato (fallback): {pattern}")
                    return oggetto.title()

        print("⚠️ Oggetto ordine CAMBIELLI non trovato vicino a 'riferimento'")
        return None

    def extract_cambielli_note(self, pdf_text):
        """Estrae note CAMBIELLI dal fondo del PDF vicino alla parola 'note'"""
        if not pdf_text:
            return None

        import re
        text = pdf_text.upper()

        # Pattern per trovare testo vicino a "NOTE" (varianti)
        note_patterns = [
            r'NOTE[:\s-]*([A-Z\s\w\d\.,\-/()%]{20,200})',
            r'NOTE[:\s]*(.+?)(?=\n\n|$)',
            r'EVENTUALE[:\s]*(.+?)(?=\n\n|$)',
            r'(?:SALDO|CONSEGNA|VALIDA)[:\s]*(.+?)(?=\n\n|$)'
        ]

        for pattern in note_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for match in matches:
                note = match.strip()

                # Pulisci il testo estratto
                note = re.sub(r'^[:\s\-\.]+', '', note)  # Rimuovi caratteri iniziali
                note = re.sub(r'[:\s\-\.]+$', '', note)  # Rimuovi caratteri finali

                # Verifica che contenga parole chiave tipiche delle note CAMBIELLI
                if any(keyword in note.upper() for keyword in [
                    'EVENTUALE', 'CONSEGNA', 'SALDO', 'MARCIAPIEDE', 'VALIDA',
                    'OFFERTA', 'ACCORDI', 'APPROVAZIONE', 'AZIENDA'
                ]) and len(note) > 15:
                    print(f"📝 Note CAMBIELLI trovate con pattern: {pattern}")
                    return note.title()  # Capitalizza per estetica

        # Cerca nel fondo del documento (ultime righe)
        lines = pdf_text.split('\n')
        bottom_text = '\n'.join(lines[-10:]).upper()  # Ultime 10 righe

        general_note_pattern = r'([A-Z\s\w\d\.,\-/()%]{30,150}(?:SALDO|CONSEGNA|VALIDA|ACCORDI)[A-Z\s\w\d\.,\-/()%]{0,100})'
        matches = re.findall(general_note_pattern, bottom_text, re.IGNORECASE)

        for match in matches:
            note = match.strip()
            if len(note) > 20:
                print(f"📝 Note CAMBIELLI trovate nel fondo documento")
                return note.title()

        print("⚠️ Note CAMBIELLI non trovate nel documento")
        return None

    def normalize_supplier_data(self, parsed_data, pdf_text=None):
        """Normalizza i dati fornitori secondo regole specifiche"""
        if not parsed_data or 'fornitore' not in parsed_data:
            return parsed_data

        fornitore_raw = str(parsed_data['fornitore']).upper()

        # Regola CAMBIELLI: se contiene "CAMBIELLI" sostituisci sempre
        if 'CAMBIELLI' in fornitore_raw:
            parsed_data['fornitore'] = '0000000030 - CAMBIELLI SPA'
            print(f"🏢 Fornitore normalizzato: CAMBIELLI -> {parsed_data['fornitore']}")

            # Per CAMBIELLI: cerca formato numero offerta XC/STD/xxxxxxx
            cambielli_pattern = r'XC/STD/\d+'

            # Prima cerca nel numero già estratto
            numero_offerta = parsed_data.get('numero_offerta') or parsed_data.get('numero_ddt', '')
            match = re.search(cambielli_pattern, str(numero_offerta))

            # Se non trovato, cerca nel testo completo del PDF
            if not match and pdf_text:
                match = re.search(cambielli_pattern, pdf_text)

            if match:
                numero_corretto = match.group()
                if 'numero_offerta' in parsed_data:
                    parsed_data['numero_offerta'] = numero_corretto
                if 'numero_ddt' in parsed_data:
                    parsed_data['numero_ddt'] = numero_corretto
                print(f"📄 Numero offerta CAMBIELLI normalizzato: {numero_corretto}")
            else:
                print("⚠️ Formato XC/STD/xxxxxxx non trovato per CAMBIELLI")

            # Per CAMBIELLI: estrai oggetto ordine vicino a "riferimento"
            if pdf_text:
                oggetto_ordine = self.extract_cambielli_oggetto(pdf_text)
                if oggetto_ordine:
                    # Aggiungi ai dati estratti (il campo può variare tra DDT e ordini)
                    if 'oggetto' in parsed_data:
                        parsed_data['oggetto'] = oggetto_ordine
                    elif 'descrizione' in parsed_data:
                        parsed_data['descrizione'] = oggetto_ordine
                    elif 'note' in parsed_data:
                        parsed_data['note'] = oggetto_ordine
                    else:
                        # Crea campo oggetto se non esiste
                        parsed_data['oggetto_ordine'] = oggetto_ordine
                    print(f"🏠 Oggetto ordine CAMBIELLI estratto: {oggetto_ordine}")

            # Per CAMBIELLI: estrai note dal fondo del documento
            if pdf_text:
                note_cambielli = self.extract_cambielli_note(pdf_text)
                if note_cambielli:
                    # Se esistono già note, aggiungi quelle di CAMBIELLI
                    existing_notes = parsed_data.get('note', '')
                    if existing_notes:
                        parsed_data['note'] = f"{existing_notes}\n\nNote fornitore: {note_cambielli}"
                    else:
                        parsed_data['note'] = note_cambielli
                    print(f"📝 Note CAMBIELLI aggiunte: {note_cambielli[:50]}...")

        # Qui puoi aggiungere altre regole di normalizzazione per altri fornitori
        # elif 'RIELLO' in fornitore_raw:
        #     parsed_data['fornitore'] = '0000000031 - RIELLO SPA'

        return parsed_data

    def get_supplier_specific_prompt(self, pdf_text):
        """Aggiungi regole specifiche al prompt basate sul fornitore rilevato"""
        supplier = self.detect_supplier_from_text(pdf_text)

        base_rules = """

🏢 REGOLE SPECIFICHE FORNITORI:"""

        if supplier == 'CAMBIELLI':
            return base_rules + """
- Per CAMBIELLI: fornitore = "0000000030 - CAMBIELLI SPA"
- Per CAMBIELLI: numero offerta formato "XC/STD/xxxxxxx"
- Per CAMBIELLI: oggetto ordine vicino a parola "riferimento" (condominio/RSA/cliente)
- Per CAMBIELLI: note sempre nel fondo del PDF vicino a "NOTE" (consegna/saldo/validità)
"""

        return ""

    def parse_ddt_with_claude(self, file_obj):
        """Parser Claude migliorato con regole specifiche"""
        print(f"🔧 Enhanced Claude: Parsing con regole specifiche fornitori")

        if not self.claude_client:
            return {'success': False, 'error': 'Claude non disponibile'}

        try:
            # Estrai testo dal PDF
            file_obj.seek(0)
            pdf_text = self._extract_pdf_text(file_obj)

            if not pdf_text or len(pdf_text.strip()) < 10:
                return {'success': False, 'error': 'Impossibile estrarre testo dal PDF'}

            # Prompt base standard
            base_prompt = """Analizza questo documento PDF e estrai i dati in formato JSON.

FORMATO JSON RICHIESTO:
{
    "numero_ddt": "numero del documento",
    "data_ddt": "data in formato YYYY-MM-DD",
    "fornitore": "nome fornitore/mittente",
    "destinazione": "nome destinatario",
    "totale_fattura": 0.00,
    "articoli": [
        {
            "codice": "codice articolo",
            "descrizione": "descrizione prodotto",
            "quantita": 0.0,
            "prezzo_unitario": 0.00,
            "totale_riga": 0.00
        }
    ]
}

IMPORTANTE:
- Il FORNITORE è chi emette il documento (mittente)
- Il DESTINATARIO è chi riceve la merce
- Se vedi "ACG CLIMA SERVICE" come destinazione, NON è il fornitore
- Quantità come numero puro, prezzi come decimali"""

            # Aggiungi regole specifiche per fornitori
            enhanced_prompt = base_prompt + self.get_supplier_specific_prompt(pdf_text)

            # Parsing con Claude
            message = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": f"{enhanced_prompt}\n\nTESTO DEL DOCUMENTO:\n{pdf_text[:8000]}"
                }]
            )

            content = message.content[0].text.strip()
            print(f"🔍 Claude Response: {content[:200]}...")

            # Pulisci la risposta da markdown
            content = content.replace('```json', '').replace('```', '').strip()

            # Cerca il JSON se non inizia con {
            if not content.startswith('{'):
                json_start = content.find('{')
                if json_start > -1:
                    content = content[json_start:]

            if not content:
                raise ValueError("Risposta vuota da Claude")

            parsed_data = json.loads(content)

            # Applica normalizzazione fornitori
            parsed_data = self.normalize_supplier_data(parsed_data, pdf_text)

            parsed_data['ai_used'] = 'claude_enhanced'
            parsed_data['ai_reason'] = 'Claude AI con regole specifiche fornitori'

            return {'success': True, 'data': parsed_data}

        except Exception as e:
            print(f"❌ Errore Enhanced Claude: {e}")
            # Fallback al parser normale
            print("🔄 Fallback al parser normale...")
            return super().parse_ddt_with_claude(file_obj)

    def parse_ordine_pdf(self, file_path, ai_service='claude'):
        """Parser ordini con regole specifiche"""
        print(f"🔧 Enhanced Ordine: Parsing con regole specifiche per {ai_service}")

        if ai_service == 'claude':
            return self.parse_ordine_with_claude_enhanced(file_path)
        else:
            # Fallback al parser normale per altri AI
            return super().parse_ordine_pdf(file_path, ai_service)

    def parse_ordine_with_claude_enhanced(self, file_path):
        """Parse ordine con Claude + regole specifiche"""
        if not self.claude_client:
            return {'success': False, 'error': 'Claude non disponibile'}

        try:
            # Leggi il PDF file
            with open(file_path, 'rb') as file_obj:
                pdf_text = self._extract_pdf_text(file_obj)

                if not pdf_text or len(pdf_text.strip()) < 10:
                    return {'success': False, 'error': 'Impossibile estrarre testo dal PDF'}

                # Prompt base per ordini
                base_prompt = """Analizza questa offerta fornitore e estrai i dati in formato JSON.

FORMATO JSON RICHIESTO:
{
    "fornitore": "nome fornitore/mittente",
    "numero_offerta": "numero offerta",
    "data_offerta": "data in formato YYYY-MM-DD",
    "validita_offerta": "data scadenza in formato YYYY-MM-DD",
    "totale": 0.00,
    "articoli": [
        {
            "codice": "codice articolo (OBBLIGATORIO - estrai sempre)",
            "descrizione": "descrizione prodotto",
            "quantita": 0.0,
            "prezzo_unitario": 0.00,
            "totale_riga": 0.00
        }
    ]
}

IMPORTANTE:
- Il FORNITORE è chi emette l'offerta (mittente)
- NUMERO_OFFERTA è il numero di riferimento dell'offerta
- Quantità come numero puro, prezzi come decimali
- CODICE ARTICOLO: estrai SEMPRE il codice/SKU/parte per ogni articolo (anche se alfanumerico)
- Se non trovi codice esplicito, usa riferimento fornitore o marca+modello"""

                # Aggiungi regole specifiche
                enhanced_prompt = base_prompt + self.get_supplier_specific_prompt(pdf_text)

                # Parsing con Claude
                message = self.claude_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=4000,
                    messages=[{
                        "role": "user",
                        "content": f"{enhanced_prompt}\n\nTESTO DELL'OFFERTA:\n{pdf_text[:8000]}"
                    }]
                )

                content = message.content[0].text.strip()
                content = content.replace('```json', '').replace('```', '').strip()

                # Cerca il JSON se necessario
                if not content.startswith('{'):
                    json_start = content.find('{')
                    if json_start > -1:
                        content = content[json_start:]

                if not content:
                    raise ValueError("Risposta vuota da Claude")

                parsed_data = json.loads(content)

                # Applica normalizzazione fornitori
                parsed_data = self.normalize_supplier_data(parsed_data, pdf_text)

                parsed_data['ai_used'] = 'claude_enhanced_ordine'
                parsed_data['ai_reason'] = 'Claude AI per ordini con regole specifiche'

                return {'success': True, 'data': parsed_data}

        except Exception as e:
            print(f"❌ Errore Enhanced Claude Ordine: {e}")
            print("🔄 Fallback al parser normale per ordini...")
            # Fallback al parser normale della classe parent
            return super().parse_ordine_with_claude(file_path)