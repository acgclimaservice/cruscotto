from flask import Blueprint, render_template, request, jsonify, current_app
from models import db, Mastrino, Magazzino, ConfigurazioneSistema
from datetime import datetime
import time

impostazioni_bp = Blueprint('impostazioni', __name__)

@impostazioni_bp.route('/debug')
def debug_config():
    """Route di debug per controllare le configurazioni"""
    current_app.logger.error("DEBUG: Route /debug chiamato!")
    try:
        configs = ConfigurazioneSistema.query.all()
        current_app.logger.error(f"DEBUG: Trovate {len(configs)} configurazioni")
        return f"Configurazioni trovate: {len(configs)}"
    except Exception as e:
        current_app.logger.error(f"DEBUG: Errore query: {e}")
        return f"Errore: {e}"

@impostazioni_bp.route('/')
def impostazioni_home():
    current_app.logger.error("DEBUG STDERR: Route impostazioni chiamato - INIZIO!")
    try:
        current_app.logger.error("DEBUG STDERR: Dentro try block")
        
        mastrini = Mastrino.query.order_by(Mastrino.tipo, Mastrino.codice).all()
        current_app.logger.error(f"DEBUG STDERR: Mastrini query ok: {len(mastrini)}")
        
        magazzini = Magazzino.query.order_by(Magazzino.codice).all()
        current_app.logger.error(f"DEBUG STDERR: Magazzini query ok: {len(magazzini)}")
        
        # Debug configurazioni step by step
        configs_query = ConfigurazioneSistema.query.all()
        current_app.logger.error(f"DEBUG STDERR: Config query result: {len(configs_query)} items")
        configurazioni = {c.chiave: c.valore for c in configs_query}
        
        # Debug: logga le configurazioni
        print(f"DEBUG IMPOSTAZIONI: Configurazioni caricate: {len(configurazioni)}", flush=True)
        print(f"DEBUG IMPOSTAZIONI: Email address: {configurazioni.get('email_address', 'N/D')}", flush=True)
        print(f"DEBUG IMPOSTAZIONI: Email password presente: {bool(configurazioni.get('email_password'))}", flush=True)
        print(f"DEBUG IMPOSTAZIONI: Tutte le chiavi: {list(configurazioni.keys())}", flush=True)
        sys.stdout.flush()
        
        current_app.logger.info(f"Configurazioni caricate: {len(configurazioni)} - Email: {configurazioni.get('email_address', 'N/D')}")
        
        return render_template('impostazioni.html',
                             mastrini=mastrini,
                             magazzini=magazzini,
                             configurazioni=configurazioni)
    except Exception as e:
        current_app.logger.error(f"Errore impostazioni: {e}")
        return render_template('impostazioni.html', mastrini=[], magazzini=[], configurazioni={})

@impostazioni_bp.route('/mastrino/nuovo', methods=['POST'])
def nuovo_mastrino():
    try:
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'error': 'Dati non forniti'}), 400
            
        codice = data.get('codice', '').strip()
        descrizione = data.get('descrizione', '').strip()
        
        if not codice or not descrizione:
            return jsonify({'success': False, 'error': 'Codice e descrizione sono obbligatori'}), 400
        
        if Mastrino.query.filter_by(codice=codice).first():
            return jsonify({'success': False, 'error': f'Mastrino con codice {codice} già esistente'}), 400
        
        # Normalizza tipo (accetta sia maiuscolo che minuscolo)
        tipo_normalizzato = data['tipo'].upper()
        if tipo_normalizzato not in ['ACQUISTI', 'RICAVI', 'ACQUISTO', 'RICAVO']:
            return jsonify({'success': False, 'error': 'Tipo deve essere ACQUISTI o RICAVI'}), 400
        
        # Converte ACQUISTO/RICAVO in ACQUISTI/RICAVI per consistenza
        if tipo_normalizzato == 'ACQUISTO':
            tipo_normalizzato = 'ACQUISTI'
        elif tipo_normalizzato == 'RICAVO':
            tipo_normalizzato = 'RICAVI'
        
        mastrino = Mastrino(
            codice=codice[:50],
            descrizione=descrizione[:200],
            tipo=tipo_normalizzato,
            attivo=True
        )
        
        db.session.add(mastrino)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'id': mastrino.id,
            'message': f'Mastrino {codice} creato con successo'
        })
        
    except Exception as e:
        current_app.logger.error(f"Errore creazione mastrino: {e}")
        return jsonify({'success': False, 'error': f'Errore durante creazione: {str(e)}'}), 500

@impostazioni_bp.route('/magazzino/nuovo', methods=['POST'])
def nuovo_magazzino():
    try:
        data = request.json
        
        if Magazzino.query.filter_by(codice=data['codice']).first():
            return jsonify({'error': 'Codice già esistente'}), 400
        
        magazzino = Magazzino(
            codice=data['codice'][:50],
            descrizione=data['descrizione'][:200],
            responsabile=data.get('responsabile', '')[:100],
            attivo=True
        )
        
        db.session.add(magazzino)
        db.session.commit()
        
        return jsonify({'success': True, 'id': magazzino.id})
        
    except Exception as e:
        current_app.logger.error(f"Errore creazione magazzino: {e}")
        return jsonify({'error': 'Errore interno'}), 500

@impostazioni_bp.route('/configurazione/salva', methods=['POST'])
def salva_configurazioni():
    try:
        data = request.json
        aggiornate = 0
        
        for chiave, valore in data.items():
            if len(chiave) > 100 or len(str(valore)) > 1000:
                continue
                
            config = ConfigurazioneSistema.query.filter_by(chiave=chiave).first()
            if config:
                config.valore = str(valore)
                config.data_modifica = datetime.now()
            else:
                config = ConfigurazioneSistema(
                    chiave=chiave,
                    valore=str(valore),
                    descrizione=f"Config {chiave}"
                )
                db.session.add(config)
            aggiornate += 1
        
        db.session.commit()
        return jsonify({'success': True, 'aggiornate': aggiornate})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Errore salvataggio config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@impostazioni_bp.route('/magazzino/<int:id>/modifica', methods=['POST'])
def modifica_magazzino(id):
    """Modifica un magazzino"""
    try:
        data = request.json
        if not data:
            data = request.form.to_dict()
        
        magazzino = Magazzino.query.get_or_404(id)
        
        if 'descrizione' in data:
            magazzino.descrizione = data['descrizione'][:200]
        if 'responsabile' in data:
            magazzino.responsabile = data['responsabile'][:100]
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Errore modifica magazzino: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@impostazioni_bp.route('/magazzino/<int:id>/elimina', methods=['POST'])
def elimina_magazzino(id):
    """Elimina un magazzino"""
    try:
        magazzino = Magazzino.query.get_or_404(id)
        db.session.delete(magazzino)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Errore eliminazione magazzino: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@impostazioni_bp.route('/email/test', methods=['POST'])
def test_email_connection():
    """Testa la connessione email IMAP"""
    try:
        import imaplib
        import ssl
        
        data = request.json
        server = data.get('email_imap_server', 'imap.gmail.com')
        port = int(data.get('email_imap_port', 993))
        email_address = data.get('email_address')
        password = data.get('email_password')
        
        if not email_address or not password:
            return jsonify({'success': False, 'error': 'Email e password sono obbligatori'}), 400
        
        # Crea connessione SSL IMAP
        context = ssl.create_default_context()
        mail = imaplib.IMAP4_SSL(server, port, ssl_context=context)
        
        # Login
        mail.login(email_address, password)
        
        # Seleziona INBOX
        mail.select('inbox')
        
        # Cerca email
        status, messages = mail.search(None, 'ALL')
        message_count = len(messages[0].split()) if messages[0] else 0
        
        # Chiudi connessione
        mail.close()
        mail.logout()
        
        return jsonify({
            'success': True, 
            'message_count': message_count,
            'message': f'Connessione riuscita! Trovate {message_count} email'
        })
        
    except Exception as e:
        current_app.logger.error(f"Errore test email: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@impostazioni_bp.route('/email/verifica-immediata', methods=['POST'])
def verifica_immediata_email():
    """Verifica immediata della casella email per DDT"""
    try:
        # Prendi l'istanza del monitor email dall'app
        email_monitor = getattr(current_app, 'email_monitor', None)
        
        if not email_monitor:
            return jsonify({'success': False, 'error': 'Monitor email non configurato'}), 400
        
        # Esegui controllo immediato
        result = email_monitor._check_emails()
        
        # Se il risultato è None, crea un result di default
        if result is None:
            result = {'processed': 0, 'created': 0, 'message': 'Nessuna email trovata'}
        
        return jsonify({
            'success': True,
            'message': f'Verifica completata. {result.get("processed", 0)} email processate.',
            'details': result
        })
        
    except Exception as e:
        current_app.logger.error(f"Errore verifica immediata email: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@impostazioni_bp.route('/email/status', methods=['GET'])
def email_monitor_status():
    """Restituisce lo status del monitor email"""
    try:
        email_monitor = getattr(current_app, 'email_monitor', None)
        
        if not email_monitor:
            return jsonify({'active': False, 'message': 'Monitor non configurato'})
        
        return jsonify({
            'active': email_monitor.running,
            'message': 'Monitor attivo' if email_monitor.running else 'Monitor inattivo'
        })
        
    except Exception as e:
        current_app.logger.error(f"Errore status email monitor: {e}")
        return jsonify({'active': False, 'error': str(e)})

@impostazioni_bp.route('/email/restart', methods=['POST'])
def restart_email_monitor():
    """Riavvia il monitor email"""
    try:
        email_monitor = getattr(current_app, 'email_monitor', None)
        
        if not email_monitor:
            return jsonify({'success': False, 'error': 'Monitor non configurato'}), 400
        
        # Ferma se è attivo
        if email_monitor.running:
            email_monitor.stop_monitoring()
            time.sleep(2)  # Aspetta che si fermi
        
        # Riavvia se è configurato come attivo
        if email_monitor.is_active():
            success = email_monitor.start_monitoring()
            if success:
                return jsonify({
                    'success': True, 
                    'message': 'Monitor email riavviato con successo'
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': 'Impossibile avviare il monitor (probabilmente già attivo)'
                })
        else:
            return jsonify({
                'success': False, 
                'error': 'Monitor non configurato come attivo nelle impostazioni'
            })
        
    except Exception as e:
        current_app.logger.error(f"Errore restart email monitor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@impostazioni_bp.route('/mastrini/aggiorna-codici', methods=['POST'])
def aggiorna_codici_mastrini():
    """Aggiunge zero iniziale ai codici mastrini che iniziano con 4 o 5"""
    try:
        from models import Mastrino
        
        # Trova mastrini che iniziano con 4 o 5 e non hanno già lo zero
        mastrini_da_aggiornare = Mastrino.query.filter(
            db.or_(
                Mastrino.codice.like('4%'),
                Mastrino.codice.like('5%')
            ),
            ~Mastrino.codice.like('04%'),
            ~Mastrino.codice.like('05%')
        ).all()
        
        if not mastrini_da_aggiornare:
            return jsonify({
                'success': True, 
                'message': 'Nessun mastrino da aggiornare trovato'
            })
        
        aggiornati = 0
        for mastrino in mastrini_da_aggiornare:
            vecchio_codice = mastrino.codice
            if vecchio_codice.startswith('4'):
                nuovo_codice = '0' + vecchio_codice
            elif vecchio_codice.startswith('5'):
                nuovo_codice = '0' + vecchio_codice
            else:
                continue
                
            # Verifica che il nuovo codice non esista già
            esistente = Mastrino.query.filter_by(codice=nuovo_codice).first()
            if not esistente:
                mastrino.codice = nuovo_codice
                aggiornati += 1
                current_app.logger.info(f"Aggiornato mastrino: {vecchio_codice} → {nuovo_codice}")
        
        if aggiornati > 0:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Aggiornati {aggiornati} codici mastrini con zero iniziale'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Nessun codice aggiornato (possibili duplicati)'
            })
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Errore aggiornamento codici mastrini: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500