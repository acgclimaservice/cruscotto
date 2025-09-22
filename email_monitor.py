"""
Sistema di monitoraggio email per importazione automatica DDT
"""
import imaplib
import email
import ssl
import os
import tempfile
import threading
import time
import logging
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

from models import db, ConfigurazioneSistema, BatchImportJob, BatchImportFile, DDTIn
from multi_ai_pdf_parser import MultiAIPDFParser

class EmailMonitor:
    def __init__(self, app):
        self.app = app
        self.running = False
        self.thread = None
        self.logger = logging.getLogger(__name__)
        
    def get_config(self, key, default=None):
        """Recupera configurazione da .env o database"""
        # Prima prova .env
        env_key = key.upper()
        env_value = os.getenv(env_key)
        if env_value:
            return env_value
            
        # Fallback al database
        with self.app.app_context():
            config = ConfigurazioneSistema.query.filter_by(chiave=key).first()
            return config.valore if config else default
    
    def is_active(self):
        """Controlla se il monitoraggio è attivo"""
        try:
            active_config = self.get_config('email_monitor_active')
            self.logger.info(f"[EMAIL DEBUG] is_active() - config value: '{active_config}'")
            return active_config == 'true'
        except Exception as e:
            self.logger.error(f"[EMAIL DEBUG] is_active() - Errore accesso config: {e}")
            # Fallback: se c'è errore durante l'avvio, assumiamo attivo se .env lo dice
            env_active = os.getenv('EMAIL_MONITOR_ACTIVE', '').lower()
            self.logger.info(f"[EMAIL DEBUG] is_active() - fallback ENV: '{env_active}'")
            return env_active == 'true'
    
    def start_monitoring(self):
        """Avvia il thread di monitoraggio"""
        self.logger.info(f"[EMAIL DEBUG] start_monitoring called - running: {self.running}, is_active: {self.is_active()}")
        
        if self.running:
            self.logger.info("[EMAIL DEBUG] Monitor già running - return False")
            return False
            
        if not self.is_active():
            self.logger.info("[EMAIL DEBUG] Monitor non attivo - return False")
            return False
            
        self.logger.info("[EMAIL DEBUG] Avvio thread monitor...")
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        self.logger.info(f"[EMAIL DEBUG] Thread creato e avviato - alive: {self.thread.is_alive()}")
        self.logger.info("[EMAIL] Email monitor started")
        return True
    
    def stop_monitoring(self):
        """Ferma il monitoraggio"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("[EMAIL] Email monitor stopped")
    
    def _monitor_loop(self):
        """Loop principale di monitoraggio"""
        self.logger.info("[EMAIL] Monitor loop started!")
        self.logger.info(f"[EMAIL DEBUG] Monitor thread loop INIZIATO - running={self.running}")
        while self.running:
            try:
                self.logger.info(f"[EMAIL] Loop iteration - running={self.running}, active={self.is_active()}")
                if self.is_active():
                    start_time = time.time()
                    self.logger.info(f"[EMAIL] Starting automatic email check at {datetime.now().strftime('%H:%M:%S')}")
                    self._check_emails()
                    elapsed = time.time() - start_time
                    self.logger.info(f"[EMAIL] Automatic email check completed in {elapsed:.2f} seconds")
                
                # Attendi l'intervallo configurato
                interval = int(self.get_config('email_check_interval', '5'))
                self.logger.debug(f"[EMAIL] Waiting {interval} minutes until next check")
                time.sleep(interval * 60)  # Converti in secondi
                
            except Exception as e:
                import traceback
                self.logger.error(f"[EMAIL DEBUG] Errore nel loop di monitoraggio: {e}")
                self.logger.error(f"[EMAIL DEBUG] Traceback: {traceback.format_exc()}")
                # Continua il loop anche in caso di errore
                time.sleep(60)  # Attendi 1 minuto prima di riprovare
                
        self.logger.info("[EMAIL DEBUG] Monitor loop TERMINATO")
    
    def _check_emails(self):
        """Controlla nuove email e processa allegati PDF"""
        try:
            server = self.get_config('email_imap_server', 'imap.gmail.com')
            port = int(self.get_config('email_imap_port', '993'))
            email_address = self.get_config('email_address')
            password = self.get_config('email_password')
            max_attachments = int(self.get_config('email_max_attachments', '10'))

            self.logger.info(f"DEBUG: Using email config - Server: {server}:{port}, Email: {email_address}, Password length: {len(password) if password else 0}")

            if not email_address or not password:
                self.logger.warning("Credenziali email non configurate")
                return
            
            # Connessione IMAP
            context = ssl.create_default_context()
            mail = imaplib.IMAP4_SSL(server, port, ssl_context=context)
            mail.login(email_address, password)
            mail.select('inbox')
            
            # Cerca email non lette (temporaneamente tutte per debug)
            status, messages = mail.search(None, 'ALL')
            self.logger.info("DEBUG: Usando 'ALL' invece di 'UNSEEN' per debug")
            
            # DEBUG: Log dettagliato
            self.logger.info(f"DEBUG: IMAP search status: {status}")
            self.logger.info(f"DEBUG: IMAP messages result: {messages}")
            
            if not messages[0]:
                self.logger.info("DEBUG: Nessuna nuova email trovata - controllando tutte le email")
                # DEBUG: Controlla tutte le email per debug
                status_all, messages_all = mail.search(None, 'ALL')
                total_emails = len(messages_all[0].split()) if messages_all[0] else 0
                self.logger.info(f"DEBUG: Totale email: {total_emails}")
                mail.close()
                mail.logout()
                return {
                    'processed': 0,
                    'total_found': 0,
                    'message': f'Nessuna email non letta trovata (totale in casella: {total_emails})'
                }
            
            email_ids = messages[0].split()
            self.logger.info(f"[EMAIL] Trovate {len(email_ids)} email totali")
            self.logger.info(f"DEBUG: Processing prime 10 email: {email_ids[:10]}")
            
            processed_count = 0
            for i, email_id in enumerate(email_ids[:10]):  # Processa max 10 email per volta
                try:
                    start_time = time.time()
                    self.logger.info(f"[EMAIL] Processing email {i+1}/{len(email_ids[:10])} (ID: {email_id})")
                    
                    # Prova il processing
                    result = self._process_email(mail, email_id, max_attachments)
                    if result:
                        processed_count += 1
                        self.logger.info(f"[EMAIL] Email {email_id} processed successfully")
                    else:
                        self.logger.info(f"[EMAIL] Email {email_id} skipped (no valid PDFs)")
                        
                    elapsed = time.time() - start_time
                    self.logger.info(f"[EMAIL] Email {email_id} completed in {elapsed:.2f} seconds")
                except Exception as e:
                    self.logger.error(f"Errore processando email {email_id}: {e}")
                    import traceback
                    self.logger.error(f"Stack trace: {traceback.format_exc()}")
            
            self.logger.info(f"[EMAIL] Total emails processed: {processed_count}/{len(email_ids[:10])}")
            
            mail.close()
            mail.logout()
            
            # Restituisce il risultato per il feedback
            return {
                'processed': processed_count,
                'total_found': len(email_ids),
                'message': f'Processate {processed_count} email su {len(email_ids)} trovate'
            }
            
        except Exception as e:
            self.logger.error(f"Errore controllo email: {e}")
    
    def _process_email(self, mail, email_id, max_attachments):
        """Processa una singola email"""
        with self.app.app_context():
            # Recupera email
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            subject = email_message.get('Subject', 'Senza oggetto')
            from_addr = email_message.get('From', 'Mittente sconosciuto')
            date = email_message.get('Date', '')
            
            self.logger.info(f"[EMAIL] Processando: {subject} da {from_addr}")
            self.logger.info(f"DEBUG: Email ID: {email_id}, Subject: '{subject}'")
            
            # Estrai allegati PDF
            pdf_files = []
            self.logger.info(f"DEBUG: Starting attachment scan...")
            attachment_count = 0
            total_parts = 0
            for part in email_message.walk():
                total_parts += 1
                content_type = part.get_content_type()
                content_disposition = part.get_content_disposition()
                filename = part.get_filename()
                self.logger.info(f"DEBUG: Part {total_parts}: Type='{content_type}', Disposition='{content_disposition}', Filename='{filename}'")

                if part.get_content_disposition() == 'attachment':
                    attachment_count += 1
                    filename = part.get_filename()
                    self.logger.info(f"DEBUG: Found attachment {attachment_count}: '{filename}' (PDF: {filename and filename.lower().endswith('.pdf') if filename else False})")
                    if filename and filename.lower().endswith('.pdf'):
                        if len(pdf_files) >= max_attachments:
                            self.logger.warning(f"Raggiunti max {max_attachments} allegati per email")
                            break
                            
                        # Salva file temporaneo
                        temp_file = tempfile.NamedTemporaryFile(
                            delete=False, 
                            suffix='.pdf',
                            prefix=f'email_{email_id.decode()}_'
                        )
                        temp_file.write(part.get_payload(decode=True))
                        temp_file.close()
                        
                        pdf_files.append({
                            'filename': filename,
                            'temp_path': temp_file.name,
                            'size': os.path.getsize(temp_file.name)
                        })
                        
                        self.logger.info(f"📎 Allegato salvato: {filename} ({pdf_files[-1]['size']} bytes)")
            
            self.logger.info(f"DEBUG: Email scan complete - Total parts: {total_parts}, Attachments: {attachment_count}, PDF files: {len(pdf_files)}")
            
            if pdf_files:
                # Crea job batch per processare i PDF
                job_id = self._create_batch_job(pdf_files, subject, from_addr)
                
                # Segna email come letta
                mail.store(email_id, '+FLAGS', '\\Seen')
                
                # Invia email di conferma
                self._send_confirmation_email(from_addr, subject, len(pdf_files), job_id)
                
                self.logger.info(f"✅ Creato job batch {job_id} con {len(pdf_files)} file")
                return True  # Email processata con successo
            else:
                # Segna comunque come letta se non ci sono PDF  
                mail.store(email_id, '+FLAGS', '\\Seen')
                self.logger.info(f"[EMAIL] Nessun PDF trovato in: {subject}")
                return False  # Email senza PDF validi
    
    def _create_batch_job(self, pdf_files, subject, from_addr):
        """Crea un job batch per processare i PDF"""
        # Crea job
        job = BatchImportJob(
            total_files=len(pdf_files),
            status='pending',
            created_at=datetime.now(),
            metadata=f"Auto-import da {from_addr}: {subject}"
        )
        db.session.add(job)
        db.session.flush()
        
        # Crea record per ogni file
        for pdf_file in pdf_files:
            batch_file = BatchImportFile(
                job_id=job.id,
                original_filename=pdf_file['filename'],
                filename=pdf_file['temp_path'],
                status='pending',
                file_size=pdf_file['size']
            )
            db.session.add(batch_file)
        
        db.session.commit()
        
        # Avvia processing in background (riutilizza sistema esistente)
        self.logger.info(f"[EMAIL] Starting background processing for job {job.id} with {len(pdf_files)} files")
        from app import process_batch_files
        thread = threading.Thread(target=process_batch_files, args=(job.id,), daemon=True)
        thread.start()
        self.logger.info(f"[EMAIL] Background processing started for job {job.id}")
        
        return job.id
    
    def _send_confirmation_email(self, to_email, original_subject, file_count, job_id):
        """Invia email di conferma ricezione"""
        try:
            smtp_server = self.get_config('email_smtp_server', 'smtp.gmail.com')
            smtp_port = int(self.get_config('email_smtp_port', '587'))
            email_address = self.get_config('email_address')
            password = self.get_config('email_password')
            
            if not email_address or not password:
                return
            
            # Crea messaggio
            msg = MIMEMultipart()
            msg['From'] = email_address
            msg['To'] = to_email
            msg['Subject'] = f"✅ DDT ricevuti e in elaborazione - Job #{job_id}"
            
            body = f"""
Gentile fornitore,

abbiamo ricevuto la vostra email "{original_subject}" con {file_count} allegato/i PDF.

I documenti sono stati acquisiti automaticamente nel nostro sistema e sono in fase di elaborazione.

Dettagli:
- Job ID: #{job_id}
- File ricevuti: {file_count} PDF
- Data ricezione: {datetime.now().strftime('%d/%m/%Y %H:%M')}
- Stato: In elaborazione

I DDT verranno processati automaticamente e saranno disponibili nel nostro gestionale entro pochi minuti.

Grazie per aver utilizzato il nostro sistema di importazione automatica!

---
Sistema di gestione DDT ACG Clima Service
Questo è un messaggio automatico, si prega di non rispondere.
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Invia email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_address, password)
            server.sendmail(email_address, to_email, msg.as_string())
            server.quit()
            
            self.logger.info(f"[EMAIL] Email di conferma inviata a {to_email}")
            
        except Exception as e:
            self.logger.error(f"Errore invio email conferma: {e}")

# Istanza globale
email_monitor = None

def init_email_monitor(app):
    """Inizializza il monitor email"""
    global email_monitor
    email_monitor = EmailMonitor(app)
    
    # Avvia automaticamente se configurato
    if email_monitor.is_active():
        email_monitor.start_monitoring()
    
    return email_monitor

def get_email_monitor():
    """Restituisce l'istanza del monitor email"""
    return email_monitor