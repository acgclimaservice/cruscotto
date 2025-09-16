# Routes per AI Training e Correzioni
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from models import db
from models_parsing_training import ParsingTrainingExample, ParsingRule
from parsing_trainer import ParsingTrainer
import json
import hashlib
from datetime import datetime

training_bp = Blueprint('training', __name__)
trainer = ParsingTrainer()

@training_bp.route('/parsing/correction/<pdf_hash>')
def show_correction_page(pdf_hash):
    """Mostra interfaccia di correzione per un parsing"""
    # Cerca l'ultimo parsing per questo PDF
    # (implementare cache/sessione per dati parsing)

    # Per ora usa dati mock - sostituire con dati reali
    parsing_data = {
        'fornitore': 'FORNITORE ESTRATTO MALE',
        'numero_ddt': 'NUM123',
        'data_ddt': '2025-01-15',
        'totale_fattura': '1500.00',
        'articoli': [
            {'codice': 'ART001', 'descrizione': 'Articolo 1', 'quantita': 2, 'prezzo_unitario': 100.0},
            {'codice': 'ART002', 'descrizione': 'Articolo 2', 'quantita': 1, 'prezzo_unitario': 200.0}
        ]
    }

    # Statistiche learning
    stats = {
        'total_corrections': ParsingTrainingExample.query.count(),
        'suppliers_with_rules': ParsingRule.query.filter_by(attiva=True).count(),
        'accuracy': 0.85  # Calcolare dall'accuratezza reale
    }

    return render_template('parsing-correction.html',
                         parsing_data=parsing_data,
                         pdf_hash=pdf_hash,
                         stats=stats)

@training_bp.route('/parsing/salva-correzione', methods=['POST'])
def salva_correzione():
    """Salva correzione e aggiorna training AI"""
    try:
        data = request.json

        # Estrai dati
        pdf_hash = data.get('pdf_hash')
        parsing_originale = json.loads(data.get('parsing_originale', '{}'))

        # Costruisci parsing corretto
        parsing_corretto = {
            'fornitore': data.get('fornitore_corretto'),
            'numero_ddt': data.get('numero_corretto'),
            'data_ddt': data.get('data_corretta'),
            'totale_fattura': data.get('totale_corretto')
        }

        campo_principale = data.get('campo_principale')
        note_correzione = data.get('note_correzione', '')

        # Salva esempio di training
        training_example = ParsingTrainingExample(
            fornitore_nome=parsing_corretto['fornitore'],
            documento_tipo='offerta',
            pdf_hash=pdf_hash,
            parsing_originale=json.dumps(parsing_originale),
            parsing_corretto=json.dumps(parsing_corretto),
            campo_corretto=campo_principale,
            valore_sbagliato=parsing_originale.get(campo_principale, ''),
            valore_corretto=parsing_corretto.get(campo_principale, ''),
            creato_da='utente_web',  # TODO: Sostituire con utente reale
            note=note_correzione
        )

        db.session.add(training_example)

        # Genera regola automatica
        _genera_regola_da_correzione(training_example)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Correzione salvata per campo {campo_principale}. L\'AI imparerà da questo esempio.'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@training_bp.route('/parsing/feedback-positivo', methods=['POST'])
def feedback_positivo():
    """Registra feedback positivo per parsing corretto"""
    try:
        data = request.json
        pdf_hash = data.get('pdf_hash')
        parsing_data = data.get('parsing_data')

        # Registra feedback positivo (per statistiche)
        # TODO: Implementare tabella feedback positivi

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@training_bp.route('/parsing/training/dashboard')
def training_dashboard():
    """Dashboard per gestire training AI"""

    # Statistiche generali
    total_examples = ParsingTrainingExample.query.count()
    active_rules = ParsingRule.query.filter_by(attiva=True).count()

    # Esempi recenti
    recent_examples = ParsingTrainingExample.query\
        .order_by(ParsingTrainingExample.data_creazione.desc())\
        .limit(10).all()

    # Regole più utilizzate
    top_rules = ParsingRule.query\
        .filter_by(attiva=True)\
        .order_by(ParsingRule.successi.desc())\
        .limit(5).all()

    # Fornitori con più correzioni
    supplier_stats = db.session.query(
        ParsingTrainingExample.fornitore_nome,
        db.func.count(ParsingTrainingExample.id).label('count')
    ).group_by(ParsingTrainingExample.fornitore_nome)\
     .order_by(db.text('count DESC'))\
     .limit(10).all()

    return render_template('training-dashboard.html',
                         stats={
                             'total_examples': total_examples,
                             'active_rules': active_rules,
                             'recent_examples': recent_examples,
                             'top_rules': top_rules,
                             'supplier_stats': supplier_stats
                         })

@training_bp.route('/parsing/rules/<int:rule_id>/toggle', methods=['POST'])
def toggle_rule(rule_id):
    """Attiva/disattiva una regola di parsing"""
    try:
        rule = ParsingRule.query.get_or_404(rule_id)
        rule.attiva = not rule.attiva
        db.session.commit()

        return jsonify({
            'success': True,
            'new_status': rule.attiva,
            'message': f'Regola {"attivata" if rule.attiva else "disattivata"}'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def _genera_regola_da_correzione(example):
    """Genera automaticamente una regola di parsing da una correzione"""

    fornitore_pattern = example.fornitore_nome.upper().replace(' ', '.*').replace('.', '\\.')

    # Costruisci prompt specifico basato sulla correzione
    prompt_aggiuntivo = f"""
🎯 REGOLA APPRESA PER {example.fornitore_nome.upper()}:

Campo '{example.campo_corretto}':
❌ EVITA: "{example.valore_sbagliato}"
✅ CERCA: pattern simile a "{example.valore_corretto}"

💡 Suggerimento: {example.note or 'Prestare attenzione alla posizione di questo campo'}

Data apprendimento: {example.data_creazione.strftime('%Y-%m-%d')}
"""

    # Verifica se esiste già una regola
    regola_esistente = ParsingRule.query.filter_by(
        fornitore_pattern=fornitore_pattern,
        campo_target=example.campo_corretto
    ).first()

    if regola_esistente:
        # Aggiorna regola esistente
        regola_esistente.prompt_aggiuntivo = prompt_aggiuntivo
        regola_esistente.priorita += 1
        print(f"Aggiornata regola esistente per {example.fornitore_nome}")
    else:
        # Crea nuova regola
        nuova_regola = ParsingRule(
            fornitore_pattern=fornitore_pattern,
            documento_tipo='offerta',
            campo_target=example.campo_corretto,
            prompt_aggiuntivo=prompt_aggiuntivo,
            priorita=5,
            attiva=True
        )
        db.session.add(nuova_regola)
        print(f"Creata nuova regola per {example.fornitore_nome}")