from flask import session, request, redirect, url_for, jsonify
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Per ora disabilitato per test
        return f(*args, **kwargs)
    return decorated_function

def validate_input(required_fields):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.form if request.form else request.json
            if not data:
                return jsonify({'error': 'Dati richiesti'}), 400
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Campo {field} richiesto'}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator
