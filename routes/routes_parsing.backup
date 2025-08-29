# routes_parsing.py
from flask import Blueprint, request, jsonify, render_template
from models import db, ConfigurazioneSistema
from multi_ai_pdf_parser import MultiAIPDFParser
from pdf_highlight_parser import PDFHighlightParser
import json
from datetime import datetime

parsing_bp = Blueprint('parsing', __name__)

def get_parser():
    """Ottiene istanza parser lazy-loaded"""
    if not hasattr(get_parser, '_parser'):
        get_parser._parser = MultiAIPDFParser()
    return get_parser._parser

def get_highlight_parser():
    """Ottiene istanza highlight parser lazy-loaded"""
    if not hasattr(get_highlight_parser, '_parser'):
        get_highlight_parser._parser = PDFHighlightParser()
    return get_highlight_parser._parser

@parsing_bp.route('/parse-pdf', methods=['POST'])
def parse_pdf():
    """API per parsing PDF con Multi-AI (Claude + Gemini)"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nessun file caricato'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nessun file selezionato'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Solo file PDF sono supportati'}), 400
    
    try:
        # Estrae testo dal PDF
        parser = get_parser()
        pdf_text = parser.extract_text_from_pdf(file)
        if not pdf_text:
            return jsonify({'error': 'Impossibile estrarre testo dal PDF'}), 400
        
        # Recupera dati di apprendimento
        learning_data = parser.get_learning_data()
        
        # Parsing con Multi-AI + learning data
        preferred_ai = request.form.get('preferred_ai', 'dual')  # dual, claude, gemini
        parsed_data = parser.parse_ddt_with_ai(pdf_text, learning_data, preferred_ai)
        
        # Salva sessione parsing per correzioni future
        parsing_session = {
            'id': f"parsing_{int(datetime.now().timestamp())}",
            'filename': file.filename,
            'parsed_data': parsed_data,
            'pdf_text': pdf_text[:1000],  # Prime 1000 caratteri per debug
            'timestamp': datetime.now().isoformat()
        }
        
        # Salva sessione temporanea
        session_config = ConfigurazioneSistema.query.filter_by(
            chiave='CURRENT_PARSING_SESSION'
        ).first()
        
        if not session_config:
            session_config = ConfigurazioneSistema(
                chiave='CURRENT_PARSING_SESSION',
                valore=json.dumps(parsing_session),
                descrizione='Sessione parsing corrente'
            )
            db.session.add(session_config)
        else:
            session_config.valore = json.dumps(parsing_session)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': parsed_data,
            'session_id': parsing_session['id'],
            'confidence': parsed_data.get('confidence', 0.8)
        })
        
    except Exception as e:
        return jsonify({'error': f'Errore durante il parsing: {str(e)}'}), 500

@parsing_bp.route('/parse-pdf-highlight', methods=['POST'])
def parse_pdf_highlight():
    """API per parsing PDF con evidenziazione dati estratti"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nessun file caricato'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nessun file selezionato'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Solo file PDF sono supportati'}), 400
    
    try:
        # Parser con highlighting
        parser = get_highlight_parser()
        
        # Parsing con coordinate e evidenziazione
        preferred_ai = request.form.get('preferred_ai', 'dual')
        learning_data = parser.get_learning_data()
        
        result = parser.parse_pdf_with_highlights(file, learning_data, preferred_ai)
        
        if not result['success']:
            return jsonify({'error': result.get('error', 'Parsing fallito')}), 400
        
        # Salva sessione per correzioni future
        parsing_session = {
            'id': f"highlight_parsing_{int(datetime.now().timestamp())}",
            'filename': file.filename,
            'parsed_data': result['parsed_data'],
            'highlight_data': result['highlight_data'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Salva sessione temporanea
        session_config = ConfigurazioneSistema.query.filter_by(
            chiave='CURRENT_HIGHLIGHT_SESSION'
        ).first()
        
        if not session_config:
            session_config = ConfigurazioneSistema(
                chiave='CURRENT_HIGHLIGHT_SESSION',
                valore=json.dumps(parsing_session),
                descrizione='Sessione parsing con highlighting corrente'
            )
            db.session.add(session_config)
        else:
            session_config.valore = json.dumps(parsing_session)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': result['parsed_data'],
            'highlight_data': result['highlight_data'],
            'pdf_image': result.get('pdf_image'),
            'session_id': parsing_session['id'],
            'confidence': result['parsed_data'].get('confidence', 0.8),
            'coordinates_found': result.get('coordinates_count', 0),
            'pages_processed': result.get('pages_processed', 0),
            'fields_highlighted': result['highlight_data']['fields_found']
        })
        
    except Exception as e:
        return jsonify({'error': f'Errore durante il parsing con highlighting: {str(e)}'}), 500

@parsing_bp.route('/correct-parsing', methods=['POST'])
def correct_parsing():
    """API per correggere dati parsing e migliorare training"""
    data = request.json
    
    if not data or 'session_id' not in data or 'corrected_data' not in data:
        return jsonify({'error': 'Dati di correzione mancanti'}), 400
    
    try:
        # Recupera sessione originale
        session_config = ConfigurazioneSistema.query.filter_by(
            chiave='CURRENT_PARSING_SESSION'
        ).first()
        
        if not session_config:
            return jsonify({'error': 'Sessione parsing non trovata'}), 404
        
        session_data = json.loads(session_config.valore)
        
        if session_data['id'] != data['session_id']:
            return jsonify({'error': 'Sessione parsing non valida'}), 400
        
        # Salva correzioni per training
        parser = get_parser()
        correction = parser.save_parsing_correction(
            original_data=session_data['parsed_data'],
            corrected_data=data['corrected_data'],
            user_feedback=data.get('user_feedback', '')
        )
        
        return jsonify({
            'success': True,
            'message': 'Correzioni salvate per migliorare parsing futuro',
            'correction_id': correction.get('timestamp'),
            'improvements_saved': len(correction.get('improvements', []))
        })
        
    except Exception as e:
        return jsonify({'error': f'Errore salvataggio correzioni: {str(e)}'}), 500

@parsing_bp.route('/parsing-stats')
def parsing_stats():
    """Statistiche e dati di training del parsing"""
    try:
        # Recupera correzioni
        corrections = ConfigurazioneSistema.query.filter_by(
            chiave='PARSING_CORRECTIONS'
        ).first()
        
        stats = {
            'total_corrections': 0,
            'accuracy_improvements': [],
            'common_errors': {},
            'learning_patterns': []
        }
        
        if corrections:
            corrections_data = json.loads(corrections.valore)
            stats['total_corrections'] = len(corrections_data)
            
            # Analizza pattern di errore comuni
            field_corrections = {}
            for correction in corrections_data:
                for improvement in correction.get('improvements', []):
                    field = improvement.get('field', 'unknown')
                    if field not in field_corrections:
                        field_corrections[field] = 0
                    field_corrections[field] += 1
            
            stats['common_errors'] = field_corrections
            
            # Pattern di apprendimento recenti
            recent = corrections_data[-5:] if corrections_data else []
            for correction in recent:
                for improvement in correction.get('improvements', []):
                    stats['learning_patterns'].append({
                        'timestamp': correction.get('timestamp'),
                        'pattern': improvement.get('pattern'),
                        'field': improvement.get('field')
                    })
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': f'Errore recupero statistiche: {str(e)}'}), 500

@parsing_bp.route('/config-api-key', methods=['POST'])
def config_api_key():
    """Configura API keys per AI (Claude/Gemini)"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Dati mancanti'}), 400
    
    try:
        updated_keys = []
        
        # Configura Claude API Key
        if 'claude_api_key' in data and data['claude_api_key']:
            claude_config = ConfigurazioneSistema.query.filter_by(
                chiave='CLAUDE_API_KEY'
            ).first()
            
            if not claude_config:
                claude_config = ConfigurazioneSistema(
                    chiave='CLAUDE_API_KEY',
                    valore=data['claude_api_key'],
                    descrizione='API Key per Claude AI parsing'
                )
                db.session.add(claude_config)
            else:
                claude_config.valore = data['claude_api_key']
            updated_keys.append('Claude')
        
        # Configura Gemini API Key
        if 'gemini_api_key' in data and data['gemini_api_key']:
            gemini_config = ConfigurazioneSistema.query.filter_by(
                chiave='GEMINI_API_KEY'
            ).first()
            
            if not gemini_config:
                gemini_config = ConfigurazioneSistema(
                    chiave='GEMINI_API_KEY',
                    valore=data['gemini_api_key'],
                    descrizione='API Key per Gemini AI parsing'
                )
                db.session.add(gemini_config)
            else:
                gemini_config.valore = data['gemini_api_key']
            updated_keys.append('Gemini')
        
        db.session.commit()
        
        # Reinizializza parser con nuove keys
        parser = get_parser()
        parser.setup_ai_clients()
        
        return jsonify({
            'success': True,
            'message': f'API Keys configurate: {", ".join(updated_keys)}',
            'updated_services': updated_keys
        })
        
    except Exception as e:
        return jsonify({'error': f'Errore configurazione: {str(e)}'}), 500

@parsing_bp.route('/ai-status')
def ai_status():
    """Status dei servizi AI disponibili"""
    try:
        parser = get_parser()
        status = parser.get_ai_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        return jsonify({'error': f'Errore recupero status: {str(e)}'}), 500

@parsing_bp.route('/parsing-management')
def parsing_management():
    """Pagina gestione parsing e training"""
    return render_template('parsing-management.html')