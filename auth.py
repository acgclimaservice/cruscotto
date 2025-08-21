from flask import session, request, redirect, url_for, jsonify, flash
from functools import wraps
import hashlib
import secrets

class AuthManager:
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        app.config.setdefault('AUTH_REQUIRED', True)
        app.config.setdefault('DEFAULT_USER', 'admin')
        app.config.setdefault('DEFAULT_PASSWORD', 'admin123')
    
    @staticmethod
    def hash_password(password, salt=None):
        if salt is None:
            salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt.encode('utf-8'), 
                                          100000)
        return f"{salt}:{password_hash.hex()}"
    
    @staticmethod
    def verify_password(password, hashed):
        try:
            salt, hash_hex = hashed.split(':')
            password_hash = hashlib.pbkdf2_hmac('sha256',
                                              password.encode('utf-8'),
                                              salt.encode('utf-8'),
                                              100000)
            return password_hash.hex() == hash_hex
        except:
            return False
    
    @staticmethod
    def login_user(username):
        session['logged_in'] = True
        session['username'] = username
        session.permanent = True
    
    @staticmethod
    def logout_user():
        session.clear()
    
    @staticmethod
    def is_authenticated():
        return session.get('logged_in', False)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthManager.is_authenticated():
            if request.is_json:
                return jsonify({'error': 'Autenticazione richiesta'}), 401
            flash('Accesso richiesto')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_input(required_fields):
    """Decorator per validazione input"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.form if request.form else request.json
            if not data:
                return jsonify({'error': 'Dati richiesti'}), 400
            
            for field in required_fields:
                if field not in data or not data[field].strip():
                    return jsonify({'error': f'Campo {field} richiesto'}), 400
            
            # Sanitize input
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = value.strip()[:500]  # Limit length
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Routes autenticazione
from flask import Blueprint, render_template

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Default credentials (in produzione usare database)
    if username == 'admin' and password == 'admin123':
        AuthManager.login_user(username)
        return redirect(url_for('dashboard'))
    
    flash('Credenziali non valide')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    AuthManager.logout_user()
    flash('Disconnesso con successo')
    return redirect(url_for('auth.login'))