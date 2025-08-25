#!/bin/bash
# Script per risolvere conflitto git e applicare fix DDT page

echo "🔄 Risolvendo conflitto git..."
git stash

echo "📥 Scaricando modifiche da GitHub..."
git pull origin main

echo "🗑️ Rimuovendo modifiche locali problematiche..."
git stash drop

echo "🔄 Riavviando webapp..."
touch /var/www/acgclimaservice_pythonanywhere_com_wsgi.py

echo "✅ Fix completato! La pagina DDT dovrebbe ora funzionare."
echo "🌐 Testa su: https://acgclimaservice.pythonanywhere.com/ddt/in/nuovo"