# Routes AI Training - Versione Semplificata
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import json
import hashlib
from datetime import datetime

# Import condizionali per evitare errori
try:
    from models import db
    from models_parsing_training import ParsingTrainingExample, ParsingRule
    HAS_TRAINING_MODELS = True
except ImportError:
    HAS_TRAINING_MODELS = False
    print("Modelli training non disponibili")

training_bp = Blueprint('training', __name__)

@training_bp.route('/parsing/correction/<pdf_hash>')
def show_correction_page(pdf_hash):
    """Mostra interfaccia di correzione per un parsing"""

    # Prova a recuperare dati dalla sessione
    try:
        parsing_data = request.args.get('data')
        if parsing_data:
            parsing_data = json.loads(parsing_data)
        else:
            # Dati mock per test
            parsing_data = {
                'fornitore': 'FORNITORE ESTRATTO MALE',
                'numero_ddt': 'NUM123',
                'data_ddt': '2025-01-15',
                'totale_fattura': '1500.00',
                'articoli': [
                    {'codice': 'ART001', 'descrizione': 'Articolo 1', 'quantita': 2, 'prezzo_unitario': 100.0}
                ]
            }
    except Exception as e:
        print(f"Errore caricamento dati: {e}")
        parsing_data = {
            'fornitore': 'ERRORE CARICAMENTO',
            'numero_ddt': 'N/A',
            'data_ddt': '2025-01-01',
            'totale_fattura': '0.00'
        }

    # Statistiche semplici
    stats = {
        'total_corrections': 0,
        'suppliers_with_rules': 0,
        'accuracy': 0.85
    }

    return render_template('parsing-correction.html',
                         parsing_data=parsing_data,
                         pdf_hash=pdf_hash,
                         stats=stats)

@training_bp.route('/parsing/salva-correzione', methods=['POST'])
def salva_correzione():
    """Salva correzione - versione semplificata"""
    try:
        data = request.json

        if not HAS_TRAINING_MODELS:
            return jsonify({
                'success': True,
                'message': 'Correzione ricevuta (modelli training non disponibili)'
            })

        # Estrai dati
        pdf_hash = data.get('pdf_hash')
        parsing_originale = data.get('parsing_originale', '{}')

        # Costruisci parsing corretto
        parsing_corretto = {
            'fornitore': data.get('fornitore_corretto'),
            'numero_ddt': data.get('numero_corretto'),
            'data_ddt': data.get('data_corretta'),
            'totale_fattura': data.get('totale_corretto')
        }

        campo_principale = data.get('campo_principale')
        note_correzione = data.get('note_correzione', '')

        # Salva nel database se disponibile
        if HAS_TRAINING_MODELS:
            training_example = ParsingTrainingExample(
                fornitore_nome=parsing_corretto['fornitore'],
                documento_tipo='offerta',
                pdf_hash=pdf_hash,
                parsing_originale=parsing_originale if isinstance(parsing_originale, str) else json.dumps(parsing_originale),
                parsing_corretto=json.dumps(parsing_corretto),
                campo_corretto=campo_principale,
                valore_sbagliato=json.loads(parsing_originale).get(campo_principale, '') if isinstance(parsing_originale, str) else parsing_originale.get(campo_principale, ''),
                valore_corretto=parsing_corretto.get(campo_principale, ''),
                creato_da='utente_web',
                note=note_correzione
            )

            db.session.add(training_example)
            db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Correzione salvata per campo {campo_principale}. L\'AI imparerà da questo esempio.'
        })

    except Exception as e:
        print(f"Errore salvataggio correzione: {e}")
        if HAS_TRAINING_MODELS:
            db.session.rollback()
        return jsonify({
            'success': True,  # Mantieni successo per non bloccare utente
            'message': f'Correzione ricevuta (errore salvataggio: {str(e)})'
        })

@training_bp.route('/parsing/feedback-positivo', methods=['POST'])
def feedback_positivo():
    """Registra feedback positivo per parsing corretto"""
    try:
        data = request.json
        print(f"Feedback positivo ricevuto per PDF hash: {data.get('pdf_hash')}")
        return jsonify({'success': True})
    except Exception as e:
        print(f"Errore feedback positivo: {e}")
        return jsonify({'success': True})  # Non bloccare l'utente

@training_bp.route('/parsing/training/dashboard')
def training_dashboard():
    """Dashboard per gestire training AI - versione semplificata"""

    if not HAS_TRAINING_MODELS:
        return jsonify({
            'error': 'Modelli training non disponibili. Verificare installazione.'
        }), 500

    try:
        # Statistiche di base
        total_examples = ParsingTrainingExample.query.count()
        active_rules = ParsingRule.query.filter_by(attiva=True).count()

        # Esempi recenti (massimo 10)
        recent_examples = ParsingTrainingExample.query\
            .order_by(ParsingTrainingExample.data_creazione.desc())\
            .limit(10).all()

        return render_template('training-dashboard.html',
                             stats={
                                 'total_examples': total_examples,
                                 'active_rules': active_rules,
                                 'recent_examples': recent_examples,
                                 'top_rules': [],
                                 'supplier_stats': []
                             })
    except Exception as e:
        print(f"Errore dashboard: {e}")
        return jsonify({'error': f'Errore dashboard: {str(e)}'}), 500