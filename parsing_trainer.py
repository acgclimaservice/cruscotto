# Sistema di Training per AI Parsing - Main Logic
import json
import hashlib
from models_parsing_training import ParsingTrainingExample, ParsingRule, db
from multi_ai_pdf_parser import MultiAIPDFParser

class ParsingTrainer:
    """Sistema per migliorare l'AI parsing tramite feedback utente"""

    def __init__(self):
        self.parser = MultiAIPDFParser()

    def salva_correzione(self, pdf_file, parsing_originale, parsing_corretto,
                        campo_corretto, fornitore_nome, creato_da):
        """Salva una correzione manuale per training futuro"""

        # Calcola hash del PDF
        pdf_file.seek(0)
        pdf_content = pdf_file.read()
        pdf_hash = hashlib.md5(pdf_content).hexdigest()
        pdf_file.seek(0)

        # Crea esempio di training
        training_example = ParsingTrainingExample(
            fornitore_nome=fornitore_nome,
            documento_tipo='offerta',
            pdf_hash=pdf_hash,
            parsing_originale=json.dumps(parsing_originale),
            parsing_corretto=json.dumps(parsing_corretto),
            campo_corretto=campo_corretto,
            valore_sbagliato=parsing_originale.get(campo_corretto, ''),
            valore_corretto=parsing_corretto.get(campo_corretto, ''),
            creato_da=creato_da
        )

        db.session.add(training_example)

        # Auto-genera regola se possibile
        self._genera_regola_automatica(training_example)

        db.session.commit()
        print(f"Correzione salvata per {fornitore_nome} - Campo: {campo_corretto}")

    def _genera_regola_automatica(self, example):
        """Genera automaticamente una regola di parsing da un esempio"""

        # Analizza il pattern del fornitore
        fornitore_pattern = example.fornitore_nome.upper().replace(' ', '.*')

        # Crea prompt specifico per questo tipo di errore
        prompt_aggiuntivo = f"""
CORREZIONE SPECIFICA PER {example.fornitore_nome.upper()}:
- Campo '{example.campo_corretto}':
  ❌ NON usare: {example.valore_sbagliato}
  ✅ CERCA invece: pattern simile a '{example.valore_corretto}'
- Questo fornitore ha specificità nel campo {example.campo_corretto}
"""

        # Verifica se esiste già una regola per questo fornitore/campo
        regola_esistente = ParsingRule.query.filter_by(
            fornitore_pattern=fornitore_pattern,
            campo_target=example.campo_corretto
        ).first()

        if regola_esistente:
            # Aggiorna la regola esistente
            regola_esistente.prompt_aggiuntivo += f"\n{prompt_aggiuntivo}"
            regola_esistente.priorita += 1
        else:
            # Crea nuova regola
            nuova_regola = ParsingRule(
                fornitore_pattern=fornitore_pattern,
                documento_tipo='offerta',
                campo_target=example.campo_corretto,
                prompt_aggiuntivo=prompt_aggiuntivo,
                priorita=5
            )
            db.session.add(nuova_regola)

    def get_prompt_enhancer(self, fornitore_nome):
        """Ottieni prompt aggiuntivi basati su regole apprese"""

        if not fornitore_nome:
            return ""

        # Cerca regole applicabili
        regole = ParsingRule.query.filter(
            ParsingRule.attiva == True,
            ParsingRule.fornitore_pattern.ilike(f'%{fornitore_nome.upper()}%')
        ).order_by(ParsingRule.priorita.desc()).all()

        prompt_extra = ""
        for regola in regole[:3]:  # Max 3 regole per non sovraccaricare
            if regola.prompt_aggiuntivo:
                prompt_extra += f"\n{regola.prompt_aggiuntivo}"

        return prompt_extra

    def parse_with_learning(self, pdf_file, fornitore_nome_hint=None):
        """Parse con utilizzo delle regole apprese"""

        # Parse normale
        result = self.parser.parse_ddt_with_ai(pdf_file)

        if result.get('success') and fornitore_nome_hint:
            # Applica correzioni specifiche apprese
            enhanced_prompt = self.get_prompt_enhancer(fornitore_nome_hint)

            if enhanced_prompt:
                print(f"Applicando regole apprese per {fornitore_nome_hint}")
                # Re-parse con prompt migliorato
                original_prompt = self.parser.SYSTEM_PROMPT
                self.parser.SYSTEM_PROMPT += enhanced_prompt

                enhanced_result = self.parser.parse_ddt_with_ai(pdf_file)

                # Ripristina prompt originale
                self.parser.SYSTEM_PROMPT = original_prompt

                if enhanced_result.get('success'):
                    enhanced_result['learning_applied'] = True
                    return enhanced_result

        return result

    def suggerisci_correzioni_comuni(self, fornitore_nome):
        """Suggerisce correzioni comuni per un fornitore"""

        examples = ParsingTrainingExample.query.filter_by(
            fornitore_nome=fornitore_nome
        ).limit(5).all()

        correzioni = {}
        for ex in examples:
            campo = ex.campo_corretto
            if campo not in correzioni:
                correzioni[campo] = []
            correzioni[campo].append({
                'valore_sbagliato': ex.valore_sbagliato,
                'valore_corretto': ex.valore_corretto,
                'note': ex.note
            })

        return correzioni