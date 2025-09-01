from flask import Blueprint, request, jsonify
import os
from werkzeug.utils import secure_filename

parsing_bp = Blueprint('parsing', __name__)

@parsing_bp.route('/status', methods=['GET'])
def parsing_status():
    """Verifica stato servizi AI"""
    try:
        services = []
        if os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY'):
            services.append('claude')
        if os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'):
            services.append('gemini')
        
        return jsonify({
            'success': True,
            'services': services,
            'count': len(services)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@parsing_bp.route('/parse', methods=['POST'])
def parse_pdf():
    """Parse PDF con AI - usa il metodo corretto parse_ddt_with_ai"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Nessun file caricato'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nessun file selezionato'}), 400
        
        # Salva temporaneamente il file
        import tempfile
        filename = secure_filename(file.filename)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        
        try:
            # Usa il parser con il metodo corretto
            from multi_ai_pdf_parser import MultiAIPDFParser
            parser = MultiAIPDFParser()
            
            # CORRETTO: Passa file object non path string
            with open(temp_path, 'rb') as file_obj:
                result = parser.parse_ddt_with_ai(file_obj)
            
            # Pulisci file temp
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            if result and result.get('success'):
                # CORRETTO: Accede ai dati tramite result['data']
                return jsonify({
                    'success': True,
                    'data': {
                        'fornitore': result['data'].get('fornitore', ''),
                        'numero_ddt': result['data'].get('numero_ddt', ''),
                        'data_ddt': result['data'].get('data_ddt', ''),
                        'articoli': result['data'].get('articoli', [])
                    }
                })
            else:
                error_msg = result.get('error', 'Parsing fallito') if result else 'Parsing fallito'
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
                
        except Exception as parse_error:
            print(f"Errore durante il parsing: {parse_error}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({
                'success': False,
                'error': f'Errore parsing: {str(parse_error)}'
            }), 500
            
    except Exception as e:
        print(f"Errore generale: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Mantieni anche la vecchia route per compatibilità
@parsing_bp.route('/parse-pdf', methods=['POST'])
def parse_pdf_legacy():
    """Route legacy per compatibilità"""
    return parse_pdf()

@parsing_bp.route('/ai-status', methods=['GET'])
def ai_status():
    """Alias per status"""
    return parsing_status()
