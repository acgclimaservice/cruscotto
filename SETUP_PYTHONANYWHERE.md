# Setup PythonAnywhere - Sistema Parsing AI

## 1. Sincronizza da GitHub
```bash
cd ~/cruscotto
git fetch origin
git reset --hard origin/main
git clean -fd
```

## 2. Installa dipendenze AI
```bash
pip3.11 install --user -r requirements.txt
```

## 3. Crea file .env con le chiavi API
**IMPORTANTE**: Devi copiare il file `.env` dalla versione locale o inserire le tue chiavi API.

```bash
cat > .env << 'EOF'
# Configurazione Sistema
SECRET_KEY=your-secret-key-here

# API Keys per AI Parsing (SOSTITUISCI CON LE TUE CHIAVI)
CLAUDE_API_KEY=sk-ant-api03-YOUR_CLAUDE_KEY_HERE
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_ANTHROPIC_KEY_HERE
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE
GEMINI_MODEL=gemini-1.5-pro

# Database - Path per PythonAnywhere
DATABASE_URL=sqlite:///ddt_database.db
EOF
```

**NOTA**: Le chiavi API reali sono nel file `.env` locale e devono essere copiate manualmente su PythonAnywhere per sicurezza.

## 4. Inizializza database
```bash
python3.11 init_db_pythonanywhere.py
```

## 5. Riavvia webapp
```bash
touch /var/www/acgclimaservice_pythonanywhere_com_wsgi.py
```

## 6. Verifica Status AI
Vai su `/ddt/in/nuovo` e verifica che lo status AI mostri:
- ✅ Claude API: Attivo
- ✅ Gemini API: Attivo

## Troubleshooting

### Se lo status AI è ancora "Non disponibile":
```bash
# Verifica installazione pacchetti
pip3.11 list | grep -E "(anthropic|google)"

# Controlla log errori
tail -f ~/mysite/error.log

# Riavvia webapp
touch /var/www/acgclimaservice_pythonanywhere_com_wsgi.py
```

### Se ci sono errori di permessi:
```bash
chmod +x ~/cruscotto/*.py
chmod 644 ~/cruscotto/.env
```