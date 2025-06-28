"""
Utilidades para validaciones y funciones auxiliares
"""
import re
import bcrypt

def validate_email(email):
    """Validar formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validar nombre de usuario"""
    if not username or len(username) < 3:
        return False, "El nombre de usuario debe tener al menos 3 caracteres"
    
    if len(username) > 50:
        return False, "El nombre de usuario no puede tener más de 50 caracteres"
    
    # Solo permitir letras, números y guiones bajos
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "El nombre de usuario solo puede contener letras, números y guiones bajos"
    
    return True, ""

def validate_password(password):
    """Validar contraseña"""
    if not password or len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres"
    
    if len(password) > 255:
        return False, "La contraseña es demasiado larga"
    
    return True, ""

def hash_password(password):
    """Crear hash de contraseña"""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    # Convertir bytes a string para almacenar en MySQL
    return hashed.decode('utf-8')

def check_password(password, hashed):
    """Verificar contraseña"""
    # Si hashed es un string (de la BD), convertirlo a bytes
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def is_logged_in():
    """Verificar si el usuario está logueado"""
    from flask import session
    return session.get('logged_in', False)

def get_current_user():
    """Obtener información del usuario actual"""
    from flask import session
    if is_logged_in():
        return {
            'id': session.get('user_id'),
            'usuario': session.get('usuario'),
            'correo': session.get('correo'),
            'is_admin': session.get('is_admin', False)
        }
    return None

def require_login():
    """Decorador para requerir login"""
    from functools import wraps
    from flask import redirect, url_for, request
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not is_logged_in():
                return redirect(url_for('auth.login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_admin():
    """Decorador para requerir permisos de administrador"""
    from functools import wraps
    from flask import redirect, url_for, request, flash
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()
            if not current_user:
                flash('Necesitas iniciar sesión para acceder a esta página', 'error')
                return redirect(url_for('auth.login', next=request.url))
            
            if not current_user.get('is_admin', False):
                flash('No tienes permisos para acceder a esta página', 'error')
                return redirect(url_for('blog.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def is_admin():
    """Verificar si el usuario actual es administrador"""
    current_user = get_current_user()
    return current_user and current_user.get('is_admin', False)
