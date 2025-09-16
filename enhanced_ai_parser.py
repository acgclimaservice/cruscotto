# Enhanced AI Parser con Sistema di Apprendimento
import os
import json
import hashlib
from multi_ai_pdf_parser import MultiAIPDFParser

class EnhancedAIParser(MultiAIPDFParser):
    """Parser AI che applica le regole apprese dalle correzioni"""

    def __init__(self):
        super().__init__()
        self.learning_enabled = True

    def get_learned_rules_for_supplier(self, supplier_name):
        """Ottieni regole apprese per un fornitore specifico"""
        if not supplier_name or not self.learning_enabled:
            return ""

        try:
            # Import condizionale per evitare errori
            from models import db
            from models_parsing_training import ParsingRule

            # Cerca regole attive per questo fornitore
            rules = ParsingRule.query.filter(
                ParsingRule.attiva == True,
                ParsingRule.fornitore_pattern.ilike(f'%{supplier_name.upper()}%')
            ).order_by(ParsingRule.priorita.desc()).limit(3).all()

            if not rules:
                return ""

            enhanced_prompt = "\n\n🎯 REGOLE APPRESE DA CORREZIONI PRECEDENTI:\n"
            for rule in rules:
                if rule.prompt_aggiuntivo:
                    enhanced_prompt += f"\n{rule.prompt_aggiuntivo}\n"

            enhanced_prompt += "\n⚠️ IMPORTANTE: Applica queste regole specifiche apprese dalle correzioni dell'utente!\n"
            return enhanced_prompt

        except ImportError:
            # Modelli training non disponibili
            return ""
        except Exception as e:
            print(f"Errore caricamento regole: {e}")
            return ""

    def detect_supplier_from_text(self, pdf_text):
        """Rileva il fornitore dal testo per applicare regole specifiche"""
        if not pdf_text:
            return None

        # Lista di fornitori comuni (puoi espandere)
        known_suppliers = [
            'CAMBIELLI', 'RIELLO', 'SIME', 'IMMERGAS',
            'BERETTA', 'FERROLI', 'VAILLANT', 'JUNKERS'
        ]

        text_upper = pdf_text.upper()
        for supplier in known_suppliers:
            if supplier in text_upper:
                return supplier

        return None

    def enhance_prompt_with_learning(self, base_prompt, pdf_text):
        """Migliora il prompt base con le regole apprese"""
        if not self.learning_enabled:
            return base_prompt

        # Rileva fornitore dal testo
        detected_supplier = self.detect_supplier_from_text(pdf_text)

        if detected_supplier:
            print(f"🧠 AI Learning: Rilevato fornitore {detected_supplier}, applicando regole apprese...")
            learned_rules = self.get_learned_rules_for_supplier(detected_supplier)

            if learned_rules:
                enhanced_prompt = base_prompt + learned_rules
                print(f"🎯 Prompt migliorato con {len(learned_rules)} caratteri di regole specifiche")
                return enhanced_prompt

        return base_prompt

    def parse_ddt_with_claude(self, file_obj):
        """Override del parser Claude con apprendimento"""
        print(f"🧠 Enhanced Claude: Inizio parsing con AI Learning")

        if not self.claude_client:
            return {'success': False, 'error': 'Claude non disponibile'}

        try:
            # Estrai testo dal PDF
            file_obj.seek(0)
            pdf_text = self._extract_pdf_text(file_obj)

            if not pdf_text or len(pdf_text.strip()) < 10:
                return {'success': False, 'error': 'Impossibile estrarre testo dal PDF'}

            # Prompt base (usa quello esistente)
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

            # Migliora prompt con regole apprese
            enhanced_prompt = self.enhance_prompt_with_learning(base_prompt, pdf_text)

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
            content = content.replace('```json', '').replace('```', '').strip()

            parsed_data = json.loads(content)
            parsed_data['ai_used'] = 'claude_enhanced'
            parsed_data['ai_reason'] = 'Claude AI Enhanced con regole apprese'

            return {'success': True, 'data': parsed_data}

        except Exception as e:
            print(f"Errore Enhanced Claude: {e}")
            return {'success': False, 'error': str(e)}

    def parse_ddt_with_ai(self, file_obj, preferred_ai='claude'):
        """Override del parser principale con apprendimento"""
        print(f"🧠 ENHANCED PARSING: AI preferita = {preferred_ai.upper()}")

        if preferred_ai == 'claude':
            result = self.parse_ddt_with_claude(file_obj)  # Usa versione enhanced
            if result['success']:
                print("✅ Enhanced Claude parsing completato")
                return result

            print(f"❌ Enhanced Claude fallito: {result.get('error')}")

        # Fallback alla versione normale se enhanced fallisce
        print("🔄 Fallback al parser normale...")
        return super().parse_ddt_with_ai(file_obj, preferred_ai)

    def record_parsing_success(self, supplier_name, parsed_data):
        """Registra un parsing di successo per statistiche"""
        try:
            from models import db
            from models_parsing_training import ParsingRule

            if supplier_name:
                # Incrementa successi per regole di questo fornitore
                rules = ParsingRule.query.filter(
                    ParsingRule.fornitore_pattern.ilike(f'%{supplier_name.upper()}%'),
                    ParsingRule.attiva == True
                ).all()

                for rule in rules:
                    rule.successi += 1

                db.session.commit()
                print(f"📊 Registrato successo parsing per {supplier_name}")

        except Exception as e:
            print(f"Errore registrazione successo: {e}")

    def set_learning_enabled(self, enabled=True):
        """Abilita/disabilita il sistema di apprendimento"""
        self.learning_enabled = enabled
        print(f"🧠 AI Learning: {'ABILITATO' if enabled else 'DISABILITATO'}")