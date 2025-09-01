#!/usr/bin/env python3
"""
File WSGI per PythonAnywhere
Questo file deve essere copiato e configurato nella sezione Web di PythonAnywhere
"""

import sys
import os
import site

# Aggiungi path librerie utente Python per PythonAnywhere
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)

# Directory progetto su PythonAnywhere per acgclimaservice
path = '/home/acgclimaservice/cruscotto'
os.chdir(path)
if path not in sys.path:
    sys.path.insert(0, path)

# Carica variabili d'ambiente
from dotenv import load_dotenv
load_dotenv()

# Importa l'applicazione Flask
from app import app as application

if __name__ == "__main__":
    application.run()