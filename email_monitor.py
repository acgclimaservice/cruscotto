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
        """Recupera configurazione dal database"""
        with self.app.app_context():
            config = ConfigurazioneSistema.query.filter_by(chiave=key).first()
            return config.valore if config else default
    
    def is_active(self):
        """Controlla se il monitoraggio è attivo"""
        return self.get_config('email_monitor_active') == 'true'
    
    def start_monitoring(self):
        """Avvia il thread di monitoraggio"""
        if self.running or not self.is_active():
            return False
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        self.logger.info("📧 Email monitor started")
        return True
    
    def stop_monitoring(self):
        """Ferma il monitoraggio"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("📧 Email monitor stopped")
    
    def _monitor_loop(self):
        """Loop principale di monitoraggio"""
        while self.running:
            try:
                if self.is_active():
                    self._check_emails()
                
                # Attendi l'intervallo configurato
                interval = int(self.get_config('email_check_interval', '5'))
                time.sleep(interval * 60)  # Converti in secondi
                
            except Exception as e:
                self.logger.error(f"Errore nel loop di monitoraggio: {e}")
                time.sleep(60)  # Attendi 1 minuto prima di riprovare
    
    def _check_emails(self):
        """Controlla nuove email e processa allegati PDF"""
        try:
            server = self.get_config('email_imap_server', 'imap.gmail.com')
            port = int(self.get_config('email_imap_port', '993'))
            email_address = self.get_config('email_address')
            password = self.get_config('email_password')
            max_attachments = int(self.get_config('email_max_attachments', '10'))
            
            if not email_address or not password:
                self.logger.warning("Credenziali email non configurate")
                return
            
            # Connessione IMAP
            context = ssl.create_default_context()
            mail = imaplib.IMAP4_SSL(server, port, ssl_context=context)
            mail.login(email_address, password)
            mail.select('inbox')
            
            # Cerca email non lette
            status, messages = mail.search(None, 'UNSEEN')
            
            if not messages[0]:
                self.logger.debug("Nessuna nuova email trovata")
                mail.close()
                mail.logout()
                return
            
            email_ids = messages[0].split()
            self.logger.info(f"📬 Trovate {len(email_ids)} nuove email")
            
            for email_id in email_ids[:10]:  # Processa max 10 email per volta
                try:
                    self._process_email(mail, email_id, max_attachments)
                except Exception as e:
                    self.logger.error(f"Errore processando email {email_id}: {e}")
            
            mail.close()
            mail.logout()
            
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
            
            self.logger.info(f"📧 Processando: {subject} da {from_addr}")
            
            # Estrai allegati PDF
            pdf_files = []
            for part in email_message.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
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
            
            if pdf_files:
                # Crea job batch per processare i PDF
                job_id = self._create_batch_job(pdf_files, subject, from_addr)
                
                # Segna email come letta
                mail.store(email_id, '+FLAGS', '\\Seen')
                
                # Invia email di conferma
                self._send_confirmation_email(from_addr, subject, len(pdf_files), job_id)
                
                self.logger.info(f"✅ Creato job batch {job_id} con {len(pdf_files)} file")
            else:
                # Segna comunque come letta se non ci sono PDF
                mail.store(email_id, '+FLAGS', '\\Seen')
                self.logger.info(f"📧 Nessun PDF trovato in: {subject}")
    
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
        from app import process_batch_files
        thread = threading.Thread(target=process_batch_files, args=(job.id,), daemon=True)
        thread.start()
        
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
            
            self.logger.info(f"📧 Email di conferma inviata a {to_email}")
            
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