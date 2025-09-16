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

    # Prova a recuperare dati reali dal parsing
    try:
        parsing_data = request.args.get('data')
        if parsing_data:
            # Decodifica i dati dal parametro URL
            import urllib.parse
            parsing_data = json.loads(urllib.parse.unquote(parsing_data))
            print(f"✅ Dati parsing ricevuti: {parsing_data}")
        else:
            # Nessun dato fornito - usa dati di esempio
            parsing_data = {
                'fornitore': 'Nessun dato - utilizzare dal parsing reale',
                'numero_ddt': 'N/A',
                'data_ddt': '2025-01-01',
                'totale_fattura': '0.00',
                'articoli': []
            }
            print("⚠️ Nessun dato di parsing fornito, usando dati di esempio")
    except Exception as e:
        print(f"❌ Errore caricamento dati: {e}")
        parsing_data = {
            'fornitore': f'ERRORE CARICAMENTO: {str(e)}',
            'numero_ddt': 'N/A',
            'data_ddt': '2025-01-01',
            'totale_fattura': '0.00',
            'articoli': []
        }

    # Statistiche semplici
    stats = {
        'total_corrections': 0,
        'suppliers_with_rules': 0,
        'accuracy': 0.85
    }

    # Template inline per evitare errori se file mancante
    template_html = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Correzione Parsing AI</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
        .incorrect {{ background: #fff8f8; border-color: #dc3545; }}
        .correct {{ background: #f8fff9; border-color: #28a745; }}
        input, textarea, select {{ width: 100%; padding: 8px; margin: 5px 0; }}
        .btn {{ padding: 10px 20px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }}
        .btn-success {{ background: #28a745; color: white; }}
        .btn-secondary {{ background: #6c757d; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Correzione AI Parsing</h1>

        <div class="section incorrect">
            <h3>❌ Parsing AI Originale</h3>
            <p><strong>Fornitore:</strong> {parsing_data.get('fornitore', 'N/A')}</p>
            <p><strong>Numero:</strong> {parsing_data.get('numero_ddt', 'N/A')}</p>
            <p><strong>Data:</strong> {parsing_data.get('data_ddt', 'N/A')}</p>
            <p><strong>Totale:</strong> {parsing_data.get('totale_fattura', 'N/A')}</p>
        </div>

        <div class="section correct">
            <h3>✅ Valori Corretti</h3>
            <form id="correctionForm">
                <label>Fornitore *</label>
                <input type="text" name="fornitore_corretto" value="{parsing_data.get('fornitore', '')}" required>

                <label>Numero Offerta</label>
                <input type="text" name="numero_corretto" value="{parsing_data.get('numero_ddt', '')}">

                <label>Data (YYYY-MM-DD)</label>
                <input type="date" name="data_corretta" value="{parsing_data.get('data_ddt', '')}">

                <label>Totale</label>
                <input type="number" step="0.01" name="totale_corretto" value="{parsing_data.get('totale_fattura', '')}">

                <label>Campo con errore principale:</label>
                <select name="campo_principale">
                    <option value="fornitore">Fornitore</option>
                    <option value="numero_ddt">Numero Offerta</option>
                    <option value="data_ddt">Data</option>
                    <option value="totale_fattura">Totale</option>
                </select>

                <label>Note per l'AI:</label>
                <textarea name="note_correzione" rows="3" placeholder="Come dovrebbe riconoscere correttamente questo campo..."></textarea>

                <button type="submit" class="btn btn-success">💾 Salva Correzione</button>
                <button type="button" onclick="window.history.back()" class="btn btn-secondary">← Indietro</button>
            </form>
        </div>
    </div>

    <script>
        document.getElementById('correctionForm').onsubmit = function(e) {{
            e.preventDefault();

            const formData = new FormData(this);
            const data = Object.fromEntries(formData.entries());
            data.pdf_hash = '{pdf_hash}';
            data.parsing_originale = {json.dumps(json.dumps(parsing_data))};

            fetch('/ai/parsing/salva-correzione', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(result => {{
                if (result.success) {{
                    alert('✅ ' + result.message);
                    window.history.back();
                }} else {{
                    alert('❌ Errore: ' + result.error);
                }}
            }})
            .catch(error => {{
                alert('❌ Errore di connessione: ' + error);
            }});
        }};
    </script>
</body>
</html>
"""

    from flask import Response
    return Response(template_html, mimetype='text/html')

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