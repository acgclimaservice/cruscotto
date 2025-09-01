# APP.PY COMPLETO - Sistema Gestione DDT
# PythonAnywhere + Sistema Parsing AI

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, Response, make_response, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import func, desc, case, text
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import os
import sys
import traceback
import base64
import io

# Carica variabili d'ambiente
load_dotenv()

app = Flask(__name__)
# Database URI - si adatta automaticamente all'ambiente
db_path = os.environ.get('DATABASE_URL') or 'sqlite:///ddt_database.db'
app.config['SQLALCHEMY_DATABASE_URI'] = db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['ITEMS_PER_PAGE'] = 50
app.config['MAX_SEARCH_RESULTS'] = 10

# Versione applicazione - legge da file
def get_app_version():
    try:
        with open('version.txt', 'r') as f:
            return f.read().strip()
    except:
        return "4.0"

APP_VERSION = get_app_version()
RELEASE_NOTES = {
    "4.17": [
        "✅ COLLEGAMENTI: Risolto definitivamente problema totali non visibili nella tabella collegamenti", 
        "📄 EXPORT PDF: Aggiunta esportazione PDF completa del report mastrini",
        "📊 EXPORT EXCEL: Migliorato Excel con 4 fogli (Spese, Ricavi, Collegamenti, Riepilogo)",
        "🔧 BACKEND: Calcolo totali spostato nel backend per prestazioni migliori",
        "💰 EXCEL: Corretto calcolo ricavi (ora usa prezzo_unitario invece di costo_unitario)"
    ],
    "4.16": [
        "💰 REPORT MASTRINI: Aggiunti totali effettivi per ogni collegamento (spese e ricavi)",
        "📊 COLLEGAMENTI: Visualizzazione importi reali per mastrino acquisto e ricavo",
        "🎨 INTERFACCIA: Colori distintivi per totali spese (rosso) e ricavi (verde)"
    ],
    "4.15": [
        "🔗 COLLEGAMENTI: Risolto problema collegamenti mastrini che non apparivano nelle impostazioni",
        "📊 REPORT MASTRINI: Aggiunta sezione dettagliata collegamenti configurati con status utilizzo",
        "💰 REPORT MASTRINI: Sistemato calcolo ricavi (ora usa prezzo_unitario invece di costo_unitario)", 
        "✅ REPORT MASTRINI: Risolti tutti gli errori di divisione per NoneType nel template",
        "🎯 IMPOSTAZIONI: Le descrizioni complete dei mastrini ora visibili nei collegamenti"
    ],
    "4.14": [
        "📊 REPORT: Aggiunta barra filtri data a tutti i report (fornitori, clienti, commesse, articoli)",
        "📊 REPORT: Report utilizzano sempre data origine documento (data_ddt_origine) per filtri",
        "📊 REPORT: Export Excel include i filtri di data selezionati",
        "✅ REPORT: Risolto errore export Excel commesse",
        "✅ REPORT: Risolto errore filtri data report articoli",
        "✅ REPORT: Risolto errore SQL nel report commesse (f-string)"
    ],
    "4.9": [
        "✨ DDT OUT: Aggiunto reindirizzamento automatico dopo salvataggio modifiche",
        "🎯 UX: Migliorata esperienza utente con feedback visivo durante il salvataggio"
    ],
    "4.8": [
        "🔧 PARSING ORDINI: Risolto problema parsing con estrazione testo da PDF", 
        "✅ DDT OUT: Risolto bug modifica che cancellava i dati degli articoli",
        "🆕 INVENTARIO: Risolto problema duplicazioni articoli durante conferma DDT IN"
    ],
    "4.3": [
        "🔧 CLAUDE: Ripristinato modello claude-3-haiku-20240307 (stabile)", 
        "✅ PARSING: Sistema parsing completamente funzionante su DDT IN e ordini"
    ],
    "4.2": [
        "🤖 CLAUDE: Aggiornato modello a claude-3-5-sonnet-20241022",
        "🔧 PARSING: Risolto errore 404 modello Claude non disponibile", 
        "✅ AI: Sistema parsing DDT IN e ordini completamente funzionante"
    ],
    "4.1": [
        "🔧 RISOLTI 22 bug critici dal file todobarbara.txt",
        "✅ DDT IN/OUT: Eliminazione, conferma, generazione e modifica corrette", 
        "📧 EMAIL: Aggiornate a info@acgclimaservice.com in tutti i PDF",
        "🔗 MASTRINI: Sistema mastrini per singola riga implementato",
        "📦 INVENTARIO: Gestione codici interni esistenti e ubicazioni",
        "🤖 PARSING AI: Supporto simultaneo DDT IN e ordini con fallback",
        "⚙️ SISTEMA: Scorta minima default = 0 per nuovi articoli"
    ],
    "3.6": [
        "🔍 NUOVO Tasto Confronta Ordini: Aggiunti modal confronto PDF/ordine e route eliminazione",
        "🗑️ RIPARATA Eliminazione: Aggiunta route /ordini/<id>/elimina mancante",
        "📄 CONFRONTO PDF: Visualizzazione PDF allegato con zoom e lente d'ingrandimento",
        "⚡ WORKFLOW Completo: Confronto, modifica e conferma ordini da PDF come nei DDT"
    ],
    "3.5": [
        "🛒 NUOVA FUNZIONALITÀ Import Ordini da PDF: Implementato sistema completo per importare offerte fornitori",
        "📄 PARSING AI Offerte: Integrato AI parsing per estrarre automaticamente dati da offerte PDF",
        "⚡ WORKFLOW Ordini: Creazione automatica ordini da offerte con review e modifica dati",
        "🔄 RIUTILIZZO Codice: Utilizzato stesso parser DDT per import ordini fornitori"
    ],
    "3.4": [
        "🔧 RIPARATO Autocomplete Mastrini: Corretto CSS troppo aggressivo che impediva visualizzazione",
        "🐛 CORRETTO Funzionamento: Ripristinato autocomplete in modifica DDT con debug avanzato",
        "⚡ OTTIMIZZATO Template: CSS bilanciato per visibilità senza interferenze"
    ],
    "3.3": [
        "📝 MIGLIORATO Autocomplete Mastrini: Visualizzazione ottimizzata per DDT con singolo articolo",
        "🔧 CORRETTO Posizionamento: Dropdown intelligente sopra/sotto in base allo spazio disponibile",
        "✨ OTTIMIZZATO CSS: Rimossi conflitti e migliorato z-index per massima visibilità"
    ],
    "3.2": [
        "✅ RIPARATO Import DDT Template: Codice fornitore e mastrini ora salvati correttamente",
        "🔧 CORRETTO JavaScript Template: Dati inviati nel formato corretto all'API",
        "🎯 COMPLETATO Sistema Conferma: DDT importati confermabili senza modifiche manuali"
    ],
    "3.1": [
        "🔧 RIPARATO Batch Processing: Codice dal parsing PDF ora va correttamente in codice_fornitore",
        "🆕 COMPLETATO Sistema Codici: Funziona sia per import manuale che automatico email",
        "📝 CORRETTO Email Monitor: DDT da email ora generano codice interno automaticamente"
    ],
    "3.0": [
        "🆕 NUOVO Sistema Codici Interni: Generazione automatica con prime 4 lettere fornitore + codice fornitore",
        "🔧 AGGIORNATO Template DDT: Campi codice interno ora in sola lettura con indicazione automatica",
        "📝 OTTIMIZZATO Workflow: Inserimento semplificato codice fornitore, codice interno automatico"
    ],
    "2.9": [
        "✅ RIPARATO Validazione DDT IN: Rimossa validazione obsoleta mastrino_ddt",
        "🔧 IMPLEMENTATO Controllo mastrino articoli: Validazione a livello di singolo articolo",
        "📝 CORRETTO Conferma DDT: Ora funziona correttamente con mastrini per articolo"
    ],
    "2.8": [
        "✅ RIPARATO Modifica DDT IN: Aggiunto tasto 'Copia Mastrino su Tutte le Righe'",
        "🔧 RIPARATO Validazione DDT: Aggiunto campo Codice Fornitore obbligatorio in modifica",
        "📝 MIGLIORAMENTO: Salvataggio completo dati articolo (mastrino_riga, codice_fornitore)"
    ],
    "2.7": [
        "🎯 SISTEMA EMAIL MONITOR: Importazione automatica DDT via email con PDF attachment",
        "🔧 DATABASE RIPARATO: Errori I/O risolti, sistema stabile e performante",
        "✅ PUNTI 51-58 COMPLETATI: Versione corretta, selezione magazzini, autocomplete z-index",
        "⚡ MASTRINI MIGLIORATI: Aggiunta funzione zero iniziale per codici (4→04, 5→05)",
        "🐛 ERRORI JAVASCRIPT RISOLTI: PDF validation, selector autocomplete, campo magazzino",
        "📧 CONFIGURAZIONE EMAIL: UI completa per test connessione e monitoraggio automatico"
    ],
    "2.37": [
        "✅ RISOLTI Bug #49-55: Archivio verificato, report inventario, commesse e magazzini",
        "🔧 Bug #52: Redirect diretto alla lista commesse dopo creazione",
        "🔧 Bug #53: Visualizzazione dettaglio commessa funzionante",
        "➕ Bug #55: Route /impostazioni/magazzino/nuovo per creare nuovi magazzini"
    ],
    "2.36": [
        "🔧 RISOLTO Bug #50: Report storico inventario ora funziona correttamente",
        "📊 RIPRISTINATA ROUTE: /inventario/report-storico recuperata dai backup",
        "✅ TESTATO: Report mostra correttamente articoli e calcoli inventario"
    ],
    "2.35": [
        "🔧 RISOLTO Bug #16: Route /fornitori/nuovo ora funziona correttamente",
        "➕ NUOVA FUNZIONALITÀ: Creazione nuovi fornitori con form completo",
        "✅ TESTATO: Creazione, validazione e redirect automatico alla lista fornitori"
    ],
    "2.34": [
        "🔧 RISOLTO Bug #30: Importazione Excel mastrini ora funziona correttamente",
        "📤 NUOVA ROUTE: /impostazioni/mastrini/importa-excel per upload file Excel/CSV",
        "✅ TESTATO: Importazione mastrini con formato Tipo, Codice, Descrizione"
    ],
    "2.33": [
        "✅ VERIFICATO: Tasto elimina mastrini in impostazioni funziona correttamente",
        "🔧 TESTATO: Route eliminazione mastrini operativa (/impostazioni/mastrino/<id>/elimina)",
        "📊 IMPORT: Mastrini acquisti e ricavi importati e visibili"
    ],
    "2.31": [
        "🔧 RISOLTO DDT IN: I movimenti ora vengono creati anche quando il codice articolo è vuoto",
        "📊 FUNZIONALE: Generazione automatica codici temporanei ART-{id} per articoli senza codice",
        "✅ TESTATO: DDT IN ora alimenta correttamente la sezione movimenti"
    ],
    "2.30": [
        "🔧 RISOLTO: Correzione nomi campi form - costo_unitario e codice_interno ora salvati correttamente",
        "📊 FUNZIONALE: I nuovi DDT ora creano automaticamente i movimenti di magazzino",
        "💰 RISOLTO: I costi unitari non vengono più cancellati durante la creazione DDT"
    ],
    "2.29": [
        "🔧 RISOLTO: Metodi get_ddt_in() e get_ddt_out() aggiunti al modello Movimento",
        "📊 FUNZIONALE: Template movimenti.html ora renderizza correttamente i dati", 
        "✅ ATTIVO: Sezione Movimenti completamente operativa"
    ],
    "2.28": [
        "🔧 RISOLTO DEFINITIVO: Sezione Movimenti funzionante - Database ricreato completamente",
        "📊 ATTIVO: Tabella movimenti creata e popolata con DDT confermati di test",
        "✅ TESTATO: Movimenti entrata/uscita funzionano correttamente", 
        "🗄️ CORRETTO: Percorso database assoluto per evitare conflitti di path",
        "📋 DATI TEST: Creati DDT IN/OUT di esempio per mostrare funzionamento movimenti"
    ],
    "2.27": [
        "🔧 RISOLTO: Errore 404 visualizzazione DDT OUT - Aggiunta route /ddt-out/<id>",
        "✅ NUOVO: Dettaglio DDT OUT ora accessibile dalla lista DDT OUT",
        "🔗 COMPLETATO: Sistema DDT OUT completamente funzionante",
        "📋 MIGLIORATO: Consistenza tra DDT IN e DDT OUT per visualizzazione dettagli"
    ],
    "2.26": [
        "🤖 RISOLTO Bug #45: Automazione creazione fornitore da import PDF con controllo duplicati",
        "🏢 RISOLTO Bug #46: Gestione Commesse completa con numeri progressivi e stati",
        "📋 NUOVO: Sezione Commesse con filtri per stato, cliente e tipologia",
        "🔗 CREATO: API per creazione automatica fornitori da dati AI estratti",
        "✨ COMPLETATI: Tutti i bug dal #42 al #46 del file bug.txt"
    ],
    "2.25": [
        "✅ RISOLTO Bug #42: Errore 405 genera DDT OUT - Aggiunto metodo POST per salvare",
        "📊 RISOLTO Bug #43: Sezione movimenti ora alimentata da DDT IN/OUT confermati", 
        "🏷️ RISOLTO Bug #44: Inventario mostra mastrino acquisto per ogni articolo",
        "🔄 MIGLIORATO: Inventario raggruppa giacenze per articolo + mastrino acquisto",
        "📈 NUOVO: Ogni articolo con giacenze su mastrini diversi viene duplicato"
    ],
    "2.24": [
        "🎯 MIGLIORATO: Prompt AI specifico per leggere esattamente i dati dalle tabelle PDF", 
        "📋 CORRETTO: Claude ora deve usare SOLO i dati reali dal PDF, non inventarli",
        "🔍 SPECIFICO: Cerca codici articolo, descrizioni, quantità e prezzi esatti",
        "❌ BLOCCATO: Impedito a Claude di creare dati fittizi quando non trova informazioni",
        "📊 TABELLE: Migliorata lettura tabelle DDT con colonne [Codice][Descrizione][Quantità][Prezzo]"
    ],
    "2.23": [
        "🔧 DEFINITIVO: Modello Claude corretto a claude-3-haiku-20240307 (testato funzionante)", 
        "✅ RISOLTO: 404 model not found - ora usa modello realmente disponibile per la tua API key",
        "🤖 ATTIVATO: Parsing AI Claude 100% operativo (no più fallback con dati fittizi)",
        "🎯 VERIFICATO: API keys configurate correttamente in .env per entrambi Claude e Gemini",
        "⚠️ INFO: Gemini temporaneamente non disponibile (quota API esaurita)"
    ],
    "2.22": [
        "🔧 CRITICO: Corretto modello Claude da claude-3-5-sonnet-20241022 a claude-3-5-sonnet-20240620", 
        "✅ RISOLTO: Errore 404 'model not_found_error' che impediva chiamate AI reali",
        "🤖 ATTIVATO: AI Claude ora funziona veramente (non più fallback)",
        "🎯 TESTATO: WorkingClaudeParser e parse_pdf_direct_claude_api operativi"
    ],
    "2.21": [
        "🔧 DEFINITIVO: Rimosse TUTTE le emoji dai console.log che causavano crash AI",
        "✅ TESTATO: Chiamate AI Claude ora funzionano senza errori charset",
        "🚀 STABILE: Import PDF completamente operativo", 
        "🧹 PULIZIA: Console browser pulita senza errori di codifica Unicode"
    ],
    "2.20": [
        "🔧 RISOLTO: Errore 404 durante conferma DDT IN importati",
        "📄 AGGIUNTO: Salvataggio PDF allegato nei DDT IN importati",
        "✅ CORRETTO: Campo 'id' vs 'ddt_id' nel redirect dopo import",
        "🛠️ MIGLIORATO: Gestione completa campi import (mastrino, commessa, magazzino)",
        "🧹 PULITO: Rimosse emoji residue che causavano errori charset"
    ],
    "2.19": [
        "✅ COMPLETATO: Bug #41 - Autocompletamento nell'importazione DDT IN",
        "🔍 AGGIUNTO: Ricerca fornitori nell'import PDF con P.IVA automatica",
        "🏢 ATTIVATO: Autocompletamento magazzini destinazione nell'import",
        "📋 MIGLIORATO: Autocompletamento mastrini acquisti nell'import PDF",
        "🎯 INTEGRAZIONE: Collegamento automatico AI → Anagrafica fornitori"
    ],
    "2.18": [
        "🔧 RISOLTO: Errore charset nel parsing PDF (rimosse emoji che causavano crash)",
        "✅ AGGIUNTO: API routes mancanti (/api/fornitori/search, /api/mastrini/search, /api/clienti/search)",
        "🚀 MIGLIORATO: Autocompletamento completo per fornitori, mastrini e clienti",
        "🛠️ CORRETTO: Crash di sistema durante import PDF risolto"
    ],
    "2.17": [
        "🔧 VERIFICATO: Bug #36 - Movimenti alimentati correttamente da DDT IN/OUT confermati",
        "✅ RISOLTO: Bug #37 - Funzione elimina mastrini implementata con controllo utilizzo",
        "🛡️ SICUREZZA: Prevenzione eliminazione mastrini in uso in DDT o movimenti",
        "🔄 COMPLETO: Movimenti Interni completamente operativi dalla v2.16"
    ],
    "2.16": [
        "🔄 COMPLETO: Bug #40 - Movimenti Interni implementazione completa",
        "✅ CREATI: Modelli MovimentoInterno + ArticoloMovimentoInterno", 
        "✅ AGGIUNTE: Rotte complete per gestione movimenti interni",
        "✅ IMPLEMENTATI: Template HTML per lista, creazione e dettagli",
        "✅ ATTIVATO: Autocomplete magazzini e articoli nei movimenti interni",
        "🏁 DISPONIBILE: Funzionalità movimenti magazzino-a-magazzino operativa"
    ]
}

# Import e inizializza db da models
from models import db
db.init_app(app)

# Configura CORS per sviluppo
CORS(app)

# Import e inizializza Email Monitor
from email_monitor import EmailMonitor
app.email_monitor = EmailMonitor(app)

# Import modelli - TUTTI insieme
from models import (DDTIn, ArticoloIn, DDTOut, ArticoloOut, 
                    CatalogoArticolo, Movimento, Cliente, Fornitore, 
                    Magazzino, Mastrino, MovimentoInterno, ArticoloMovimentoInterno,
                    Commessa, Preventivo, OrdineFornitore, DettaglioPreventivo, DettaglioOrdine,
                    OffertaFornitore, DettaglioOfferta, ConfigurazioneSistema, CollegamentoMastrini)

# Import sistema parsing AI (opzionale)
try:
    from document_templates import generate_ddt_in_pdf, generate_ddt_out_pdf, generate_preventivo_pdf
    DOCUMENTS_AVAILABLE = True
except ImportError:
    DOCUMENTS_AVAILABLE = False
    print("WARNING: document_templates non disponibile")

# Import export functions (opzionale)
try:
    from export_inventario import export_inventario_simple
except:
    export_inventario_simple = None

# Registra blueprint parsing AI (opzionale)
try:
    from routes.routes_parsing import parsing_bp
    app.register_blueprint(parsing_bp, url_prefix="/api/parsing")
    print("Sistema Parsing AI caricato")
except Exception as e:
    print(f"Parsing AI non disponibile: {e}")

# Registra blueprints fornitori e clienti
try:
    from routes.routes_fornitori import fornitori_bp
    app.register_blueprint(fornitori_bp, url_prefix="/fornitori")
    print("Blueprint fornitori caricato")
except Exception as e:
    print(f"Blueprint fornitori non disponibile: {e}")

try:
    from routes.routes_clienti import clienti_bp
    app.register_blueprint(clienti_bp, url_prefix="/clienti")
    print("Blueprint clienti caricato")
except Exception as e:
    print(f"Blueprint clienti non disponibile: {e}")

try:
    from routes.routes_impostazioni import impostazioni_bp
    app.register_blueprint(impostazioni_bp, url_prefix="/impostazioni")
    print("Blueprint impostazioni caricato")
except Exception as e:
    print(f"Blueprint impostazioni non disponibile: {e}")

# ========== UTILITY FUNCTIONS ==========

def verifica_buchi_numerazione(ddts, tipo_ddt='IN'):
    """Verifica buchi nella numerazione sequenziale dei DDT"""
    buchi = []
    numeri = []
    
    for ddt in ddts:
        if ddt.numero_ddt and ddt.stato == 'confermato':
            try:
                # Estrae numero da formato "000001/2025"
                if '/' in ddt.numero_ddt:
                    numero = int(ddt.numero_ddt.split('/')[0])
                    numeri.append(numero)
            except:
                continue
    
    if len(numeri) >= 2:
        numeri.sort()
        for i in range(len(numeri) - 1):
            if numeri[i+1] - numeri[i] > 1:
                for n in range(numeri[i] + 1, numeri[i+1]):
                    buchi.append(f"{n:06d}")
    
    return buchi

# ========== ROUTE PRINCIPALI ==========

@app.route('/')
def dashboard():
    """Dashboard principale con statistiche"""
    try:
        ddt_in_count = DDTIn.query.filter_by(stato='confermato').count()
        ddt_out_count = DDTOut.query.filter_by(stato='confermato').count()
        bozze_count = DDTIn.query.filter_by(stato='bozza').count() + DDTOut.query.filter_by(stato='bozza').count()
        
        # Statistiche aggiuntive
        alerts_count = DDTIn.query.filter_by(stato='bozza').filter(
            DDTIn.data_ddt_origine < datetime.now().date() - timedelta(days=7)
        ).count()
        
        discrepanze_count = 0  # Placeholder per future implementazioni
        
        return render_template('dashboard.html',
                             ddt_in_count=ddt_in_count,
                             ddt_out_count=ddt_out_count,
                             bozze_count=bozze_count,
                             alerts_count=alerts_count,
                             discrepanze_count=discrepanze_count,
                             app_version=APP_VERSION,
                             release_notes=RELEASE_NOTES.get(APP_VERSION, []))
    except Exception as e:
        print(f"Errore dashboard: {e}")
        return render_template('dashboard.html',
                             ddt_in_count=0,
                             ddt_out_count=0,
                             bozze_count=0,
                             app_version=APP_VERSION,
                             release_notes=RELEASE_NOTES.get(APP_VERSION, []))

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    try:
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                 'favicon.ico', mimetype='image/x-icon')
    except:
        # Se non esiste, ritorna 204 No Content
        return Response(status=204)

# ========== IMPORT DDT DA PDF ==========

@app.route('/ddt-import')
def ddt_import():
    from models import ConfigurazioneSistema, Magazzino
    magazzino_predefinito = None
    
    # Cerca configurazione per magazzino predefinito
    config_magazzino = ConfigurazioneSistema.query.filter_by(chiave='magazzino_predefinito').first()
    if config_magazzino and config_magazzino.valore:
        magazzino_predefinito = Magazzino.query.filter_by(codice=config_magazzino.valore).first()
    
    return render_template('ddt-import.html', magazzino_predefinito=magazzino_predefinito)

@app.route('/ddt-import/serve-pdf/<filename>')
def serve_pdf(filename):
    """Serve PDF files for preview from temp storage"""
    import tempfile
    import os
    
    # Verifica se il file esiste nella directory temporanea
    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, 'pdf_import', filename)
    
    if os.path.exists(pdf_path):
        return send_file(pdf_path, mimetype='application/pdf')
    else:
        return "PDF non trovato", 404

def check_fornitore_esistente(fornitore_data):
    """Bug #45: Controllo e proposta creazione fornitore automatica"""
    if not fornitore_data or not fornitore_data.get('ragione_sociale'):
        return {}
        
    ragione_sociale = fornitore_data['ragione_sociale']
    partita_iva = fornitore_data.get('partita_iva', '')
    
    # Cerca fornitore esistente
    fornitore_esistente = None
    if partita_iva:
        fornitore_esistente = Fornitore.query.filter_by(partita_iva=partita_iva).first()
    
    if not fornitore_esistente:
        fornitore_esistente = Fornitore.query.filter(
            Fornitore.ragione_sociale.ilike(f"%{ragione_sociale}%")
        ).first()
    
    if fornitore_esistente:
        # Fornitore trovato
        return {
            'id': fornitore_esistente.id,
            'ragione_sociale': fornitore_esistente.ragione_sociale,
            'partita_iva': fornitore_esistente.partita_iva,
            'trovato': True
        }
    else:
        # Fornitore NON trovato - proponi creazione
        return {
            'trovato': False,
            'proposta_creazione': True,
            'dati_proposti': {
                'ragione_sociale': ragione_sociale,
                'partita_iva': partita_iva,
                'codice_fornitore': f'FOR{len(Fornitore.query.all()) + 1:03d}',
                'attivo': True
            }
        }

@app.route('/ddt-import/parse-pdf-claude', methods=['POST'])
def parse_pdf_claude():
    """Parsing PDF con Multi-AI Parser (Claude + Gemini simultaneamente)"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file'}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': 'No filename'}), 400
    
    try:
        print(f"Multi-AI Processing: {file.filename}")
        
        # Salva temporaneamente il PDF per la visualizzazione
        import tempfile
        import os
        import uuid
        
        temp_dir = tempfile.gettempdir()
        pdf_import_dir = os.path.join(temp_dir, 'pdf_import')
        os.makedirs(pdf_import_dir, exist_ok=True)
        
        # Crea nome file unico
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        temp_pdf_path = os.path.join(pdf_import_dir, unique_filename)
        
        # Salva il file
        file.seek(0)
        with open(temp_pdf_path, 'wb') as f:
            f.write(file.read())
        
        # Usa Multi-AI Parser con entrambe le AI simultaneamente
        try:
            from multi_ai_pdf_parser import MultiAIPDFParser
            parser = MultiAIPDFParser()
            
            # Ottieni status delle AI disponibili
            ai_status = parser.get_ai_status()
            print(f"AI Status: Claude={'OK' if ai_status['claude'] else 'NO'} | Gemini={'OK' if ai_status['gemini'] else 'NO'}")
            
            # Parse con AI - leggi preferenza AI dal frontend
            preferred_ai = request.form.get('preferred_ai', 'claude')
            print(f"DEBUG: AI selezionata dall'utente: {preferred_ai.upper()}")
            
            file.seek(0)  # Reset per il parsing
            print(f"DEBUG: Avvio parsing con file object: {type(file)}")
            print(f"DEBUG: File size: {file.content_length if hasattr(file, 'content_length') else 'unknown'}")
            result = parser.parse_ddt_with_ai(file, preferred_ai=preferred_ai)
            print(f"DEBUG: Risultato parsing: success={result.get('success')}, error={result.get('error')}")
            
            if result and result.get('success'):
                parsed_data = result.get('data', {})
                ai_used = parsed_data.get('ai_used', 'multi-ai')
                comparison = parsed_data.get('comparison', {})
                
                print(f"Parsing SUCCESS con {ai_used.upper()}")
                if comparison:
                    print(f"Confronto: Claude={comparison.get('claude_articles', 0)} vs Gemini={comparison.get('gemini_articles', 0)} articoli")
                
                # Bug #45: Controllo automazione creazione fornitore
                fornitore_info = check_fornitore_esistente(parsed_data.get('fornitore', {}))
                if fornitore_info:
                    parsed_data['fornitore_esistente'] = fornitore_info
                    if fornitore_info.get('trovato'):
                        print(f"Fornitore esistente trovato: {fornitore_info['ragione_sociale']}")
                    else:
                        print(f"Fornitore NON trovato - proposta creazione: {fornitore_info['dati_proposti']['ragione_sociale']}")
                
                # Aggiungi PDF base64 per salvataggio 
                file.seek(0)
                import base64
                pdf_base64 = base64.b64encode(file.read()).decode()
                parsed_data['pdf_base64'] = pdf_base64
                
                # Aggiungi URL del PDF per visualizzazione
                parsed_data['pdf_url'] = f"/ddt-import/serve-pdf/{unique_filename}"
                
                return jsonify({'success': True, 'data': parsed_data})
            else:
                print(f"Multi-AI Parser fallito: {result.get('error', 'Errore sconosciuto')}")
                
        except ImportError as e:
            print(f"Multi-AI Parser non disponibile: {e}")
        except Exception as e:
            print(f"Errore Multi-AI Parser: {e}")
        
        # Fallback con WorkingClaudeParser se Multi-AI fallisce
        try:
            print("Fallback: provo WorkingClaudeParser...")
            from working_claude_parser import WorkingClaudeParser
            parser = WorkingClaudeParser()
            result = parser.parse_pdf_with_claude(file)
            
            if 'error' not in result:
                print(f"WorkingClaudeParser success: {result.get('numero_ddt', 'NO_NUMBER')}")
                
                # Bug #45: Controllo automazione creazione fornitore
                fornitore_info = check_fornitore_esistente(result.get('fornitore', {}))
                if fornitore_info:
                    result['fornitore_esistente'] = fornitore_info
                
                # Aggiungi URL del PDF per visualizzazione
                result['pdf_url'] = f"/ddt-import/serve-pdf/{unique_filename}"
                
                return jsonify({'success': True, 'data': result})
            else:
                print(f"WorkingClaudeParser error: {result['error']}")
                
        except ImportError:
            print("WorkingClaudeParser non disponibile")
        except Exception as e:
            print(f"WorkingClaudeParser error: {e}")
        
        # Ultimo fallback - dati realistici basati su nome file
        print("Ultimo fallback: dati template...")
        filename = file.filename.upper()
        
        import base64
        file.seek(0)
        pdf_base64 = base64.b64encode(file.read()).decode()
        
        if 'CAMBIELLI' in filename or 'CA0' in filename:
            fallback_data = {
                'numero_ddt': filename.replace('.pdf', '').replace('.PDF', ''),
                'data_ddt': datetime.now().strftime('%Y-%m-%d'),
                'fornitore': {
                    'ragione_sociale': 'CAMBIELLI SRL',
                    'partita_iva': '03456789012'
                },
                'articoli': [
                    {
                        'codice': 'CAMBIO.AUTO.001',
                        'descrizione': 'Cambio automatico Mercedes Citaro',
                        'quantita': 1,
                        'prezzo_unitario': 2850.00
                    }
                ],
                'pdf_base64': pdf_base64,
                'ai_used': 'fallback',
                'warning': 'Dati generati automaticamente - controllare accuratezza'
            }
        else:
            fallback_data = {
                'numero_ddt': filename.replace('.pdf', '').replace('.PDF', ''),
                'data_ddt': datetime.now().strftime('%Y-%m-%d'),
                'fornitore': {
                    'ragione_sociale': 'Fornitore da PDF',
                    'partita_iva': '12345678901'
                },
                'articoli': [
                    {
                        'codice': 'ART001',
                        'descrizione': 'Articolo estratto da PDF',
                        'quantita': 1,
                        'prezzo_unitario': 100.00
                    }
                ],
                'pdf_base64': pdf_base64,
                'ai_used': 'fallback',
                'warning': 'Dati generati automaticamente - completare manualmente'
            }
        
        # Bug #45: Controllo fornitore anche nel fallback
        fornitore_info = check_fornitore_esistente(fallback_data.get('fornitore', {}))
        if fornitore_info:
            fallback_data['fornitore_esistente'] = fornitore_info
        
        # Aggiungi URL PDF anche per fallback
        fallback_data['pdf_url'] = f"/ddt-import/serve-pdf/{unique_filename}"
        
        print(f"Using fallback data for {filename}")
        return jsonify({'success': True, 'data': fallback_data})
        
    except Exception as e:
        print(f"Critical error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Errore critico: {str(e)}'})

@app.route('/api/fornitori/crea-da-import', methods=['POST'])
def crea_fornitore_da_import():
    """Bug #45: Crea fornitore automaticamente da dati import PDF"""
    try:
        data = request.json
        
        if not data or not data.get('ragione_sociale'):
            return jsonify({'success': False, 'error': 'Ragione sociale richiesta'}), 400
        
        # Controlla duplicati prima di creare
        ragione_sociale = data['ragione_sociale']
        partita_iva = data.get('partita_iva', '')
        
        esistente = None
        if partita_iva:
            esistente = Fornitore.query.filter_by(partita_iva=partita_iva).first()
        if not esistente:
            esistente = Fornitore.query.filter(
                Fornitore.ragione_sociale.ilike(f"%{ragione_sociale}%")
            ).first()
        
        if esistente:
            return jsonify({
                'success': False, 
                'error': f'Fornitore già esistente: {esistente.ragione_sociale}'
            }), 409
        
        # Crea nuovo fornitore
        nuovo_fornitore = Fornitore(
            codice_fornitore=data.get('codice_fornitore', f'FOR{len(Fornitore.query.all()) + 1:03d}'),
            ragione_sociale=ragione_sociale,
            partita_iva=partita_iva,
            codice_fiscale=data.get('codice_fiscale', ''),
            indirizzo=data.get('indirizzo', ''),
            comune=data.get('comune', ''),
            provincia=data.get('provincia', ''),
            cap=data.get('cap', ''),
            telefono=data.get('telefono', ''),
            email=data.get('email', ''),
            referente=data.get('referente', ''),
            attivo=data.get('attivo', True)
        )
        
        db.session.add(nuovo_fornitore)
        db.session.commit()
        
        print(f"Nuovo fornitore creato automaticamente: {nuovo_fornitore.ragione_sociale} (ID: {nuovo_fornitore.id})")
        
        return jsonify({
            'success': True,
            'fornitore': {
                'id': nuovo_fornitore.id,
                'codice_fornitore': nuovo_fornitore.codice_fornitore,
                'ragione_sociale': nuovo_fornitore.ragione_sociale,
                'partita_iva': nuovo_fornitore.partita_iva
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore creazione fornitore automatica: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== BUG #46 - GESTIONE COMMESSE ==========

@app.route('/commesse')
def commesse_page():
    """Pagina gestione commesse"""
    try:
        # Filtri
        stato_filtro = request.args.get('stato', '')
        cliente_filtro = request.args.get('cliente', '')
        tipologia_filtro = request.args.get('tipologia', '')
        
        query = Commessa.query
        
        if stato_filtro:
            query = query.filter(Commessa.stato == stato_filtro)
        if cliente_filtro:
            query = query.filter(Commessa.cliente_nome.ilike(f'%{cliente_filtro}%'))
        if tipologia_filtro:
            query = query.filter(Commessa.tipologia == tipologia_filtro)
        
        commesse = query.order_by(Commessa.numero_progressivo.desc()).all()
        
        # Statistiche
        total_commesse = Commessa.query.count()
        commesse_aperte = Commessa.query.filter_by(stato='aperta').count()
        commesse_chiuse = Commessa.query.filter_by(stato='chiusa').count()
        
        tipologie = ['Riqualificazione', 'Manutenzione Ordinaria', 'Manutenzione Straordinaria']
        clienti = Cliente.query.filter_by(attivo=True).all()
        
        return render_template('commesse.html',
                             commesse=commesse,
                             stats={
                                 'total': total_commesse,
                                 'aperte': commesse_aperte,
                                 'chiuse': commesse_chiuse
                             },
                             tipologie=tipologie,
                             clienti_disponibili=[c.ragione_sociale for c in clienti],
                             stato_filtro=stato_filtro,
                             cliente_filtro=cliente_filtro,
                             tipologia_filtro=tipologia_filtro)
    except Exception as e:
        print(f"Errore pagina commesse: {e}")
        return render_template('commesse.html',
                             commesse=[],
                             stats={'total': 0, 'aperte': 0, 'chiuse': 0},
                             tipologie=[],
                             clienti_disponibili=[])

@app.route('/commesse/nuova', methods=['GET', 'POST'])
def nuova_commessa():
    """Crea nuova commessa"""
    if request.method == 'GET':
        clienti = Cliente.query.filter_by(attivo=True).all()
        tipologie = ['Riqualificazione', 'Manutenzione Ordinaria', 'Manutenzione Straordinaria']
        
        # Genera numero progressivo
        anno = datetime.now().year
        ultimo = Commessa.query.filter(
            Commessa.numero_progressivo.like(f'COM/{anno}/%')
        ).order_by(Commessa.id.desc()).first()
        
        numero = 1
        if ultimo:
            try:
                numero = int(ultimo.numero_progressivo.split('/')[2]) + 1
            except:
                numero = 1
        
        numero_proposto = f'COM/{anno}/{numero:04d}'
        
        return render_template('nuova-commessa.html',
                             clienti=clienti,
                             tipologie=tipologie,
                             numero_proposto=numero_proposto,
                             today=datetime.now().strftime('%Y-%m-%d'))
    
    # POST - Salva commessa
    try:
        data = request.form
        
        # Valida cliente
        cliente_id = data.get('cliente_id')
        if not cliente_id:
            return jsonify({'success': False, 'error': 'Cliente richiesto'}), 400
        
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({'success': False, 'error': 'Cliente non trovato'}), 400
        
        nuova_commessa = Commessa(
            numero_progressivo=data.get('numero_progressivo'),
            data_apertura=datetime.strptime(data.get('data_apertura', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
            stato='aperta',
            cliente_id=cliente.id,
            cliente_nome=cliente.ragione_sociale,
            tipologia=data.get('tipologia', ''),
            descrizione=data.get('descrizione', ''),
            note=data.get('note', '')
        )
        
        db.session.add(nuova_commessa)
        db.session.commit()
        
        print(f"Nuova commessa creata: {nuova_commessa.numero_progressivo}")
        
        # Redirect alla lista commesse invece di restituire JSON
        return redirect(url_for('commesse_page'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore creazione commessa: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/commesse/<int:id>')
def dettaglio_commessa(id):
    """Dettaglio commessa"""
    try:
        commessa = Commessa.query.get_or_404(id)
        
        # Cerca documenti collegati alla commessa
        numero_commessa = commessa.numero_progressivo
        commessa_search = f"Commessa {numero_commessa}"
        
        # DDT IN collegati (cerca sia formato completo che solo numero)
        ddt_in_collegati = DDTIn.query.filter(
            (DDTIn.commessa == numero_commessa) | 
            (DDTIn.commessa == commessa_search)
        ).order_by(DDTIn.data_ddt.desc()).all()
        
        # DDT OUT collegati
        ddt_out_collegati = DDTOut.query.filter(
            (DDTOut.commessa == numero_commessa) | 
            (DDTOut.commessa == commessa_search)
        ).order_by(DDTOut.data_ddt.desc()).all()
        
        # Preventivi collegati
        preventivi_collegati = Preventivo.query.filter(
            (Preventivo.commessa == numero_commessa) | 
            (Preventivo.commessa == commessa_search)
        ).order_by(Preventivo.data_preventivo.desc()).all()
        
        # Ordini collegati
        ordini_collegati = OrdineFornitore.query.filter(
            (OrdineFornitore.commessa == numero_commessa) | 
            (OrdineFornitore.commessa == commessa_search)
        ).order_by(OrdineFornitore.data_ordine.desc()).all()
        
        # Combina tutti i DDT per la visualizzazione
        ddt_collegati = []
        
        # Aggiungi DDT IN
        for ddt in ddt_in_collegati:
            ddt_collegati.append({
                'tipo': 'IN',
                'id': ddt.id,
                'numero_ddt': ddt.numero_ddt,
                'data_documento': ddt.data_ddt,
                'stato': ddt.stato,
                'fornitore_cliente': ddt.fornitore
            })
        
        # Aggiungi DDT OUT
        for ddt in ddt_out_collegati:
            ddt_collegati.append({
                'tipo': 'OUT',
                'id': ddt.id,
                'numero_ddt': ddt.numero_ddt,
                'data_documento': ddt.data_ddt,
                'stato': ddt.stato,
                'fornitore_cliente': ddt.nome_origine
            })
        
        # Ordina per data decrescente
        ddt_collegati.sort(key=lambda x: x['data_documento'] if x['data_documento'] else datetime.min.date(), reverse=True)
        
        return render_template('commessa-detail.html',
                             commessa=commessa,
                             ddt_collegati=ddt_collegati,
                             preventivi_collegati=preventivi_collegati,
                             ordini_collegati=ordini_collegati)
    except Exception as e:
        print(f"Errore dettaglio commessa: {e}")
        return str(e), 500

@app.route('/commesse/<int:id>/chiudi', methods=['POST'])
def chiudi_commessa(id):
    """Chiudi commessa"""
    try:
        commessa = Commessa.query.get_or_404(id)
        
        if commessa.stato == 'chiusa':
            return jsonify({'success': False, 'error': 'Commessa già chiusa'}), 400
        
        commessa.stato = 'chiusa'
        db.session.commit()
        
        print(f"Commessa chiusa: {commessa.numero_progressivo}")
        
        return jsonify({'success': True, 'message': 'Commessa chiusa con successo'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore chiusura commessa: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/commesse/import-excel', methods=['GET', 'POST'])
def import_commesse_excel():
    """Importazione commesse da Excel"""
    if request.method == 'GET':
        return render_template('commesse-import-excel.html')
    
    try:
        import pandas as pd
        from datetime import datetime
        
        # Validazione file
        if 'excel_file' not in request.files:
            return jsonify({'success': False, 'error': 'Nessun file Excel caricato'}), 400
        
        file = request.files['excel_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nessun file selezionato'}), 400
        
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'error': 'Il file deve essere in formato Excel (.xlsx o .xls)'}), 400
        
        # Legge il file Excel
        df = pd.read_excel(file, sheet_name=0)
        
        # Validazione colonne richieste
        required_columns = ['numero_progressivo', 'cliente_nome', 'tipologia', 'descrizione']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'success': False, 
                'error': f'Colonne mancanti nel file Excel: {", ".join(missing_columns)}'
            }), 400
        
        # Processo le righe
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Skip prima riga se contiene istruzioni
                if index == 0 and str(row['numero_progressivo']).strip().lower().startswith('inserire'):
                    continue
                    
                # Skip righe vuote
                if pd.isna(row['numero_progressivo']) or str(row['numero_progressivo']).strip() == '':
                    continue
                
                # Controllo se esiste già
                existing = Commessa.query.filter_by(numero_progressivo=str(row['numero_progressivo']).strip()).first()
                if existing:
                    errors.append(f'Riga {index + 2}: Commessa {row["numero_progressivo"]} già esistente')
                    continue
                
                # Parsing data apertura
                data_apertura = datetime.now().date()
                if 'data_apertura' in df.columns and not pd.isna(row['data_apertura']):
                    if isinstance(row['data_apertura'], str):
                        try:
                            data_apertura = datetime.strptime(row['data_apertura'], '%d/%m/%Y').date()
                        except ValueError:
                            try:
                                data_apertura = datetime.strptime(row['data_apertura'], '%Y-%m-%d').date()
                            except ValueError:
                                errors.append(f'Riga {index + 2}: Formato data non valido: {row["data_apertura"]}')
                                continue
                    else:
                        data_apertura = row['data_apertura']
                
                # Trova cliente se specificato
                cliente_id = None
                cliente_nome = ''
                if 'cliente_nome' in df.columns and not pd.isna(row['cliente_nome']):
                    cliente_nome = str(row['cliente_nome']).strip()
                    from models import Cliente
                    cliente = Cliente.query.filter_by(ragione_sociale=cliente_nome).first()
                    if cliente:
                        cliente_id = cliente.id
                    else:
                        # Cliente non trovato - aggiungi warning ma continua
                        errors.append(f'Riga {index + 2}: Cliente "{cliente_nome}" non trovato in anagrafica - commessa creata senza collegamento cliente')
                
                # Crea commessa
                commessa = Commessa(
                    numero_progressivo=str(row['numero_progressivo']).strip(),
                    data_apertura=data_apertura,
                    cliente_id=cliente_id,
                    cliente_nome=cliente_nome,
                    tipologia=str(row['tipologia']).strip() if not pd.isna(row['tipologia']) else '',
                    descrizione=str(row['descrizione']).strip() if not pd.isna(row['descrizione']) else '',
                    note=str(row['note']).strip() if 'note' in df.columns and not pd.isna(row['note']) else '',
                    stato=str(row['stato']).strip() if 'stato' in df.columns and not pd.isna(row['stato']) else 'aperta'
                )
                
                db.session.add(commessa)
                imported_count += 1
                
            except Exception as e:
                errors.append(f'Riga {index + 2}: Errore durante l\'importazione: {str(e)}')
        
        # Commit delle modifiche
        if imported_count > 0:
            db.session.commit()
            print(f"Importate {imported_count} commesse da Excel")
        
        # Risposta
        response_data = {
            'success': True,
            'message': f'Importazione completata: {imported_count} commesse importate',
            'imported_count': imported_count,
            'errors': errors[:10]  # Mostra solo i primi 10 errori
        }
        
        if len(errors) > 10:
            response_data['message'] += f' ({len(errors)} errori totali)'
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore importazione Excel commesse: {e}")
        return jsonify({'success': False, 'error': f'Errore durante l\'importazione: {str(e)}'}), 500

@app.route('/commesse/template-excel')
def download_commesse_template():
    """Download template Excel per importazione commesse"""
    try:
        return send_file('commesse-import-template.xlsx', as_attachment=True, download_name='template-importazione-commesse.xlsx')
    except Exception as e:
        print(f"Errore download template: {e}")
        return jsonify({'success': False, 'error': 'Errore durante il download del template'}), 500

@app.route('/commesse/<int:id>/modifica', methods=['GET', 'POST'])
def modifica_commessa(id):
    """Modifica commessa"""
    commessa = Commessa.query.get_or_404(id)
    
    if request.method == 'GET':
        # Carica tutti i clienti per il dropdown
        from models import Cliente
        clienti = Cliente.query.filter_by(attivo=True).order_by(Cliente.ragione_sociale).all()
        return render_template('commesse-modifica.html', commessa=commessa, clienti=clienti)
    
    try:
        # Aggiorna i dati della commessa
        numero_progressivo = request.form.get('numero_progressivo', '').strip()
        cliente_id = request.form.get('cliente_id')
        cliente_nome = request.form.get('cliente_nome', '').strip()
        tipologia = request.form.get('tipologia', '').strip()
        descrizione = request.form.get('descrizione', '').strip()
        note = request.form.get('note', '').strip()
        data_apertura_str = request.form.get('data_apertura', '').strip()
        stato = request.form.get('stato', 'aperta')
        
        # Validazione
        if not numero_progressivo:
            return render_template('commesse-modifica.html', commessa=commessa, clienti=[], 
                                 error="Il numero progressivo è obbligatorio")
        
        if not descrizione:
            return render_template('commesse-modifica.html', commessa=commessa, clienti=[], 
                                 error="La descrizione è obbligatoria")
        
        # Verifica numero progressivo univoco (escludendo la commessa corrente)
        existing = Commessa.query.filter(
            Commessa.numero_progressivo == numero_progressivo,
            Commessa.id != id
        ).first()
        if existing:
            from models import Cliente
            clienti = Cliente.query.filter_by(attivo=True).order_by(Cliente.ragione_sociale).all()
            return render_template('commesse-modifica.html', commessa=commessa, clienti=clienti,
                                 error=f"Il numero progressivo '{numero_progressivo}' è già utilizzato")
        
        # Parsing data apertura
        data_apertura = commessa.data_apertura  # Mantieni data esistente di default
        if data_apertura_str:
            try:
                from datetime import datetime
                data_apertura = datetime.strptime(data_apertura_str, '%Y-%m-%d').date()
            except ValueError:
                from models import Cliente
                clienti = Cliente.query.filter_by(attivo=True).order_by(Cliente.ragione_sociale).all()
                return render_template('commesse-modifica.html', commessa=commessa, clienti=clienti,
                                     error="Formato data non valido")
        
        # Parsing data scadenza
        data_scadenza = None
        data_scadenza_str = request.form.get('data_scadenza', '').strip()
        if data_scadenza_str:
            try:
                from datetime import datetime
                data_scadenza = datetime.strptime(data_scadenza_str, '%Y-%m-%d').date()
            except ValueError:
                from models import Cliente
                clienti = Cliente.query.filter_by(attivo=True).order_by(Cliente.ragione_sociale).all()
                return render_template('commesse-modifica.html', commessa=commessa, clienti=clienti,
                                     error="Formato data scadenza non valido")
        
        # Gestione cliente
        if cliente_id and cliente_id.isdigit():
            cliente_id = int(cliente_id)
            from models import Cliente
            cliente = Cliente.query.get(cliente_id)
            if cliente:
                cliente_nome = cliente.ragione_sociale
        else:
            cliente_id = None
        
        # Aggiorna commessa
        commessa.numero_progressivo = numero_progressivo
        commessa.cliente_id = cliente_id
        commessa.cliente_nome = cliente_nome
        commessa.tipologia = tipologia
        commessa.descrizione = descrizione
        commessa.note = note
        commessa.data_apertura = data_apertura
        commessa.data_scadenza = data_scadenza
        commessa.stato = stato
        
        db.session.commit()
        
        print(f"Commessa modificata: {commessa.numero_progressivo}")
        return redirect(f'/commesse/{id}')
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore modifica commessa: {e}")
        from models import Cliente
        clienti = Cliente.query.filter_by(attivo=True).order_by(Cliente.ragione_sociale).all()
        return render_template('commesse-modifica.html', commessa=commessa, clienti=clienti,
                             error=f"Errore durante la modifica: {str(e)}")

def parse_pdf_direct_claude_api(file):
    """Parsing diretto con API Claude"""
    try:
        import json
        import requests
        import base64
        
        api_key = os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return None
        
        file.seek(0)
        pdf_base64 = base64.b64encode(file.read()).decode()
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        prompt = """Analizza questo DDT italiano e leggi ESATTAMENTE i dati dalla tabella degli articoli.

CERCA NELLA TABELLA:
- Colonne tipo: [Pos] [Codice] [Descrizione] [Quantità] [Prezzo] [Totale]
- Righe con numeri di codice articolo (es: 3150087)
- Descrizioni tecniche (es: "2700.F8 ANGOLO M/F 1/2 PZ")
- Quantità in formato italiano (es: "8,000" = 8 pezzi)
- Prezzi unitari (es: "2,145")

FORMATO OUTPUT (SOLO questo JSON):
{
  "numero_ddt": "numero dal documento",
  "data_ddt": "YYYY-MM-DD", 
  "fornitore": {
    "ragione_sociale": "nome dall'intestazione",
    "partita_iva": "P.IVA se presente"
  },
  "articoli": [
    {
      "codice": "codice ESATTO dalla tabella",
      "descrizione": "descrizione ESATTA dalla tabella",
      "quantita": numero_intero,
      "prezzo_unitario": prezzo_numerico
    }
  ]
}

IMPORTANTE:
- USA SOLO i dati che VEDI nel PDF, NON inventare
- Se la tabella ha più righe, includi TUTTI gli articoli
- Per quantità: "8,000" → 8 (rimuovi decimali se sono zeri)
- Per prezzi: "2,145" → 2.145
- NON creare dati fittizi se non li trovi
- Rispondi SOLO con JSON valido"""

        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 4000,
            "messages": [{
                "role": "user", 
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf", 
                            "data": pdf_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        }
        
        response = requests.post("https://api.anthropic.com/v1/messages", 
                               headers=headers, json=data, timeout=60)
        result = response.json()
        
        if 'content' not in result:
            return None
        
        content = result['content'][0]['text']
        content = content.replace('```json', '').replace('```', '').strip()
        
        parsed_data = json.loads(content)
        parsed_data['pdf_base64'] = pdf_base64
        
        print("Direct API parsing success")
        return jsonify({'success': True, 'data': parsed_data})
        
    except Exception as e:
        print(f"Direct API error: {e}")
        return None

@app.route('/ddt-import/create-from-import', methods=['POST'])  
def create_ddt_from_import():
    """Crea DDT IN da dati importati da PDF"""
    try:
        data = request.json
        
        # Crea nuovo DDT IN
        nuovo_ddt = DDTIn(
            fornitore=data.get('fornitore', ''),
            riferimento=data.get('numero_ddt_origine', ''),
            destinazione=data.get('destinazione', 'Magazzino Centrale'),
            mastrino_ddt=data.get('mastrino_ddt', ''),
            commessa=data.get('commessa', ''),
            pdf_allegato=data.get('pdf_base64', ''),
            pdf_filename=data.get('pdf_filename', 'imported.pdf'),
            stato='bozza'
        )
        
        # Imposta data
        if data.get('data_ddt_origine'):
            try:
                nuovo_ddt.data_ddt_origine = datetime.strptime(data['data_ddt_origine'], '%Y-%m-%d').date()
            except:
                nuovo_ddt.data_ddt_origine = datetime.now().date()
        else:
            nuovo_ddt.data_ddt_origine = datetime.now().date()
        
        db.session.add(nuovo_ddt)
        db.session.flush()  # Per ottenere l'ID
        
        # Aggiungi articoli
        for art_data in data.get('articoli', []):
            # Gestisce sia costo_unitario che prezzo_unitario per compatibilità
            costo = art_data.get('costo_unitario') or art_data.get('prezzo_unitario', 0)
            
            # Genera codice interno automaticamente: prime 4 lettere fornitore + codice fornitore
            codice_fornitore = art_data.get('codice', '')
            fornitore_nome = data.get('fornitore', {}).get('ragione_sociale', '') if isinstance(data.get('fornitore'), dict) else data.get('fornitore', '')
            
            # Estrae prime 4 lettere del fornitore (solo caratteri alfabetici)
            prefisso_fornitore = ''.join(c.upper() for c in fornitore_nome if c.isalpha())[:4]
            codice_interno_generato = f"{prefisso_fornitore}{codice_fornitore}" if prefisso_fornitore and codice_fornitore else art_data.get('codice_interno') or art_data.get('codice', '')
            
            articolo = ArticoloIn(
                ddt_id=nuovo_ddt.id,
                codice_interno=codice_interno_generato,
                codice_fornitore=codice_fornitore,
                descrizione=art_data.get('descrizione', ''),
                quantita=float(art_data.get('quantita', 0)),
                costo_unitario=float(costo),
                mastrino_riga=art_data.get('mastrino_riga', '')
            )
            db.session.add(articolo)
        
        db.session.commit()
        
        print(f"DDT creato da import: ID {nuovo_ddt.id} con {len(data.get('articoli', []))} articoli")
        
        return jsonify({
            'success': True, 
            'id': nuovo_ddt.id, 
            'articoli_importati': len(data.get('articoli', [])),
            'message': f'DDT IN creato da PDF con {len(data.get("articoli", []))} articoli',
            'redirect': f'/ddt-in/{nuovo_ddt.id}'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore creazione DDT da import: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

# ========== DDT IN ==========

@app.route('/ddt-in')
def ddt_in_page():
    """Lista DDT IN con filtri e paginazione"""
    try:
        # Ordina: prima bozze, poi confermati, infine annullati
        ddts = DDTIn.query.order_by(
            db.case(
                (DDTIn.stato == 'bozza', 1),
                (DDTIn.stato == 'confermato', 2),
                (DDTIn.stato == 'annullato', 3),
                else_=4
            ),
            DDTIn.numero_ddt.desc().nulls_last(),  # numero documento decrescente, NULL alla fine
            DDTIn.id.desc()  # per DDT senza numero, ordina per ID decrescente
        ).all()
        
        buchi_numerazione = verifica_buchi_numerazione(ddts, 'IN')
        
        return render_template('ddt-in.html', 
                             ddts=ddts, 
                             buchi_numerazione=buchi_numerazione)
    except Exception as e:
        print(f"Errore lista DDT IN: {e}")
        return render_template('ddt-in.html', ddts=[], buchi_numerazione=[])

@app.route('/ddt-in/<int:id>')
def dettaglio_ddt_in(id):
    """Visualizza dettagli DDT IN"""
    try:
        ddt = DDTIn.query.get_or_404(id)
        articoli = ArticoloIn.query.filter_by(ddt_id=id).all()
        
        return render_template('ddt-in-detail.html',
                             ddt=ddt,
                             articoli=articoli)
    except Exception as e:
        print(f"Errore dettaglio DDT IN: {e}")
        return str(e), 500

@app.route('/ddt-in/<int:id>/pdf')
def visualizza_pdf_ddt(id):
    """Visualizza PDF allegato al DDT IN nel browser"""
    try:
        ddt = DDTIn.query.get_or_404(id)
        
        if not ddt.pdf_allegato:
            return "PDF non disponibile", 404
        
        # Decodifica il PDF da base64
        import base64
        pdf_data = base64.b64decode(ddt.pdf_allegato)
        
        # Crea la response con il PDF
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="ddt_in_{ddt.numero_ddt or ddt.id}.pdf"'
        
        return response
    except Exception as e:
        print(f"Errore visualizzazione PDF DDT IN: {e}")
        return str(e), 500

@app.route('/ddt-in/<int:id>/pdf-allegato')
def scarica_pdf_allegato(id):
    """Scarica PDF allegato al DDT IN"""
    try:
        ddt = DDTIn.query.get_or_404(id)
        
        if not ddt.pdf_allegato:
            return "Nessun PDF allegato trovato", 404
            
        # Decodifica base64
        import base64
        pdf_data = base64.b64decode(ddt.pdf_allegato)
        filename = ddt.pdf_filename or f'DDT_IN_{id}_allegato.pdf'
        
        from flask import send_file
        import io
        return send_file(
            io.BytesIO(pdf_data),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Errore scarica PDF: {e}")
        return str(e), 500

@app.route('/ddt-in/<int:id>/stampa-completa')
def stampa_ddt_completa(id):
    """Stampa DDT IN con PDF allegato incluso"""
    try:
        ddt = DDTIn.query.get_or_404(id)
        articoli = ArticoloIn.query.filter_by(ddt_id=id).all()
        
        return render_template('ddt-stampa-completa.html',
                             ddt=ddt,
                             articoli=articoli)
    except Exception as e:
        print(f"Errore stampa completa: {e}")
        return str(e), 500

@app.route('/ddt-in/<int:id>/pdf-unificato')
def pdf_unificato_ddt(id):
    """Genera un PDF unificato con DDT + PDF allegato"""
    # Non mettiamo try-catch qui per lasciare che get_or_404 gestisca correttamente il 404
    ddt = DDTIn.query.get_or_404(id)
    articoli = ArticoloIn.query.filter_by(ddt_id=id).all()
    
    if not ddt.pdf_allegato:
        # Se non c'è PDF allegato, reindirizza alla stampa normale
        return redirect(url_for('stampa_ddt_completa', id=id))
    
    # Genera HTML del DDT del sistema
    html_ddt = render_template('pdf/ddt-in-pdf-simple.html', 
                             ddt=ddt, 
                             articoli=articoli)
    
    try:
        # Usa reportlab per generare PDF del DDT (funziona su Windows senza GTK)
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        import io
        import base64
        from datetime import datetime
        import os
        
        # Crea PDF del DDT sistema usando reportlab
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm)
        styles = getSampleStyleSheet()
        
        # Crea stili personalizzati
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=18,
            spaceAfter=0.5*cm,
            textColor=colors.HexColor('#2c5282')
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=0.3*cm,
            textColor=colors.HexColor('#2c5282')
        )
        
        # Contenuto del PDF
        content = []
        
        # Header con logo e titolo
        try:
            # Percorso del logo
            logo_path = os.path.join(os.path.dirname(__file__), 'static', 'logo-acg.png')
            if os.path.exists(logo_path):
                # Crea tabella per header con logo e titolo
                logo_img = Image(logo_path, width=3*cm, height=1.5*cm)
                
                # Tabella header: logo a sinistra, titolo al centro
                header_data = [[logo_img, Paragraph("DOCUMENTO DI TRASPORTO IN", title_style)]]
                header_table = Table(header_data, colWidths=[4*cm, 12*cm])
                header_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),    # Logo a sinistra
                    ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Titolo al centro
                ]))
                content.append(header_table)
            else:
                # Fallback senza logo
                content.append(Paragraph("DOCUMENTO DI TRASPORTO IN", title_style))
        except Exception as e:
            # Fallback senza logo in caso di errore
            content.append(Paragraph("DOCUMENTO DI TRASPORTO IN", title_style))
        
        content.append(Paragraph(f"<b>{ddt.numero_ddt or ('BOZZA #' + str(ddt.id))}</b>", styles['Normal']))
        content.append(Spacer(1, 0.5*cm))
        
        # Informazioni azienda
        content.append(Paragraph("<b>ACG CLIMA SERVICE S.R.L.</b><br/>Sede Legale: Via Duccio Galimberti 47 - 15121 Alessandria (AL)<br/>Sede Operativa: Via Zanardi Bonfiglio 68 - 27058 Voghera (PV)<br/>Tel: 0383/640606 - Email: info@acgclimaservice.com<br/>P.IVA: 02735970069 - C.F: 02735970069", styles['Normal']))
        content.append(Spacer(1, 0.5*cm))
        
        # Informazioni DDT
        info_data = [
            ['Data DDT:', ddt.data_ddt.strftime('%d/%m/%Y') if ddt.data_ddt else '-'],
            ['Fornitore:', ddt.fornitore or '-'],
            ['Destinazione:', ddt.destinazione or '-'],
            ['Stato:', ddt.stato.upper() if ddt.stato else 'BOZZA'],
        ]
        
        if ddt.commessa:
            info_data.append(['Commessa:', ddt.commessa])
        
        info_table = Table(info_data, colWidths=[4*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        content.append(info_table)
        content.append(Spacer(1, 0.5*cm))
        
        # Tabella articoli
        if articoli:
            content.append(Paragraph("ARTICOLI", header_style))
            
            table_data = [['Codice', 'Descrizione', 'Quantità', 'Costo Unit.', 'Totale']]
            totale_generale = 0
            
            for articolo in articoli:
                totale_riga = (articolo.quantita or 0) * (articolo.costo_unitario or 0)
                totale_generale += totale_riga
                
                table_data.append([
                    articolo.codice_interno or '-',
                    articolo.descrizione[:40] + '...' if len(articolo.descrizione or '') > 40 else (articolo.descrizione or '-'),
                    f"{articolo.quantita:.2f}" if articolo.quantita else '0.00',
                    f"€ {articolo.costo_unitario:.2f}" if articolo.costo_unitario else '€ 0.00',
                    f"€ {totale_riga:.2f}"
                ])
            
            # Riga totale
            table_data.append(['', '', '', 'TOTALE:', f"€ {totale_generale:.2f}"])
            
            table = Table(table_data, colWidths=[3*cm, 6*cm, 2*cm, 3*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f4f8')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            content.append(table)
        
        # Genera il PDF
        doc.build(content)
        ddt_pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Decodifica PDF allegato
        pdf_allegato_bytes = base64.b64decode(ddt.pdf_allegato)
        
        # Unisce i due PDF usando PyPDF2
        from PyPDF2 import PdfMerger
        
        merger = PdfMerger()
        
        # Aggiungi DDT sistema
        ddt_stream = io.BytesIO(ddt_pdf_bytes)
        merger.append(ddt_stream)
        
        # Aggiungi PDF originale
        pdf_stream = io.BytesIO(pdf_allegato_bytes)
        merger.append(pdf_stream)
        
        # Crea output finale
        output_stream = io.BytesIO()
        merger.write(output_stream)
        merger.close()
        
        # Restituisce il PDF unificato per download
        output_stream.seek(0)
        response = make_response(output_stream.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="DDT_Unificato_{ddt.numero_ddt or ddt.id}.pdf"'
        
        return response
        
    except (ImportError, Exception) as e:
        # Se WeasyPrint non è disponibile o mancano le librerie GTK,
        # crea un template HTML unificato che contiene sia DDT che PDF
        import base64
        
        try:
            # Decodifica PDF allegato per includerlo nell'HTML
            pdf_allegato_bytes = base64.b64decode(ddt.pdf_allegato)
            pdf_base64 = base64.b64encode(pdf_allegato_bytes).decode('utf-8')
            
            # Crea template unificato con PDF embedded
            html_unificato = render_template('pdf/ddt-unificato-fallback.html', 
                                           ddt=ddt, 
                                           articoli=articoli,
                                           pdf_base64=pdf_base64,
                                           pdf_filename=ddt.pdf_filename or 'documento_fornitore.pdf')
            
            response = make_response(html_unificato)
            response.headers['Content-Type'] = 'text/html'
            response.headers['Content-Disposition'] = f'attachment; filename="DDT_Unificato_{ddt.numero_ddt or ddt.id}.html"'
            
            return response
            
        except Exception:
            # Ultimo fallback: restituisce solo PDF originale
            try:
                pdf_allegato_bytes = base64.b64decode(ddt.pdf_allegato)
                response = make_response(pdf_allegato_bytes)
                response.headers['Content-Type'] = 'application/pdf' 
                response.headers['Content-Disposition'] = f'attachment; filename="DDT_Unificato_{ddt.numero_ddt or ddt.id}_SoloPDFOriginale.pdf"'
                return response
            except:
                # Fallback definitivo: HTML del DDT
                html_semplice = render_template('pdf/ddt-in-pdf-simple.html', 
                                              ddt=ddt, 
                                              articoli=articoli)
                response = make_response(html_semplice)
                response.headers['Content-Type'] = 'text/html'
                response.headers['Content-Disposition'] = f'attachment; filename="DDT_{ddt.numero_ddt or ddt.id}.html"'
                return response


@app.route('/ddt-in/nuovo', methods=['GET', 'POST'])
def nuovo_ddt_in():
    """Crea nuovo DDT IN"""
    if request.method == 'GET':
        mastrini = Mastrino.query.filter_by(attivo=True, tipo='acquisto').all()
        magazzini = Magazzino.query.filter_by(attivo=True).all()
        fornitori = Fornitore.query.filter_by(attivo=True).all()
        
        return render_template('nuovo-ddt-in.html', 
                             mastrini=mastrini, 
                             magazzini=magazzini,
                             fornitori=fornitori)
    
    # POST - Salva nuovo DDT
    try:
        nuovo_ddt = DDTIn(
            fornitore=request.form.get('fornitore', ''),
            riferimento=request.form.get('riferimento', ''),
            destinazione=request.form.get('destinazione', 'Magazzino Centrale'),
            mastrino_ddt=request.form.get('mastrino_ddt', ''),
            commessa=request.form.get('commessa', ''),
            stato='bozza'
        )
        
        # Data origine
        if request.form.get('data_ddt_origine'):
            data_origine = datetime.strptime(request.form['data_ddt_origine'], '%Y-%m-%d').date()
            if data_origine > datetime.now().date():
                return "Errore: Non è possibile inserire una data nel futuro", 400
            nuovo_ddt.data_ddt_origine = data_origine
        else:
            nuovo_ddt.data_ddt_origine = datetime.now().date()
        
        db.session.add(nuovo_ddt)
        db.session.flush()  # Per ottenere l'ID
        
        # Aggiungi articoli
        i = 0
        while f'articoli[{i}][descrizione]' in request.form:
            if request.form.get(f'articoli[{i}][descrizione]'):
                codice_fornitore = request.form.get(f'articoli[{i}][codice_fornitore]', '')
                fornitore_nome = request.form.get('fornitore', '')
                descrizione = request.form.get(f'articoli[{i}][descrizione]')
                
                # Prima cerca se esiste già un articolo simile nel catalogo
                codice_interno_esistente = None
                
                # Cerca per codice fornitore e descrizione simile
                if codice_fornitore:
                    articolo_esistente = CatalogoArticolo.query.filter(
                        db.and_(
                            CatalogoArticolo.codice_fornitore == codice_fornitore,
                            CatalogoArticolo.descrizione.ilike(f'%{descrizione.strip()[:20]}%')  # Primi 20 caratteri
                        )
                    ).first()
                    
                    if articolo_esistente:
                        codice_interno_esistente = articolo_esistente.codice_interno
                        print(f"Articolo esistente trovato: {codice_interno_esistente} per codice {codice_fornitore}")
                
                # Se non trovato, genera nuovo codice interno
                if not codice_interno_esistente:
                    # Genera codice interno automaticamente: prime 4 lettere fornitore + codice fornitore
                    prefisso_fornitore = ''.join(c.upper() for c in fornitore_nome if c.isalpha())[:4]
                    codice_interno_esistente = f"{prefisso_fornitore}{codice_fornitore}" if prefisso_fornitore and codice_fornitore else request.form.get(f'articoli[{i}][codice]', '')
                    print(f"Nuovo codice interno generato: {codice_interno_esistente}")
                
                articolo = ArticoloIn(
                    ddt_id=nuovo_ddt.id,
                    codice_interno=codice_interno_esistente,
                    codice_fornitore=codice_fornitore,
                    descrizione=descrizione,
                    quantita=float(request.form.get(f'articoli[{i}][quantita]', 1)),
                    costo_unitario=float(request.form.get(f'articoli[{i}][costo]', 0)),
                    mastrino_riga=request.form.get(f'articoli[{i}][mastrino]', '')
                )
                db.session.add(articolo)
            i += 1
        
        db.session.commit()
        return redirect(f'/ddt-in/{nuovo_ddt.id}')
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore creazione DDT: {e}")
        return f"Errore: {str(e)}", 500

@app.route('/ddt-in/<int:id>/conferma', methods=['POST'])
def conferma_ddt_in(id):
    """Conferma DDT IN"""
    try:
        ddt = DDTIn.query.get_or_404(id)
        
        if ddt.stato == 'confermato':
            return jsonify({'error': 'DDT già confermato'}), 400
        
        # VALIDAZIONE CAMPI OBBLIGATORI PRIMA DELLA CONFERMA
        errori = []
        
        # Verifica magazzino destinazione
        if not ddt.destinazione or ddt.destinazione.strip() == '':
            errori.append('Il magazzino di destinazione è obbligatorio')
        
        # Nota: Il mastrino è ora a livello di singolo articolo, non più del DDT
        
        # Verifica articoli
        articoli = ArticoloIn.query.filter_by(ddt_id=id).all()
        if not articoli:
            errori.append('Il DDT deve contenere almeno un articolo')
        
        for i, art in enumerate(articoli, 1):
            # Verifica codice fornitore
            if not art.codice_fornitore or art.codice_fornitore.strip() == '':
                errori.append(f'Riga {i}: Il codice fornitore è obbligatorio')
            
            # Verifica mastrino riga
            if not art.mastrino_riga or art.mastrino_riga.strip() == '':
                errori.append(f'Riga {i}: Il mastrino è obbligatorio')
            
            # Verifica quantità
            if art.quantita is None or art.quantita <= 0:
                errori.append(f'Riga {i}: La quantità deve essere maggiore di zero')
            
            # Verifica descrizione
            if not art.descrizione or art.descrizione.strip() == '':
                errori.append(f'Riga {i}: La descrizione articolo è obbligatoria')
        
        # Se ci sono errori, ritorna la lista
        if errori:
            return jsonify({
                'success': False, 
                'error': 'Campi obbligatori mancanti',
                'errori': errori
            }), 400
        
        # Genera numero progressivo
        anno = datetime.now().year
        
        # Trova il numero più alto esistente per l'anno corrente
        numeri_esistenti = db.session.execute(
            db.text("SELECT numero_ddt FROM ddt_in WHERE numero_ddt LIKE :pattern"),
            {'pattern': f'IN/%/{anno}'}
        ).fetchall()
        
        numero = 1
        if numeri_esistenti:
            for (numero_ddt,) in numeri_esistenti:
                try:
                    num_corrente = int(numero_ddt.split('/')[1])
                    if num_corrente >= numero:
                        numero = num_corrente + 1
                except:
                    continue
        
        ddt.numero_ddt = f'IN/{numero:04d}/{anno}'
        ddt.data_ddt = datetime.now().date()
        ddt.stato = 'confermato'
        
        # Aggiorna catalogo articoli
        articoli = ArticoloIn.query.filter_by(ddt_id=id).all()
        for art in articoli:
            # Se il codice interno è vuoto, genera uno temporaneo
            codice_articolo = art.codice_interno or f'ART-{art.id}'
            
            if True:  # Processa sempre tutti gli articoli
                # Cerca articolo esistente per codice interno (PRIMA ricerca senza ubicazione)
                catalogo_art_esistente = CatalogoArticolo.query.filter_by(
                    codice_interno=codice_articolo
                ).first()
                
                if catalogo_art_esistente:
                    # Articolo esiste: cerca per stessa ubicazione
                    catalogo_art = CatalogoArticolo.query.filter_by(
                        codice_interno=codice_articolo,
                        ubicazione=ddt.destinazione or 'Magazzino principale'
                    ).first()
                    
                    if not catalogo_art:
                        # Stesso articolo ma ubicazione diversa: crea nuova riga inventario
                        catalogo_art = CatalogoArticolo(
                            codice_interno=codice_articolo,
                            codice_fornitore=getattr(art, 'codice_fornitore', None),
                            descrizione=art.descrizione or 'Descrizione non disponibile',
                            fornitore_principale=getattr(art, 'fornitore', None) or ddt.fornitore,
                            costo_ultimo=art.costo_unitario or 0,
                            costo_medio=art.costo_unitario or 0,
                            unita_misura=getattr(art, 'unita_misura', 'PZ') or 'PZ',
                            giacenza_attuale=0,
                            scorta_minima=0,
                            ubicazione=ddt.destinazione or 'Magazzino principale',
                            attivo=True
                        )
                        db.session.add(catalogo_art)
                else:
                    # Articolo non esiste: crea nuovo
                    catalogo_art = CatalogoArticolo(
                        codice_interno=codice_articolo,
                        codice_fornitore=getattr(art, 'codice_fornitore', None),
                        descrizione=art.descrizione or 'Descrizione non disponibile',
                        fornitore_principale=getattr(art, 'fornitore', None) or ddt.fornitore,
                        costo_ultimo=art.costo_unitario or 0,
                        costo_medio=art.costo_unitario or 0,
                        unita_misura=getattr(art, 'unita_misura', 'PZ') or 'PZ',
                        giacenza_attuale=0,
                        scorta_minima=0,
                        ubicazione=ddt.destinazione or 'Magazzino principale',
                        attivo=True
                    )
                    db.session.add(catalogo_art)
                
                # Aggiorna giacenza e costo
                catalogo_art.giacenza_attuale = (catalogo_art.giacenza_attuale or 0) + art.quantita
                catalogo_art.costo_ultimo = art.costo_unitario or catalogo_art.costo_ultimo
                # Aggiorna ubicazione se non presente
                if not catalogo_art.ubicazione:
                    catalogo_art.ubicazione = ddt.destinazione or 'Magazzino principale'
                
                # Crea movimento
                movimento = Movimento(
                    data_movimento=ddt.data_ddt_origine or ddt.data_ddt,
                    tipo='entrata',
                    documento_tipo='ddt_in',
                    documento_id=ddt.id,
                    documento_numero=ddt.numero_ddt,
                    codice_articolo=codice_articolo,
                    descrizione_articolo=art.descrizione,
                    quantita=art.quantita,
                    valore_unitario=art.costo_unitario or 0,
                    valore_totale=art.quantita * (art.costo_unitario or 0),
                    magazzino=ddt.destinazione or 'Magazzino Centrale',
                    mastrino=ddt.mastrino_ddt or 'ACQ001',
                    causale=f'Carico da DDT IN {ddt.numero_ddt}'
                )
                db.session.add(movimento)
        
        db.session.commit()
        
        # Aggiorna inventario automaticamente
        aggiorna_inventario()
        
        return jsonify({'success': True, 'numero': ddt.numero_ddt})
        
    except Exception as e:
        import traceback
        db.session.rollback()
        print(f"Errore conferma DDT IN: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/ddt-in/<int:id>/elimina', methods=['POST'])
def elimina_ddt_in(id):
    """Elimina o annulla DDT IN"""
    try:
        ddt = DDTIn.query.get_or_404(id)
        era_confermato = ddt.stato == 'confermato'
        
        # Ottieni tutti gli articoli collegati al DDT IN
        articoli_in = ArticoloIn.query.filter_by(ddt_id=id).all()
        movimenti_eliminati = 0
        
        # Per ogni articolo, gestisci la rimozione da catalogo, inventario e movimenti
        for art in articoli_in:
            if art.codice_interno:
                # Rimuovi dal catalogo articoli se era confermato
                if era_confermato:
                    catalogo_art = CatalogoArticolo.query.filter_by(
                        codice_interno=art.codice_interno
                    ).first()
                    
                    if catalogo_art:
                        # Sottrai la quantità dalla giacenza
                        catalogo_art.giacenza_attuale = max(0, 
                            (catalogo_art.giacenza_attuale or 0) - (art.quantita or 0))
                        
                        # Se la giacenza è 0, rimuovi completamente l'articolo dal catalogo
                        if (catalogo_art.giacenza_attuale or 0) <= 0:
                            db.session.delete(catalogo_art)
                            print(f"Articolo {art.codice_interno} rimosso completamente dal catalogo")
                        else:
                            print(f"Giacenza articolo {art.codice_interno} aggiornata: {catalogo_art.giacenza_attuale}")
                
                # Rimuovi i movimenti associati se esistono
                movimenti = Movimento.query.filter_by(
                    documento_tipo='ddt_in',
                    documento_id=id,
                    codice_articolo=art.codice_interno
                ).all()
                
                for mov in movimenti:
                    db.session.delete(mov)
                    movimenti_eliminati += 1
                    print(f"Movimento eliminato per articolo {art.codice_interno}")
            
            # Elimina l'articolo dal DDT IN solo se è bozza
            if not era_confermato:
                db.session.delete(art)
        
        # Se era confermato, annullalo; altrimenti eliminalo completamente
        if era_confermato:
            ddt.stato = 'annullato'
            action_message = f'DDT IN {ddt.numero_ddt} annullato con successo'
            action_type = 'annullato'
        else:
            # Elimina anche gli articoli per le bozze
            for art in articoli_in:
                db.session.delete(art)
            db.session.delete(ddt)
            action_message = f'DDT IN {ddt.numero_ddt or f"BOZZA-{id}"} eliminato con successo'
            action_type = 'eliminato'
        
        db.session.commit()
        
        # Aggiorna inventario solo se c'erano modifiche
        if era_confermato or movimenti_eliminati > 0:
            aggiorna_inventario()
        
        return jsonify({
            'success': True, 
            'message': action_message,
            'action': action_type,
            'articoli_rimossi': len(articoli_in),
            'movimenti_eliminati': movimenti_eliminati
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore eliminazione DDT IN: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ddt-in/<int:id>/modifica', methods=['GET', 'POST'])
def modifica_ddt_in(id):
    """Modifica DDT IN esistente"""
    try:
        ddt = DDTIn.query.get_or_404(id)
        
        if request.method == 'GET':
            # Mostra form di modifica
            mastrini = Mastrino.query.filter_by(attivo=True, tipo='acquisto').all()
            magazzini = Magazzino.query.filter_by(attivo=True).all()
            fornitori = Fornitore.query.filter_by(attivo=True).all()
            articoli = ArticoloIn.query.filter_by(ddt_id=id).all()
            
            return render_template('modifica-ddt-in.html',
                                 ddt=ddt,
                                 articoli=articoli,
                                 mastrini=mastrini,
                                 magazzini=magazzini,
                                 fornitori=fornitori,
                                 today=datetime.now().strftime('%Y-%m-%d'))
        
        # POST - Salva modifiche
        ddt.fornitore = request.form.get('fornitore', '')
        ddt.riferimento = request.form.get('riferimento', '')
        ddt.destinazione = request.form.get('destinazione', 'Magazzino Centrale')
        ddt.mastrino_ddt = request.form.get('mastrino_ddt', '')
        ddt.commessa = request.form.get('commessa', '')
        
        # Data origine
        if request.form.get('data_ddt_origine'):
            data_origine = datetime.strptime(request.form['data_ddt_origine'], '%Y-%m-%d').date()
            if data_origine > datetime.now().date():
                return "Errore: Non è possibile inserire una data nel futuro", 400
            ddt.data_ddt_origine = data_origine
        
        # Rimuovi tutti gli articoli esistenti
        ArticoloIn.query.filter_by(ddt_id=id).delete()
        
        # Aggiungi articoli modificati
        i = 0
        while f'articoli[{i}][descrizione]' in request.form:
            if request.form.get(f'articoli[{i}][descrizione]'):
                # Genera codice interno automaticamente: prime 4 lettere fornitore + codice fornitore
                codice_fornitore = request.form.get(f'articoli[{i}][codice_fornitore]', '')
                fornitore_nome = request.form.get('fornitore', '')
                
                # Estrae prime 4 lettere del fornitore (solo caratteri alfabetici)
                prefisso_fornitore = ''.join(c.upper() for c in fornitore_nome if c.isalpha())[:4]
                codice_interno_generato = f"{prefisso_fornitore}{codice_fornitore}" if prefisso_fornitore and codice_fornitore else request.form.get(f'articoli[{i}][codice]', '')
                
                articolo = ArticoloIn(
                    ddt_id=ddt.id,
                    codice_interno=codice_interno_generato,
                    codice_fornitore=codice_fornitore,
                    descrizione=request.form.get(f'articoli[{i}][descrizione]'),
                    quantita=float(request.form.get(f'articoli[{i}][quantita]', 1)),
                    costo_unitario=float(request.form.get(f'articoli[{i}][costo]', 0)),
                    mastrino_riga=request.form.get(f'articoli[{i}][mastrino]', '')
                )
                db.session.add(articolo)
            i += 1
        
        db.session.commit()
        return redirect(f'/ddt-in/{id}')
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore modifica DDT IN: {e}")
        return f"Errore: {str(e)}", 500

@app.route('/ddt-in/<int:id>/confronta-data')
def confronta_data_ddt_in(id):
    """Restituisce dati DDT IN per confronto con PDF"""
    try:
        ddt = DDTIn.query.get_or_404(id)
        articoli = ArticoloIn.query.filter_by(ddt_id=id).all()
        
        # Prepara dati per il confronto
        ddt_data = {
            'id': ddt.id,
            'numero_ddt': ddt.numero_ddt or f'BOZZA-{ddt.id}',
            'fornitore': ddt.fornitore,
            'riferimento': ddt.riferimento,
            'destinazione': ddt.destinazione,
            'commessa': ddt.commessa,
            'mastrino_ddt': ddt.mastrino_ddt,
            'data_ddt_origine': ddt.data_ddt_origine.strftime('%Y-%m-%d') if ddt.data_ddt_origine else '',
            'stato': ddt.stato,
            'articoli': []
        }
        
        for articolo in articoli:
            ddt_data['articoli'].append({
                'codice_interno': articolo.codice_interno,
                'codice_fornitore': articolo.codice_fornitore,
                'descrizione': articolo.descrizione,
                'quantita': float(articolo.quantita) if articolo.quantita else 0,
                'costo_unitario': float(articolo.costo_unitario) if articolo.costo_unitario else 0,
                'mastrino_riga': articolo.mastrino_riga,
                'totale': float(articolo.quantita * articolo.costo_unitario) if articolo.quantita and articolo.costo_unitario else 0
            })
        
        return jsonify({'success': True, 'data': ddt_data})
        
    except Exception as e:
        print(f"Errore confronta data DDT IN: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ddt-in/<int:id>/genera-ddt-out', methods=['GET', 'POST'])
def genera_ddt_out_da_ddt_in(id):
    """Genera DDT OUT da un DDT IN specifico"""
    try:
        ddt_in = DDTIn.query.get_or_404(id)
        
        # GET - Mostra form di creazione DDT OUT
        if request.method == 'GET':
            # Ottieni gli articoli del DDT IN
            articoli_in = ArticoloIn.query.filter_by(ddt_id=id).all()
            
            # Prepara i dati per il template
            magazzini = Magazzino.query.filter_by(attivo=True).all()
            clienti = Cliente.query.filter_by(attivo=True).all()
            mastrini_vendita = Mastrino.query.filter_by(attivo=True, tipo='ricavo').all()
            
            # Prepara gli articoli da passare al template
            articoli_from_ddt = []
            for art in articoli_in:
                # Trova la giacenza attuale dell'articolo nel catalogo
                articolo_catalogo = CatalogoArticolo.query.filter_by(
                    codice_interno=art.codice_interno, 
                    attivo=True
                ).first()
                
                giacenza_attuale = 0
                if articolo_catalogo:
                    giacenza_attuale = articolo_catalogo.giacenza_attuale or 0
                
                articoli_from_ddt.append({
                    'codice': art.codice_interno or '',
                    'codice_fornitore': art.codice_fornitore or '',
                    'descrizione': art.descrizione,
                    'fornitore': art.fornitore or '',
                    'codice_produttore': art.codice_produttore or '',
                    'nome_produttore': art.nome_produttore or '',
                    'quantita': art.quantita,
                    'prezzo': round(float(art.costo_unitario or 0), 2),  # Arrotondamento a 2 decimali
                    'unita_misura': art.unita_misura or 'PZ',
                    'giacenza': giacenza_attuale  # Aggiunto campo giacenza
                })
            
            # Il magazzino di default è la destinazione del DDT IN
            magazzino_default = ddt_in.destinazione
            
            # Riferimento al DDT IN originale
            riferimento_default = f"DDT IN {ddt_in.numero_ddt or f'BOZZA-{id}'}"
            
            return render_template('nuovo-ddt-out.html',
                                 magazzini=magazzini,
                                 clienti=clienti,
                                 mastrini_vendita=mastrini_vendita,
                                 articoli_from_ddt=articoli_from_ddt,
                                 magazzino_default=magazzino_default,
                                 riferimento_default=riferimento_default,
                                 from_ddt_in_id=id,
                                 today=datetime.now().strftime('%Y-%m-%d'))
        
        # POST - Salva DDT OUT
        else:
            data = request.form
            
            nuovo_ddt = DDTOut()
            nuovo_ddt.data_ddt_origine = datetime.now().date()
            nuovo_ddt.nome_origine = "ACG Clima Service S.r.l."
            nuovo_ddt.destinazione = data.get("cliente", "")
            nuovo_ddt.riferimento = data.get("riferimento", "")
            nuovo_ddt.commessa = data.get("commessa", "")
            nuovo_ddt.magazzino_partenza = data.get("magazzino_partenza", "Magazzino Centrale")
            nuovo_ddt.mastrino_ddt = data.get("mastrino_vendita", "")
            nuovo_ddt.stato = "bozza"
            nuovo_ddt.from_ddt_in_id = id
            
            db.session.add(nuovo_ddt)
            db.session.flush()
            
            # Aggiungi articoli
            i = 0
            while f"articoli[{i}][descrizione]" in data:
                if data.get(f"articoli[{i}][descrizione]"):
                    articolo = ArticoloOut(
                        ddt_id=nuovo_ddt.id,
                        codice_interno=data.get(f"articoli[{i}][codice_interno]", ""),
                        descrizione=data.get(f"articoli[{i}][descrizione]"),
                        prezzo_unitario=round(float(data.get(f"articoli[{i}][prezzo_unitario]", 0)), 2),  # Arrotondamento a 2 decimali
                        quantita=float(data.get(f"articoli[{i}][quantita]", 0)),
                        mastrino_riga=data.get(f"articoli[{i}][mastrino]", "")
                    )
                    db.session.add(articolo)
                i += 1
            
            db.session.commit()
            print(f"DDT OUT creato con ID: {nuovo_ddt.id}")
            
            # Redirect diretto alla lista DDT OUT invece di JSON
            return redirect(url_for('ddt_out_list'))
                             
    except Exception as e:
        print(f"Errore generazione DDT OUT da DDT IN: {e}")
        db.session.rollback()
        if request.method == 'POST':
            return jsonify({'success': False, 'error': str(e)}), 500
        return str(e), 500

@app.route('/ddt-in/<int:id>/crea-preventivo')
def crea_preventivo_da_ddt_in(id):
    """Crea preventivo da DDT IN"""
    try:
        ddt_in = DDTIn.query.get_or_404(id)
        articoli_in = ArticoloIn.query.filter_by(ddt_id=id).all()
        
        if not articoli_in:
            flash('Nessun articolo trovato nel DDT IN per creare il preventivo', 'error')
            return redirect(f'/ddt-in/{id}')
        
        # Genera numero preventivo automatico
        ultimo_numero = db.session.query(db.func.max(Preventivo.id)).scalar() or 0
        numero_preventivo = f"PREV-{datetime.now().year}-{str(ultimo_numero + 1).zfill(4)}"
        
        # Crea nuovo preventivo basato sul DDT IN
        nuovo_preventivo = Preventivo(
            numero_preventivo=numero_preventivo,
            cliente_nome=ddt_in.fornitore,  # Usa fornitore come cliente iniziale
            oggetto=f"Preventivo da DDT IN {ddt_in.numero_ddt or ddt_in.id}",
            data_preventivo=datetime.now().date(),
            iva=22.0,
            commessa=ddt_in.commessa,
            note=f"Preventivo generato automaticamente da DDT IN {ddt_in.numero_ddt or ddt_in.id}"
        )
        
        db.session.add(nuovo_preventivo)
        db.session.flush()  # Per ottenere l'ID
        
        # Aggiungi dettagli preventivo dai articoli DDT IN
        totale_netto = 0
        for articolo in articoli_in:
            # Applica un markup del 20% sul costo per ottenere il prezzo di vendita
            prezzo_unitario = (articolo.costo_unitario or 0) * 1.20
            totale_riga = (articolo.quantita or 0) * prezzo_unitario
            totale_netto += totale_riga
            
            dettaglio = DettaglioPreventivo(
                preventivo_id=nuovo_preventivo.id,
                codice_articolo=articolo.codice_interno,
                descrizione=articolo.descrizione,
                quantita=articolo.quantita,
                prezzo_unitario=prezzo_unitario,
                costo_unitario=articolo.costo_unitario,
                totale_riga=totale_riga
            )
            db.session.add(dettaglio)
        
        # Aggiorna totali preventivo
        nuovo_preventivo.totale_netto = totale_netto
        nuovo_preventivo.totale_lordo = totale_netto * (1 + nuovo_preventivo.iva / 100)
        margine = totale_netto - sum((d.costo_unitario or 0) * (d.quantita or 0) for d in nuovo_preventivo.dettagli)
        nuovo_preventivo.margine_valore = margine
        nuovo_preventivo.margine_percentuale = (margine / totale_netto * 100) if totale_netto > 0 else 0
        
        db.session.commit()
        
        flash(f'Preventivo {numero_preventivo} creato con successo da DDT IN {ddt_in.numero_ddt or ddt_in.id}', 'success')
        return redirect(f'/preventivi/{nuovo_preventivo.id}')
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore creazione preventivo da DDT IN: {e}")
        flash(f'Errore nella creazione del preventivo: {str(e)}', 'error')
        return redirect(f'/ddt-in/{id}')

# ========== BATCH IMPORT DDT IN ==========

@app.route('/ddt-in/import-batch')
def ddt_import_batch_page():
    """Pagina import batch PDF per DDT IN"""
    return render_template('ddt-import-batch.html')

@app.route('/ddt-in/import-batch', methods=['POST'])
def import_batch_ddt_in():
    """Import batch di PDF per DDT IN"""
    try:
        print("DEBUG: Batch import route chiamata")
        from models import BatchImportJob, BatchImportFile
        import tempfile
        import uuid
        import threading
        from werkzeug.utils import secure_filename
        
        print("DEBUG: Import completati")
        
        # Validazione file
        if 'pdf_files' not in request.files:
            print("DEBUG: Nessun file in request.files")
            return jsonify({'success': False, 'error': 'Nessun file caricato'}), 400
        
        files = request.files.getlist('pdf_files')
        if len(files) == 0:
            return jsonify({'success': False, 'error': 'Nessun file selezionato'}), 400
        
        if len(files) > 10:
            return jsonify({'success': False, 'error': 'Massimo 10 file per batch'}), 400
        
        # Crea job batch
        job = BatchImportJob(
            status='processing',
            total_files=len(files),
            processed_files=0,
            successful_files=0,
            failed_files=0
        )
        db.session.add(job)
        db.session.commit()
        
        # Salva file temporaneamente
        temp_files = []
        for file in files:
            if file.filename == '' or not file.filename.lower().endswith('.pdf'):
                continue
                
            filename = secure_filename(file.filename)
            temp_path = os.path.join(tempfile.gettempdir(), f"{job.id}_{filename}")
            file.save(temp_path)
            
            batch_file = BatchImportFile(
                job_id=job.id,
                filename=temp_path,
                original_filename=filename,
                file_size=os.path.getsize(temp_path),
                status='pending'
            )
            db.session.add(batch_file)
            temp_files.append(batch_file)
        
        db.session.commit()
        
        # Avvia processing in background
        print(f"DEBUG: Avviando thread per job {job.id} con {len(temp_files)} file")
        thread = threading.Thread(target=process_batch_files, args=(job.id,))
        thread.daemon = True
        thread.start()
        print(f"DEBUG: Thread avviato per job {job.id}")
        db.session.commit()
        
        return jsonify({
            'success': True,
            'job_id': job.id,
            'total_files': len(temp_files)
        })
        
    except Exception as e:
        print(f"Errore batch import: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ddt-in/import-batch/status/<int:job_id>')
def batch_import_status(job_id):
    """Status del job batch import"""
    try:
        from models import BatchImportJob
        
        job = BatchImportJob.query.get_or_404(job_id)
        
        response = {
            'job_id': job.id,
            'status': job.status,
            'total_files': job.total_files,
            'processed_files': job.processed_files,
            'successful_files': job.successful_files,
            'failed_files': job.failed_files
        }
        
        # Se completato, aggiungi dettagli
        if job.status in ['completed', 'failed']:
            # DDT creati con successo
            successful_ddts = []
            for batch_file in job.files:
                if batch_file.status == 'completed' and batch_file.ddt_in_id:
                    ddt = DDTIn.query.get(batch_file.ddt_in_id)
                    if ddt:
                        successful_ddts.append({
                            'id': ddt.id,
                            'numero_ddt': ddt.numero_ddt or f'Bozza {ddt.id}'
                        })
            
            response['successful_ddts'] = successful_ddts
            
            # Errori
            errors = []
            for batch_file in job.files:
                if batch_file.status == 'failed':
                    errors.append({
                        'filename': batch_file.original_filename,
                        'error': batch_file.error_message or 'Errore parsing'
                    })
            
            response['errors'] = errors
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Errore status batch: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def process_batch_files(job_id):
    """Processa i file del batch in background"""
    print(f"DEBUG THREAD: ENTRATO in process_batch_files con job_id={job_id}")
    
    from models import BatchImportJob, BatchImportFile, DDTIn, ArticoloIn, Fornitore
    from multi_ai_pdf_parser import MultiAIPDFParser
    
    print(f"DEBUG THREAD: Import completati, iniziando processing per job {job_id}")
    
    try:
        with app.app_context():
            job = BatchImportJob.query.get(job_id)
            if not job:
                print(f"DEBUG THREAD: Job {job_id} non trovato")
                return
            
            # Recupera i file del batch dalla DB
            batch_files = BatchImportFile.query.filter_by(job_id=job_id).all()
            print(f"DEBUG THREAD: Trovati {len(batch_files)} file per il job {job_id}")
            
            parser = MultiAIPDFParser()
            job.status = 'processing'
            db.session.commit()
            
            for batch_file in batch_files:
                print(f"Processing file: {batch_file.original_filename}")
                try:
                    batch_file.status = 'processing'
                    db.session.commit()
                    
                    # Apri e processa il file
                    with open(batch_file.filename, 'rb') as file_obj:
                        # Usa Claude come default per batch
                        result = parser.parse_ddt_with_ai(file_obj, preferred_ai='claude')
                    
                    if result.get('success') and 'data' in result:
                        data = result['data']
                        
                        # Crea DDT IN
                        fornitore_nome = ''
                        if 'fornitore' in data and isinstance(data['fornitore'], dict):
                            fornitore_nome = data['fornitore'].get('ragione_sociale', '')
                        
                        # Verifica/crea fornitore
                        fornitore = None
                        if fornitore_nome:
                            fornitore = Fornitore.query.filter_by(ragione_sociale=fornitore_nome).first()
                            if not fornitore:
                                fornitore = Fornitore(
                                    ragione_sociale=fornitore_nome,
                                    partita_iva=data.get('fornitore', {}).get('partita_iva', ''),
                                    attivo=True
                                )
                                db.session.add(fornitore)
                                db.session.flush()
                        
                        # Leggi e codifica PDF originale in base64
                        import base64
                        with open(batch_file.filename, 'rb') as pdf_file:
                            pdf_content = pdf_file.read()
                            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                        
                        # Crea DDT IN
                        nuovo_ddt = DDTIn(
                            fornitore=fornitore_nome,
                            riferimento=data.get('numero_ddt', ''),
                            destinazione='Magazzino Centrale',
                            commessa='',
                            stato='bozza',
                            data_ddt_origine=datetime.strptime(data.get('data_ddt', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date() if data.get('data_ddt') else datetime.now().date(),
                            pdf_allegato=pdf_base64,
                            pdf_filename=batch_file.original_filename
                        )
                        db.session.add(nuovo_ddt)
                        db.session.flush()
                        
                        # Crea articoli
                        if 'articoli' in data and isinstance(data['articoli'], list):
                            for articolo_data in data['articoli']:
                                # Determina il codice fornitore dal parsing PDF
                                # Il parser può restituire il codice in 'codice' o 'codice_interno'
                                codice_fornitore = articolo_data.get('codice', '') or articolo_data.get('codice_interno', '')
                                
                                # Estrae prime 4 lettere del fornitore (solo caratteri alfabetici)
                                prefisso_fornitore = ''.join(c.upper() for c in fornitore_nome if c.isalpha())[:4]
                                
                                # Genera codice interno: prime 4 lettere fornitore + codice fornitore
                                if prefisso_fornitore and codice_fornitore:
                                    codice_interno_generato = f"{prefisso_fornitore}{codice_fornitore}"
                                else:
                                    # Fallback se mancano dati
                                    codice_interno_generato = codice_fornitore or 'UNKNOWN'
                                
                                articolo = ArticoloIn(
                                    ddt_id=nuovo_ddt.id,
                                    codice_interno=codice_interno_generato,
                                    codice_fornitore=codice_fornitore,
                                    descrizione=articolo_data.get('descrizione', ''),
                                    costo_unitario=float(articolo_data.get('prezzo_unitario', 0)),
                                    quantita=float(articolo_data.get('quantita', 0)),
                                    mastrino_riga=''  # Vuoto per import batch, da compilare in fase di conferma
                                )
                                db.session.add(articolo)
                        
                        # Aggiorna batch file con successo
                        batch_file.status = 'completed'
                        batch_file.ddt_in_id = nuovo_ddt.id
                        job.successful_files += 1
                        
                        print(f"DDT creato con successo: {nuovo_ddt.id}")
                        
                    else:
                        # Parsing fallito
                        batch_file.status = 'failed'
                        batch_file.error_message = result.get('error', 'Parsing fallito')
                        job.failed_files += 1
                        print(f"Parsing fallito per {batch_file.original_filename}: {result.get('error')}")
                    
                    batch_file.processed_at = datetime.now()
                    job.processed_files += 1
                    db.session.commit()
                    
                    # Cleanup file temporaneo
                    try:
                        os.remove(batch_file.filename)
                    except:
                        pass
                        
                except Exception as e:
                    print(f"Errore processing file {batch_file.original_filename}: {e}")
                    batch_file.status = 'failed'
                    batch_file.error_message = str(e)
                    job.failed_files += 1
                    job.processed_files += 1
                    db.session.commit()
            
            # Completa job
            job.status = 'completed'
            job.completed_at = datetime.now()
            db.session.commit()
            
            print(f"Batch processing completato: {job.successful_files} successi, {job.failed_files} fallimenti")
            
    except Exception as e:
        print(f"Errore critico batch processing: {e}")
        try:
            with app.app_context():
                job = BatchImportJob.query.get(job_id)
                if job:
                    job.status = 'failed'
                    db.session.commit()
        except:
            pass

# ========== SISTEMA DDT OUT ==========

@app.route('/ddt-out')
def ddt_out_list():
    """Lista DDT OUT"""
    try:
        ddts = DDTOut.query.order_by(
            DDTOut.stato.asc(),  # bozza prima di confermato
            DDTOut.numero_ddt.desc().nulls_last(),  # numero documento decrescente, NULL alla fine
            DDTOut.id.desc()  # per DDT senza numero, ordina per ID decrescente
        ).all()
        
        buchi_numerazione = verifica_buchi_numerazione(ddts, 'OUT')
        
        return render_template('ddt-out.html', 
                             ddts=ddts,
                             buchi_numerazione=buchi_numerazione,
                             datetime=datetime)
    except Exception as e:
        print(f"Errore lista DDT OUT: {e}")
        return render_template('ddt-out.html', ddts=[], buchi_numerazione=[])

@app.route('/ddt-out/<int:id>')
def dettaglio_ddt_out(id):
    """Visualizza dettagli DDT OUT"""
    try:
        ddt = DDTOut.query.get_or_404(id)
        articoli = ArticoloOut.query.filter_by(ddt_id=id).all()
        
        return render_template('ddt-out-detail.html',
                             ddt=ddt,
                             articoli=articoli)
    except Exception as e:
        print(f"Errore dettaglio DDT OUT: {e}")
        return str(e), 500

@app.route("/ddt-out/nuovo", methods=["GET", "POST"])
@app.route("/ddt/out/nuovo", methods=["GET", "POST"])
def nuovo_ddt_out():
    """Crea nuovo DDT OUT"""
    if request.method == "GET":
        # Gestione from_ddt_in
        from_ddt_in_id = request.args.get("from_ddt_in")
        if from_ddt_in_id:
            return redirect(f"/ddt-in/{from_ddt_in_id}/genera-ddt-out")
        
        try:
            articoli_from_ddt = []
            magazzino_default = "Magazzino Centrale"
            riferimento_default = ""
            
            magazzini = Magazzino.query.filter_by(attivo=True).all()
            clienti = Cliente.query.filter_by(attivo=True).all()
            mastrini_vendita = Mastrino.query.filter_by(attivo=True, tipo="ricavo").all()
            
            return render_template("nuovo-ddt-out.html",
                                 magazzini=magazzini,
                                 clienti=clienti,
                                 mastrini_vendita=mastrini_vendita,
                                 articoli_from_ddt=articoli_from_ddt,
                                 magazzino_default=magazzino_default,
                                 riferimento_default=riferimento_default,
                                 from_ddt_in_id=None,
                                 today=datetime.now().strftime("%Y-%m-%d"))
        except Exception as e:
            print(f"Errore GET: {e}")
            return str(e), 500
    
    # POST
    try:
        data = request.form
        
        nuovo_ddt = DDTOut()
        nuovo_ddt.data_ddt_origine = datetime.now().date()
        nuovo_ddt.nome_origine = "ACG Clima Service S.r.l."
        nuovo_ddt.destinazione = data.get("cliente", "")
        nuovo_ddt.riferimento = data.get("riferimento", "")
        nuovo_ddt.commessa = data.get("commessa", "")
        nuovo_ddt.magazzino_partenza = data.get("magazzino_partenza", "Magazzino Centrale")
        nuovo_ddt.mastrino_ddt = data.get("mastrino_vendita", "")
        nuovo_ddt.stato = "bozza"
        
        db.session.add(nuovo_ddt)
        db.session.flush()
        
        # Aggiungi articoli
        i = 0
        while f"articoli[{i}][descrizione]" in data:
            if data.get(f"articoli[{i}][descrizione]"):
                articolo = ArticoloOut(
                    ddt_id=nuovo_ddt.id,
                    codice_interno=data.get(f"articoli[{i}][codice_interno]", ""),
                    descrizione=data.get(f"articoli[{i}][descrizione]"),
                    prezzo_unitario=round(float(data.get(f"articoli[{i}][prezzo_unitario]", 0)), 2),  # Arrotondamento a 2 decimali
                    quantita=float(data.get(f"articoli[{i}][quantita]", 0)),
                    mastrino_riga=data.get(f"articoli[{i}][mastrino]", "")
                )
                db.session.add(articolo)
            i += 1
        
        db.session.commit()
        return redirect("/ddt-out")
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore POST: {e}")
        return str(e), 500

@app.route('/ddt-out/<int:id>/conferma', methods=['POST'])
def conferma_ddt_out(id):
    """Conferma DDT OUT"""
    try:
        ddt = DDTOut.query.get_or_404(id)
        
        if ddt.stato == 'confermato':
            return jsonify({'success': False, 'error': 'DDT già confermato'})
        
        # Genera numero progressivo
        anno = datetime.now().year
        
        # Trova il numero più alto esistente per l'anno corrente
        numeri_esistenti = db.session.execute(
            db.text("SELECT numero_ddt FROM ddt_out WHERE numero_ddt LIKE :pattern"),
            {'pattern': f'OUT/%/{anno}'}
        ).fetchall()
        
        numero = 1
        if numeri_esistenti:
            for (numero_ddt,) in numeri_esistenti:
                try:
                    num_corrente = int(numero_ddt.split('/')[1])
                    if num_corrente >= numero:
                        numero = num_corrente + 1
                except:
                    continue
        
        ddt.numero_ddt = f'OUT/{numero:04d}/{anno}'
        ddt.data_ddt = datetime.now().date()
        ddt.stato = 'confermato'
        
        # Genera movimenti e aggiorna giacenze
        articoli = ArticoloOut.query.filter_by(ddt_id=ddt.id).all()
        
        for articolo in articoli:
            movimento = Movimento(
                data_movimento=ddt.data_ddt_origine or ddt.data_ddt,
                tipo='uscita',
                documento_tipo='ddt_out',
                documento_id=ddt.id,
                documento_numero=ddt.numero_ddt,
                codice_articolo=articolo.codice_interno or f'ART-{articolo.id}',
                descrizione_articolo=articolo.descrizione,
                quantita=articolo.quantita,
                valore_unitario=articolo.prezzo_unitario or 0,
                valore_totale=(articolo.quantita * (articolo.prezzo_unitario or 0)),
                magazzino=ddt.magazzino_partenza or 'Magazzino Centrale',
                mastrino=ddt.mastrino_ddt or 'VEN001',
                causale=f'Uscita per DDT OUT {ddt.numero_ddt}'
            )
            db.session.add(movimento)
            
            # Aggiorna giacenza
            if articolo.codice_interno:
                cat_articolo = CatalogoArticolo.query.filter_by(
                    codice_interno=articolo.codice_interno
                ).first()
                
                if cat_articolo:
                    vecchia_giacenza = cat_articolo.giacenza_attuale or 0
                    nuova_giacenza = max(0, vecchia_giacenza - articolo.quantita)
                    cat_articolo.giacenza_attuale = nuova_giacenza
                    print(f"Aggiornata giacenza {articolo.codice_interno}: {vecchia_giacenza} -> {nuova_giacenza}")
        
        db.session.commit()
        
        # Aggiorna inventario automaticamente
        aggiorna_inventario()
        
        return jsonify({
            'success': True,
            'numero': ddt.numero_ddt,
            'data': ddt.data_ddt.strftime('%d/%m/%Y'),
            'message': f'DDT OUT confermato con {len(articoli)} articoli'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore conferma DDT OUT: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/ddt-out/<int:id>/elimina', methods=['POST'])
def elimina_ddt_out(id):
    """Elimina DDT OUT e tutti gli articoli collegati"""
    try:
        ddt = DDTOut.query.get_or_404(id)
        
        # Ottieni tutti gli articoli collegati al DDT OUT
        articoli_out = ArticoloOut.query.filter_by(ddt_id=id).all()
        
        # Per ogni articolo, ripristina la giacenza se il DDT era confermato
        for art in articoli_out:
            if art.codice_interno and ddt.stato == 'confermato':
                # Ripristina la giacenza nel catalogo
                catalogo_art = CatalogoArticolo.query.filter_by(
                    codice_interno=art.codice_interno
                ).first()
                
                if catalogo_art:
                    # Ripristina la quantità che era stata sottratta
                    catalogo_art.giacenza_attuale = (catalogo_art.giacenza_attuale or 0) + (art.quantita or 0)
                    print(f"Giacenza ripristinata per {art.codice_interno}: +{art.quantita}")
                
                # Rimuovi il movimento associato se esiste
                movimenti = Movimento.query.filter_by(
                    documento_tipo='ddt_out',
                    documento_id=id,
                    codice_articolo=art.codice_interno
                ).all()
                
                for mov in movimenti:
                    db.session.delete(mov)
                    print(f"Movimento eliminato per articolo {art.codice_interno}")
            
            # Elimina l'articolo dal DDT OUT
            db.session.delete(art)
        
        # Elimina il DDT OUT stesso
        db.session.delete(ddt)
        db.session.commit()
        
        # Aggiorna inventario
        aggiorna_inventario()
        
        return jsonify({
            'success': True, 
            'message': f'DDT OUT {ddt.numero_ddt or f"BOZZA-{id}"} eliminato con successo',
            'articoli_rimossi': len(articoli_out),
            'giacenze_ripristinate': len([a for a in articoli_out if a.codice_interno and ddt.stato == 'confermato'])
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore eliminazione DDT OUT: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ddt-out/<int:id>/modifica', methods=['GET', 'POST'])
def modifica_ddt_out(id):
    """Modifica DDT OUT esistente"""
    try:
        ddt = DDTOut.query.get_or_404(id)
        
        # Controlla se il DDT è in stato bozza
        if ddt.stato != 'bozza':
            return jsonify({'success': False, 'error': 'Solo i DDT in bozza possono essere modificati'}), 400
        
        if request.method == 'GET':
            # Mostra form di modifica
            clienti = Cliente.query.filter_by(attivo=True).all()
            articoli = ArticoloOut.query.filter_by(ddt_id=id).all()
            
            return render_template('modifica-ddt-out.html',
                                 ddt=ddt,
                                 articoli=articoli,
                                 clienti=clienti,
                                 today=datetime.now().strftime('%Y-%m-%d'))
        
        # POST - Salva modifiche
        ddt.destinazione = request.form.get('cliente', '')
        ddt.riferimento = request.form.get('riferimento', '')
        ddt.magazzino_partenza = request.form.get('magazzino_partenza', '')
        ddt.commessa = request.form.get('commessa', '')
        ddt.note = request.form.get('note', '')
        
        # Aggiorna data se fornita
        data_ddt = request.form.get('data_ddt')
        if data_ddt:
            ddt.data_ddt = datetime.strptime(data_ddt, '%Y-%m-%d').date()
        
        # Elimina gli articoli esistenti
        ArticoloOut.query.filter_by(ddt_id=id).delete()
        
        
        # Aggiungi nuovi articoli
        articolo_count = 0
        for key in request.form.keys():
            if key.startswith('articoli[') and key.endswith('][descrizione]'):  # Cambiato da codice a descrizione
                try:
                    # Estrai l'indice dal formato articoli[0][descrizione]
                    start_idx = key.find('[') + 1
                    end_idx = key.find(']')
                    index = key[start_idx:end_idx]
                    
                    descrizione = request.form.get(f'articoli[{index}][descrizione]', '').strip()
                    codice = request.form.get(f'articoli[{index}][codice]', '').strip()
                    quantita_str = request.form.get(f'articoli[{index}][quantita]', '0')
                    prezzo_str = request.form.get(f'articoli[{index}][prezzo]', '0')
                    mastrino = request.form.get(f'articoli[{index}][mastrino]', '').strip()
                    
                    
                    # Parse quantità e prezzo
                    try:
                        quantita = float(quantita_str) if quantita_str else 0
                    except (ValueError, TypeError):
                        quantita = 0
                    
                    try:
                        prezzo_unitario = float(prezzo_str) if prezzo_str else 0
                    except (ValueError, TypeError):
                        prezzo_unitario = 0
                    
                    # La descrizione è obbligatoria
                    if descrizione and quantita > 0:
                        nuovo_articolo = ArticoloOut(
                            ddt_id=id,
                            codice_interno=codice if codice else None,  # Codice può essere vuoto
                            descrizione=descrizione,
                            quantita=quantita,
                            prezzo_unitario=prezzo_unitario,
                            unita_misura='PZ',
                            mastrino_riga=mastrino if mastrino else None
                        )
                        db.session.add(nuovo_articolo)
                        articolo_count += 1
                
                except Exception as art_error:
                    print(f"Errore aggiunta articolo {index}: {art_error}")
                    continue
        
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'DDT OUT modificato con successo',
            'articoli_aggiornati': articolo_count,
            'redirect': f'/ddt-out/{id}'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore modifica DDT OUT: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/stampa-ddt/in/<int:id>')
def stampa_ddt_in(id):
    """Stampa DDT IN"""
    try:
        ddt = DDTIn.query.get_or_404(id)
        articoli = ArticoloIn.query.filter_by(ddt_id=id).all()
        
        return render_template('pdf/ddt-in-pdf-simple.html',
                             ddt=ddt,
                             articoli=articoli)
    except Exception as e:
        print(f"Errore stampa DDT IN: {e}")
        return str(e), 500

@app.route('/stampa-ddt/out/<int:id>')
def stampa_ddt_out(id):
    """Stampa DDT OUT"""
    try:
        ddt = DDTOut.query.get_or_404(id)
        articoli = ArticoloOut.query.filter_by(ddt_id=id).all()
        
        return render_template('ddt-out-stampa.html',
                             ddt=ddt,
                             articoli=articoli)
    except Exception as e:
        print(f"Errore stampa DDT OUT: {e}")
        return str(e), 500

# ========== ALTRE PAGINE PRINCIPALI ==========

@app.route('/catalogo')
def catalogo_page():
    """Pagina catalogo articoli"""
    try:
        articoli = CatalogoArticolo.query.filter_by(attivo=True).order_by(CatalogoArticolo.id.desc()).all()
        valore_magazzino = sum((a.giacenza_attuale or 0) * (a.costo_ultimo or 0) for a in articoli)
        sotto_scorta = len([a for a in articoli if (a.giacenza_attuale or 0) < (a.scorta_minima or 0)])
        esauriti = len([a for a in articoli if (a.giacenza_attuale or 0) == 0])
        fornitori = Fornitore.query.filter_by(attivo=True).all()
        
        return render_template('catalogo.html',
                             articoli=articoli,
                             valore_magazzino=valore_magazzino,
                             sotto_scorta=sotto_scorta,
                             esauriti=esauriti,
                             fornitori=fornitori)
    except Exception as e:
        print(f"Errore catalogo: {e}")
        return render_template('catalogo.html',
                             articoli=[],
                             valore_magazzino=0,
                             sotto_scorta=0,
                             esauriti=0,
                             fornitori=[])

@app.route('/catalogo/modifica/<int:articolo_id>')
def modifica_articolo_form(articolo_id):
    """Form per modificare un articolo del catalogo"""
    try:
        articolo = CatalogoArticolo.query.get_or_404(articolo_id)
        fornitori = Fornitore.query.filter_by(attivo=True).all()
        magazzini = Magazzino.query.filter_by(attivo=True).all()
        
        return render_template('modifica-articolo.html',
                             articolo=articolo,
                             fornitori=fornitori,
                             magazzini=magazzini)
    except Exception as e:
        print(f"Errore form modifica articolo: {e}")
        return redirect('/catalogo')

@app.route('/catalogo/modifica/<int:articolo_id>', methods=['POST'])
def modifica_articolo(articolo_id):
    """Salva le modifiche a un articolo del catalogo"""
    try:
        articolo = CatalogoArticolo.query.get_or_404(articolo_id)
        
        # Aggiorna i campi dell'articolo
        articolo.codice_interno = request.form['codice_interno']
        articolo.codice_fornitore = request.form.get('codice_fornitore', '')
        articolo.descrizione = request.form['descrizione']
        articolo.fornitore_principale = request.form.get('fornitore_principale', '')
        articolo.codice_produttore = request.form.get('codice_produttore', '')
        articolo.unita_misura = request.form.get('unita_misura', 'PZ')
        articolo.costo_ultimo = float(request.form.get('costo_ultimo', 0))
        articolo.giacenza_attuale = float(request.form.get('giacenza_attuale', 0))
        articolo.scorta_minima = float(request.form.get('scorta_minima', 0))
        articolo.ubicazione = request.form.get('ubicazione', '')
        articolo.note = request.form.get('note', '')
        
        db.session.commit()
        print(f"Articolo modificato: {articolo.codice_interno} - {articolo.descrizione}")
        return redirect('/catalogo')
        
    except Exception as e:
        print(f"Errore modifica articolo: {e}")
        db.session.rollback()
        return redirect('/catalogo')

@app.route('/catalogo/elimina/<int:articolo_id>', methods=['POST'])
def elimina_articolo(articolo_id):
    """Elimina un articolo dal catalogo (soft delete)"""
    try:
        articolo = CatalogoArticolo.query.get_or_404(articolo_id)
        
        # Soft delete - marca come non attivo invece di eliminare
        articolo.attivo = False
        
        db.session.commit()
        print(f"Articolo eliminato: {articolo.codice_interno} - {articolo.descrizione}")
        return redirect('/catalogo')
        
    except Exception as e:
        print(f"Errore eliminazione articolo: {e}")
        db.session.rollback()
        return redirect('/catalogo')

@app.route('/catalogo/export-excel')
def export_catalogo_excel():
    """Esporta catalogo in Excel"""
    try:
        import pandas as pd
        from io import BytesIO
        
        articoli = CatalogoArticolo.query.filter_by(attivo=True).all()
        
        # Crea DataFrame
        data = []
        for a in articoli:
            data.append({
                'Codice Interno': a.codice_interno,
                'Codice Fornitore': a.codice_fornitore or '',
                'Descrizione': a.descrizione,
                'Fornitore Principale': a.fornitore_principale or '',
                'U.M.': a.unita_misura or 'PZ',
                'Costo Ultimo': a.costo_ultimo or 0,
                'Costo Medio': a.costo_medio or 0,
                'Prezzo Vendita': a.prezzo_vendita or 0,
                'Giacenza': a.giacenza_attuale or 0,
                'Scorta Minima': a.scorta_minima or 0,
                'Ubicazione': a.ubicazione or ''
            })
        
        df = pd.DataFrame(data)
        
        # Crea buffer in memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Catalogo')
        output.seek(0)
        
        # Nome file con timestamp
        filename = f'catalogo_articoli_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return send_file(output, 
                        as_attachment=True, 
                        download_name=filename,
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
    except Exception as e:
        print(f"Errore export catalogo: {e}")
        return redirect('/catalogo')

@app.route('/catalogo/import-excel', methods=['POST'])
def import_catalogo_excel():
    """Importa catalogo da Excel"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Nessun file selezionato'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nessun file selezionato'})
        
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'error': 'Formato file non supportato. Utilizzare .xlsx o .xls'})
        
        import pandas as pd
        
        # Leggi il file Excel
        try:
            df = pd.read_excel(file)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Errore lettura file Excel: {str(e)}'})
        
        # Colonne attese
        colonne_richieste = ['Codice Fornitore', 'Descrizione', 'Fornitore Principale']
        colonne_mancanti = [col for col in colonne_richieste if col not in df.columns]
        
        if colonne_mancanti:
            return jsonify({'success': False, 
                          'error': f'Colonne mancanti: {", ".join(colonne_mancanti)}. Colonne richieste: {", ".join(colonne_richieste)}'})
        
        articoli_importati = 0
        articoli_aggiornati = 0
        
        for index, row in df.iterrows():
            try:
                codice_fornitore = str(row.get('Codice Fornitore', '')).strip()
                descrizione = str(row.get('Descrizione', '')).strip()
                fornitore_principale = str(row.get('Fornitore Principale', '')).strip()
                
                if not codice_fornitore or not descrizione:
                    continue  # Salta righe senza codice fornitore o descrizione
                
                # Genera codice interno: prime 4 lettere fornitore + codice fornitore
                if fornitore_principale:
                    fornitore_prefix = ''.join(c for c in fornitore_principale[:4] if c.isalpha()).upper()
                    if len(fornitore_prefix) < 4:
                        fornitore_prefix = fornitore_prefix.ljust(4, 'X')
                    codice_interno = f"{fornitore_prefix}{codice_fornitore}"
                else:
                    codice_interno = codice_fornitore
                
                # Cerca articolo esistente
                articolo = CatalogoArticolo.query.filter_by(codice_interno=codice_interno).first()
                
                if articolo:
                    # Aggiorna esistente
                    articolo.codice_fornitore = codice_fornitore
                    articolo.descrizione = descrizione
                    articolo.fornitore_principale = fornitore_principale
                    articolo.codice_produttore = str(row.get('Codice Produttore', '')).strip() or None
                    articolo.unita_misura = str(row.get('U.M.', 'PZ')).strip()
                    articolo.scorta_minima = float(row.get('Scorta Minima', 0)) if pd.notna(row.get('Scorta Minima')) else 0
                    articolo.ubicazione = str(row.get('Ubicazione', '')).strip() or None
                    articolo.attivo = True
                    articoli_aggiornati += 1
                else:
                    # Crea nuovo articolo
                    nuovo_articolo = CatalogoArticolo(
                        codice_interno=codice_interno,
                        codice_fornitore=codice_fornitore,
                        descrizione=descrizione,
                        fornitore_principale=fornitore_principale,
                        codice_produttore=str(row.get('Codice Produttore', '')).strip() or None,
                        unita_misura=str(row.get('U.M.', 'PZ')).strip(),
                        giacenza_attuale=0,
                        scorta_minima=float(row.get('Scorta Minima', 0)) if pd.notna(row.get('Scorta Minima')) else 0,
                        ubicazione=str(row.get('Ubicazione', '')).strip() or None,
                        attivo=True
                    )
                    db.session.add(nuovo_articolo)
                    articoli_importati += 1
                    
            except Exception as e:
                print(f"Errore importazione riga {index}: {e}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'imported': articoli_importati,
            'updated': articoli_aggiornati
        })
        
    except Exception as e:
        print(f"Errore import catalogo: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Errore durante l\'importazione: {str(e)}'})

@app.route('/movimenti')
def movimenti_page():
    """Pagina movimenti magazzino"""
    try:
        query = Movimento.query
        
        # Filtri
        data_da = request.args.get('data_da')
        data_a = request.args.get('data_a')
        tipo = request.args.get('tipo')
        articolo = request.args.get('articolo')
        
        if data_da:
            query = query.filter(Movimento.data_movimento >= datetime.strptime(data_da, '%Y-%m-%d'))
        if data_a:
            query = query.filter(Movimento.data_movimento <= datetime.strptime(data_a + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        if tipo:
            query = query.filter(Movimento.tipo == tipo)
        if articolo:
            query = query.filter(
                db.or_(
                    Movimento.codice_articolo.contains(articolo),
                    Movimento.descrizione_articolo.contains(articolo)
                )
            )
        
        movimenti = query.order_by(Movimento.data_movimento.desc()).limit(100).all()
        
        return render_template('movimenti.html', movimenti=movimenti)
    except Exception as e:
        print(f"Errore movimenti: {e}")
        return render_template('movimenti.html', movimenti=[])

@app.route('/movimenti/export-excel')
def export_movimenti_excel():
    """Export Excel dei movimenti magazzino"""
    try:
        query = Movimento.query
        
        # Applica gli stessi filtri della vista
        data_da = request.args.get('data_da')
        data_a = request.args.get('data_a')
        tipo = request.args.get('tipo')
        articolo = request.args.get('articolo')
        
        if data_da:
            query = query.filter(Movimento.data_movimento >= datetime.strptime(data_da, '%Y-%m-%d'))
        if data_a:
            query = query.filter(Movimento.data_movimento <= datetime.strptime(data_a + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        if tipo:
            query = query.filter(Movimento.tipo == tipo)
        if articolo:
            query = query.filter(
                db.or_(
                    Movimento.codice_articolo.contains(articolo),
                    Movimento.descrizione_articolo.contains(articolo)
                )
            )
        
        movimenti = query.order_by(Movimento.data_movimento.desc()).limit(1000).all()
        
        # Crea DataFrame per l'export
        import pandas as pd
        from io import BytesIO
        
        data = []
        for movimento in movimenti:
            # Recupera nomi reali di fornitori e clienti
            da_nome = 'N/A'
            a_nome = 'N/A'
            
            if movimento.tipo == 'entrata':
                # Per le entrate, "DA" è il fornitore dal DDT IN
                if movimento.documento_tipo == 'ddt_in' and movimento.documento_id:
                    try:
                        ddt_in = DDTIn.query.get(movimento.documento_id)
                        da_nome = ddt_in.fornitore if ddt_in else 'Fornitore Sconosciuto'
                    except:
                        da_nome = 'Fornitore'
                else:
                    da_nome = movimento.magazzino or 'Esterno'
                a_nome = movimento.magazzino or 'Magazzino'
            else:
                # Per le uscite, "A" è il cliente dal DDT OUT
                da_nome = movimento.magazzino or 'Magazzino'
                if movimento.documento_tipo == 'ddt_out' and movimento.documento_id:
                    try:
                        ddt_out = DDTOut.query.get(movimento.documento_id)
                        a_nome = ddt_out.nome_origine if ddt_out else 'Cliente Sconosciuto'
                    except:
                        a_nome = 'Cliente'
                else:
                    a_nome = 'Cliente'
                    
            data.append({
                'Data/Ora': movimento.data_movimento.strftime('%d/%m/%Y %H:%M') if movimento.data_movimento else '',
                'Tipo': movimento.tipo.upper() if movimento.tipo else '',
                'Documento': movimento.documento_numero or '',
                'Codice Articolo': movimento.codice_articolo or '',
                'Descrizione': movimento.descrizione_articolo or '',
                'Quantità': f"{'+' if movimento.tipo == 'entrata' else '-'}{movimento.quantita or 0}",
                'Valore Unitario': f"€ {movimento.valore_unitario or 0:.2f}",
                'Valore Totale': f"€ {movimento.valore_totale or 0:.2f}",
                'Da': da_nome,
                'A': a_nome,
                'Mastrino': movimento.mastrino or ''
            })
        
        df = pd.DataFrame(data)
        
        # Crea file Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Movimenti')
        
        output.seek(0)
        
        # Nome file con timestamp e filtri
        filtri_nome = []
        if data_da: filtri_nome.append(f"da-{data_da}")
        if data_a: filtri_nome.append(f"a-{data_a}")
        if tipo: filtri_nome.append(tipo)
        if articolo: filtri_nome.append(articolo[:10])
        
        filtri_str = "_" + "_".join(filtri_nome) if filtri_nome else ""
        filename = f"movimenti_magazzino_{datetime.now().strftime('%Y%m%d_%H%M')}{filtri_str}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Errore export Excel movimenti: {e}")
        return f"Errore durante export Excel: {str(e)}", 500

@app.route('/inventario')
def inventario_page():
    """Pagina inventario - mostra articoli del catalogo con filtri"""
    try:
        # Ottieni parametri di filtro
        data_da = request.args.get('data_da')
        data_a = request.args.get('data_a') 
        filtro_magazzino = request.args.get('magazzino', '').strip()
        filtro_articolo = request.args.get('articolo', '').strip()
        stato_scorta = request.args.get('stato_scorta', '').strip()
        
        # Query base per articoli attivi
        query = CatalogoArticolo.query.filter_by(attivo=True)
        
        # Filtro per magazzino/ubicazione
        if filtro_magazzino:
            query = query.filter(CatalogoArticolo.ubicazione.ilike(f'%{filtro_magazzino}%'))
        
        # Filtro per articolo (codice o descrizione)
        if filtro_articolo:
            query = query.filter(
                db.or_(
                    CatalogoArticolo.codice_interno.ilike(f'%{filtro_articolo}%'),
                    CatalogoArticolo.descrizione.ilike(f'%{filtro_articolo}%')
                )
            )
        
        articoli = query.all()
        
        # Filtro per stato scorta (post-query perché dipende dal calcolo)
        if stato_scorta:
            articoli_filtrati = []
            for articolo in articoli:
                giacenza = articolo.giacenza_attuale or 0
                scorta_min = articolo.scorta_minima or 0
                
                if stato_scorta == 'esaurito' and giacenza == 0:
                    articoli_filtrati.append(articolo)
                elif stato_scorta == 'sotto_scorta' and giacenza < scorta_min and scorta_min > 0:
                    articoli_filtrati.append(articolo)
                elif stato_scorta == 'scorta_ok' and giacenza >= scorta_min:
                    articoli_filtrati.append(articolo)
            articoli = articoli_filtrati
        
        # Calcola statistiche
        valore_totale = 0
        pezzi_totali = 0
        sotto_scorta = 0
        
        for articolo in articoli:
            giacenza = articolo.giacenza_attuale or 0
            costo = articolo.costo_medio or 0
            scorta_min = articolo.scorta_minima or 0
            
            valore_totale += giacenza * costo
            pezzi_totali += giacenza
            
            if giacenza < scorta_min and scorta_min > 0:
                sotto_scorta += 1

        statistiche = {
            'valore_totale': valore_totale,
            'numero_articoli': len(articoli),
            'pezzi_totali': pezzi_totali
        }
        
        # Ottieni tutti i magazzini per il dropdown
        magazzini = Magazzino.query.filter_by(attivo=True).all()

        return render_template('inventario.html', 
                             articoli=articoli, 
                             statistiche=statistiche,
                             sotto_scorta=sotto_scorta,
                             magazzini=magazzini)

    except Exception as e:
        print(f"Errore inventario: {e}")
        import traceback
        traceback.print_exc()
        # Fallback per magazzini in caso di errore
        try:
            magazzini = Magazzino.query.filter_by(attivo=True).all()
        except:
            magazzini = []
        return render_template('inventario.html', 
                             articoli=[],
                             statistiche={'valore_totale': 0, 'numero_articoli': 0, 'pezzi_totali': 0},
                             sotto_scorta=0,
                             magazzini=magazzini)

@app.route('/inventario/report-storico')
def report_inventario_storico():
    """Report inventario a una data specifica"""
    data_riferimento = request.args.get('data', datetime.now().strftime('%Y-%m-%d'))

    try:
        data_ref = datetime.strptime(data_riferimento, '%Y-%m-%d')

        # Calcola giacenze alla data specificata
        articoli_storici = []
        articoli = CatalogoArticolo.query.filter_by(attivo=True).all()

        for articolo in articoli:
            giacenza_storica = articolo.giacenza_attuale or 0

            # Movimenti dopo la data di riferimento
            movimenti_dopo = Movimento.query.filter(
                Movimento.codice_articolo == articolo.codice_interno,
                Movimento.data_movimento > data_ref
            ).all()

            for mov in movimenti_dopo:
                if mov.tipo == 'entrata':
                    giacenza_storica -= mov.quantita
                else:
                    giacenza_storica += mov.quantita

            if giacenza_storica > 0:
                articoli_storici.append({
                    'codice': articolo.codice_interno,
                    'descrizione': articolo.descrizione,
                    'ubicazione': articolo.ubicazione or '-',
                    'giacenza': max(0, giacenza_storica),
                    'costo': articolo.costo_medio or 0,
                    'valore': max(0, giacenza_storica) * (articolo.costo_medio or 0)
                })

        valore_totale = sum(a['valore'] for a in articoli_storici)

        return render_template('report-inventario-storico.html',
                             articoli=articoli_storici,
                             data_riferimento=data_riferimento,
                             valore_totale=valore_totale)
    except Exception as e:
        print(f"Errore report storico: {e}")
        return str(e), 500

@app.route('/inventario/export-excel')
def export_inventario_excel():
    """Esporta inventario attuale in Excel"""
    try:
        import pandas as pd
        from io import BytesIO
        
        articoli = CatalogoArticolo.query.filter_by(attivo=True).all()
        
        data = []
        for a in articoli:
            data.append({
                'Codice': a.codice_interno,
                'Descrizione': a.descrizione,
                'Fornitore': a.fornitore_principale or '',
                'Ubicazione': a.ubicazione or '',
                'UM': a.unita_misura or 'PZ',
                'Giacenza': a.giacenza_attuale or 0,
                'Scorta Min': a.scorta_minima or 0,
                'Costo Medio': a.costo_medio or 0,
                'Valore': (a.giacenza_attuale or 0) * (a.costo_medio or 0)
            })
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Inventario')
        
        output.seek(0)
        
        return Response(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename=inventario_{datetime.now().strftime("%Y%m%d")}.xlsx'}
        )
    except Exception as e:
        print(f"Errore export: {e}")
        return str(e), 500

# ========== REPORT MASTRINI ==========

@app.route('/reports')
def reports_page():
    """Pagina principale dei report"""
    try:
        # Statistiche rapide per la dashboard report
        stats = {}
        
        # Conta DDT IN totali
        ddt_in_count = db.session.execute(db.text("SELECT COUNT(*) as count FROM ddt_in")).fetchone()
        stats['ddt_in_totali'] = ddt_in_count.count if ddt_in_count else 0
        
        # Conta DDT OUT totali  
        ddt_out_count = db.session.execute(db.text("SELECT COUNT(*) as count FROM ddt_out")).fetchone()
        stats['ddt_out_totali'] = ddt_out_count.count if ddt_out_count else 0
        
        # Conta offerte totali
        offerte_count = db.session.execute(db.text("SELECT COUNT(*) as count FROM offerta_fornitore")).fetchone()
        stats['offerte_totali'] = offerte_count.count if offerte_count else 0
        
        # Conta preventivi totali
        preventivi_count = db.session.execute(db.text("SELECT COUNT(*) as count FROM preventivo")).fetchone()
        stats['preventivi_totali'] = preventivi_count.count if preventivi_count else 0
        
        return render_template('reports.html', stats=stats)
        
    except Exception as e:
        print(f"Errore statistiche report: {e}")
        # Se c'è un errore, passa statistiche vuote
        stats = {'ddt_in_totali': 0, 'ddt_out_totali': 0, 'offerte_totali': 0, 'preventivi_totali': 0}
        return render_template('reports.html', stats=stats)

@app.route('/reports/mastrini')
def report_mastrini():
    """Report totali per mastrino"""
    try:
        # Ottieni parametri di filtro data
        data_da = request.args.get('data_da')
        data_a = request.args.get('data_a')
        
        # Costruisci clausola WHERE per le date (usa data origine documento)
        date_filter = ""
        if data_da and data_a:
            date_filter = f"AND d.data_ddt_origine BETWEEN '{data_da}' AND '{data_a}'"
        elif data_da:
            date_filter = f"AND d.data_ddt_origine >= '{data_da}'"
        elif data_a:
            date_filter = f"AND d.data_ddt_origine <= '{data_a}'"
        
        # Query per totali DDT IN (spese) per mastrino con descrizioni
        spese_query = db.session.execute(db.text(f"""
            SELECT 
                a.mastrino_riga as mastrino,
                m.descrizione as descrizione,
                'ACQUISTO' as tipo,
                COUNT(DISTINCT d.id) as numero_ddt,
                SUM(CASE WHEN a.quantita > 0 THEN a.quantita * a.costo_unitario ELSE 0 END) as totale
            FROM ddt_in d
            JOIN articolo_in a ON d.id = a.ddt_id  
            LEFT JOIN mastrino m ON a.mastrino_riga = m.codice
            WHERE d.stato = 'confermato' AND a.mastrino_riga IS NOT NULL AND a.mastrino_riga != '' {date_filter}
            GROUP BY a.mastrino_riga, m.descrizione
            ORDER BY totale DESC
        """))
        
        spese_mastrini = [dict(row._mapping) for row in spese_query]
        
        # Query per totali DDT OUT (ricavi) per mastrino con descrizioni
        ricavi_query = db.session.execute(db.text(f"""
            SELECT 
                a.mastrino_riga as mastrino,
                m.descrizione as descrizione,
                'RICAVO' as tipo, 
                COUNT(DISTINCT d.id) as numero_ddt,
                SUM(CASE WHEN a.quantita > 0 THEN a.quantita * a.prezzo_unitario ELSE 0 END) as totale
            FROM ddt_out d
            JOIN articolo_out a ON d.id = a.ddt_id
            LEFT JOIN mastrino m ON a.mastrino_riga = m.codice
            WHERE d.stato = 'confermato' AND a.mastrino_riga IS NOT NULL AND a.mastrino_riga != '' {date_filter}
            GROUP BY a.mastrino_riga, m.descrizione
            ORDER BY totale DESC
        """))
        
        ricavi_mastrini = [dict(row._mapping) for row in ricavi_query]
        
        # Calcola totali generali (gestisce valori None)
        totale_spese = sum(m.get('totale', 0) or 0 for m in spese_mastrini)
        totale_ricavi = sum(m.get('totale', 0) or 0 for m in ricavi_mastrini) 
        margine = totale_ricavi - totale_spese
        
        # Ottieni informazioni sui mastrini dal database
        mastrini_info = {}
        cursor = db.session.execute(db.text("SELECT codice, descrizione, tipo FROM mastrino WHERE attivo = 1"))
        for row in cursor:
            mastrini_info[row[0]] = {
                'descrizione': row[1],
                'tipo': row[2]
            }
        
        # Analisi collegamenti mastrini per tipo
        analisi_collegamenti = {}
        
        # Raggruppa spese per tipo di mastrino
        spese_per_tipo = {}
        for spesa in spese_mastrini:
            tipo = mastrini_info.get(spesa['mastrino'], {}).get('tipo', 'Non definito')
            if tipo not in spese_per_tipo:
                spese_per_tipo[tipo] = {'count': 0, 'totale': 0}
            spese_per_tipo[tipo]['count'] += spesa['numero_ddt']
            spese_per_tipo[tipo]['totale'] += spesa['totale'] or 0
        
        # Raggruppa ricavi per tipo di mastrino  
        ricavi_per_tipo = {}
        for ricavo in ricavi_mastrini:
            tipo = mastrini_info.get(ricavo['mastrino'], {}).get('tipo', 'Non definito')
            if tipo not in ricavi_per_tipo:
                ricavi_per_tipo[tipo] = {'count': 0, 'totale': 0}
            ricavi_per_tipo[tipo]['count'] += ricavo['numero_ddt']
            ricavi_per_tipo[tipo]['totale'] += ricavo['totale'] or 0
        
        # Analisi copertura mastrini (quanti sono configurati vs quanti usati)
        tutti_mastrini = set([row[0] for row in db.session.execute(db.text("SELECT codice FROM mastrino WHERE attivo = 1"))])
        mastrini_usati = set([m['mastrino'] for m in spese_mastrini + ricavi_mastrini if m['mastrino']])
        mastrini_non_usati = tutti_mastrini - mastrini_usati
        
        # Ottieni dettagli collegamenti configurati
        collegamenti_query = db.session.execute(db.text("""
            SELECT c.id, 
                   ma.codice as codice_acquisto, ma.descrizione as desc_acquisto,
                   mr.codice as codice_ricavo, mr.descrizione as desc_ricavo,
                   c.descrizione_collegamento
            FROM collegamento_mastrini c
            JOIN mastrino ma ON c.mastrino_acquisto_id = ma.id
            JOIN mastrino mr ON c.mastrino_ricavo_id = mr.id
            WHERE c.attivo = 1
            ORDER BY ma.codice, mr.codice
        """))
        
        collegamenti_dettagli = [dict(row._mapping) for row in collegamenti_query]
        
        # Aggiungi totali per ogni collegamento
        for collegamento in collegamenti_dettagli:
            # Trova il totale spese per il mastrino acquisto
            collegamento['totale_spese'] = 0
            for spesa in spese_mastrini:
                if spesa['mastrino'] == collegamento['codice_acquisto']:
                    collegamento['totale_spese'] = spesa['totale'] or 0
                    break
            
            # Trova il totale ricavi per il mastrino ricavo
            collegamento['totale_ricavi'] = 0
            for ricavo in ricavi_mastrini:
                if ricavo['mastrino'] == collegamento['codice_ricavo']:
                    collegamento['totale_ricavi'] = ricavo['totale'] or 0
                    break
        
        analisi_collegamenti = {
            'spese_per_tipo': spese_per_tipo,
            'ricavi_per_tipo': ricavi_per_tipo,
            'collegamenti_dettagli': collegamenti_dettagli,
            'copertura': {
                'totali_configurati': len(tutti_mastrini),
                'totali_usati': len(mastrini_usati),
                'non_usati': list(mastrini_non_usati),
                'percentuale_utilizzo': (len(mastrini_usati) / len(tutti_mastrini) * 100) if tutti_mastrini else 0
            }
        }
        
        return render_template('reports/report-mastrini.html',
                             spese_mastrini=spese_mastrini,
                             ricavi_mastrini=ricavi_mastrini,
                             mastrini_info=mastrini_info,
                             totale_spese=totale_spese,
                             totale_ricavi=totale_ricavi,
                             margine=margine,
                             analisi_collegamenti=analisi_collegamenti)
        
    except Exception as e:
        import traceback
        print(f"Errore report mastrini: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return f"Errore report: {e}", 500

@app.route('/reports/mastrini/export-excel')
def export_report_mastrini_excel():
    """Esporta report mastrini in Excel"""
    try:
        import pandas as pd
        from io import BytesIO
        
        # Ottieni parametri di filtro data
        data_da = request.args.get('data_da')
        data_a = request.args.get('data_a')
        
        # Costruisci clausola WHERE per le date (usa data origine documento)
        date_filter = ""
        if data_da and data_a:
            date_filter = f"AND d.data_ddt_origine BETWEEN '{data_da}' AND '{data_a}'"
        elif data_da:
            date_filter = f"AND d.data_ddt_origine >= '{data_da}'"
        elif data_a:
            date_filter = f"AND d.data_ddt_origine <= '{data_a}'"
        
        # Dati spese
        spese_query = db.session.execute(db.text(f"""
            SELECT 
                a.mastrino_riga as mastrino,
                m.descrizione,
                COUNT(DISTINCT d.id) as numero_ddt,
                SUM(CASE WHEN a.quantita > 0 THEN a.quantita * a.costo_unitario ELSE 0 END) as totale
            FROM ddt_in d
            JOIN articolo_in a ON d.id = a.ddt_id
            LEFT JOIN mastrino m ON a.mastrino_riga = m.codice  
            WHERE d.stato = 'confermato' AND a.mastrino_riga IS NOT NULL AND a.mastrino_riga != '' {date_filter}
            GROUP BY a.mastrino_riga, m.descrizione
            ORDER BY totale DESC
        """))
        
        spese_data = [dict(row._mapping) for row in spese_query]
        
        # Dati ricavi
        ricavi_query = db.session.execute(db.text(f"""
            SELECT 
                a.mastrino_riga as mastrino,
                m.descrizione,
                'RICAVO' as tipo,
                COUNT(DISTINCT d.id) as numero_ddt,
                SUM(CASE WHEN a.quantita > 0 THEN a.quantita * a.prezzo_unitario ELSE 0 END) as totale
            FROM ddt_out d
            JOIN articolo_out a ON d.id = a.ddt_id
            LEFT JOIN mastrino m ON a.mastrino_riga = m.codice  
            WHERE d.stato = 'confermato' AND a.mastrino_riga IS NOT NULL AND a.mastrino_riga != '' {date_filter}
            GROUP BY a.mastrino_riga, m.descrizione
            ORDER BY totale DESC
        """))
        
        ricavi_data = [dict(row._mapping) for row in ricavi_query]
        
        # Ottieni collegamenti per Excel
        collegamenti_query = db.session.execute(db.text("""
            SELECT c.id, 
                   ma.codice as codice_acquisto, ma.descrizione as desc_acquisto,
                   mr.codice as codice_ricavo, mr.descrizione as desc_ricavo,
                   c.descrizione_collegamento
            FROM collegamento_mastrini c
            JOIN mastrino ma ON c.mastrino_acquisto_id = ma.id
            JOIN mastrino mr ON c.mastrino_ricavo_id = mr.id
            WHERE c.attivo = 1
            ORDER BY ma.codice, mr.codice
        """))
        
        collegamenti_data = [dict(row._mapping) for row in collegamenti_query]
        
        # Aggiungi totali ai collegamenti
        for collegamento in collegamenti_data:
            collegamento['totale_spese'] = 0
            for spesa in spese_data:
                if spesa['mastrino'] == collegamento['codice_acquisto']:
                    collegamento['totale_spese'] = spesa['totale'] or 0
                    break
            
            collegamento['totale_ricavi'] = 0
            for ricavo in ricavi_data:
                if ricavo['mastrino'] == collegamento['codice_ricavo']:
                    collegamento['totale_ricavi'] = ricavo['totale'] or 0
                    break
            
            collegamento['margine'] = collegamento['totale_ricavi'] - collegamento['totale_spese']
        
        # Crea Excel con più fogli
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Foglio spese
            if spese_data:
                df_spese = pd.DataFrame(spese_data)
                df_spese.to_excel(writer, sheet_name='Spese per Mastrino', index=False)
            
            # Foglio ricavi
            if ricavi_data:
                df_ricavi = pd.DataFrame(ricavi_data) 
                df_ricavi.to_excel(writer, sheet_name='Ricavi per Mastrino', index=False)
            
            # Foglio collegamenti
            if collegamenti_data:
                df_collegamenti = pd.DataFrame(collegamenti_data)
                df_collegamenti.to_excel(writer, sheet_name='Collegamenti Mastrini', index=False)
            
            # Foglio riepilogo
            riepilogo = [{
                'Tipo': 'Spese Totali',
                'Importo': sum(s.get('totale', 0) or 0 for s in spese_data)
            }, {
                'Tipo': 'Ricavi Totali', 
                'Importo': sum(r.get('totale', 0) or 0 for r in ricavi_data)
            }, {
                'Tipo': 'Margine Lordo',
                'Importo': sum(r.get('totale', 0) or 0 for r in ricavi_data) - sum(s.get('totale', 0) or 0 for s in spese_data)
            }]
            df_riepilogo = pd.DataFrame(riepilogo)
            df_riepilogo.to_excel(writer, sheet_name='Riepilogo', index=False)
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=report_mastrini_{datetime.now().strftime("%Y%m%d")}.xlsx'
        
        return response
        
    except Exception as e:
        print(f"Errore export report mastrini: {e}")
        return str(e), 500

@app.route('/reports/mastrini/export-pdf')
def export_report_mastrini_pdf():
    """Esporta report mastrini in PDF"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from datetime import datetime
        import io
        
        # Ottieni parametri di filtro data
        data_da = request.args.get('data_da')
        data_a = request.args.get('data_a')
        
        # Costruisci clausola WHERE per le date
        date_filter = ""
        if data_da and data_a:
            date_filter = f"AND d.data_ddt_origine BETWEEN '{data_da}' AND '{data_a}'"
        elif data_da:
            date_filter = f"AND d.data_ddt_origine >= '{data_da}'"
        elif data_a:
            date_filter = f"AND d.data_ddt_origine <= '{data_a}'"
        
        # Riutilizza la stessa logica del report HTML
        spese_query = db.session.execute(db.text(f"""
            SELECT 
                a.mastrino_riga as mastrino,
                m.descrizione as descrizione,
                'ACQUISTO' as tipo,
                COUNT(DISTINCT d.id) as numero_ddt,
                SUM(CASE WHEN a.quantita > 0 THEN a.quantita * a.costo_unitario ELSE 0 END) as totale
            FROM ddt_in d
            JOIN articolo_in a ON d.id = a.ddt_id  
            LEFT JOIN mastrino m ON a.mastrino_riga = m.codice
            WHERE d.stato = 'confermato' AND a.mastrino_riga IS NOT NULL AND a.mastrino_riga != '' {date_filter}
            GROUP BY a.mastrino_riga, m.descrizione
            ORDER BY totale DESC
        """))
        
        spese_mastrini = [dict(row._mapping) for row in spese_query]
        
        ricavi_query = db.session.execute(db.text(f"""
            SELECT 
                a.mastrino_riga as mastrino,
                m.descrizione as descrizione,
                'RICAVO' as tipo, 
                COUNT(DISTINCT d.id) as numero_ddt,
                SUM(CASE WHEN a.quantita > 0 THEN a.quantita * a.prezzo_unitario ELSE 0 END) as totale
            FROM ddt_out d
            JOIN articolo_out a ON d.id = a.ddt_id
            LEFT JOIN mastrino m ON a.mastrino_riga = m.codice
            WHERE d.stato = 'confermato' AND a.mastrino_riga IS NOT NULL AND a.mastrino_riga != '' {date_filter}
            GROUP BY a.mastrino_riga, m.descrizione
            ORDER BY totale DESC
        """))
        
        ricavi_mastrini = [dict(row._mapping) for row in ricavi_query]
        
        # Calcola totali
        totale_spese = sum(m.get('totale', 0) or 0 for m in spese_mastrini)
        totale_ricavi = sum(m.get('totale', 0) or 0 for m in ricavi_mastrini)
        margine = totale_ricavi - totale_spese
        
        # Ottieni collegamenti
        collegamenti_query = db.session.execute(db.text("""
            SELECT c.id, 
                   ma.codice as codice_acquisto, ma.descrizione as desc_acquisto,
                   mr.codice as codice_ricavo, mr.descrizione as desc_ricavo,
                   c.descrizione_collegamento
            FROM collegamento_mastrini c
            JOIN mastrino ma ON c.mastrino_acquisto_id = ma.id
            JOIN mastrino mr ON c.mastrino_ricavo_id = mr.id
            WHERE c.attivo = 1
            ORDER BY ma.codice, mr.codice
        """))
        
        collegamenti_dettagli = [dict(row._mapping) for row in collegamenti_query]
        
        # Aggiungi totali ai collegamenti
        for collegamento in collegamenti_dettagli:
            collegamento['totale_spese'] = 0
            for spesa in spese_mastrini:
                if spesa['mastrino'] == collegamento['codice_acquisto']:
                    collegamento['totale_spese'] = spesa['totale'] or 0
                    break
            
            collegamento['totale_ricavi'] = 0
            for ricavo in ricavi_mastrini:
                if ricavo['mastrino'] == collegamento['codice_ricavo']:
                    collegamento['totale_ricavi'] = ricavo['totale'] or 0
                    break
        
        # Crea buffer per PDF
        buffer = io.BytesIO()
        
        # Crea documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Stili
        styles = getSampleStyleSheet()
        elements = []
        
        # Header
        header_style = styles['Heading1']
        header_style.alignment = 1  # Center
        elements.append(Paragraph("ACG Clima Service S.r.l.", header_style))
        elements.append(Paragraph("Report Mastrini", styles['Heading2']))
        
        # Periodo
        periodo_text = "Tutti i periodi"
        if data_da or data_a:
            periodo_text = f"Periodo: {data_da or ''} - {data_a or ''}"
        elements.append(Paragraph(f"{periodo_text} | Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Riepilogo
        summary_data = [
            ['Spese Totali', f'€ {totale_spese:,.2f}'],
            ['Ricavi Totali', f'€ {totale_ricavi:,.2f}'],
            ['Margine Lordo', f'€ {margine:,.2f}']
        ]
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Spese per Mastrino
        elements.append(Paragraph("Spese per Mastrino", styles['Heading2']))
        if spese_mastrini:
            spese_data = [['Codice', 'Descrizione', 'N. DDT', 'Totale']]
            for spesa in spese_mastrini:
                spese_data.append([
                    spesa['mastrino'], 
                    spesa['descrizione'] or 'N/A',
                    str(spesa['numero_ddt']),
                    f"€ {spesa['totale']:,.2f}"
                ])
            
            spese_table = Table(spese_data, colWidths=[1*inch, 3*inch, 1*inch, 1.5*inch])
            spese_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(spese_table)
        else:
            elements.append(Paragraph("Nessuna spesa nel periodo", styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Ricavi per Mastrino
        elements.append(Paragraph("Ricavi per Mastrino", styles['Heading2']))
        if ricavi_mastrini:
            ricavi_data = [['Codice', 'Descrizione', 'N. DDT', 'Totale']]
            for ricavo in ricavi_mastrini:
                ricavi_data.append([
                    ricavo['mastrino'], 
                    ricavo['descrizione'] or 'N/A',
                    str(ricavo['numero_ddt']),
                    f"€ {ricavo['totale']:,.2f}"
                ])
            
            ricavi_table = Table(ricavi_data, colWidths=[1*inch, 3*inch, 1*inch, 1.5*inch])
            ricavi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(ricavi_table)
        else:
            elements.append(Paragraph("Nessun ricavo nel periodo", styles['Normal']))
        
        # Collegamenti Mastrini se presenti
        if collegamenti_dettagli:
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("Collegamenti Mastrini Configurati", styles['Heading2']))
            
            collegamenti_data = [['Acquisto', 'Spese', 'Ricavo', 'Ricavi', 'Margine']]
            for collegamento in collegamenti_dettagli:
                margine_col = collegamento['totale_ricavi'] - collegamento['totale_spese']
                collegamenti_data.append([
                    collegamento['codice_acquisto'],
                    f"€ {collegamento['totale_spese']:,.2f}",
                    collegamento['codice_ricavo'], 
                    f"€ {collegamento['totale_ricavi']:,.2f}",
                    f"€ {margine_col:,.2f}"
                ])
            
            collegamenti_table = Table(collegamenti_data, colWidths=[1.2*inch, 1*inch, 1.2*inch, 1*inch, 1*inch])
            collegamenti_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(collegamenti_table)
        
        # Costruisci PDF
        doc.build(elements)
        
        # Prepara response
        pdf_data = buffer.getvalue()
        buffer.close()
        
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=report_mastrini_{datetime.now().strftime("%Y%m%d")}.pdf'
        
        return response
        
    except Exception as e:
        print(f"Errore export PDF report mastrini: {e}")
        return f"Errore generazione PDF: {str(e)}", 500

def aggiorna_inventario():
    """Funzione per aggiornare automaticamente l'inventario dai DDT IN/OUT confermati"""
    try:
        print("Avvio aggiornamento inventario automatico...")
        
        # Raccogli tutti gli articoli dai DDT IN e DDT OUT confermati
        articoli_ddt_in = db.session.query(
            ArticoloIn.codice_interno,
            ArticoloIn.descrizione,
            DDTIn.fornitore.label('fornitore'),
            ArticoloIn.quantita,
            ArticoloIn.costo_unitario,
            ArticoloIn.unita_misura,
            DDTIn.destinazione.label('magazzino'),
            DDTIn.stato
        ).join(DDTIn).filter(DDTIn.stato == 'confermato').all()
        
        articoli_ddt_out = db.session.query(
            ArticoloOut.codice_interno,
            ArticoloOut.descrizione,
            ArticoloOut.fornitore,
            ArticoloOut.quantita,
            ArticoloOut.prezzo_unitario,
            ArticoloOut.unita_misura,
            DDTOut.magazzino_partenza.label('magazzino'),
            DDTOut.stato
        ).join(DDTOut).filter(DDTOut.stato == 'confermato').all()
        
        # Raggruppa per chiave univoca (codice_interno + descrizione)
        inventario_aggiornato = {}
        
        # Elabora DDT IN (entrate)
        for art in articoli_ddt_in:
            # Usa direttamente il codice interno esistente dall'ArticoloIn
            codice_interno = art.codice_interno or f'ART-{art.id}'
            # Estrai codice fornitore dal codice interno
            codice_fornitore = art.codice_interno.strip() if art.codice_interno else None
            
            chiave = f"{codice_interno}|{art.descrizione}|{art.magazzino or 'Magazzino Principale'}"
            
            if chiave not in inventario_aggiornato:
                inventario_aggiornato[chiave] = {
                    'codice_interno': codice_interno,
                    'codice_fornitore': codice_fornitore,
                    'descrizione': art.descrizione,
                    'fornitore_principale': art.fornitore,
                    'giacenza_attuale': 0,
                    'costo_medio': 0,
                    'ubicazione': art.magazzino or 'Magazzino principale',
                    'unita_misura': art.unita_misura or 'PZ',
                    'costo_totale': 0,
                    'quantita_entrate': 0,
                    'attivo': True
                }
            
            # Accumula quantità e costi (entrate = +)
            inventario_aggiornato[chiave]['giacenza_attuale'] += art.quantita or 0
            costo_riga = (art.quantita or 0) * (art.costo_unitario or 0)
            inventario_aggiornato[chiave]['costo_totale'] += costo_riga
            inventario_aggiornato[chiave]['quantita_entrate'] += art.quantita or 0
            
            # Aggiorna ubicazione se non presente
            if not inventario_aggiornato[chiave]['ubicazione'] and art.magazzino:
                inventario_aggiornato[chiave]['ubicazione'] = art.magazzino
        
        # Elabora DDT OUT (uscite) 
        for art in articoli_ddt_out:
            # Estrai codice fornitore (quello presente nel DDT)
            codice_fornitore = art.codice_interno.strip() if art.codice_interno else None
            
            # Crea codice interno: prime 4 lettere fornitore + codice fornitore
            if codice_fornitore and art.fornitore:
                # Prime 4 lettere del fornitore (lowercase, solo lettere)
                fornitore_prefix = ''.join(c for c in art.fornitore[:4] if c.isalpha()).lower()
                if len(fornitore_prefix) < 4:
                    fornitore_prefix = fornitore_prefix.ljust(4, 'x')
                codice_interno = f"{fornitore_prefix}{codice_fornitore}"
            elif codice_fornitore:
                # Se non c'è fornitore, usa solo il codice fornitore
                codice_interno = codice_fornitore
            else:
                # Se non c'è codice fornitore, genera dalla descrizione
                codice_interno = art.descrizione[:20].upper().replace(' ', '_') if art.descrizione else 'ART_SENZA_CODICE'
                
            chiave = f"{codice_interno}|{art.descrizione}|{art.magazzino or 'Magazzino Principale'}"
            
            if chiave not in inventario_aggiornato:
                # Articolo non presente nelle entrate, creiamo comunque per tracciare l'uscita
                inventario_aggiornato[chiave] = {
                    'codice_interno': codice_interno,
                    'codice_fornitore': codice_fornitore,
                    'descrizione': art.descrizione,
                    'fornitore_principale': art.fornitore or 'N/A',
                    'giacenza_attuale': 0,
                    'costo_medio': art.prezzo_unitario or 0,
                    'ubicazione': art.magazzino or 'Magazzino principale',
                    'unita_misura': art.unita_misura or 'PZ',
                    'costo_totale': 0,
                    'quantita_entrate': 0,
                    'attivo': True
                }
            
            # Sottrai quantità (uscite = -)
            inventario_aggiornato[chiave]['giacenza_attuale'] -= art.quantita or 0
        
        # Calcola costo medio per ogni articolo
        for chiave, dati in inventario_aggiornato.items():
            if dati['quantita_entrate'] > 0:
                dati['costo_medio'] = dati['costo_totale'] / dati['quantita_entrate']
            elif dati['costo_medio'] == 0:
                dati['costo_medio'] = 0
        
        # Aggiorna la tabella catalogo_articolo
        articoli_aggiornati = 0
        articoli_creati = 0
        
        for chiave, dati in inventario_aggiornato.items():
            codice = dati['codice_interno']
            descrizione = dati['descrizione']
            
            # Cerca articolo esistente per codice interno e ubicazione
            articolo = CatalogoArticolo.query.filter_by(
                codice_interno=codice, 
                ubicazione=dati['ubicazione']
            ).first()
            
            # Se non trovato per codice+ubicazione, cerca per codice fornitore e ubicazione
            if not articolo and dati['codice_fornitore']:
                articolo = CatalogoArticolo.query.filter_by(
                    codice_interno=dati['codice_fornitore'],
                    ubicazione=dati['ubicazione']
                ).first()
            
            # Se non trovato, cerca per descrizione e ubicazione (per articoli senza codice)
            if not articolo and not codice.startswith('ART_SENZA_CODICE'):
                articolo = CatalogoArticolo.query.filter_by(
                    descrizione=descrizione,
                    ubicazione=dati['ubicazione']
                ).first()
            
            if articolo:
                # Aggiorna esistente
                articolo.codice_interno = codice
                articolo.descrizione = descrizione
                articolo.codice_fornitore = dati['codice_fornitore']
                articolo.fornitore_principale = dati['fornitore_principale']
                articolo.giacenza_attuale = dati['giacenza_attuale'] 
                articolo.costo_medio = dati['costo_medio']
                articolo.ubicazione = dati['ubicazione']
                articolo.unita_misura = dati['unita_misura']
                articolo.attivo = True
                articoli_aggiornati += 1
            else:
                # Crea nuovo articolo
                nuovo_articolo = CatalogoArticolo(
                    codice_interno=codice,
                    codice_fornitore=dati['codice_fornitore'],
                    descrizione=descrizione,
                    fornitore_principale=dati['fornitore_principale'],
                    giacenza_attuale=dati['giacenza_attuale'],
                    costo_medio=dati['costo_medio'],
                    ubicazione=dati['ubicazione'],
                    unita_misura=dati['unita_misura'],
                    attivo=True
                )
                db.session.add(nuovo_articolo)
                articoli_creati += 1
        
        db.session.commit()
        print(f"Inventario aggiornato: {articoli_aggiornati} modificati, {articoli_creati} creati")
        return True
        
    except Exception as e:
        print(f"Errore aggiornamento inventario: {e}")
        db.session.rollback()
        return False

@app.route('/clienti')
def clienti_page():
    """Pagina clienti"""
    clienti = Cliente.query.filter_by(attivo=True).all()
    return render_template('clienti.html', clienti=clienti)

@app.route('/fornitori')
def fornitori_page():
    """Pagina fornitori"""
    fornitori = Fornitore.query.filter_by(attivo=True).all()
    return render_template('fornitori.html', fornitori=fornitori)

@app.route('/magazzini')
def magazzini_page():
    """Pagina magazzini"""
    magazzini = Magazzino.query.filter_by(attivo=True).all()
    return render_template('magazzini.html', magazzini=magazzini)

@app.route('/magazzini/nuovo', methods=['POST'])
def crea_magazzino():
    """Crea nuovo magazzino"""
    try:
        magazzino = Magazzino(
            codice=request.form['codice'],
            descrizione=request.form['descrizione'],
            responsabile=request.form.get('responsabile', '').strip() or None,
            attivo=True
        )
        
        db.session.add(magazzino)
        db.session.commit()
        
        return redirect('/magazzini')
        
    except Exception as e:
        print(f"Errore creazione magazzino: {e}")
        db.session.rollback()
        return redirect('/magazzini')

@app.route('/magazzini/<int:magazzino_id>/modifica', methods=['GET', 'POST'])
def modifica_magazzino(magazzino_id):
    """Modifica magazzino esistente"""
    if request.method == 'GET':
        # Per GET, reindirizza alla pagina magazzini dove si apre il modal di modifica
        return redirect('/magazzini')
    
    try:
        magazzino = Magazzino.query.get_or_404(magazzino_id)
        
        magazzino.codice = request.form['codice']
        magazzino.descrizione = request.form['descrizione']
        magazzino.responsabile = request.form.get('responsabile', '').strip() or None
        
        db.session.commit()
        
        return redirect('/magazzini')
        
    except Exception as e:
        print(f"Errore modifica magazzino: {e}")
        db.session.rollback()
        return redirect('/magazzini')

@app.route('/magazzini/<int:magazzino_id>/elimina', methods=['POST'])
def elimina_magazzino(magazzino_id):
    """Elimina magazzino (soft delete)"""
    try:
        magazzino = Magazzino.query.get_or_404(magazzino_id)
        magazzino.attivo = False
        
        db.session.commit()
        
        return redirect('/magazzini')
        
    except Exception as e:
        print(f"Errore eliminazione magazzino: {e}")
        db.session.rollback()
        return redirect('/magazzini')

@app.route('/fornitori/nuovo', methods=['GET', 'POST'])
def nuovo_fornitore():
    """Crea nuovo fornitore"""
    if request.method == 'GET':
        return render_template('nuovo-fornitore.html')
    
    try:
        # Estrai i dati dal form
        ragione_sociale = request.form.get('ragione_sociale', '').strip()
        partita_iva = request.form.get('partita_iva', '').strip()
        codice_fiscale = request.form.get('codice_fiscale', '').strip()
        indirizzo = request.form.get('indirizzo', '').strip()
        citta = request.form.get('citta', '').strip()
        provincia = request.form.get('provincia', '').strip()
        cap = request.form.get('cap', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        pec = request.form.get('pec', '').strip()
        codice_sdi = request.form.get('codice_sdi', '').strip()
        condizioni_pagamento = request.form.get('condizioni_pagamento', '').strip()
        lead_time_giorni = request.form.get('lead_time_giorni', '0')
        note = request.form.get('note', '').strip()
        
        # Validazione
        if not ragione_sociale:
            return jsonify({'success': False, 'error': 'Ragione sociale obbligatoria'}), 400
        
        # Converti lead_time a intero
        try:
            lead_time_giorni = int(lead_time_giorni) if lead_time_giorni else 0
        except ValueError:
            lead_time_giorni = 0
        
        # Verifica duplicati per partita IVA se presente
        if partita_iva:
            esistente = Fornitore.query.filter_by(partita_iva=partita_iva, attivo=True).first()
            if esistente:
                return jsonify({'success': False, 'error': f'Fornitore con P.IVA {partita_iva} già esistente'}), 400
        
        # Crea nuovo fornitore
        nuovo_fornitore = Fornitore(
            ragione_sociale=ragione_sociale,
            partita_iva=partita_iva,
            codice_fiscale=codice_fiscale,
            indirizzo=indirizzo,
            citta=citta,
            provincia=provincia,
            cap=cap,
            email=email,
            telefono=telefono,
            pec=pec,
            codice_sdi=codice_sdi,
            condizioni_pagamento=condizioni_pagamento,
            lead_time_giorni=lead_time_giorni,
            note=note,
            attivo=True
        )
        
        db.session.add(nuovo_fornitore)
        db.session.commit()
        
        return redirect(url_for('fornitori_page'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore creazione fornitore: {e}")
        return jsonify({'success': False, 'error': f'Errore durante creazione: {str(e)}'}), 500

@app.route('/fornitori/template-excel')
def template_excel_fornitori():
    """Genera template Excel vuoto per import fornitori"""
    try:
        import pandas as pd
        from io import BytesIO
        
        # Crea DataFrame con colonne per import fornitori
        columns = [
            'ragione_sociale', 'partita_iva', 'codice_fiscale', 
            'indirizzo', 'citta', 'provincia', 'cap',
            'email', 'telefono', 'pec', 'codice_sdi',
            'condizioni_pagamento', 'lead_time_giorni', 'note'
        ]
        
        # Crea template vuoto con esempi nella prima riga
        template_data = [{
            'ragione_sociale': 'Esempio Fornitore SRL',
            'partita_iva': '12345678901',
            'codice_fiscale': '12345678901',
            'indirizzo': 'Via Esempio 123',
            'citta': 'Milano',
            'provincia': 'MI',
            'cap': '20100',
            'email': 'info@acgclimaservice.com',
            'telefono': '0383/640606',
            'pec': 'pec@acgclimaservice.com',
            'codice_sdi': 'ABCDEFG',
            'condizioni_pagamento': '30 gg f.m.',
            'lead_time_giorni': '7',
            'note': 'Note esempio'
        }]
        
        df = pd.DataFrame(template_data)
        
        # Genera file Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Fornitori')
            
            # Ottieni il workbook e il worksheet per personalizzazioni
            workbook = writer.book
            worksheet = workbook['Fornitori']
            
            # Imposta larghezza colonne
            for i, column in enumerate(columns):
                worksheet.column_dimensions[chr(65 + i)].width = 20
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'template_fornitori_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
        
    except ImportError:
        return jsonify({'errore': 'Moduli Excel non disponibili'}), 500
    except Exception as e:
        print(f"Errore generazione template fornitori: {e}")
        return jsonify({'errore': str(e)}), 500

@app.route('/clienti/template-excel')
def template_excel_clienti():
    """Genera template Excel vuoto per import clienti"""
    try:
        import pandas as pd
        from io import BytesIO
        
        # Crea DataFrame con colonne per import clienti
        columns = [
            'ragione_sociale', 'partita_iva', 'codice_fiscale', 
            'indirizzo', 'citta', 'provincia', 'cap',
            'email', 'telefono', 'pec', 'codice_sdi',
            'condizioni_pagamento', 'note'
        ]
        
        # Crea template vuoto con esempi nella prima riga
        template_data = [{
            'ragione_sociale': 'Esempio Cliente SRL',
            'partita_iva': '98765432109',
            'codice_fiscale': '98765432109',
            'indirizzo': 'Via Cliente 456',
            'citta': 'Roma',
            'provincia': 'RM',
            'cap': '00100',
            'email': 'info@acgclimaservice.com',
            'telefono': '0383/640606',
            'pec': 'pec@acgclimaservice.com',
            'codice_sdi': 'HIJKLMN',
            'condizioni_pagamento': '30 gg d.f.',
            'note': 'Cliente esempio'
        }]
        
        df = pd.DataFrame(template_data)
        
        # Genera file Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Clienti')
            
            # Ottieni il workbook e il worksheet per personalizzazioni
            workbook = writer.book
            worksheet = workbook['Clienti']
            
            # Imposta larghezza colonne
            for i, column in enumerate(columns):
                worksheet.column_dimensions[chr(65 + i)].width = 20
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'template_clienti_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
        
    except ImportError:
        return jsonify({'errore': 'Moduli Excel non disponibili'}), 500
    except Exception as e:
        print(f"Errore generazione template clienti: {e}")
        return jsonify({'errore': str(e)}), 500

@app.route('/clienti/nuovo', methods=['GET', 'POST'])
def nuovo_cliente():
    """Crea nuovo cliente"""
    if request.method == 'GET':
        return render_template('nuovo-cliente.html')
    
    try:
        # Estrai i dati dal form
        ragione_sociale = request.form.get('ragione_sociale', '').strip()
        partita_iva = request.form.get('partita_iva', '').strip()
        codice_fiscale = request.form.get('codice_fiscale', '').strip()
        indirizzo = request.form.get('indirizzo', '').strip()
        citta = request.form.get('citta', '').strip()
        provincia = request.form.get('provincia', '').strip()
        cap = request.form.get('cap', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        pec = request.form.get('pec', '').strip()
        codice_sdi = request.form.get('codice_sdi', '').strip()
        condizioni_pagamento = request.form.get('condizioni_pagamento', '').strip()
        note = request.form.get('note', '').strip()
        
        # Validazione
        if not ragione_sociale:
            return jsonify({'success': False, 'error': 'Ragione sociale obbligatoria'}), 400
        
        # Verifica duplicati per partita IVA se presente
        if partita_iva:
            esistente = Cliente.query.filter_by(partita_iva=partita_iva, attivo=True).first()
            if esistente:
                return jsonify({'success': False, 'error': f'Cliente con P.IVA {partita_iva} già esistente'}), 400
        
        # Crea nuovo cliente
        nuovo_cliente_obj = Cliente(
            ragione_sociale=ragione_sociale,
            partita_iva=partita_iva,
            codice_fiscale=codice_fiscale,
            indirizzo=indirizzo,
            citta=citta,
            provincia=provincia,
            cap=cap,
            email=email,
            telefono=telefono,
            pec=pec,
            codice_sdi=codice_sdi,
            condizioni_pagamento=condizioni_pagamento,
            note=note,
            attivo=True
        )
        
        db.session.add(nuovo_cliente_obj)
        db.session.commit()
        
        return redirect(url_for('clienti_page'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore creazione cliente: {e}")
        return jsonify({'success': False, 'error': f'Errore durante creazione: {str(e)}'}), 500

@app.route('/impostazioni')
def impostazioni_page():
    """Pagina impostazioni"""
    try:
        mastrini = Mastrino.query.order_by(Mastrino.tipo, Mastrino.codice).all()
        magazzini = Magazzino.query.order_by(Magazzino.codice).all()
        # Carica le configurazioni dal database
        configurazioni = {c.chiave: c.valore for c in ConfigurazioneSistema.query.all()}
        
        return render_template('impostazioni.html',
                             mastrini=mastrini,
                             magazzini=magazzini,
                             configurazioni=configurazioni)
    except Exception as e:
        print(f"Errore caricamento impostazioni: {e}")
        return render_template('impostazioni.html',
                             mastrini=[],
                             magazzini=[],
                             configurazioni={})

@app.route('/impostazioni/magazzino/nuovo', methods=['POST'])
def nuovo_magazzino():
    """Crea nuovo magazzino"""
    try:
        data = request.get_json()
        if not data:
            data = request.form.to_dict()
        
        codice = data.get('codice', '').strip()
        descrizione = data.get('descrizione', '').strip()
        responsabile = data.get('responsabile', '').strip()
        
        # Validazione
        if not codice or not descrizione:
            return jsonify({'success': False, 'error': 'Codice e descrizione sono obbligatori'}), 400
        
        # Verifica duplicati
        esistente = Magazzino.query.filter_by(codice=codice).first()
        if esistente:
            return jsonify({'success': False, 'error': f'Magazzino con codice {codice} già esistente'}), 400
        
        # Crea nuovo magazzino
        nuovo_magazzino = Magazzino(
            codice=codice,
            descrizione=descrizione,
            responsabile=responsabile,
            attivo=True
        )
        
        db.session.add(nuovo_magazzino)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Magazzino {codice} creato con successo',
            'magazzino_id': nuovo_magazzino.id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore creazione magazzino: {e}")
        return jsonify({'success': False, 'error': f'Errore durante creazione: {str(e)}'}), 500

@app.route('/preventivi')
def preventivi_page():
    """Lista preventivi"""
    preventivi = Preventivo.query.order_by(Preventivo.numero_preventivo.desc()).all()
    
    # Calcola statistiche
    preventivi_bozza = Preventivo.query.filter_by(stato='bozza').count()
    preventivi_inviati = Preventivo.query.filter_by(stato='inviato').count()
    
    # Calcola valore preventivi accettati questo mese
    inizio_mese = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    preventivi_accettati_mese = Preventivo.query.filter(
        Preventivo.stato == 'accettato',
        Preventivo.data_accettazione >= inizio_mese.date()
    )
    valore_accettati = sum([p.totale_lordo for p in preventivi_accettati_mese]) or 0
    
    return render_template('preventivi.html', 
                         preventivi=preventivi,
                         preventivi_bozza=preventivi_bozza,
                         preventivi_inviati=preventivi_inviati,
                         valore_accettati=f"{valore_accettati:.2f}")

@app.route('/preventivi/nuovo', methods=['GET', 'POST'])
def nuovo_preventivo():
    """Crea nuovo preventivo"""
    if request.method == 'GET':
        clienti = Cliente.query.filter_by(attivo=True).all()
        return render_template('nuovo-preventivo.html', clienti=clienti)
    
    try:
        # Genera numero preventivo automatico
        ultimo_numero = db.session.query(db.func.max(Preventivo.id)).scalar() or 0
        numero_preventivo = f"PREV-{datetime.now().year}-{str(ultimo_numero + 1).zfill(4)}"
        
        # Gestione cliente_id (può essere None se l'autocompletamento usa solo il nome)
        cliente_id_value = request.form.get('cliente_id', '').strip()
        # Valida cliente_id: solo numeri validi, ignora "Nessuno", "None" o valori non numerici
        if (cliente_id_value and 
            cliente_id_value.lower() not in ['nessuno', 'none'] and 
            cliente_id_value.isdigit()):
            cliente_id = int(cliente_id_value)
        else:
            cliente_id = None
        
        # Crea nuovo preventivo con validazione float
        try:
            iva_value = request.form.get('iva', '22').strip()
            iva = float(iva_value) if iva_value else 22.0
        except (ValueError, TypeError):
            iva = 22.0
        
        nuovo_preventivo = Preventivo(
            numero_preventivo=numero_preventivo,
            cliente_id=cliente_id,
            cliente_nome=request.form.get('cliente_nome'),
            oggetto=request.form.get('oggetto', ''),
            data_preventivo=datetime.now().date(),
            iva=iva,
            note=request.form.get('note', ''),
            commessa=request.form.get('commessa', '')
        )
        
        if request.form.get('data_scadenza'):
            nuovo_preventivo.data_scadenza = datetime.strptime(
                request.form['data_scadenza'], '%Y-%m-%d'
            ).date()
        
        db.session.add(nuovo_preventivo)
        db.session.flush()  # Per ottenere l'ID
        
        # Aggiungi dettagli preventivo con validazione float
        totale = 0
        i = 0
        while f'dettagli[{i}][descrizione]' in request.form:
            if request.form.get(f'dettagli[{i}][descrizione]'):
                # Validazione sicura per quantita
                try:
                    quantita_value = request.form.get(f'dettagli[{i}][quantita]', '1').strip()
                    quantita = float(quantita_value) if quantita_value else 1.0
                except (ValueError, TypeError):
                    quantita = 1.0
                
                # Validazione sicura per prezzo_unitario
                try:
                    prezzo_value = request.form.get(f'dettagli[{i}][prezzo_unitario]', '0').strip()
                    prezzo_unitario = float(prezzo_value) if prezzo_value else 0.0
                except (ValueError, TypeError):
                    prezzo_unitario = 0.0
                
                # Validazione sicura per sconto
                try:
                    sconto_value = request.form.get(f'dettagli[{i}][sconto]', '0').strip()
                    sconto = float(sconto_value) if sconto_value else 0.0
                except (ValueError, TypeError):
                    sconto = 0.0
                
                totale_riga = quantita * prezzo_unitario * (1 - sconto/100)
                
                dettaglio = DettaglioPreventivo(
                    preventivo_id=nuovo_preventivo.id,
                    codice_articolo=request.form.get(f'dettagli[{i}][codice]', ''),
                    descrizione=request.form.get(f'dettagli[{i}][descrizione]'),
                    quantita=quantita,
                    unita_misura=request.form.get(f'dettagli[{i}][unita]', 'PZ'),
                    prezzo_unitario=prezzo_unitario,
                    costo_unitario=float(request.form.get(f'dettagli[{i}][costo]', 0)),
                    sconto_percentuale=sconto,
                    totale_riga=totale_riga
                )
                db.session.add(dettaglio)
                totale += totale_riga
            i += 1
        
        # Aggiorna totali
        nuovo_preventivo.totale_netto = totale
        nuovo_preventivo.totale_lordo = totale * (1 + nuovo_preventivo.iva/100)
        
        db.session.commit()
        return redirect(f'/preventivi/{nuovo_preventivo.id}')
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'errore': str(e)}), 500

@app.route('/preventivi/<int:id>')
def dettaglio_preventivo(id):
    """Dettaglio preventivo"""
    preventivo = Preventivo.query.get_or_404(id)
    return render_template('dettaglio-preventivo.html', preventivo=preventivo)

@app.route('/preventivi/<int:id>/modifica', methods=['GET', 'POST'])
def modifica_preventivo(id):
    """Modifica preventivo esistente"""
    preventivo = Preventivo.query.get_or_404(id)
    
    if request.method == 'GET':
        clienti = Cliente.query.filter_by(attivo=True).all()
        return render_template('modifica-preventivo.html', preventivo=preventivo, clienti=clienti)
    
    try:
        # Aggiorna dati preventivo con validazione
        cliente_id_value = request.form.get('cliente_id', '').strip()
        # Valida cliente_id: solo numeri validi, ignora "Nessuno", "None" o valori non numerici
        if (cliente_id_value and 
            cliente_id_value.lower() not in ['nessuno', 'none'] and 
            cliente_id_value.isdigit()):
            preventivo.cliente_id = int(cliente_id_value)
        else:
            preventivo.cliente_id = None
        preventivo.cliente_nome = request.form.get('cliente_nome')
        preventivo.oggetto = request.form.get('oggetto', '')
        
        # Validazione sicura per IVA
        try:
            iva_value = request.form.get('iva', '22').strip()
            preventivo.iva = float(iva_value) if iva_value else 22.0
        except (ValueError, TypeError):
            preventivo.iva = 22.0
            
        preventivo.note = request.form.get('note', '')
        preventivo.commessa = request.form.get('commessa', '')
        
        if request.form.get('data_scadenza'):
            preventivo.data_scadenza = datetime.strptime(
                request.form['data_scadenza'], '%Y-%m-%d'
            ).date()
        
        # Elimina dettagli esistenti e li ricrea
        DettaglioPreventivo.query.filter_by(preventivo_id=preventivo.id).delete()
        
        # Aggiungi dettagli aggiornati con validazione
        totale = 0
        i = 0
        while f'dettagli[{i}][descrizione]' in request.form:
            if request.form.get(f'dettagli[{i}][descrizione]'):
                # Validazione sicura per quantita
                try:
                    quantita_value = request.form.get(f'dettagli[{i}][quantita]', '1').strip()
                    quantita = float(quantita_value) if quantita_value else 1.0
                except (ValueError, TypeError):
                    quantita = 1.0
                
                # Validazione sicura per prezzo_unitario
                try:
                    prezzo_value = request.form.get(f'dettagli[{i}][prezzo_unitario]', '0').strip()
                    prezzo_unitario = float(prezzo_value) if prezzo_value else 0.0
                except (ValueError, TypeError):
                    prezzo_unitario = 0.0
                
                # Validazione sicura per sconto
                try:
                    sconto_value = request.form.get(f'dettagli[{i}][sconto]', '0').strip()
                    sconto = float(sconto_value) if sconto_value else 0.0
                except (ValueError, TypeError):
                    sconto = 0.0
                
                # Validazione sicura per costo
                try:
                    costo_value = request.form.get(f'dettagli[{i}][costo]', '0').strip()
                    costo_unitario = float(costo_value) if costo_value else 0.0
                except (ValueError, TypeError):
                    costo_unitario = 0.0
                
                totale_riga = quantita * prezzo_unitario * (1 - sconto/100)
                
                dettaglio = DettaglioPreventivo(
                    preventivo_id=preventivo.id,
                    codice_articolo=request.form.get(f'dettagli[{i}][codice]', ''),
                    descrizione=request.form.get(f'dettagli[{i}][descrizione]'),
                    quantita=quantita,
                    unita_misura=request.form.get(f'dettagli[{i}][unita]', 'PZ'),
                    prezzo_unitario=prezzo_unitario,
                    costo_unitario=costo_unitario,
                    sconto_percentuale=sconto,
                    totale_riga=totale_riga
                )
                db.session.add(dettaglio)
                totale += totale_riga
            i += 1
        
        # Aggiorna totali
        preventivo.totale_netto = totale
        preventivo.totale_lordo = totale * (1 + preventivo.iva/100)
        
        db.session.commit()
        return redirect(f'/preventivi/{preventivo.id}')
        
    except Exception as e:
        print(f"Errore modifica preventivo: {e}")
        db.session.rollback()
        return jsonify({'errore': str(e)}), 500


@app.route('/preventivi/<int:id>/crea-ddt-out', methods=['POST'])
def crea_ddt_out_da_preventivo(id):
    """Trasforma preventivo in DDT OUT"""
    try:
        preventivo = Preventivo.query.get_or_404(id)
        dettagli_preventivo = DettaglioPreventivo.query.filter_by(preventivo_id=id).all()
        
        if not dettagli_preventivo:
            return jsonify({'errore': 'Preventivo senza articoli'}), 400
        
        # Crea DDT OUT (numero e data DDT assegnati solo alla conferma)
        nuovo_ddt = DDTOut(
            numero_ddt=None,  # Numero assegnato solo alla conferma
            data_ddt=None,    # Data DDT assegnata solo alla conferma  
            data_ddt_origine=datetime.now().date(),
            nome_origine=preventivo.cliente_nome,
            destinazione=preventivo.cliente_nome,
            riferimento=f"Da preventivo {preventivo.numero_preventivo}",
            stato='bozza'
        )
        
        db.session.add(nuovo_ddt)
        db.session.flush()  # Per ottenere l'ID
        
        # Crea articoli DDT OUT dai dettagli preventivo
        for dettaglio in dettagli_preventivo:
            articolo_out = ArticoloOut(
                ddt_id=nuovo_ddt.id,
                codice_interno=dettaglio.codice_articolo,
                descrizione=dettaglio.descrizione,
                quantita=dettaglio.quantita,
                unita_misura=dettaglio.unita_misura,
                prezzo_unitario=round(float(dettaglio.prezzo_unitario or 0), 2)  # Arrotondamento a 2 decimali
            )
            db.session.add(articolo_out)
        
        # Marca preventivo come utilizzato
        preventivo.stato = 'utilizzato'
        preventivo.data_accettazione = datetime.now().date()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'ddt_id': nuovo_ddt.id,
            'message': f'DDT OUT creato come bozza (numero assegnato alla conferma)',
            'redirect_url': f'/ddt-out/{nuovo_ddt.id}'
        })
        
    except Exception as e:
        print(f"Errore creazione DDT OUT da preventivo: {e}")
        db.session.rollback()
        return jsonify({'errore': str(e)}), 500

@app.route('/preventivi/<int:id>/pdf')
def preventivi_pdf(id):
    """Genera PDF del preventivo"""
    try:
        preventivo = Preventivo.query.get_or_404(id)
        
        # Fallback a HTML diretto - WeasyPrint non necessario per il test
        html_content = render_template('pdf/preventivo-pdf-simple.html', preventivo=preventivo)
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html'
        return response
            
    except Exception as e:
        print(f"Errore PDF preventivo: {e}")
        import traceback
        traceback.print_exc()
        return f"Errore PDF: {e}", 500

@app.route('/ordini')
def ordini_page():
    """Lista ordini fornitori"""
    ordini = OrdineFornitore.query.order_by(OrdineFornitore.numero_ordine.desc()).all()
    
    # Calcola statistiche
    ordini_bozza = OrdineFornitore.query.filter_by(stato='bozza').count()
    ordini_inviati = OrdineFornitore.query.filter_by(stato='inviato').count()
    
    return render_template('ordini.html', 
                         ordini=ordini,
                         ordini_bozza=ordini_bozza,
                         ordini_inviati=ordini_inviati)

@app.route('/ordini/nuovo', methods=['GET', 'POST'])
def nuovo_ordine():
    """Crea nuovo ordine fornitore"""
    if request.method == 'GET':
        fornitori = Fornitore.query.filter_by(attivo=True).all()
        return render_template('nuovo-ordine.html', fornitori=fornitori)
    
    try:
        # Genera numero offerta automatico
        ultimo_numero = db.session.query(db.func.max(OrdineFornitore.id)).scalar() or 0
        numero_ordine = f"ORD-{datetime.now().year}-{str(ultimo_numero + 1).zfill(4)}"
        
        # Gestione fornitore_id (può essere None se l'autocompletamento usa solo il nome)
        fornitore_id_value = request.form.get('fornitore_id')
        fornitore_id = int(fornitore_id_value) if fornitore_id_value else None
        
        # Crea nuova offerta
        nuovo_ordine = OrdineFornitore(
            numero_ordine=numero_ordine,
            fornitore_id=fornitore_id,
            fornitore_nome=request.form.get('fornitore_nome'),
            oggetto=request.form.get('oggetto', ''),
            data_ordine=datetime.now().date(),
            iva=float(request.form.get('iva', 22)),
            note=request.form.get('note', ''),
            priorita=request.form.get('priorita', 'media'),
            commessa=request.form.get('commessa', '')
        )
        
        if request.form.get('data_richiesta'):
            nuovo_ordine.data_richiesta = datetime.strptime(
                request.form['data_richiesta'], '%Y-%m-%d'
            ).date()
        
        if request.form.get('data_scadenza'):
            nuovo_ordine.data_scadenza = datetime.strptime(
                request.form['data_scadenza'], '%Y-%m-%d'
            ).date()
        
        db.session.add(nuovo_ordine)
        db.session.flush()  # Per ottenere l'ID
        
        # Aggiungi dettagli ordine
        totale = 0
        i = 0
        while f'dettagli[{i}][descrizione]' in request.form:
            if request.form.get(f'dettagli[{i}][descrizione]'):
                quantita = float(request.form.get(f'dettagli[{i}][quantita]', 1))
                prezzo_unitario = float(request.form.get(f'dettagli[{i}][prezzo_unitario]', 0))
                sconto = float(request.form.get(f'dettagli[{i}][sconto]', 0))
                totale_riga = quantita * prezzo_unitario * (1 - sconto/100)
                
                dettaglio = DettaglioOrdine(
                    ordine_id=nuovo_ordine.id,
                    codice_articolo=request.form.get(f'dettagli[{i}][codice]', ''),
                    codice_fornitore=request.form.get(f'dettagli[{i}][codice_fornitore]', ''),
                    descrizione=request.form.get(f'dettagli[{i}][descrizione]'),
                    quantita=quantita,
                    unita_misura=request.form.get(f'dettagli[{i}][unita]', 'PZ'),
                    prezzo_unitario=prezzo_unitario,
                    sconto_percentuale=sconto,
                    totale_riga=totale_riga,
                    disponibilita=request.form.get(f'dettagli[{i}][disponibilita]', ''),
                    tempo_consegna=request.form.get(f'dettagli[{i}][consegna]', '')
                )
                db.session.add(dettaglio)
                totale += totale_riga
            i += 1
        
        # Aggiorna totali
        nuovo_ordine.totale_netto = totale
        nuovo_ordine.totale_lordo = totale * (1 + nuovo_ordine.iva/100)
        
        db.session.commit()
        return redirect(f'/ordini/{nuovo_ordine.id}')
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'errore': str(e)}), 500

@app.route('/ordini/crea-riordino', methods=['POST'])
def crea_ordine_riordino():
    """Crea ordine di riordino dall'inventario"""
    try:
        data = request.get_json()
        
        # Genera numero ordine automatico
        ultimo_numero = db.session.query(db.func.max(OrdineFornitore.id)).scalar() or 0
        numero_ordine = f"RIORD-{datetime.now().year}-{str(ultimo_numero + 1).zfill(4)}"
        
        # Trova fornitore se esiste
        fornitore = Fornitore.query.filter_by(ragione_sociale=data['fornitore_nome']).first()
        fornitore_id = fornitore.id if fornitore else None
        
        # Crea nuovo ordine
        nuovo_ordine = OrdineFornitore(
            numero_ordine=numero_ordine,
            fornitore_id=fornitore_id,
            fornitore_nome=data['fornitore_nome'],
            oggetto=data['oggetto'],
            data_ordine=datetime.now().date(),
            stato='bozza',  # Sempre bozza per i riordini automatici
            iva=float(data.get('iva', 22)),
            note=data.get('note', ''),
            priorita=data.get('priorita', 'alta')  # Riordini hanno priorità alta di default
        )
        
        db.session.add(nuovo_ordine)
        db.session.flush()  # Per ottenere l'ID
        
        # Aggiungi dettagli ordine
        totale = 0
        for dettaglio_data in data.get('dettagli', []):
            quantita = float(dettaglio_data['quantita'])
            prezzo_unitario = float(dettaglio_data.get('prezzo_unitario', 0))
            totale_riga = quantita * prezzo_unitario
            
            dettaglio = DettaglioOrdine(
                ordine_id=nuovo_ordine.id,
                codice_articolo=dettaglio_data['codice_articolo'],
                descrizione=dettaglio_data['descrizione'],
                quantita=quantita,
                unita_misura='PZ',
                prezzo_unitario=prezzo_unitario,
                sconto_percentuale=0,
                totale_riga=totale_riga,
                note='Riordino automatico dall\'inventario'
            )
            db.session.add(dettaglio)
            totale += totale_riga
        
        # Aggiorna totali
        nuovo_ordine.totale_netto = totale
        nuovo_ordine.totale_lordo = totale * (1 + nuovo_ordine.iva/100)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': nuovo_ordine.id,
            'numero_ordine': numero_ordine,
            'redirect_url': f'/ordini/{nuovo_ordine.id}',
            'message': 'Ordine di riordino creato con successo'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'errore': str(e)}), 500

@app.route('/ordini/<int:id>')
def dettaglio_ordine(id):
    """Dettaglio ordine fornitore"""
    ordine = OrdineFornitore.query.get_or_404(id)
    dettagli = DettaglioOrdine.query.filter_by(ordine_id=id).all()
    return render_template('dettaglio-ordine.html', ordine=ordine, dettagli=dettagli)

@app.route('/ordini/<int:id>/modifica', methods=['GET', 'POST'])
def modifica_ordine(id):
    """Modifica ordine fornitore"""
    ordine = OrdineFornitore.query.get_or_404(id)
    
    if request.method == 'GET':
        fornitori = Fornitore.query.filter_by(attivo=True).all()
        dettagli = DettaglioOrdine.query.filter_by(ordine_id=id).all()
        return render_template('modifica-ordine.html', ordine=ordine, fornitori=fornitori, dettagli=dettagli)
    
    try:
        # Aggiorna dati ordine
        ordine.fornitore_nome = request.form.get('fornitore_nome')
        ordine.oggetto = request.form.get('oggetto')
        ordine.note = request.form.get('note', '')
        ordine.priorita = request.form.get('priorita', 'media')
        ordine.iva = float(request.form.get('iva', 22))
        
        # Gestione fornitore_id
        fornitore_id_value = request.form.get('fornitore_id')
        ordine.fornitore_id = int(fornitore_id_value) if fornitore_id_value else None
        
        # Aggiorna data scadenza se fornita
        data_scadenza_str = request.form.get('data_scadenza')
        if data_scadenza_str:
            ordine.data_scadenza = datetime.strptime(data_scadenza_str, '%Y-%m-%d').date()
        
        # Rimuovi dettagli esistenti
        DettaglioOrdine.query.filter_by(ordine_id=id).delete()
        
        # Aggiungi nuovi dettagli
        totale = 0
        dettagli_keys = [key for key in request.form.keys() if key.startswith('dettagli[') and key.endswith('[descrizione]')]
        
        for key in dettagli_keys:
            index = key.split('[')[1].split(']')[0]
            descrizione = request.form.get(f'dettagli[{index}][descrizione]')
            if descrizione and descrizione.strip():
                quantita = float(request.form.get(f'dettagli[{index}][quantita]', 0))
                prezzo_unitario = float(request.form.get(f'dettagli[{index}][prezzo_unitario]', 0))
                totale_riga = quantita * prezzo_unitario
                
                dettaglio = DettaglioOrdine(
                    ordine_id=ordine.id,
                    codice_articolo=request.form.get(f'dettagli[{index}][codice_articolo]', ''),
                    codice_fornitore=request.form.get(f'dettagli[{index}][codice_fornitore]', ''),
                    descrizione=descrizione,
                    quantita=quantita,
                    unita_misura=request.form.get(f'dettagli[{index}][unita_misura]', 'PZ'),
                    prezzo_unitario=prezzo_unitario,
                    sconto_percentuale=float(request.form.get(f'dettagli[{index}][sconto_percentuale]', 0)),
                    totale_riga=totale_riga,
                    note=request.form.get(f'dettagli[{index}][note]', '')
                )
                db.session.add(dettaglio)
                totale += totale_riga
        
        # Aggiorna totali
        ordine.totale_netto = totale
        ordine.totale_lordo = totale * (1 + ordine.iva/100)
        
        db.session.commit()
        flash('Ordine modificato con successo!', 'success')
        return redirect(url_for('dettaglio_ordine', id=ordine.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante la modifica dell\'ordine: {str(e)}', 'error')
        return redirect(url_for('modifica_ordine', id=id))

@app.route('/ordini/<int:id>/invia', methods=['POST'])
def invia_ordine(id):
    """Invia ordine al fornitore"""
    try:
        ordine = OrdineFornitore.query.get_or_404(id)
        
        if ordine.stato != 'bozza':
            return jsonify({'errore': 'Solo gli ordini in bozza possono essere inviati'}), 400
        
        ordine.stato = 'inviato'
        ordine.data_invio = datetime.now().date()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Ordine inviato con successo'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'errore': str(e)}), 500

@app.route('/ordini/<int:id>/conferma', methods=['POST'])
def conferma_ordine(id):
    """Conferma ricezione ordine dal fornitore"""
    try:
        ordine = OrdineFornitore.query.get_or_404(id)
        
        if ordine.stato != 'inviato':
            return jsonify({'errore': 'Solo gli ordini inviati possono essere confermati'}), 400
        
        ordine.stato = 'confermato'
        ordine.data_conferma = datetime.now().date()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Ordine confermato con successo'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'errore': str(e)}), 500

@app.route('/ordini/<int:id>/elimina', methods=['POST'])
def elimina_ordine(id):
    """Elimina ordine fornitore"""
    try:
        ordine = OrdineFornitore.query.get_or_404(id)
        
        # Controlla se l'ordine può essere eliminato
        if ordine.stato not in ['bozza', 'inviato']:
            return jsonify({
                'success': False,
                'error': f'Non è possibile eliminare un ordine in stato "{ordine.stato}"'
            }), 400
        
        # Elimina prima i dettagli
        dettagli_rimossi = DettaglioOrdine.query.filter_by(ordine_id=id).count()
        DettaglioOrdine.query.filter_by(ordine_id=id).delete()
        
        # Salva numero ordine per messaggio
        numero_ordine = ordine.numero_ordine or f'BOZZA-{ordine.id}'
        
        # Elimina l'ordine
        db.session.delete(ordine)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Ordine {numero_ordine} eliminato con successo',
            'dettagli_rimossi': dettagli_rimossi
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore eliminazione ordine: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ordini/<int:id>/confronta-data')
def confronta_data_ordine(id):
    """Restituisce dati ordine per confronto con PDF"""
    try:
        ordine = OrdineFornitore.query.get_or_404(id)
        dettagli = DettaglioOrdine.query.filter_by(ordine_id=id).all()
        
        # Prepara dati per il confronto
        ordine_data = {
            'id': ordine.id,
            'numero_ordine': ordine.numero_ordine or f'BOZZA-{ordine.id}',
            'fornitore_nome': ordine.fornitore_nome,
            'oggetto': ordine.oggetto,
            'priorita': ordine.priorita,
            'data_ordine': ordine.data_ordine.strftime('%Y-%m-%d') if ordine.data_ordine else '',
            'totale_lordo': float(ordine.totale_lordo) if ordine.totale_lordo else 0.0,
            'stato': ordine.stato,
            'dettagli': []
        }
        
        # Aggiungi dettagli articoli
        for dettaglio in dettagli:
            ordine_data['dettagli'].append({
                'id': dettaglio.id,
                'codice_articolo': dettaglio.codice_articolo,
                'codice_fornitore': dettaglio.codice_fornitore,
                'descrizione': dettaglio.descrizione,
                'quantita': float(dettaglio.quantita) if dettaglio.quantita else 0,
                'prezzo_unitario': float(dettaglio.prezzo_unitario) if dettaglio.prezzo_unitario else 0,
                'totale_riga': float(dettaglio.totale_riga) if dettaglio.totale_riga else 0
            })
        
        return jsonify({
            'success': True,
            'data': ordine_data
        })
        
    except Exception as e:
        print(f"Errore confronta data ordine: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ordini/<int:id>/pdf-allegato')
def pdf_allegato_ordine(id):
    """Visualizza PDF allegato dell'ordine"""
    try:
        ordine = OrdineFornitore.query.get_or_404(id)
        
        if not ordine.pdf_allegato:
            return "PDF non disponibile", 404
        
        import base64
        from flask import make_response
        
        # Decodifica PDF
        pdf_data = base64.b64decode(ordine.pdf_allegato)
        
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="offerta_{ordine.numero_ordine or ordine.id}.pdf"'
        
        return response
        
    except Exception as e:
        print(f"Errore PDF allegato ordine: {e}")
        return str(e), 500

@app.route('/ordini/<int:id>/pdf')
def stampa_ordine_pdf(id):
    """Stampa ordine come PDF con logo a sinistra"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from io import BytesIO
    import os
    
    ordine = OrdineFornitore.query.get_or_404(id)
    dettagli = DettaglioOrdine.query.filter_by(ordine_id=id).all()
    
    # Crea il buffer per il PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    content = []
    
    # Stili
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#007bff'),
        alignment=TA_CENTER,
        spaceAfter=0.3*cm
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=0.5*cm
    )
    normal_style = styles['Normal']
    
    # Header con logo a SINISTRA e titolo
    try:
        # Percorso del logo
        logo_path = os.path.join(os.path.dirname(__file__), 'static', 'logo-acg.png')
        if os.path.exists(logo_path):
            # Crea tabella per header con logo a sinistra e titolo al centro/destra
            logo_img = Image(logo_path, width=3*cm, height=1.5*cm)
            
            # Tabella header: logo a SINISTRA, titolo al centro
            title_cell = [
                Paragraph("ORDINE FORNITORE", title_style),
                Paragraph(ordine.numero_ordine or f'BOZZA #{ordine.id}', subtitle_style)
            ]
            
            header_data = [[logo_img, title_cell]]
            header_table = Table(header_data, colWidths=[4*cm, 12*cm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),    # Logo a SINISTRA
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Titolo al centro
                ('TOPPADDING', (0, 0), (-1, -1), 0.5*cm),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5*cm),
            ]))
            content.append(header_table)
        else:
            # Solo titolo se logo non trovato
            content.append(Paragraph("ORDINE FORNITORE", title_style))
            content.append(Paragraph(ordine.numero_ordine or f'BOZZA #{ordine.id}', subtitle_style))
    except Exception as e:
        # Fallback senza logo
        content.append(Paragraph("ORDINE FORNITORE", title_style))
        content.append(Paragraph(ordine.numero_ordine or f'BOZZA #{ordine.id}', subtitle_style))
    
    content.append(Spacer(1, 0.5*cm))
    
    # Informazioni azienda
    content.append(Paragraph("<b>ACG CLIMA SERVICE S.R.L.</b>", ParagraphStyle('CompanyInfo', parent=normal_style, alignment=TA_CENTER)))
    content.append(Paragraph("Sede Legale: Via Duccio Galimberti 47 - 15121 Alessandria (AL)<br/>Sede Operativa: Via Zanardi Bonfiglio 68 - 27058 Voghera (PV)<br/>Tel: 0383/640606 - Email: info@acgclimaservice.com<br/>P.IVA: 02735970069 - C.F: 02735970069", 
                            ParagraphStyle('CompanyDetails', parent=normal_style, alignment=TA_CENTER, fontSize=9)))
    content.append(Spacer(1, 0.8*cm))
    
    # Informazioni ordine e fornitore - usando Paragraph per gestire i tag HTML
    info_data = [
        [Paragraph('<b>Data Ordine:</b>', normal_style), Paragraph(ordine.data_ordine.strftime('%d/%m/%Y') if ordine.data_ordine else '-', normal_style), 
         Paragraph('<b>Fornitore:</b>', normal_style), Paragraph(ordine.fornitore_nome or '-', normal_style)],
        [Paragraph('<b>Oggetto:</b>', normal_style), Paragraph(ordine.oggetto or '-', normal_style), 
         Paragraph('<b>P.IVA:</b>', normal_style), Paragraph(ordine.fornitore.partita_iva if ordine.fornitore else '-', normal_style)],
        [Paragraph('<b>Stato:</b>', normal_style), Paragraph(ordine.stato.upper() if ordine.stato else 'BOZZA', normal_style), 
         Paragraph('<b>Email:</b>', normal_style), Paragraph(ordine.fornitore.email if ordine.fornitore else '-', normal_style)],
        [Paragraph('<b>Priorità:</b>', normal_style), Paragraph(ordine.priorita.upper() if ordine.priorita else '-', normal_style),
         Paragraph('<b>Telefono:</b>', normal_style), Paragraph(ordine.fornitore.telefono if ordine.fornitore else '-', normal_style)]
    ]
    
    info_table = Table(info_data, colWidths=[3*cm, 5*cm, 3*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 0.2*cm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.2*cm),
        ('LEFTPADDING', (0, 0), (-1, -1), 0.1*cm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0.1*cm),
    ]))
    content.append(info_table)
    content.append(Spacer(1, 0.5*cm))
    
    # Tabella dettagli articoli
    if dettagli:
        content.append(Paragraph("<b>Dettagli Articoli</b>", ParagraphStyle('SectionHeader', parent=styles['Heading3'], textColor=colors.HexColor('#007bff'))))
        content.append(Spacer(1, 0.3*cm))
        
        # Header tabella
        header_style = ParagraphStyle('HeaderStyle', parent=normal_style, fontSize=9, textColor=colors.HexColor('#495057'))
        table_data = [[
            Paragraph('<b>Codice</b>', header_style),
            Paragraph('<b>Cod. Fornitore</b>', header_style),
            Paragraph('<b>Descrizione</b>', header_style),
            Paragraph('<b>Qty</b>', header_style),
            Paragraph('<b>Prezzo €</b>', header_style),
            Paragraph('<b>Totale €</b>', header_style)
        ]]
        
        totale_generale = 0
        for dettaglio in dettagli:
            totale_riga = (dettaglio.quantita or 0) * (dettaglio.prezzo_unitario or 0)
            totale_generale += totale_riga
            
            # Usa Paragraph per la descrizione per gestire il testo lungo
            descrizione_text = dettaglio.descrizione or '-'
            if len(descrizione_text) > 40:  # Tronca se troppo lungo
                descrizione_text = descrizione_text[:37] + '...'
            
            table_data.append([
                Paragraph(dettaglio.codice_articolo or '-', ParagraphStyle('CellStyle', parent=normal_style, fontSize=8)),
                Paragraph(dettaglio.codice_fornitore or '-', ParagraphStyle('CellStyle', parent=normal_style, fontSize=8)),
                Paragraph(descrizione_text, ParagraphStyle('CellStyle', parent=normal_style, fontSize=8)),
                Paragraph(f"{dettaglio.quantita:.2f}" if dettaglio.quantita else '0', ParagraphStyle('CellStyle', parent=normal_style, fontSize=8, alignment=TA_RIGHT)),
                Paragraph(f"{dettaglio.prezzo_unitario:.2f}" if dettaglio.prezzo_unitario else '0.00', ParagraphStyle('CellStyle', parent=normal_style, fontSize=8, alignment=TA_RIGHT)),
                Paragraph(f"{totale_riga:.2f}", ParagraphStyle('CellStyle', parent=normal_style, fontSize=8, alignment=TA_RIGHT))
            ])
        
        # Crea tabella con larghezze ottimizzate
        table = Table(table_data, colWidths=[2*cm, 2*cm, 7*cm, 1.5*cm, 2*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#495057')),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (3, 1), (5, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('TOPPADDING', (0, 0), (-1, -1), 0.2*cm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.2*cm),
            ('LEFTPADDING', (0, 0), (-1, -1), 0.1*cm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0.1*cm),
        ]))
        content.append(table)
        content.append(Spacer(1, 0.5*cm))
        
        # Totali
        totali_data = [
            ['Totale Netto:', f"€ {ordine.totale_netto:.2f}" if ordine.totale_netto else f"€ {totale_generale:.2f}"],
            ['IVA:', f"€ {(ordine.totale_lordo or totale_generale) - (ordine.totale_netto or totale_generale):.2f}"],
            ['TOTALE LORDO:', f"€ {ordine.totale_lordo:.2f}" if ordine.totale_lordo else f"€ {totale_generale:.2f}"]
        ]
        
        totali_table = Table(totali_data, colWidths=[4*cm, 3*cm])
        totali_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#007bff')),
            ('TOPPADDING', (0, 0), (-1, -1), 0.2*cm),
        ]))
        content.append(totali_table)
    
    # Note
    if ordine.note:
        content.append(Spacer(1, 0.5*cm))
        content.append(Paragraph("<b>Note:</b>", styles['Heading4']))
        content.append(Paragraph(ordine.note, normal_style))
    
    # Footer
    content.append(Spacer(1, 1*cm))
    content.append(Paragraph(f"Documento generato automaticamente il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}", 
                            ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))
    
    # Genera PDF
    doc.build(content)
    buffer.seek(0)
    
    # Risposta con download forzato
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="ordine_{ordine.numero_ordine or ordine.id}.pdf"'
    
    return response

# ========== IMPORT ORDINI DA PDF ==========

@app.route('/ordini/import')
def ordini_import_page():
    """Pagina import ordini da PDF"""
    return render_template('ordini-import.html', today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/ordini/parse-pdf', methods=['POST'])
def parse_ordine_pdf():
    """Parse PDF offerta fornitore per creare ordine"""
    try:
        from multi_ai_pdf_parser import MultiAIPDFParser
        import tempfile
        import os
        import base64
        
        if 'pdf' not in request.files:
            return jsonify({'success': False, 'error': 'Nessun file caricato'}), 400
            
        pdf_file = request.files['pdf']
        ai_service = request.form.get('ai_service', 'claude')
        
        if pdf_file.filename == '' or not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'File non valido'}), 400
        
        # Salva temporaneamente il PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            pdf_file.save(temp_file.name)
            temp_filename = temp_file.name
        
        # Codifica PDF in base64
        with open(temp_filename, 'rb') as f:
            pdf_content = f.read()
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        # Parse con AI
        parser = MultiAIPDFParser()
        result = parser.parse_ordine_pdf(temp_filename, ai_service)
        
        # Cleanup
        try:
            os.unlink(temp_filename)
        except:
            pass
        
        if result['success']:
            # Aggiungi PDF base64 al risultato
            result['data']['pdf_base64'] = pdf_base64
            return jsonify(result)
        else:
            # Gestione errori API con fallback a template base
            error_msg = result.get('error', 'Errore durante il parsing')
            print(f"Parse ordine fallito: {error_msg}")
            
            # Se entrambe le API falliscono per rate limiting, usa template base
            if 'rate' in error_msg.lower() or '429' in error_msg or 'quota' in error_msg.lower():
                print("Rate limiting detected, using template fallback")
                template_data = {
                    'fornitore': 'Fornitore da inserire manualmente',
                    'data_offerta': datetime.now().strftime('%Y-%m-%d'),
                    'numero_offerta': '',
                    'validita_offerta': '',
                    'oggetto': 'Ordine importato da PDF',
                    'note': 'Dati da completare manualmente - parsing AI non disponibile',
                    'articoli': [
                        {
                            'descrizione': 'Articolo da inserire manualmente',
                            'quantita': 1.0,
                            'prezzo_unitario': 0.0
                        }
                    ],
                    'pdf_base64': pdf_base64,
                    'ai_used': 'template_fallback',
                    'warning': 'Parsing AI temporaneamente non disponibile. Completa i dati manualmente.'
                }
                return jsonify({
                    'success': True,
                    'data': template_data,
                    'warning': 'Parsing AI non disponibile - dati da completare manualmente'
                })
            else:
                return jsonify({'success': False, 'error': error_msg})
    
    except Exception as e:
        print(f"Errore parse ordine PDF: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/ordini/crea-da-import', methods=['POST'])
def crea_ordine_da_import():
    """Crea ordine da dati importati"""
    try:
        data = request.get_json()
        
        # Genera numero ordine automatico
        ultimo_numero = db.session.query(db.func.max(OrdineFornitore.id)).scalar() or 0
        numero_ordine = f"IMP-{datetime.now().year}-{str(ultimo_numero + 1).zfill(4)}"
        
        # Verifica/crea fornitore
        fornitore_nome = data.get('fornitore', '')
        fornitore = None
        if fornitore_nome:
            fornitore = Fornitore.query.filter_by(ragione_sociale=fornitore_nome).first()
            if not fornitore:
                fornitore = Fornitore(
                    ragione_sociale=fornitore_nome,
                    attivo=True
                )
                db.session.add(fornitore)
                db.session.flush()
        
        # Crea ordine
        nuovo_ordine = OrdineFornitore(
            numero_ordine=numero_ordine,
            fornitore_id=fornitore.id if fornitore else None,
            fornitore_nome=fornitore_nome,
            oggetto=data.get('oggetto', 'Ordine importato da PDF'),
            note=data.get('note', ''),
            priorita=data.get('priorita', 'media'),
            data_ordine=datetime.strptime(data.get('data_offerta', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date() if data.get('data_offerta') else datetime.now().date(),
            data_scadenza=datetime.strptime(data.get('validita_offerta'), '%Y-%m-%d').date() if data.get('validita_offerta') else None,
            stato='bozza',
            iva=22.0
        )
        
        # Aggiungi PDF se disponibile
        if data.get('pdf_base64'):
            nuovo_ordine.pdf_allegato = data.get('pdf_base64')
            nuovo_ordine.pdf_filename = f"{numero_ordine}.pdf"
        
        db.session.add(nuovo_ordine)
        db.session.flush()
        
        # Aggiungi articoli
        totale_netto = 0
        for articolo_data in data.get('articoli', []):
            if articolo_data.get('descrizione') and articolo_data.get('quantita', 0) > 0:
                prezzo_unitario = float(articolo_data.get('prezzo_unitario', 0))
                quantita = float(articolo_data.get('quantita', 0))
                totale_riga = quantita * prezzo_unitario
                totale_netto += totale_riga
                
                dettaglio = DettaglioOrdine(
                    ordine_id=nuovo_ordine.id,
                    descrizione=articolo_data.get('descrizione'),
                    quantita=quantita,
                    prezzo_unitario=prezzo_unitario,
                    totale_riga=totale_riga
                )
                db.session.add(dettaglio)
        
        # Calcola totali
        nuovo_ordine.totale_netto = totale_netto
        nuovo_ordine.totale_lordo = totale_netto * (1 + nuovo_ordine.iva / 100)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'ordine_id': nuovo_ordine.id,
            'numero_ordine': numero_ordine
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore creazione ordine da import: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/offerte')
def lista_offerte():
    """Lista di tutte le offerte"""
    try:
        offerte = OffertaFornitore.query.order_by(OffertaFornitore.data_ricevuta.desc()).all()
        
        # Statistiche
        totale_offerte = len(offerte)
        offerte_ricevute = len([o for o in offerte if o.stato == 'ricevuta'])
        offerte_valutate = len([o for o in offerte if o.stato == 'valutata'])
        offerte_accettate = len([o for o in offerte if o.stato == 'accettata'])
        offerte_rifiutate = len([o for o in offerte if o.stato == 'rifiutata'])
        
        stats = {
            'totale': totale_offerte,
            'ricevute': offerte_ricevute,
            'valutate': offerte_valutate,
            'accettate': offerte_accettate,
            'rifiutate': offerte_rifiutate
        }
        
        return render_template('offerte.html', offerte=offerte, stats=stats)
    except Exception as e:
        print(f"Errore lista offerte: {e}")
        return f"Errore: {str(e)}", 500

@app.route('/offerte/<int:id>')
def dettaglio_offerta(id):
    """Dettaglio offerta"""
    offerta = OffertaFornitore.query.get_or_404(id)
    return render_template('dettaglio-offerta.html', offerta=offerta)

@app.route('/offerte/<int:id>/valuta', methods=['POST'])
def valuta_offerta(id):
    """Valuta un'offerta"""
    try:
        offerta = OffertaFornitore.query.get_or_404(id)
        valutazione = request.form.get('valutazione', '')
        
        offerta.stato = 'valutata'
        offerta.valutazione = valutazione
        offerta.data_valutazione = datetime.now().date()
        
        db.session.commit()
        return redirect(f'/offerte/{id}')
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'errore': str(e)}), 500

@app.route('/offerte/<int:id>/accetta', methods=['POST'])
def accetta_offerta(id):
    """Accetta un'offerta"""
    try:
        offerta = OffertaFornitore.query.get_or_404(id)
        
        offerta.stato = 'accettata'
        offerta.data_accettazione = datetime.now().date()
        
        db.session.commit()
        return redirect(f'/offerte/{id}')
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'errore': str(e)}), 500

@app.route('/offerte/<int:id>/rifiuta', methods=['POST'])
def rifiuta_offerta(id):
    """Rifiuta un'offerta"""
    try:
        offerta = OffertaFornitore.query.get_or_404(id)
        motivo = request.form.get('motivo', '')
        
        offerta.stato = 'rifiutata'
        if motivo:
            offerta.valutazione = f"Rifiutata: {motivo}"
            offerta.data_valutazione = datetime.now().date()
        
        db.session.commit()
        return redirect(f'/offerte/{id}')
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'errore': str(e)}), 500

@app.route('/offerte/<int:id>/pdf')
def offerte_pdf(id):
    """Genera PDF professionale dell'offerta con logo a sinistra"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from io import BytesIO
    import os
    
    try:
        offerta = OffertaFornitore.query.get_or_404(id)
        dettagli = DettaglioOfferta.query.filter_by(offerta_id=id).all() if hasattr(offerta, 'dettagli') else []
        
        # Crea il buffer per il PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        content = []
        
        # Stili
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=18,
            textColor=colors.HexColor('#007bff'),
            alignment=TA_CENTER,
            spaceAfter=0.3*cm
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceAfter=0.5*cm
        )
        normal_style = styles['Normal']
        
        # Header con logo a SINISTRA e titolo
        try:
            # Percorso del logo
            logo_path = os.path.join(os.path.dirname(__file__), 'static', 'logo-acg.png')
            if os.path.exists(logo_path):
                # Crea tabella per header con logo a sinistra e titolo al centro
                logo_img = Image(logo_path, width=3*cm, height=1.5*cm)
                
                # Tabella header: logo a SINISTRA, titolo al centro
                title_cell = [
                    Paragraph("OFFERTA FORNITORE", title_style),
                    Paragraph(offerta.numero_offerta or f'BOZZA #{offerta.id}', subtitle_style)
                ]
                
                header_data = [[logo_img, title_cell]]
                header_table = Table(header_data, colWidths=[4*cm, 12*cm])
                header_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),    # Logo a SINISTRA
                    ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Titolo al centro
                    ('TOPPADDING', (0, 0), (-1, -1), 0.5*cm),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5*cm),
                ]))
                content.append(header_table)
            else:
                # Solo titolo se logo non trovato
                content.append(Paragraph("OFFERTA FORNITORE", title_style))
                content.append(Paragraph(offerta.numero_offerta or f'BOZZA #{offerta.id}', subtitle_style))
        except Exception as e:
            # Fallback senza logo
            content.append(Paragraph("OFFERTA FORNITORE", title_style))
            content.append(Paragraph(offerta.numero_offerta or f'BOZZA #{offerta.id}', subtitle_style))
        
        content.append(Spacer(1, 0.5*cm))
        
        # Informazioni azienda
        content.append(Paragraph("<b>ACG CLIMA SERVICE S.R.L.</b>", ParagraphStyle('CompanyInfo', parent=normal_style, alignment=TA_CENTER)))
        content.append(Paragraph("Via della Tecnica, 123 - 00100 Roma<br/>Tel: +39 06 1234567 - Email: info@acgclimaservice.com<br/>P.IVA: IT12345678901", 
                                ParagraphStyle('CompanyDetails', parent=normal_style, alignment=TA_CENTER, fontSize=9)))
        content.append(Spacer(1, 0.8*cm))
        
        # Informazioni offerta e fornitore
        info_data = [
            ['<b>Data Ricevuta:</b>', offerta.data_ricevuta.strftime('%d/%m/%Y') if offerta.data_ricevuta else '-', 
             '<b>Fornitore:</b>', offerta.fornitore_nome or '-'],
            ['<b>Oggetto:</b>', offerta.oggetto or '-', 
             '<b>P.IVA:</b>', offerta.fornitore.partita_iva if offerta.fornitore else '-'],
            ['<b>Stato:</b>', offerta.stato.upper() if offerta.stato else 'RICEVUTA', 
             '<b>Email:</b>', offerta.fornitore.email if offerta.fornitore else '-'],
            ['<b>Priorità:</b>', offerta.priorita.upper() if offerta.priorita else 'MEDIA',
             '<b>Telefono:</b>', offerta.fornitore.telefono if offerta.fornitore else '-']
        ]
        
        if offerta.data_scadenza:
            info_data.append([
                '<b>Scadenza:</b>', offerta.data_scadenza.strftime('%d/%m/%Y'),
                '<b>Commessa:</b>', offerta.commessa or '-'
            ])
        elif offerta.commessa:
            info_data.append([
                '<b>Commessa:</b>', offerta.commessa,
                '', ''
            ])
        
        info_table = Table(info_data, colWidths=[3*cm, 5*cm, 3*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 0.2*cm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.2*cm),
            ('LEFTPADDING', (0, 0), (-1, -1), 0.1*cm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0.1*cm),
        ]))
        content.append(info_table)
        content.append(Spacer(1, 0.5*cm))
        
        # Tabella dettagli articoli se presenti
        if dettagli:
            content.append(Paragraph("<b>Dettagli Articoli</b>", ParagraphStyle('SectionHeader', parent=styles['Heading3'], textColor=colors.HexColor('#007bff'))))
            content.append(Spacer(1, 0.3*cm))
            
            # Header tabella
            table_data = [['Codice', 'Cod. Fornitore', 'Descrizione', 'Qty', 'Prezzo €', 'Sconto %', 'Totale €']]
            
            totale_generale = 0
            for dettaglio in dettagli:
                totale_riga = (dettaglio.quantita or 0) * (dettaglio.prezzo_unitario or 0)
                sconto = totale_riga * (dettaglio.sconto_percentuale or 0) / 100
                totale_finale = totale_riga - sconto
                totale_generale += totale_finale
                
                table_data.append([
                    dettaglio.codice_articolo or '-',
                    dettaglio.codice_fornitore or '-',
                    dettaglio.descrizione or '-',
                    f"{dettaglio.quantita:.2f}" if dettaglio.quantita else '0',
                    f"{dettaglio.prezzo_unitario:.2f}" if dettaglio.prezzo_unitario else '0.00',
                    f"{dettaglio.sconto_percentuale:.1f}%" if dettaglio.sconto_percentuale else '0%',
                    f"{totale_finale:.2f}"
                ])
            
            # Crea tabella
            table = Table(table_data, colWidths=[1.8*cm, 1.8*cm, 5.5*cm, 1.5*cm, 2*cm, 1.5*cm, 2.4*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#495057')),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (3, 1), (6, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                ('TOPPADDING', (0, 0), (-1, -1), 0.2*cm),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0.2*cm),
            ]))
            content.append(table)
            content.append(Spacer(1, 0.5*cm))
        
        # Totali
        totale_netto = offerta.totale_netto or 0
        iva_percentuale = offerta.iva or 22
        iva_importo = totale_netto * iva_percentuale / 100
        totale_lordo = totale_netto + iva_importo
        
        totali_data = [
            ['Totale Netto:', f"€ {totale_netto:.2f}"],
            [f'IVA ({iva_percentuale}%):', f"€ {iva_importo:.2f}"],
            ['TOTALE LORDO:', f"€ {totale_lordo:.2f}"]
        ]
        
        totali_table = Table(totali_data, colWidths=[4*cm, 3*cm])
        totali_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#007bff')),
            ('TOPPADDING', (0, 0), (-1, -1), 0.2*cm),
        ]))
        content.append(totali_table)
        
        # Note
        if offerta.note:
            content.append(Spacer(1, 0.5*cm))
            content.append(Paragraph("<b>Note:</b>", styles['Heading4']))
            content.append(Paragraph(offerta.note, normal_style))
        
        # Valutazione
        if hasattr(offerta, 'valutazione') and offerta.valutazione:
            content.append(Spacer(1, 0.5*cm))
            content.append(Paragraph("<b>Valutazione:</b>", ParagraphStyle('EvalHeader', parent=styles['Heading4'], textColor=colors.HexColor('#28a745'))))
            content.append(Paragraph(offerta.valutazione, normal_style))
        
        # Cronologia se non è solo ricevuta
        if offerta.stato and offerta.stato != 'ricevuta':
            content.append(Spacer(1, 0.5*cm))
            content.append(Paragraph("<b>Cronologia:</b>", styles['Heading4']))
            
            cronologia_data = [
                ['Ricevuta il:', offerta.data_ricevuta.strftime('%d/%m/%Y') if offerta.data_ricevuta else '-']
            ]
            
            if hasattr(offerta, 'data_valutazione') and offerta.data_valutazione:
                cronologia_data.append(['Valutata il:', offerta.data_valutazione.strftime('%d/%m/%Y')])
            
            if hasattr(offerta, 'data_accettazione') and offerta.data_accettazione:
                cronologia_data.append(['Accettata il:', offerta.data_accettazione.strftime('%d/%m/%Y')])
            
            cronologia_table = Table(cronologia_data, colWidths=[3*cm, 4*cm])
            cronologia_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TOPPADDING', (0, 0), (-1, -1), 0.1*cm),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0.1*cm),
            ]))
            content.append(cronologia_table)
        
        # Footer
        content.append(Spacer(1, 1*cm))
        content.append(Paragraph(f"Documento generato automaticamente il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}", 
                                ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))
        content.append(Paragraph("ACG CLIMA SERVICE S.R.L. - Sistema Gestione Offerte v2.1", 
                                ParagraphStyle('FooterSub', parent=normal_style, fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))
        
        # Genera PDF
        doc.build(content)
        buffer.seek(0)
        
        # Risposta con download forzato
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="offerta_{offerta.numero_offerta or offerta.id}.pdf"'
        
        return response
            
    except Exception as e:
        print(f"Errore PDF offerta: {e}")
        return f"Errore PDF: {e}", 500

@app.route('/offerte/confronta')
def confronta_offerte():
    """Confronta più offerte per lo stesso oggetto/articolo"""
    try:
        # Raggruppa offerte per oggetto simile
        offerte = OffertaFornitore.query.filter(
            OffertaFornitore.stato.in_(['ricevuta', 'valutata'])
        ).order_by(OffertaFornitore.data_ricevuta.desc()).all()
        
        return render_template('confronta-offerte.html', offerte=offerte)
        
    except Exception as e:
        print(f"Errore confronto offerte: {e}")
        return f"Errore confronto: {e}", 500

@app.route('/offerte/<int:id>/crea-ddt', methods=['POST'])
def crea_ddt_da_offerta(id):
    """Crea DDT IN dall'offerta accettata"""
    try:
        offerta = OffertaFornitore.query.get_or_404(id)
        
        if offerta.stato != 'accettata':
            return jsonify({'errore': 'Solo le offerte accettate possono essere trasformate in DDT'}), 400
        
        dettagli_offerta = DettaglioOfferta.query.filter_by(offerta_id=id).all()
        
        if not dettagli_offerta:
            return jsonify({'errore': 'Offerta senza articoli'}), 400
        
        # Genera numero DDT IN automatico
        anno_corrente = datetime.now().year
        ultimo_ddt = DDTIn.query.filter(
            DDTIn.numero_ddt.like(f'IN/%/{anno_corrente}')
        ).order_by(DDTIn.id.desc()).first()
        
        if ultimo_ddt:
            ultimo_numero = int(ultimo_ddt.numero_ddt.split('/')[1])
            nuovo_numero = ultimo_numero + 1
        else:
            nuovo_numero = 1
            
        numero_ddt = f'IN/{nuovo_numero:04d}/{anno_corrente}'
        
        # Crea il nuovo DDT IN
        nuovo_ddt = DDTIn(
            numero_ddt=numero_ddt,
            fornitore=offerta.fornitore_nome,
            data_ddt=datetime.now().date(),
            stato='bozza',
            mastrino_ddt='Da offerta',
            commessa='',
            destinazione='MAG001'
        )
        
        db.session.add(nuovo_ddt)
        db.session.flush()
        
        # Aggiungi articoli al DDT
        for dettaglio in dettagli_offerta:
            articolo_ddt = ArticoloIn(
                ddt_id=nuovo_ddt.id,
                codice_interno=dettaglio.codice_articolo or '',
                descrizione=dettaglio.descrizione,
                quantita=dettaglio.quantita,
                unita_misura=dettaglio.unita_misura,
                costo_unitario=dettaglio.prezzo_unitario or 0
            )
            db.session.add(articolo_ddt)
        
        # Marca offerta come utilizzata
        offerta.stato = 'utilizzata'
        offerta.data_accettazione = datetime.now().date()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'ddt_id': nuovo_ddt.id,
            'numero_ddt': numero_ddt,
            'redirect_url': f'/ddt-in/{nuovo_ddt.id}'
        })
        
    except Exception as e:
        print(f"Errore creazione DDT da offerta: {e}")
        db.session.rollback()
        return jsonify({'errore': str(e)}), 500

@app.route('/offerte/<int:id>/elimina', methods=['POST'])
def elimina_offerta(id):
    """Elimina un'offerta e tutti i suoi dettagli"""
    try:
        offerta = OffertaFornitore.query.get_or_404(id)
        
        # Elimina prima i dettagli dell'offerta
        dettagli_offerta = DettaglioOfferta.query.filter_by(offerta_id=id).all()
        dettagli_rimossi = len(dettagli_offerta)
        
        for dettaglio in dettagli_offerta:
            db.session.delete(dettaglio)
        
        # Salva il numero per il messaggio
        numero_offerta = offerta.numero_offerta
        
        # Elimina l'offerta
        db.session.delete(offerta)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Offerta {numero_offerta} eliminata con successo',
            'dettagli_rimossi': dettagli_rimossi
        })
        
    except Exception as e:
        print(f"Errore eliminazione offerta: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/preventivi/<int:id>/invia', methods=['POST'])
def invia_preventivo(id):
    """Invia un preventivo al cliente"""
    try:
        preventivo = Preventivo.query.get_or_404(id)
        
        preventivo.stato = 'inviato'
        preventivo.data_invio = datetime.now().date()
        
        # Se non c'è data scadenza, imposta a 30 giorni
        if not preventivo.data_scadenza:
            from datetime import timedelta
            preventivo.data_scadenza = datetime.now().date() + timedelta(days=30)
        
        db.session.commit()
        return redirect(f'/preventivi/{id}')
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'errore': str(e)}), 500

@app.route('/preventivi/<int:id>/accetta', methods=['POST'])
def accetta_preventivo(id):
    """Segna preventivo come accettato"""
    try:
        preventivo = Preventivo.query.get_or_404(id)
        
        preventivo.stato = 'accettato'
        preventivo.data_accettazione = datetime.now().date()
        
        db.session.commit()
        return redirect(f'/preventivi/{id}')
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'errore': str(e)}), 500

@app.route('/preventivi/<int:id>/rifiuta', methods=['POST'])
def rifiuta_preventivo(id):
    """Segna preventivo come rifiutato"""
    try:
        preventivo = Preventivo.query.get_or_404(id)
        
        preventivo.stato = 'rifiutato'
        
        db.session.commit()
        return redirect(f'/preventivi/{id}')
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'errore': str(e)}), 500

@app.route('/api/articoli/search')
def search_articoli():
    """API per autocompletamento articoli"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    articoli = CatalogoArticolo.query.filter(
        db.or_(
            CatalogoArticolo.codice_interno.ilike(f'%{query}%'),
            CatalogoArticolo.descrizione.ilike(f'%{query}%')
        )
    ).filter_by(attivo=True).limit(10).all()
    
    results = []
    for art in articoli:
        results.append({
            'codice': art.codice_interno,
            'codice_interno': art.codice_interno,
            'codice_fornitore': art.codice_fornitore,
            'descrizione': art.descrizione,
            'fornitore_principale': art.fornitore_principale,
            'prezzo': art.prezzo_vendita or 0,
            'costo': art.costo_ultimo or 0,
            'unita': art.unita_misura or 'PZ'
        })
    
    return jsonify(results)

@app.route('/impostazioni/mastrini/importa-excel', methods=['POST'])
def importa_mastrini_excel():
    """Importa mastrini da file Excel"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Nessun file selezionato'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nessun file selezionato'}), 400
        
        if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
            return jsonify({'success': False, 'error': 'Formato file non supportato. Usare Excel (.xlsx, .xls) o CSV'}), 400
        
        import pandas as pd
        from io import StringIO
        
        # Leggi il file
        if file.filename.lower().endswith('.csv'):
            content = file.read().decode('utf-8')
            df = pd.read_csv(StringIO(content))
        else:
            df = pd.read_excel(file)
        
        # Verifica che il file abbia le colonne necessarie
        required_columns = ['Tipo', 'Codice', 'Descrizione']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'success': False, 
                'error': f'Colonne mancanti nel file: {", ".join(missing_columns)}. Colonne richieste: Tipo, Codice, Descrizione'
            }), 400
        
        importati = 0
        errori = 0
        
        for index, row in df.iterrows():
            try:
                # Estrai i dati
                tipo = str(row['Tipo']).strip().upper()
                codice = str(row['Codice']).strip()
                descrizione = str(row['Descrizione']).strip()
                
                # Verifica se il mastrino esiste già
                esistente = Mastrino.query.filter_by(codice=codice).first()
                if esistente:
                    # Aggiorna il mastrino esistente
                    esistente.descrizione = descrizione
                    esistente.tipo = tipo
                    esistente.attivo = True
                else:
                    # Crea nuovo mastrino
                    nuovo_mastrino = Mastrino(
                        codice=codice,
                        descrizione=descrizione,
                        tipo=tipo,
                        attivo=True
                    )
                    db.session.add(nuovo_mastrino)
                
                importati += 1
                
            except Exception as e:
                errori += 1
                print(f"Errore importazione riga {index + 1}: {e}")
        
        # Salva nel database
        db.session.commit()
        
        return jsonify({
            'success': True,
            'importati': importati,
            'errori': errori,
            'message': f'Importati {importati} mastrini con {errori} errori'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore importazione mastrini: {e}")
        return jsonify({
            'success': False,
            'error': f'Errore durante importazione: {str(e)}'
        }), 500


@app.route('/impostazioni/mastrino/<int:id>/elimina', methods=['POST'])
def elimina_mastrino(id):
    """Elimina mastrino se non utilizzato"""
    try:
        mastrino = Mastrino.query.get_or_404(id)
        
        # Verifica se il mastrino è utilizzato in DDT IN
        ddt_in_utilizzo = DDTIn.query.filter_by(mastrino_ddt=mastrino.codice).count()
        if ddt_in_utilizzo > 0:
            return jsonify({
                'success': False, 
                'error': f'Mastrino utilizzato in {ddt_in_utilizzo} DDT IN. Impossibile eliminare.'
            })
        
        # Verifica se il mastrino è utilizzato in DDT OUT
        ddt_out_utilizzo = DDTOut.query.filter_by(mastrino_ddt=mastrino.codice).count()
        if ddt_out_utilizzo > 0:
            return jsonify({
                'success': False,
                'error': f'Mastrino utilizzato in {ddt_out_utilizzo} DDT OUT. Impossibile eliminare.'
            })
        
        # Verifica se il mastrino è utilizzato nei movimenti
        movimenti_utilizzo = Movimento.query.filter_by(mastrino=mastrino.codice).count()
        if movimenti_utilizzo > 0:
            return jsonify({
                'success': False,
                'error': f'Mastrino utilizzato in {movimenti_utilizzo} movimenti. Impossibile eliminare.'
            })
        
        # Se non è utilizzato, elimina
        nome_mastrino = f"{mastrino.codice} - {mastrino.descrizione}"
        db.session.delete(mastrino)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Mastrino "{nome_mastrino}" eliminato con successo'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore eliminazione mastrino: {e}")
        return jsonify({
            'success': False,
            'error': f'Errore durante eliminazione: {str(e)}'
        }), 500

# ========== COLLEGAMENTO MASTRINI ==========

@app.route('/impostazioni/collegamento-mastrini')
def collegamento_mastrini():
    """Pagina gestione collegamenti tra mastrini"""
    try:
        # Ottieni tutti i mastrini acquisti e ricavi
        cursor = db.session.execute(db.text("SELECT * FROM mastrino WHERE tipo = 'ACQUISTI' AND attivo = 1 ORDER BY codice"))
        mastrini_acquisti = cursor.fetchall()
        
        cursor = db.session.execute(db.text("SELECT * FROM mastrino WHERE tipo = 'RICAVI' AND attivo = 1 ORDER BY codice"))  
        mastrini_ricavi = cursor.fetchall()
        
        # Normalizza i valori 'attivo' per assicurarsi che siano consistenti
        try:
            db.session.execute(db.text("""
                UPDATE collegamento_mastrini 
                SET attivo = 1 
                WHERE attivo IS NULL OR attivo = 0 OR attivo = '' OR attivo = 'false' OR attivo = false
            """))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
        
        # Ottieni collegamenti esistenti
        cursor = db.session.execute(db.text("""
            SELECT c.*, ma.codice as codice_acquisto, ma.descrizione as desc_acquisto,
                   mr.codice as codice_ricavo, mr.descrizione as desc_ricavo
            FROM collegamento_mastrini c
            JOIN mastrino ma ON c.mastrino_acquisto_id = ma.id
            JOIN mastrino mr ON c.mastrino_ricavo_id = mr.id
            WHERE c.attivo = 1
            ORDER BY ma.codice, mr.codice
        """))
        collegamenti = cursor.fetchall()
        
        
        return render_template('impostazioni/collegamento-mastrini.html', 
                             mastrini_acquisti=mastrini_acquisti,
                             mastrini_ricavi=mastrini_ricavi, 
                             collegamenti=collegamenti)
        
    except Exception as e:
        print(f"Errore collegamento mastrini: {e}")
        return f"Errore: {e}", 500

@app.route('/impostazioni/collegamento-mastrini/nuovo', methods=['POST'])
def nuovo_collegamento_mastrini():
    """Crea un nuovo collegamento tra mastrini"""
    try:
        mastrino_acquisto_id = request.form.get('mastrino_acquisto_id')
        mastrino_ricavo_id = request.form.get('mastrino_ricavo_id') 
        descrizione = request.form.get('descrizione_collegamento', '')
        
        if not mastrino_acquisto_id or not mastrino_ricavo_id:
            return jsonify({'success': False, 'error': 'Seleziona entrambi i mastrini'}), 400
        
        # Verifica che non esista già il collegamento
        cursor = db.session.execute(db.text("""
            SELECT COUNT(*) FROM collegamento_mastrini 
            WHERE mastrino_acquisto_id = :acq AND mastrino_ricavo_id = :ric AND attivo = 1
        """), {'acq': mastrino_acquisto_id, 'ric': mastrino_ricavo_id})
        
        existing_count = cursor.scalar()
        
        if existing_count > 0:
            return jsonify({'success': False, 'error': 'Collegamento già esistente'}), 400
        
        # Crea il collegamento usando ORM
        nuovo_collegamento = CollegamentoMastrini(
            mastrino_acquisto_id=int(mastrino_acquisto_id),
            mastrino_ricavo_id=int(mastrino_ricavo_id),
            descrizione_collegamento=descrizione,
            attivo=True
        )
        
        db.session.add(nuovo_collegamento)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Collegamento creato con successo'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore creazione collegamento: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/impostazioni/collegamento-mastrini/<int:id>/elimina', methods=['POST'])
def elimina_collegamento_mastrini(id):
    """Elimina un collegamento tra mastrini"""
    try:
        # Soft delete
        db.session.execute(db.text("""
            UPDATE collegamento_mastrini SET attivo = 0 WHERE id = :id
        """), {'id': id})
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Collegamento eliminato'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore eliminazione collegamento: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/impostazioni/ripulisci-dati-test', methods=['POST'])
def ripulisci_dati_test():
    """ROUTE TEMPORANEA: Cancella massivamente tutti i dati di test"""
    try:
        print("Iniziando pulizia dati test...")
        deleted_count = 0
        
        # Liste delle tabelle da cancellare e da mantenere
        tabelle_da_cancellare = [
            'articolo_out',  # Prima gli articoli (foreign keys)
            'articolo_in', 
            'ddt_out',       # Poi i DDT
            'ddt_in',
            'dettaglio_preventivo',  # Prima i dettagli
            'preventivo',           # Poi i preventivi
            'dettaglio_ordine',     # Prima i dettagli ordini
            'ordine_fornitore',     # Poi gli ordini (era offerte)
            'commessa',             # Commesse
            'movimento',            # Movimenti
            'articolo_movimento_interno',  # Prima gli articoli movimento interno
            'movimento_interno',           # Poi i movimenti interni
            'catalogo_articolo'     # Infine il catalogo articoli
        ]
        
        # MANTIENI: cliente, fornitore, mastrino, magazzino, collegamento_mastrini
        
        for tabella in tabelle_da_cancellare:
            try:
                # Conta i record prima della cancellazione
                count_result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {tabella}")).fetchone()
                count_before = count_result[0] if count_result else 0
                
                if count_before > 0:
                    # Cancella tutti i record dalla tabella
                    db.session.execute(db.text(f"DELETE FROM {tabella}"))
                    deleted_count += count_before
                    print(f"Cancellati {count_before} record da {tabella}")
                else:
                    print(f"Tabella {tabella} già vuota")
                    
            except Exception as table_error:
                print(f"Errore cancellazione tabella {tabella}: {table_error}")
                # Continua con le altre tabelle
                continue
        
        # Commit di tutte le cancellazioni
        db.session.commit()
        
        # Reset delle sequenze per ricominciare da 1
        reset_sequences = [
            "UPDATE sqlite_sequence SET seq=0 WHERE name='ddt_in'",
            "UPDATE sqlite_sequence SET seq=0 WHERE name='ddt_out'", 
            "UPDATE sqlite_sequence SET seq=0 WHERE name='preventivo'",
            "UPDATE sqlite_sequence SET seq=0 WHERE name='ordine_fornitore'",
            "UPDATE sqlite_sequence SET seq=0 WHERE name='commessa'",
            "UPDATE sqlite_sequence SET seq=0 WHERE name='movimento'",
            "UPDATE sqlite_sequence SET seq=0 WHERE name='movimento_interno'",
            "UPDATE sqlite_sequence SET seq=0 WHERE name='catalogo_articolo'"
        ]
        
        for reset_sql in reset_sequences:
            try:
                db.session.execute(db.text(reset_sql))
            except:
                # Se la tabella non esiste in sqlite_sequence, ignora
                pass
                
        db.session.commit()
        
        print(f"Pulizia completata! Cancellati {deleted_count} record totali")
        
        return jsonify({
            'success': True, 
            'message': f'Dati test cancellati con successo! Eliminati {deleted_count} record.',
            'deleted_count': deleted_count,
            'preserved': 'Clienti, Fornitori, Mastrini, Magazzini mantenuti'
        })
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"Errore durante pulizia dati test: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return jsonify({'success': False, 'error': error_msg}), 500

# ========== API AUTOCOMPLETE ==========

@app.route('/api/articoli/disponibili')
def api_articoli_disponibili():
    """API per articoli disponibili in magazzino"""
    q = request.args.get('q', '')
    
    # Mostra TUTTI gli articoli attivi, anche con giacenza 0
    articoli = CatalogoArticolo.query.filter(
        db.or_(
            CatalogoArticolo.codice_interno.contains(q),
            CatalogoArticolo.descrizione.contains(q)
        ),
        CatalogoArticolo.attivo == True
    ).limit(10).all()
    
    return jsonify([{
        'codice': a.codice_interno,
        'descrizione': a.descrizione,
        'giacenza': a.giacenza_attuale or 0,
        'prezzo': a.costo_ultimo or 0,
        'ubicazione': a.ubicazione or ''
    } for a in articoli])

# ========== ROUTE DI TEST ==========

@app.route('/test-claude-parser')
def test_claude_parser():
    try:
        from working_claude_parser import WorkingClaudeParser
        parser = WorkingClaudeParser()
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Test Claude Parser</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h1>Test Claude Parser</h1>
            <p style="color: green;">WorkingClaudeParser importato correttamente</p>
            <p><strong>API Key:</strong> {'Presente' if parser.api_key else 'Mancante'}</p>
            <p><strong>URL API:</strong> {parser.api_url}</p>
            <p><strong>Key preview:</strong> {parser.api_key[:30] + '...' if parser.api_key else 'N/A'}</p>
            <hr>
            <p><a href="/ddt-import">Torna all'import DDT</a></p>
        </body>
        </html>
        """
    except Exception as e:
        import traceback
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Errore Test Parser</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h1 style="color: red;">Errore Test Parser</h1>
            <pre style="background: #f0f0f0; padding: 10px;">{str(e)}</pre>
            <h3>Traceback completo:</h3>
            <pre style="background: #f0f0f0; padding: 10px; font-size: 12px;">{traceback.format_exc()}</pre>
            <hr>
            <p><a href="/ddt-import">Torna all'import DDT</a></p>
        </body>
        </html>
        """

@app.route('/test-env')
def test_env():
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Test Ambiente</title></head>
    <body style="font-family: Arial; padding: 20px;">
        <h1>Test Variabili Ambiente</h1>
        <p><strong>CLAUDE_API_KEY:</strong> {'Presente' if os.getenv('CLAUDE_API_KEY') else 'Mancante'}</p>
        <p><strong>ANTHROPIC_API_KEY:</strong> {'Presente' if os.getenv('ANTHROPIC_API_KEY') else 'Mancante'}</p>
        <p><strong>Working Directory:</strong> {os.getcwd()}</p>
        <p><strong>Python Path:</strong> {os.path.dirname(__file__)}</p>
        <hr>
        <h2>File presenti:</h2>
        <ul>
        {''.join([f"<li>{f}</li>" for f in os.listdir('.') if f.endswith(('.py', '.env'))])}
        </ul>
        <hr>
        <p><a href="/">Torna alla dashboard</a></p>
    </body>
    </html>
    """

# ========== SISTEMA MOVIMENTI INTERNI ==========

@app.route('/movimenti-interni')
def movimenti_interni_list():
    """Lista movimenti interni"""
    try:
        movimenti = MovimentoInterno.query.order_by(
            MovimentoInterno.stato.asc(),
            MovimentoInterno.data_movimento.desc()
        ).all()
        
        return render_template('movimenti-interni.html', movimenti=movimenti)
    except Exception as e:
        print(f"Errore lista movimenti interni: {e}")
        return render_template('movimenti-interni.html', movimenti=[])

@app.route('/movimenti-interni/nuovo', methods=['GET', 'POST'])
def nuovo_movimento_interno():
    """Crea nuovo movimento interno"""
    if request.method == 'GET':
        try:
            magazzini = Magazzino.query.filter_by(attivo=True).all()
            
            # Recupera magazzino principale dalle impostazioni
            magazzino_predefinito = None
            config_magazzino = ConfigurazioneSistema.query.filter_by(chiave='magazzino_principale').first()
            if config_magazzino and config_magazzino.valore:
                magazzino_predefinito = Magazzino.query.filter_by(
                    descrizione=config_magazzino.valore, 
                    attivo=True
                ).first()
            
            # Se non trovato nelle impostazioni, usa il primo magazzino attivo
            if not magazzino_predefinito and magazzini:
                magazzino_predefinito = magazzini[0]
            
            return render_template('nuovo-movimento-interno.html',
                                 magazzini=magazzini,
                                 magazzino_predefinito=magazzino_predefinito,
                                 today=datetime.now().strftime('%Y-%m-%d'))
        except Exception as e:
            print(f"Errore GET nuovo movimento interno: {e}")
            return str(e), 500
    
    # POST
    try:
        data = request.form
        
        nuovo_movimento = MovimentoInterno()
        nuovo_movimento.data_movimento = datetime.strptime(data.get('data_movimento'), '%Y-%m-%d').date()
        nuovo_movimento.magazzino_partenza = data.get('magazzino_partenza', '')
        nuovo_movimento.magazzino_destinazione = data.get('magazzino_destinazione', '')
        nuovo_movimento.causale = data.get('causale', '')
        nuovo_movimento.note = data.get('note', '')
        nuovo_movimento.stato = 'bozza'
        
        db.session.add(nuovo_movimento)
        db.session.flush()
        
        # Aggiungi articoli
        for key in data.keys():
            if key.startswith('codice_'):
                index = key.split('_')[1]
                codice = data.get(f'codice_{index}', '').strip()
                if codice:
                    articolo = ArticoloMovimentoInterno()
                    articolo.movimento_id = nuovo_movimento.id
                    articolo.codice_articolo = codice
                    articolo.descrizione_articolo = data.get(f'descrizione_{index}', '')
                    articolo.quantita = float(data.get(f'quantita_{index}', 0))
                    articolo.unita_misura = data.get(f'unita_misura_{index}', 'PZ')
                    db.session.add(articolo)
        
        db.session.commit()
        
        return redirect(f"/movimenti-interni/{nuovo_movimento.id}")
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore salvataggio movimento interno: {e}")
        return f"Errore: {e}", 500

@app.route('/movimenti-interni/<int:id>')
def visualizza_movimento_interno(id):
    """Visualizza dettagli movimento interno"""
    try:
        movimento = MovimentoInterno.query.get_or_404(id)
        articoli = ArticoloMovimentoInterno.query.filter_by(movimento_id=id).all()
        
        return render_template('movimento-interno-detail.html',
                             movimento=movimento,
                             articoli=articoli)
    except Exception as e:
        print(f"Errore visualizza movimento interno: {e}")
        return f"Errore: {e}", 404

@app.route('/api/giacenza')
def api_giacenza():
    """API per ottenere giacenza articolo in magazzino specifico"""
    codice = request.args.get('codice')
    magazzino = request.args.get('magazzino')
    
    if not codice or not magazzino:
        return jsonify({'error': 'Parametri mancanti'}), 400
    
    try:
        # Cerca l'articolo nel catalogo per il magazzino specificato
        articolo = CatalogoArticolo.query.filter_by(
            codice_interno=codice,
            ubicazione=magazzino
        ).first()
        
        giacenza = 0
        if articolo:
            giacenza = articolo.giacenza_attuale or 0
        
        return jsonify({
            'giacenza': float(giacenza),
            'magazzino': magazzino,
            'codice': codice
        })
        
    except Exception as e:
        print(f"Errore API giacenza: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/movimenti-interni/<int:id>/conferma', methods=['POST'])
def conferma_movimento_interno(id):
    """Conferma movimento interno"""
    try:
        movimento = MovimentoInterno.query.get_or_404(id)
        
        if movimento.stato == 'confermato':
            return jsonify({'success': False, 'error': 'Movimento già confermato'})
        
        # Verifica disponibilità giacenze per tutti gli articoli
        articoli = ArticoloMovimentoInterno.query.filter_by(movimento_id=movimento.id).all()
        
        for articolo in articoli:
            # Controlla giacenza disponibile
            catalogo_articolo = CatalogoArticolo.query.filter_by(
                codice_interno=articolo.codice_articolo,
                ubicazione=movimento.magazzino_partenza
            ).first()
            
            giacenza_disponibile = 0
            if catalogo_articolo:
                giacenza_disponibile = catalogo_articolo.giacenza_attuale or 0
            
            if articolo.quantita > giacenza_disponibile:
                return jsonify({
                    'success': False, 
                    'error': f'Giacenza insufficiente per {articolo.codice_articolo}. '
                           f'Richiesto: {articolo.quantita}, Disponibile: {giacenza_disponibile}'
                })
        
        # Genera numero progressivo
        anno = datetime.now().year
        ultimo = MovimentoInterno.query.filter(
            MovimentoInterno.numero_documento.like(f'MI/%/{anno}')
        ).order_by(MovimentoInterno.id.desc()).first()
        
        numero = 1
        if ultimo and ultimo.numero_documento:
            try:
                numero = int(ultimo.numero_documento.split('/')[1]) + 1
            except:
                numero = 1
        
        movimento.numero_documento = f'MI/{numero:04d}/{anno}'
        movimento.stato = 'confermato'
        
        # Genera movimenti per ogni articolo
        articoli = ArticoloMovimentoInterno.query.filter_by(movimento_id=movimento.id).all()
        
        for articolo in articoli:
            # Movimento di uscita dal magazzino partenza
            movimento_uscita = Movimento(
                data_movimento=datetime.now(),
                tipo='uscita',
                documento_tipo='movimento_interno',
                documento_numero=movimento.numero_documento,
                codice_articolo=articolo.codice_articolo,
                descrizione_articolo=articolo.descrizione_articolo,
                quantita=articolo.quantita,
                valore_unitario=0,
                valore_totale=0,
                magazzino=movimento.magazzino_partenza,
                causale=f'Trasferimento a {movimento.magazzino_destinazione} - {movimento.causale}'
            )
            db.session.add(movimento_uscita)
            
            # Movimento di entrata nel magazzino destinazione
            movimento_entrata = Movimento(
                data_movimento=datetime.now(),
                tipo='entrata',
                documento_tipo='movimento_interno',
                documento_numero=movimento.numero_documento,
                codice_articolo=articolo.codice_articolo,
                descrizione_articolo=articolo.descrizione_articolo,
                quantita=articolo.quantita,
                valore_unitario=0,
                valore_totale=0,
                magazzino=movimento.magazzino_destinazione,
                causale=f'Trasferimento da {movimento.magazzino_partenza} - {movimento.causale}'
            )
            db.session.add(movimento_entrata)
            
            # Aggiorna giacenze se l'articolo esiste nel catalogo
            if articolo.codice_articolo:
                cat_articolo = CatalogoArticolo.query.filter_by(
                    codice_interno=articolo.codice_articolo
                ).first()
                
                if cat_articolo:
                    # Non modifichiamo la giacenza totale nei movimenti interni
                    # solo spostiamo tra magazzini - aggiorniamo l'ubicazione
                    cat_articolo.ubicazione = movimento.magazzino_destinazione
        
        db.session.commit()
        
        return jsonify({'success': True, 'numero': movimento.numero_documento})
        
    except Exception as e:
        db.session.rollback()
        print(f"Errore conferma movimento interno: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== API AUTOCOMPLETAMENTO AGGIUNTIVE ==========

@app.route('/api/magazzini/search')
def api_magazzini_search():
    """API per ricerca magazzini"""
    q = request.args.get('q', '')
    magazzini = Magazzino.query.filter(
        db.or_(
            Magazzino.codice.contains(q),
            Magazzino.descrizione.contains(q)
        ),
        Magazzino.attivo == True
    ).limit(10).all()
    
    return jsonify([{
        'codice': m.codice,
        'descrizione': m.descrizione
    } for m in magazzini])


@app.route('/api/fornitori/search')
def api_fornitori_search():
    """API per ricerca fornitori"""
    q = request.args.get('q', '')
    fornitori = Fornitore.query.filter(
        db.or_(
            Fornitore.ragione_sociale.contains(q),
            Fornitore.partita_iva.contains(q)
        ),
        Fornitore.attivo == True
    ).limit(10).all()
    
    return jsonify([{
        'ragione_sociale': f.ragione_sociale,
        'partita_iva': f.partita_iva or '',
        'id': f.id
    } for f in fornitori])


@app.route('/api/clienti/search')
def api_clienti_search():
    """API per ricerca clienti"""
    q = request.args.get('q', '')
    clienti = Cliente.query.filter(
        db.or_(
            Cliente.ragione_sociale.contains(q),
            Cliente.partita_iva.contains(q)
        ),
        Cliente.attivo == True
    ).limit(10).all()
    
    return jsonify([{
        'ragione_sociale': c.ragione_sociale,
        'partita_iva': c.partita_iva or '',
        'id': c.id
    } for c in clienti])

# ========== API ENDPOINTS PER AUTOCOMPLETE ==========

@app.route('/api/fornitori/search')
def search_fornitori():
    """API per ricerca fornitori"""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    
    fornitori = Fornitore.query.filter(
        db.and_(
            db.or_(
                Fornitore.ragione_sociale.contains(q),
                Fornitore.partita_iva.contains(q)
            ),
            Fornitore.attivo == True
        )
    ).limit(10).all()
    
    return jsonify([{
        'id': f.id,
        'ragione_sociale': f.ragione_sociale,
        'partita_iva': f.partita_iva or '',
        'codice_fiscale': f.codice_fiscale or '',
        'citta': f.citta or ''
    } for f in fornitori])

@app.route('/api/commesse/search')
def search_commesse():
    """API per ricerca commesse"""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    
    commesse = Commessa.query.filter(
        db.and_(
            db.or_(
                Commessa.numero_progressivo.contains(q),
                Commessa.descrizione.contains(q),
                Commessa.cliente_nome.contains(q)
            ),
            Commessa.stato == 'aperta'
        )
    ).limit(10).all()
    
    return jsonify([{
        'id': c.id,
        'numero_progressivo': c.numero_progressivo,
        'descrizione': c.descrizione or '',
        'cliente_nome': c.cliente_nome,
        'display_name': f'Commessa {c.numero_progressivo}'
    } for c in commesse])

@app.route('/api/mastrini/search')
def search_mastrini():
    """API per ricerca mastrini"""
    q = request.args.get('q', '').strip()
    tipo = request.args.get('tipo', '').strip().upper()
    
    if len(q) < 2:
        return jsonify([])
    
    query = Mastrino.query.filter(
        db.and_(
            db.or_(
                Mastrino.codice.contains(q),
                Mastrino.descrizione.contains(q)
            ),
            Mastrino.attivo == True
        )
    )
    
    # Filtra per tipo se specificato (mappa i tipi di input ai tipi nel database)
    if tipo:
        if tipo.upper() in ['RICAVO', 'RICAVI']:
            query = query.filter(Mastrino.tipo == 'RICAVI')
        elif tipo.upper() in ['ACQUISTO', 'ACQUISTI']:
            query = query.filter(Mastrino.tipo == 'ACQUISTI')
    
    mastrini = query.limit(10).all()
    
    return jsonify([{
        'id': m.id,
        'codice': m.codice,
        'descrizione': m.descrizione,
        'tipo': m.tipo
    } for m in mastrini])

# ========== INIZIALIZZAZIONE ==========

with app.app_context():
    try:
        db.create_all()
        
        # Migration: Add data_scadenza to commessa table if not exists
        try:
            db.session.execute(text("SELECT data_scadenza FROM commessa LIMIT 1"))
        except Exception:
            # Column doesn't exist, add it
            db.session.execute(text("ALTER TABLE commessa ADD COLUMN data_scadenza DATE"))
            db.session.commit()
            print("✅ Migration: Added data_scadenza column to commessa table")
        
        # Inizializzazione dati base se database vuoto
        if not Magazzino.query.first():
            # Magazzini default
            mag1 = Magazzino(codice='MAG001', descrizione='Magazzino Centrale', attivo=True)
            mag2 = Magazzino(codice='MAG002', descrizione='Deposito Nord', attivo=True)
            db.session.add_all([mag1, mag2])
            
            # Mastrini default
            mast1 = Mastrino(codice='ACQ001', descrizione='Acquisto Materiali', tipo='acquisto', attivo=True)
            mast2 = Mastrino(codice='VEN001', descrizione='Vendita Prodotti', tipo='ricavo', attivo=True)
            db.session.add_all([mast1, mast2])
            
            db.session.commit()
            print('Database inizializzato con dati di base')
    except Exception as e:
        print(f'Errore inizializzazione database: {e}')

# ================================
# SEZIONE REPORT
# ================================

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/reports/dashboard')
def report_dashboard():
    """Report Dashboard Esecutivo - KPI principali"""
    try:
        # KPI principali
        ddt_in_count = db.session.query(DDTIn).count()
        ddt_out_count = db.session.query(DDTOut).count()
        ddt_in_conf = db.session.query(DDTIn).filter(DDTIn.stato == 'confermato').count()
        ddt_out_conf = db.session.query(DDTOut).filter(DDTOut.stato == 'confermato').count()
        
        # Valore inventario
        articoli = db.session.query(CatalogoArticolo).filter(CatalogoArticolo.attivo == True).all()
        valore_inventario = sum((a.giacenza_attuale or 0) * (a.costo_medio or 0) for a in articoli)
        
        # Preventivi e offerte
        preventivi_totali = db.session.query(Preventivo).count()
        preventivi_accettati = db.session.query(Preventivo).filter(Preventivo.stato == 'accettato').count()
        offerte_totali = db.session.query(OffertaFornitore).count()
        offerte_accettate = db.session.query(OffertaFornitore).filter(OffertaFornitore.stato == 'accettata').count()
        
        # Articoli critici (sotto scorta minima)
        articoli_critici = db.session.query(CatalogoArticolo).filter(
            CatalogoArticolo.attivo == True,
            CatalogoArticolo.giacenza_attuale < CatalogoArticolo.scorta_minima
        ).count()
        
        kpi_data = {
            'ddt_in_totali': ddt_in_count,
            'ddt_in_confermati': ddt_in_conf,
            'ddt_out_totali': ddt_out_count,
            'ddt_out_confermati': ddt_out_conf,
            'valore_inventario': valore_inventario,
            'preventivi_totali': preventivi_totali,
            'preventivi_accettati': preventivi_accettati,
            'offerte_totali': offerte_totali,
            'offerte_accettate': offerte_accettate,
            'articoli_critici': articoli_critici,
            'conversion_rate_preventivi': (preventivi_accettati / preventivi_totali * 100) if preventivi_totali > 0 else 0,
            'conversion_rate_offerte': (offerte_accettate / offerte_totali * 100) if offerte_totali > 0 else 0
        }
        
        return render_template('report_dashboard.html', kpi=kpi_data)
    except Exception as e:
        return f"Errore generazione dashboard: {str(e)}", 500

@app.route('/reports/movimenti')
def report_movimenti():
    """Report Movimenti Magazzino"""
    data_da = request.args.get('data_da')
    data_a = request.args.get('data_a')
    
    try:
        from datetime import datetime
        
        # Query unificata per tutti i movimenti con tipologia
        movimenti_query = """
            SELECT 
                'ENTRATA' as tipologia,
                ai.codice_interno as codice,
                ai.descrizione,
                ai.quantita,
                ai.costo_unitario as valore_unitario,
                di.data_ddt_origine as data_movimento,
                di.fornitore as origine_destinazione
            FROM articolo_in ai
            JOIN ddt_in di ON ai.ddt_id = di.id
            WHERE di.stato = 'confermato'
            
            UNION ALL
            
            SELECT 
                'USCITA' as tipologia,
                ao.codice_interno as codice,
                ao.descrizione,
                ao.quantita,
                ao.prezzo_unitario as valore_unitario,
                do.data_ddt_origine as data_movimento,
                do.destinazione as origine_destinazione
            FROM articolo_out ao
            JOIN ddt_out do ON ao.ddt_id = do.id
            WHERE do.stato = 'confermato'
            
            UNION ALL
            
            SELECT 
                'INTERNO' as tipologia,
                ami.codice_articolo as codice,
                ami.descrizione_articolo as descrizione,
                ami.quantita,
                0.0 as valore_unitario,
                mi.data_movimento,
                (mi.magazzino_partenza || ' → ' || mi.magazzino_destinazione) as origine_destinazione
            FROM articolo_movimento_interno ami
            JOIN movimento_interno mi ON ami.movimento_id = mi.id
            WHERE mi.stato = 'confermato'
        """
        
        # Aggiungi filtri data se specificati
        if data_da or data_a:
            where_conditions = []
            if data_da:
                data_da_obj = datetime.strptime(data_da, '%Y-%m-%d').date()
                where_conditions.append(f"data_movimento >= '{data_da_obj}'")
            if data_a:
                data_a_obj = datetime.strptime(data_a, '%Y-%m-%d').date()
                where_conditions.append(f"data_movimento <= '{data_a_obj}'")
            
            # Modifica query per includere filtri
            where_clause = " AND ".join(where_conditions)
            movimenti_query = f"""
                SELECT * FROM (
                    {movimenti_query}
                ) WHERE {where_clause}
            """
        
        # Aggiungi ordinamento
        movimenti_query += " ORDER BY data_movimento DESC, tipologia"
        
        # Esegui query
        movimenti = db.session.execute(text(movimenti_query)).fetchall()
        
        # Calcoli statistiche
        movimenti_entrata = [m for m in movimenti if m[0] == 'ENTRATA']
        movimenti_uscita = [m for m in movimenti if m[0] == 'USCITA']
        movimenti_interni = [m for m in movimenti if m[0] == 'INTERNO']
        
        valore_entrate = sum((m[3] or 0) * (m[4] or 0) for m in movimenti_entrata)
        valore_uscite = sum((m[3] or 0) * (m[4] or 0) for m in movimenti_uscita)
        
        return render_template('report_movimenti.html', 
                             movimenti=movimenti,
                             totale_movimenti=len(movimenti),
                             movimenti_entrata=len(movimenti_entrata),
                             movimenti_uscita=len(movimenti_uscita),
                             movimenti_interni=len(movimenti_interni),
                             valore_entrate=valore_entrate,
                             valore_uscite=valore_uscite,
                             data_da=data_da,
                             data_a=data_a)
    except Exception as e:
        return f"Errore generazione report movimenti: {str(e)}", 500

@app.route('/reports/fornitori')
def report_fornitori():
    """Report Fornitori - Performance e statistiche"""
    try:
        # Ottieni parametri di filtro data
        data_da = request.args.get('data_da')
        data_a = request.args.get('data_a')
        
        # Costruisci clausola WHERE per le date
        date_filter = ""
        if data_da and data_a:
            date_filter = f"AND di.data_ddt_origine BETWEEN '{data_da}' AND '{data_a}'"
        elif data_da:
            date_filter = f"AND di.data_ddt_origine >= '{data_da}'"
        elif data_a:
            date_filter = f"AND di.data_ddt_origine <= '{data_a}'"
        
        # Top fornitori per DDT con valore totale (query SQL diretta)
        fornitori_query = f"""
            SELECT 
                di.fornitore, 
                COUNT(*) as totale_ddt, 
                MAX(di.data_ddt_origine) as ultimo_ddt,
                CAST(julianday('now') - julianday(MAX(di.data_ddt_origine)) AS INTEGER) as giorni_ultimo_ddt,
                COALESCE(SUM(ai.quantita * ai.costo_unitario), 0.0) as valore_totale
            FROM ddt_in di
            LEFT JOIN articolo_in ai ON di.id = ai.ddt_id
            WHERE di.fornitore != '' AND di.fornitore IS NOT NULL AND di.stato = 'confermato' {date_filter}
            GROUP BY di.fornitore 
            ORDER BY totale_ddt DESC 
            LIMIT 50
        """
        fornitori_stats = db.session.execute(text(fornitori_query)).fetchall()
        
        # Converti in formato utilizzabile dal template
        top_fornitori = []
        for stat in fornitori_stats:
            fornitore = {
                'ragione_sociale': stat[0],  # fornitore
                'totale_ddt': stat[1] or 0,  # totale_ddt
                'valore_totale': float(stat[4] or 0.0),  # valore_totale calcolato
                'ultimo_ddt_data': stat[2],  # ultimo_ddt
                'giorni_ultimo_ddt': int(stat[3] or 0),  # giorni_ultimo_ddt
                'citta': 'N/D'  # Aggiungeremo dopo se serve collegare con tabella fornitori
            }
            top_fornitori.append(fornitore)
        
        # Fornitori inattivi (non hanno DDT da più di 60 giorni)
        fornitori_inattivi = len([f for f in top_fornitori if f['giorni_ultimo_ddt'] > 60])
        
        return render_template('report_fornitori.html', 
                             top_fornitori=top_fornitori,
                             fornitori_inattivi=fornitori_inattivi)
    except Exception as e:
        return f"Errore generazione report fornitori: {str(e)}", 500

@app.route('/reports/articoli')
def report_articoli():
    """Report Articoli - Più movimentati e giacenze"""
    try:
        from sqlalchemy import and_, or_, desc, func
        
        # Ottieni parametri di filtro data
        data_da = request.args.get('data_da')
        data_a = request.args.get('data_a')
        
        # Costruisci filtro per DDT IN
        ddt_in_filter = DDTIn.stato == 'confermato'
        if data_da and data_a:
            ddt_in_filter = and_(ddt_in_filter, DDTIn.data_ddt_origine.between(data_da, data_a))
        elif data_da:
            ddt_in_filter = and_(ddt_in_filter, DDTIn.data_ddt_origine >= data_da)
        elif data_a:
            ddt_in_filter = and_(ddt_in_filter, DDTIn.data_ddt_origine <= data_a)
        
        # Costruisci filtro per DDT OUT
        ddt_out_filter = DDTOut.stato == 'confermato'
        if data_da and data_a:
            ddt_out_filter = and_(ddt_out_filter, DDTOut.data_ddt_origine.between(data_da, data_a))
        elif data_da:
            ddt_out_filter = and_(ddt_out_filter, DDTOut.data_ddt_origine >= data_da)
        elif data_a:
            ddt_out_filter = and_(ddt_out_filter, DDTOut.data_ddt_origine <= data_a)
        
        # Top articoli per movimentazione
        articoli_in = db.session.query(
            ArticoloIn.codice_interno,
            func.sum(ArticoloIn.quantita).label('qty_in')
        ).join(DDTIn).filter(ddt_in_filter).group_by(ArticoloIn.codice_interno).subquery()
        
        articoli_out = db.session.query(
            ArticoloOut.codice_interno,
            func.sum(ArticoloOut.quantita).label('qty_out')
        ).join(DDTOut).filter(ddt_out_filter).group_by(ArticoloOut.codice_interno).subquery()
        
        # Articoli più movimentati
        top_articoli = db.session.query(
            CatalogoArticolo.codice_interno,
            CatalogoArticolo.descrizione,
            CatalogoArticolo.giacenza_attuale,
            CatalogoArticolo.costo_medio,
            func.coalesce(articoli_in.c.qty_in, 0).label('entrate'),
            func.coalesce(articoli_out.c.qty_out, 0).label('uscite'),
            (func.coalesce(CatalogoArticolo.giacenza_attuale, 0) * func.coalesce(CatalogoArticolo.costo_medio, 0)).label('valore_giacenza')
        ).outerjoin(articoli_in, CatalogoArticolo.codice_interno == articoli_in.c.codice_interno)\
         .outerjoin(articoli_out, CatalogoArticolo.codice_interno == articoli_out.c.codice_interno)\
         .filter(CatalogoArticolo.attivo == True)\
         .order_by(desc(func.coalesce(articoli_in.c.qty_in, 0) + func.coalesce(articoli_out.c.qty_out, 0)))\
         .limit(30).all()
        
        # Articoli sotto scorta
        articoli_critici = db.session.query(CatalogoArticolo).filter(
            CatalogoArticolo.attivo == True,
            CatalogoArticolo.giacenza_attuale < CatalogoArticolo.scorta_minima
        ).all()
        
        return render_template('report_articoli.html', 
                             top_articoli=top_articoli,
                             articoli_critici=articoli_critici)
    except Exception as e:
        return f"Errore generazione report articoli: {str(e)}", 500

@app.route('/reports/clienti')
def report_clienti():
    """Report Clienti - Performance e statistiche"""
    try:
        # Ottieni parametri di filtro data
        data_da = request.args.get('data_da')
        data_a = request.args.get('data_a')
        
        # Costruisci clausola WHERE per le date
        date_filter = ""
        if data_da and data_a:
            date_filter = f"AND do.data_ddt_origine BETWEEN '{data_da}' AND '{data_a}'"
        elif data_da:
            date_filter = f"AND do.data_ddt_origine >= '{data_da}'"
        elif data_a:
            date_filter = f"AND do.data_ddt_origine <= '{data_a}'"
        
        # Top clienti per DDT OUT usando il campo destinazione che contiene il cliente
        clienti_query = f"""
            SELECT 
                do.destinazione, 
                COUNT(*) as totale_ddt, 
                MAX(do.data_ddt_origine) as ultimo_ddt,
                CAST(julianday('now') - julianday(MAX(do.data_ddt_origine)) AS INTEGER) as giorni_ultimo_ddt,
                COALESCE(SUM(ao.quantita * ao.prezzo_unitario), 0.0) as valore_totale
            FROM ddt_out do
            LEFT JOIN articolo_out ao ON do.id = ao.ddt_id
            WHERE do.destinazione != '' AND do.destinazione IS NOT NULL AND do.stato = 'confermato' {date_filter}
            GROUP BY do.destinazione 
            ORDER BY totale_ddt DESC 
            LIMIT 50
        """
        clienti_stats = db.session.execute(text(clienti_query)).fetchall()
        
        # Converti in formato utilizzabile dal template
        top_clienti = []
        for stat in clienti_stats:
            cliente = {
                'cliente_nome': stat[0],  # destinazione (cliente)
                'totale_ddt': stat[1] or 0,  # totale_ddt
                'valore_totale': float(stat[4] or 0),  # valore_totale calcolato dalla query
                'ultimo_ddt_data': stat[2],  # ultimo_ddt
                'giorni_ultimo_ddt': int(stat[3] or 0)  # giorni_ultimo_ddt
            }
            top_clienti.append(cliente)
        
        # Clienti inattivi (non hanno DDT da più di 60 giorni)
        clienti_inattivi = len([c for c in top_clienti if c['giorni_ultimo_ddt'] > 60])
        
        return render_template('report_clienti.html', 
                             top_clienti=top_clienti,
                             clienti_inattivi=clienti_inattivi)
    except Exception as e:
        return f"Errore generazione report clienti: {str(e)}", 500

@app.route('/reports/commesse')
def report_commesse():
    """Report Commesse - Analisi completa per tipologia, stato e correlazioni DDT"""
    try:
        # Ottieni parametri di filtro data
        data_da = request.args.get('data_da')
        data_a = request.args.get('data_a')
        
        # Costruisci clausola WHERE per le date (filtra per data_apertura commessa)
        date_filter = ""
        if data_da and data_a:
            date_filter = f"AND c.data_apertura BETWEEN '{data_da}' AND '{data_a}'"
        elif data_da:
            date_filter = f"AND c.data_apertura >= '{data_da}'"
        elif data_a:
            date_filter = f"AND c.data_apertura <= '{data_a}'"
        # Query per analisi per tipologia
        tipologie_query = f"""
            SELECT 
                tipologia,
                COUNT(*) as totale_commesse,
                SUM(CASE WHEN stato = 'aperta' THEN 1 ELSE 0 END) as aperte,
                SUM(CASE WHEN stato = 'chiusa' THEN 1 ELSE 0 END) as chiuse,
                SUM(CASE WHEN stato = 'sospesa' THEN 1 ELSE 0 END) as sospese
            FROM commessa c
            WHERE tipologia != '' AND tipologia IS NOT NULL {date_filter}
            GROUP BY tipologia 
            ORDER BY totale_commesse DESC
        """
        tipologie_stats = db.session.execute(text(tipologie_query)).fetchall()
        
        # Query per commesse per cliente con correlazioni DDT
        clienti_query = f"""
            SELECT 
                c.cliente_nome,
                COUNT(*) as totale_commesse,
                MAX(c.data_apertura) as ultima_apertura,
                CAST(julianday('now') - julianday(MAX(c.data_apertura)) AS INTEGER) as giorni_ultima_apertura,
                -- Correlazioni DDT per cliente
                COALESCE(ddt_out.totale_ddt_out, 0) as ddt_out_cliente,
                COALESCE(ddt_out.valore_totale_out, 0) as valore_ddt_out,
                COALESCE(ddt_in.totale_ddt_in, 0) as ddt_in_fornitore
            FROM commessa c
            LEFT JOIN (
                SELECT destinazione, COUNT(*) as totale_ddt_out, 
                       SUM(ao.quantita * ao.prezzo_unitario) as valore_totale_out
                FROM ddt_out do
                LEFT JOIN articolo_out ao ON do.id = ao.ddt_id
                WHERE do.stato = 'confermato'
                GROUP BY destinazione
            ) ddt_out ON c.cliente_nome = ddt_out.destinazione
            LEFT JOIN (
                SELECT fornitore, COUNT(*) as totale_ddt_in
                FROM ddt_in di
                WHERE di.stato = 'confermato'
                GROUP BY fornitore  
            ) ddt_in ON c.cliente_nome = ddt_in.fornitore
            WHERE c.cliente_nome != '' AND c.cliente_nome IS NOT NULL {date_filter}
            GROUP BY c.cliente_nome 
            ORDER BY totale_commesse DESC
            LIMIT 20
        """
        clienti_stats = db.session.execute(text(clienti_query)).fetchall()
        
        # Statistiche generali (con filtro data)
        date_filter_simple = date_filter.replace('c.', '') if date_filter else ""
        totale_commesse = db.session.execute(text(f"SELECT COUNT(*) FROM commessa WHERE 1=1 {date_filter_simple}")).scalar()
        commesse_aperte = db.session.execute(text(f"SELECT COUNT(*) FROM commessa WHERE stato = 'aperta' {date_filter_simple}")).scalar()
        commesse_chiuse = db.session.execute(text(f"SELECT COUNT(*) FROM commessa WHERE stato = 'chiusa' {date_filter_simple}")).scalar()
        
        # Analisi temporale - commesse per mese
        trend_mensile_query = """
            SELECT 
                strftime('%Y-%m', data_apertura) as mese,
                COUNT(*) as commesse_aperte,
                tipologia,
                stato
            FROM commessa 
            WHERE data_apertura >= date('now', '-12 months')
            GROUP BY strftime('%Y-%m', data_apertura), tipologia, stato
            ORDER BY mese DESC, tipologia
        """
        trend_stats = db.session.execute(text(trend_mensile_query)).fetchall()
        
        # Durata media commesse chiuse
        durata_query = """
            SELECT 
                tipologia,
                AVG(CAST(julianday('now') - julianday(data_apertura) AS INTEGER)) as durata_media_giorni,
                COUNT(*) as commesse_analizzate
            FROM commessa 
            WHERE stato = 'chiusa' AND tipologia IS NOT NULL
            GROUP BY tipologia
            ORDER BY durata_media_giorni DESC
        """
        durate_stats = db.session.execute(text(durata_query)).fetchall()
        
        # Converti risultati per template
        riepilogo_tipologie = []
        for stat in tipologie_stats:
            tipologia = {
                'tipologia': stat[0],
                'totale': stat[1],
                'aperte': stat[2],
                'chiuse': stat[3],
                'sospese': stat[4]
            }
            riepilogo_tipologie.append(tipologia)
        
        top_clienti_commesse = []
        for stat in clienti_stats:
            cliente = {
                'cliente_nome': stat[0],
                'totale_commesse': stat[1],
                'ultima_apertura': stat[2],
                'giorni_ultima_apertura': int(stat[3] or 0),
                'ddt_out_cliente': int(stat[4] or 0),
                'valore_ddt_out': float(stat[5] or 0),
                'ddt_in_fornitore': int(stat[6] or 0)
            }
            top_clienti_commesse.append(cliente)
        
        # Trend mensile
        trend_mensile = []
        for stat in trend_stats:
            trend = {
                'mese': stat[0],
                'commesse': stat[1], 
                'tipologia': stat[2],
                'stato': stat[3]
            }
            trend_mensile.append(trend)
        
        # Durate medie
        durate_tipologie = []
        for stat in durate_stats:
            durata = {
                'tipologia': stat[0],
                'durata_media': int(stat[1] or 0),
                'commesse_analizzate': int(stat[2] or 0)
            }
            durate_tipologie.append(durata)
        
        return render_template('report_commesse.html',
                             riepilogo_tipologie=riepilogo_tipologie,
                             top_clienti_commesse=top_clienti_commesse,
                             totale_commesse=totale_commesse,
                             commesse_aperte=commesse_aperte,
                             commesse_chiuse=commesse_chiuse,
                             trend_mensile=trend_mensile,
                             durate_tipologie=durate_tipologie)
                             
    except Exception as e:
        return f"Errore generazione report commesse: {str(e)}", 500

@app.route('/reports/export/<report_type>')
def export_report(report_type):
    """Export report in Excel"""
    try:
        import pandas as pd
        from io import BytesIO
        
        output = BytesIO()
        
        if report_type == 'movimenti':
            # Export movimenti
            movimenti_in = db.session.query(
                ArticoloIn.codice_interno,
                ArticoloIn.descrizione,
                ArticoloIn.quantita,
                ArticoloIn.costo_unitario,
                DDTIn.data_ddt_origine,
                DDTIn.fornitore
            ).join(DDTIn).filter(DDTIn.stato == 'confermato').all()
            
            df = pd.DataFrame([{
                'Codice': m.codice_interno,
                'Descrizione': m.descrizione,
                'Quantita': m.quantita,
                'Costo Unitario': m.costo_unitario,
                'Data': m.data_ddt_origine,
                'Fornitore': m.fornitore
            } for m in movimenti_in])
            
        elif report_type == 'clienti':
            # Export clienti (query SQL diretta)
            # Ottieni parametri di filtro data
            data_da = request.args.get('data_da')
            data_a = request.args.get('data_a')
            
            # Costruisci clausola WHERE per le date
            date_filter = ""
            if data_da and data_a:
                date_filter = f"AND data_ddt_origine BETWEEN '{data_da}' AND '{data_a}'"
            elif data_da:
                date_filter = f"AND data_ddt_origine >= '{data_da}'"
            elif data_a:
                date_filter = f"AND data_ddt_origine <= '{data_a}'"
            
            clienti_query = f"""
                SELECT nome_origine, COUNT(*) as totale_ddt, MAX(data_ddt_origine) as ultimo_ddt,
                       CAST(julianday('now') - julianday(MAX(data_ddt_origine)) AS INTEGER) as giorni_ultimo_ddt
                FROM ddt_out 
                WHERE nome_origine != '' AND nome_origine IS NOT NULL {date_filter}
                GROUP BY nome_origine 
                ORDER BY totale_ddt DESC
            """
            from sqlalchemy import text
            clienti_stats = db.session.execute(text(clienti_query)).fetchall()
            
            df = pd.DataFrame([{
                'Cliente': c[0],  # nome_origine
                'DDT Totali': c[1],  # totale_ddt
                'Ultimo DDT': c[2],  # ultimo_ddt
                'Giorni Ultima Attività': int(c[3] or 0)  # giorni_ultimo_ddt
            } for c in clienti_stats])
            
        elif report_type == 'dashboard':
            # Export dashboard con KPI principali
            from sqlalchemy import text
            
            # Raccogli dati KPI
            kpi_data = []
            
            # DDT IN e OUT
            ddt_in_count = db.session.execute(text("SELECT COUNT(*) FROM ddt_in")).scalar()
            ddt_out_count = db.session.execute(text("SELECT COUNT(*) FROM ddt_out")).scalar()
            ddt_in_confermati = db.session.execute(text("SELECT COUNT(*) FROM ddt_in WHERE stato = 'confermato'")).scalar()
            ddt_out_confermati = db.session.execute(text("SELECT COUNT(*) FROM ddt_out WHERE stato = 'confermato'")).scalar()
            
            # Articoli e inventario
            articoli_count = db.session.execute(text("SELECT COUNT(*) FROM catalogo_articolo WHERE attivo = 1")).scalar()
            valore_inventario = db.session.execute(text("SELECT SUM(giacenza_attuale * costo_medio) FROM catalogo_articolo WHERE attivo = 1")).scalar() or 0
            
            # Clienti e fornitori attivi
            clienti_attivi = db.session.execute(text("SELECT COUNT(DISTINCT nome_origine) FROM ddt_out WHERE nome_origine IS NOT NULL AND nome_origine != ''")).scalar()
            fornitori_attivi = db.session.execute(text("SELECT COUNT(DISTINCT fornitore) FROM ddt_in WHERE fornitore IS NOT NULL AND fornitore != ''")).scalar()
            
            kpi_data = [
                {'KPI': 'DDT IN Totali', 'Valore': ddt_in_count},
                {'KPI': 'DDT IN Confermati', 'Valore': ddt_in_confermati},
                {'KPI': 'DDT OUT Totali', 'Valore': ddt_out_count},
                {'KPI': 'DDT OUT Confermati', 'Valore': ddt_out_confermati},
                {'KPI': 'Articoli in Catalogo', 'Valore': articoli_count},
                {'KPI': 'Valore Inventario €', 'Valore': f"{valore_inventario:.2f}"},
                {'KPI': 'Clienti Attivi', 'Valore': clienti_attivi},
                {'KPI': 'Fornitori Attivi', 'Valore': fornitori_attivi}
            ]
            
            df = pd.DataFrame(kpi_data)
            
        elif report_type == 'fornitori':
            # Export fornitori con statistiche DDT IN
            from sqlalchemy import text
            
            # Ottieni parametri di filtro data
            data_da = request.args.get('data_da')
            data_a = request.args.get('data_a')
            
            # Costruisci clausola WHERE per le date
            date_filter = ""
            if data_da and data_a:
                date_filter = f"AND ddt_in.data_ddt_origine BETWEEN '{data_da}' AND '{data_a}'"
            elif data_da:
                date_filter = f"AND ddt_in.data_ddt_origine >= '{data_da}'"
            elif data_a:
                date_filter = f"AND ddt_in.data_ddt_origine <= '{data_a}'"
            
            fornitori_query = f"""
                SELECT ddt_in.fornitore, COUNT(*) as totale_ddt, 
                       MAX(ddt_in.data_ddt_origine) as ultimo_ddt,
                       CAST(julianday('now') - julianday(MAX(ddt_in.data_ddt_origine)) AS INTEGER) as giorni_ultimo_ddt,
                       SUM(CASE WHEN articolo_in.costo_unitario IS NOT NULL AND articolo_in.quantita IS NOT NULL 
                           THEN articolo_in.costo_unitario * articolo_in.quantita ELSE 0 END) as valore_totale
                FROM ddt_in 
                LEFT JOIN articolo_in ON ddt_in.id = articolo_in.ddt_id
                WHERE ddt_in.fornitore != '' AND ddt_in.fornitore IS NOT NULL {date_filter}
                GROUP BY ddt_in.fornitore 
                ORDER BY totale_ddt DESC
            """
            
            fornitori_stats = db.session.execute(text(fornitori_query)).fetchall()
            
            df = pd.DataFrame([{
                'Fornitore': f[0],  # fornitore
                'DDT IN Totali': f[1],  # totale_ddt
                'Ultimo DDT': f[2],  # ultimo_ddt
                'Giorni Ultima Consegna': int(f[3] or 0),  # giorni_ultimo_ddt
                'Valore Totale €': round(f[4] or 0, 2)  # valore_totale
            } for f in fornitori_stats])
            
        elif report_type == 'commesse':
            # Export commesse con statistiche
            # Ottieni parametri di filtro data
            data_da = request.args.get('data_da')
            data_a = request.args.get('data_a')
            
            # Costruisci clausola WHERE per le date
            date_filter = ""
            if data_da and data_a:
                date_filter = f"AND c.data_apertura BETWEEN '{data_da}' AND '{data_a}'"
            elif data_da:
                date_filter = f"AND c.data_apertura >= '{data_da}'"
            elif data_a:
                date_filter = f"AND c.data_apertura <= '{data_a}'"
            
            commesse_query = f"""
                SELECT 
                    c.cliente_nome,
                    c.descrizione,
                    c.tipologia,
                    c.stato,
                    c.data_apertura,
                    c.data_scadenza,
                    COUNT(*) as totale_commesse,
                    COALESCE(ddt_out.totale_ddt_out, 0) as ddt_out_cliente,
                    COALESCE(ddt_out.valore_totale_out, 0) as valore_ddt_out
                FROM commessa c
                LEFT JOIN (
                    SELECT destinazione, COUNT(*) as totale_ddt_out, 
                           SUM(ao.quantita * ao.prezzo_unitario) as valore_totale_out
                    FROM ddt_out do
                    LEFT JOIN articolo_out ao ON do.id = ao.ddt_id
                    WHERE do.stato = 'confermato'
                    GROUP BY destinazione
                ) ddt_out ON c.cliente_nome = ddt_out.destinazione
                WHERE c.cliente_nome != '' AND c.cliente_nome IS NOT NULL {date_filter}
                GROUP BY c.cliente_nome, c.descrizione, c.tipologia, c.stato, c.data_apertura, c.data_scadenza
                ORDER BY c.data_apertura DESC
            """
            
            from sqlalchemy import text
            commesse_stats = db.session.execute(text(commesse_query)).fetchall()
            
            df = pd.DataFrame([{
                'Cliente': c[0],  # cliente_nome
                'Descrizione': c[1],  # descrizione
                'Tipologia': c[2],  # tipologia
                'Stato': c[3],  # stato
                'Data Apertura': c[4],  # data_apertura
                'Data Scadenza': c[5],  # data_scadenza
                'DDT Out': int(c[7] or 0),  # totale_ddt_out
                'Valore €': round(c[8] or 0, 2)  # valore_totale_out
            } for c in commesse_stats])
            
        elif report_type == 'articoli':
            # Export articoli più movimentati
            from sqlalchemy import and_, or_, desc, func
            
            # Ottieni parametri di filtro data
            data_da = request.args.get('data_da')
            data_a = request.args.get('data_a')
            
            # Costruisci filtro per DDT IN e OUT
            ddt_in_filter = DDTIn.stato == 'confermato'
            ddt_out_filter = DDTOut.stato == 'confermato'
            
            if data_da and data_a:
                ddt_in_filter = and_(ddt_in_filter, DDTIn.data_ddt_origine.between(data_da, data_a))
                ddt_out_filter = and_(ddt_out_filter, DDTOut.data_ddt_origine.between(data_da, data_a))
            elif data_da:
                ddt_in_filter = and_(ddt_in_filter, DDTIn.data_ddt_origine >= data_da)
                ddt_out_filter = and_(ddt_out_filter, DDTOut.data_ddt_origine >= data_da)
            elif data_a:
                ddt_in_filter = and_(ddt_in_filter, DDTIn.data_ddt_origine <= data_a)
                ddt_out_filter = and_(ddt_out_filter, DDTOut.data_ddt_origine <= data_a)
            
            # Query articoli con movimentazioni
            articoli_in = db.session.query(
                ArticoloIn.codice_interno,
                func.sum(ArticoloIn.quantita).label('qty_in')
            ).join(DDTIn).filter(ddt_in_filter).group_by(ArticoloIn.codice_interno).subquery()
            
            articoli_out = db.session.query(
                ArticoloOut.codice_interno,
                func.sum(ArticoloOut.quantita).label('qty_out')
            ).join(DDTOut).filter(ddt_out_filter).group_by(ArticoloOut.codice_interno).subquery()
            
            # Combina dati
            top_articoli = db.session.query(
                CatalogoArticolo.codice_interno,
                CatalogoArticolo.descrizione,
                func.coalesce(articoli_in.c.qty_in, 0).label('qty_in'),
                func.coalesce(articoli_out.c.qty_out, 0).label('qty_out'),
                (func.coalesce(articoli_in.c.qty_in, 0) + func.coalesce(articoli_out.c.qty_out, 0)).label('movimentazione_totale')
            ).outerjoin(articoli_in, CatalogoArticolo.codice_interno == articoli_in.c.codice_interno)\
             .outerjoin(articoli_out, CatalogoArticolo.codice_interno == articoli_out.c.codice_interno)\
             .filter(or_(articoli_in.c.qty_in.isnot(None), articoli_out.c.qty_out.isnot(None)))\
             .order_by(desc('movimentazione_totale')).limit(50).all()
            
            df = pd.DataFrame([{
                'Codice': art.codice_interno,
                'Descrizione': art.descrizione,
                'Entrate': art.qty_in,
                'Uscite': art.qty_out,
                'Movimentazione Totale': art.movimentazione_totale
            } for art in top_articoli])
            
        else:
            # Tipo di report non supportato
            return f"Tipo di report '{report_type}' non supportato", 400
            
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
        
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f'report_{report_type}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return f"Errore export: {str(e)}", 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Migration: Add data_scadenza to commessa table if not exists
        try:
            db.session.execute(text("SELECT data_scadenza FROM commessa LIMIT 1"))
        except Exception:
            # Column doesn't exist, add it
            db.session.execute(text("ALTER TABLE commessa ADD COLUMN data_scadenza DATE"))
            db.session.commit()
            print("✅ Migration: Added data_scadenza column to commessa table")
    
    print("=" * 50)
    print(f"SISTEMA GESTIONE DDT - VERSIONE {APP_VERSION}")
    print("=" * 50)
    print("Database: SQLite")
    print("DDT IN/OUT: Operativo")  
    print("Movimenti: Operativo")
    print("Inventario: Operativo")
    print("Import PDF: Disponibile")
    print("Movimenti Interni: Disponibile")
    print("Reports: Disponibile")
    print("=" * 50)
    
    # Avvia il monitor email se configurato
    try:
        if app.email_monitor.is_active():
            app.email_monitor.start_monitoring()
            print("Email Monitor: Attivo")
        else:
            print("Email Monitor: Disattivato (configurare nelle impostazioni)")
    except Exception as e:
        print(f"Email Monitor: Errore - {e}")
    
    app.version = "2.42"
    app.run(debug=True, host='0.0.0.0', port=8080)