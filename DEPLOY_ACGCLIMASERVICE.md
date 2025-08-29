# 🚀 DEPLOYMENT PERSONALIZZATO - ACGCLIMASERVICE

## 📍 **I TUOI DATI:**
- **Account**: acgclimaservice  
- **URL finale**: https://acgclimaservice.pythonanywhere.com
- **Directory progetto**: `/home/acgclimaservice/cruscotto`

---

## 🔧 **STEP 1: CARICA I FILE**

### Opzione A - Upload ZIP (Veloce):
1. Comprimi la cartella `CRUSCOTTO_1.2` in un file ZIP
2. Login su https://www.pythonanywhere.com/user/acgclimaservice/
3. Vai su **Files** > **Upload a file**
4. Carica il ZIP nella home directory (`/home/acgclimaservice/`)
5. Estrai con: `unzip CRUSCOTTO_1.2.zip`
6. Rinomina: `mv CRUSCOTTO_1.2 cruscotto`

---

## 🔧 **STEP 2: CONFIGURA AMBIENTE**

### 2.1 Apri **Bash Console** e esegui:

```bash
# Vai nella directory del progetto
cd ~/cruscotto

# Installa dipendenze Python
pip3.10 install --user -r requirements.txt

# Crea file .env con le tue chiavi API
cp .env.example .env
nano .env
```

### 2.2 Nel file `.env` inserisci:
```bash
# Configurazione Sistema
SECRET_KEY=acgclima-secret-key-2025

# API Keys per AI Parsing (INSERISCI LE TUE CHIAVI REALI)
CLAUDE_API_KEY=sk-ant-api03-YOUR_REAL_CLAUDE_KEY
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_REAL_CLAUDE_KEY  
GEMINI_API_KEY=YOUR_REAL_GEMINI_KEY
GOOGLE_API_KEY=YOUR_REAL_GEMINI_KEY
GEMINI_MODEL=gemini-2.0-flash-exp

# Database per PythonAnywhere
DATABASE_URL=sqlite:///ddt_database.db
```

### 2.3 Inizializza database:
```bash
python3.10 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('✅ Database creato con successo!')
"
```

---

## 🔧 **STEP 3: CONFIGURA WEB APP**

### 3.1 Crea Web App:
1. Vai su **Web** tab
2. Se non hai app, click **Add a new web app**
3. Se hai già un'app, puoi riconfigurare quella esistente
4. Scegli **Manual configuration**  
5. Python version: **3.10**

### 3.2 Configura WSGI File:
1. Nel tab **Web**, trova **WSGI configuration file**
2. Click sul link del file per modificarlo
3. **CANCELLA TUTTO** e inserisci questo codice:

```python
import sys
import os
import site

# Aggiungi path librerie utente Python
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)

# Directory progetto per acgclimaservice
path = '/home/acgclimaservice/cruscotto'
os.chdir(path)
if path not in sys.path:
    sys.path.insert(0, path)

# Carica variabili d'ambiente
from dotenv import load_dotenv
load_dotenv()

# Importa applicazione Flask
from app import app as application
```

### 3.3 Configura Static Files:
Nel tab **Web**, sezione **Static files**:
- **URL**: `/static/`
- **Directory**: `/home/acgclimaservice/cruscotto/static/`

---

## 🔧 **STEP 4: AVVIO E TEST**

### 4.1 Riavvia l'app:
1. Nel tab **Web**, click **Reload acgclimaservice.pythonanywhere.com**
2. Aspetta 30-60 secondi per il caricamento

### 4.2 Apri l'app:
**https://acgclimaservice.pythonanywhere.com**

### 4.3 Test funzionalità:
- ✅ Dashboard si apre correttamente
- ✅ DDT IN/OUT funzionano  
- ✅ Clienti e Fornitori visibili
- ✅ Reports accessibili

---

## 🔧 **STEP 5: IMPORT DATI INIZIALI**

Se hai i file Excel di clienti/fornitori:

```bash
cd ~/cruscotto

# Import clienti (se hai il file)
python3.10 import_clienti_excel.py

# Import fornitori (se hai il file)  
python3.10 import_fornitori_excel.py

# Import mastrini (se hai il file)
python3.10 import_mastrini_excel.py
```

---

## 🛠️ **TROUBLESHOOTING SPECIFICO**

### Errore: "No module named 'anthropic'"
```bash
pip3.10 install --user --upgrade anthropic google-generativeai PyMuPDF
touch /var/www/acgclimaservice_pythonanywhere_com_wsgi.py
```

### Errore database:
```bash
cd ~/cruscotto
rm -f ddt_database.db  # Rimuovi se esiste
python3.10 -c "from app import app, db; app.app_context().push(); db.create_all(); print('DB ricreato!')"
```

### Check log errori:
```bash
tail -f /var/www/acgclimaservice_pythonanywhere_com_error.log
```

---

## 📊 **MONITORAGGIO**

### URL di verifica:
- **App principale**: https://acgclimaservice.pythonanywhere.com
- **Dashboard**: https://acgclimaservice.pythonanywhere.com/
- **DDT Import**: https://acgclimaservice.pythonanywhere.com/ddt-import

### Log files:
- **Errori**: `/var/www/acgclimaservice_pythonanywhere_com_error.log`  
- **Accessi**: `/var/www/acgclimaservice_pythonanywhere_com_access.log`

---

## 🎉 **COMPLETAMENTO**

Una volta completato, avrai:

✅ **Sistema DDT v2.5** online 24/7  
✅ **URL**: https://acgclimaservice.pythonanywhere.com  
✅ **Accessibile da qualsiasi dispositivo**  
✅ **Database persistente e sicuro**  
✅ **Parsing AI funzionante** (se configurato)  
✅ **Backup automatici PythonAnywhere**

### Costo: €5/mese - Piano Hacker PythonAnywhere

### Prossimi step (opzionali):
- Sistema login/autenticazione
- Dominio personalizzato (es: ddt.acgclima.it)  
- Backup automatici avanzati