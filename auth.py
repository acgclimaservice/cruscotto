# auth.py - Modulo di autenticazione per CRUSCOTTO
from functools import wraps
from flask import session, request, redirect, url_for, jsonify, flash
import re


def login_required(f):
    """Decorator per richiedere l'autenticazione"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Per ora, permettiamo l'accesso senza autenticazione
        # Puoi modificare questo comportamento in seguito
        return f(*args, **kwargs)
    return decorated_function


def validate_input(data, required_fields=None, max_lengths=None):
    """
    Valida i dati di input
    
    Args:
        data: dizionario con i dati da validare
        required_fields: lista dei campi obbligatori
        max_lengths: dizionario con lunghezze massime per campo
    
    Returns:
        tuple: (is_valid, errors_list)
    """
    errors = []
    
    if required_fields:
        for field in required_fields:
            if field not in data or not data.get(field, '').strip():
                errors.append(f"Il campo '{field}' è obbligatorio")
    
    if max_lengths:
        for field, max_len in max_lengths.items():
            if field in data and len(str(data.get(field, ''))) > max_len:
                errors.append(f"Il campo '{field}' non può superare {max_len} caratteri")
    
    # Validazione email se presente
    if 'email' in data and data['email']:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            errors.append("Formato email non valido")
    
    # Validazione codice fiscale/partita IVA se presente
    if 'codice_fiscale' in data and data['codice_fiscale']:
        cf = data['codice_fiscale'].replace(' ', '').upper()
        if len(cf) not in [11, 16]:
            errors.append("Codice fiscale/P.IVA deve essere di 11 o 16 caratteri")
    
    return len(errors) == 0, errors


# Funzioni di supporto per l'autenticazione (future implementazioni)
def create_user(username, password, email=None):
    """Crea un nuovo utente (da implementare)"""
    pass


def authenticate_user(username, password):
    """Autentica un utente (da implementare)"""
    pass


def get_current_user():
    """Ottieni l'utente corrente dalla sessione (da implementare)"""
    return None


def logout_user():
    """Logout dell'utente corrente (da implementare)"""
    session.clear()