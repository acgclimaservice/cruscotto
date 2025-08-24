# Istruzioni Finali - Fix Sistema AI su PythonAnywhere

## Problema Identificato
Le librerie AI sono installate ma non visibili dall'applicazione web perché il path Python dell'app non include le librerie utente.

## Soluzione

### 1. Aggiorna da GitHub
```bash
cd ~/cruscotto
git pull origin main
```

### 2. Esegui script installer
```bash
python3.9 fix_pythonanywhere_packages.py
```

### 3. Se lo script fallisce, installa manualmente
```bash
# Prova installazione globale (richiede permessi)
python3.9 -m pip install anthropic==0.25.0
python3.9 -m pip install google-generativeai==0.5.0
python3.9 -m pip install PyMuPDF==1.23.0

# Se fallisce, usa --user
python3.9 -m pip install --user anthropic==0.25.0
python3.9 -m pip install --user google-generativeai==0.5.0  
python3.9 -m pip install --user PyMuPDF==1.23.0
```

### 4. Modifica file WSGI (IMPORTANTE)
Vai su **Files** > **Web** > **WSGI configuration file** e sostituisci tutto con:

```python
import sys
import os
import site

# Aggiungi path librerie utente Python
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)

# Directory progetto
path = '/home/acgclimaservice/cruscotto'
os.chdir(path)
if path not in sys.path:
    sys.path.insert(0, path)

# Carica environment
from dotenv import load_dotenv
load_dotenv()

# Importa app
from app import app as application
```

### 5. Riavvia webapp
```bash
touch /var/www/acgclimaservice_pythonanywhere_com_wsgi.py
```

### 6. Verifica finale
Vai su: `https://acgclimaservice.pythonanywhere.com/debug-system`

Dovrebbe mostrare:
- ✅ anthropic: [version]
- ✅ google-generativeai: [version]  
- ✅ PyMuPDF: [version]

## Troubleshooting

### Se ancora non funziona:
```bash
# Verifica path Python
python3.9 -c "import site; print(site.getusersitepackages())"

# Verifica installazioni
python3.9 -c "import anthropic; import google.generativeai; print('AI OK')"
```

### Se ci sono problemi di spazio disco:
```bash
# Pulisci cache pip
python3.9 -m pip cache purge

# Rimuovi installazioni doppie
rm -rf ~/.local/lib/python3.11/
```

## Note Importanti
- Il webapp usa Python 3.9, non 3.11
- Le librerie devono essere nel path dell'applicazione web
- Il file .env deve essere nella directory del progetto
- Dopo ogni modifica WSGI, riavvia l'app