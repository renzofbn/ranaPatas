"""
Utilidades para validaciones y funciones auxiliares
"""
import re
import bcrypt
import secrets
import hashlib
from datetime import datetime, timedelta
from flask import request

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
    from flask import session, request
    
    # Usar get_current_user que ya tiene toda la lógica de validación
    current_user = get_current_user()
    return current_user is not None

def get_current_user():
    """Obtener información del usuario actual"""
    from flask import session, request
    
    # Siempre validar primero con token si existe (más confiable)
    token = request.cookies.get('session_token')
    if token:
        user_data = validate_session_token(token)
        if user_data:
            # Actualizar session con los datos del token
            session['user_id'] = user_data['id']
            session['usuario'] = user_data['usuario']
            session['correo'] = user_data['correo']
            session['is_admin'] = user_data['is_admin']
            session['rol'] = user_data.get('rol', 1)
            session['logged_in'] = True
            return user_data
        else:
            # Token inválido, limpiar sesión
            session.clear()
            return None
    
    # Si no hay token, verificar session tradicional
    if session.get('logged_in', False):
        # Verificar que el usuario sigue teniendo permisos válidos
        user_id = session.get('user_id')
        if user_id:
            # Re-validar el usuario contra la base de datos
            from db_connector import get_mysql
            try:
                mysql = get_mysql()
                cur = mysql.connection.cursor()
                cur.execute("""
                    SELECT id, usuario, correo, isAdmin, rol 
                    FROM usuarios 
                    WHERE id = %s AND estado_aprobacion = 'aprobado'
                """, (user_id,))
                user_db = cur.fetchone()
                cur.close()
                
                if user_db:
                    # Actualizar datos de sesión con info actualizada de BD
                    user_data = {
                        'id': user_db[0],
                        'usuario': user_db[1],
                        'correo': user_db[2],
                        'is_admin': bool(user_db[3]),
                        'rol': user_db[4] or 1
                    }
                    # Actualizar session
                    session['usuario'] = user_data['usuario']
                    session['correo'] = user_data['correo']
                    session['is_admin'] = user_data['is_admin']
                    session['rol'] = user_data['rol']
                    return user_data
                else:
                    # Usuario ya no válido, limpiar sesión
                    session.clear()
                    return None
                    
            except Exception as e:
                print(f"Error al re-validar usuario: {e}")
                session.clear()
                return None
        
        return {
            'id': session.get('user_id'),
            'usuario': session.get('usuario'),
            'correo': session.get('correo'),
            'is_admin': session.get('is_admin', False),
            'rol': session.get('rol', 1)
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

# ===============================
# FUNCIONES DE MANEJO DE SESIONES
# ===============================

def generate_session_token():
    """Generar un token de sesión único"""
    return secrets.token_urlsafe(32)

def hash_token(token):
    """Crear hash del token para almacenar en BD"""
    return hashlib.sha256(token.encode()).hexdigest()

def create_session(user_id, remember_me=False):
    """Crear una nueva sesión para el usuario"""
    from db_connector import get_mysql
    
    # Generar token
    token = generate_session_token()
    token_hash = hash_token(token)
    
    # Calcular fecha de expiración
    if remember_me:
        expires_at = datetime.now() + timedelta(days=30)  # 30 días
    else:
        expires_at = datetime.now() + timedelta(hours=24)  # 24 horas
    
    # Obtener información del request
    ip_address = request.remote_addr if request else None
    user_agent = request.headers.get('User-Agent', '') if request else ''
    
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Insertar nueva sesión
        cur.execute("""
            INSERT INTO sesiones (usuario_id, token, fecha_expiracion, ip_address, user_agent, activa)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, token_hash, expires_at, ip_address, user_agent, True))
        
        # Actualizar último login del usuario
        cur.execute("UPDATE usuarios SET ultimo_login = %s WHERE id = %s", 
                   (datetime.now(), user_id))
        
        mysql.connection.commit()
        cur.close()
        
        return token
        
    except Exception as e:
        print(f"Error al crear sesión: {e}")
        return None

def validate_session_token(token):
    """Validar token de sesión y retornar información del usuario"""
    from db_connector import get_mysql
    
    if not token:
        return None
    
    token_hash = hash_token(token)
    
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Buscar sesión activa y no expirada
        cur.execute("""
            SELECT s.usuario_id, s.fecha_expiracion, u.usuario, u.correo, u.isAdmin, u.rol
            FROM sesiones s
            JOIN usuarios u ON s.usuario_id = u.id
            WHERE s.token = %s AND s.activa = 1 AND s.fecha_expiracion > %s
              AND u.estado_aprobacion = 'aprobado'
        """, (token_hash, datetime.now()))
        
        session_data = cur.fetchone()
        cur.close()
        
        if session_data:
            return {
                'id': session_data[0],
                'usuario': session_data[2],
                'correo': session_data[3],
                'is_admin': bool(session_data[4]),
                'rol': session_data[5] or 1
            }
        
        return None
        
    except Exception as e:
        print(f"Error al validar sesión: {e}")
        return None

def invalidate_session(token, motivo='logout_manual'):
    """Invalidar una sesión específica"""
    from db_connector import get_mysql
    
    if not token:
        return False
    
    token_hash = hash_token(token)
    
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener información de la sesión antes de invalidarla
        cur.execute("SELECT usuario_id FROM sesiones WHERE token = %s", (token_hash,))
        session_info = cur.fetchone()
        
        if session_info:
            user_id = session_info[0]
            
            # Invalidar la sesión
            cur.execute("UPDATE sesiones SET activa = 0 WHERE token = %s", (token_hash,))
            
            # Registrar la invalidación
            cur.execute("""
                INSERT INTO invalidaciones_sesion (usuario_id, motivo)
                VALUES (%s, %s)
            """, (user_id, motivo))
            
            mysql.connection.commit()
            cur.close()
            return True
        
        cur.close()
        return False
        
    except Exception as e:
        print(f"Error al invalidar sesión: {e}")
        return False

def invalidate_all_user_sessions(user_id, motivo='cambio_password', invalidado_por=None):
    """Invalidar todas las sesiones de un usuario"""
    from db_connector import get_mysql
    
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Invalidar todas las sesiones del usuario
        cur.execute("UPDATE sesiones SET activa = 0 WHERE usuario_id = %s", (user_id,))
        
        # Registrar la invalidación
        cur.execute("""
            INSERT INTO invalidaciones_sesion (usuario_id, motivo, invalidado_por)
            VALUES (%s, %s, %s)
        """, (user_id, motivo, invalidado_por))
        
        mysql.connection.commit()
        cur.close()
        return True
        
    except Exception as e:
        print(f"Error al invalidar todas las sesiones: {e}")
        return False

def cleanup_expired_sessions():
    """Limpiar sesiones expiradas (para ejecutar periódicamente)"""
    from db_connector import get_mysql
    
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Invalidar sesiones expiradas
        cur.execute("UPDATE sesiones SET activa = 0 WHERE fecha_expiracion < %s AND activa = 1", 
                   (datetime.now(),))
        
        mysql.connection.commit()
        cur.close()
        return True
        
    except Exception as e:
        print(f"Error al limpiar sesiones expiradas: {e}")
        return False

def get_user_sessions(user_id):
    """Obtener todas las sesiones activas de un usuario"""
    from db_connector import get_mysql
    
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        cur.execute("""
            SELECT token, fecha_creacion, fecha_expiracion, ip_address, user_agent
            FROM sesiones
            WHERE usuario_id = %s AND activa = 1 AND fecha_expiracion > %s
            ORDER BY fecha_creacion DESC
        """, (user_id, datetime.now()))
        
        sessions = cur.fetchall()
        cur.close()
        
        return sessions
        
    except Exception as e:
        print(f"Error al obtener sesiones de usuario: {e}")
        return []

def count_active_user_sessions(user_id):
    """Contar sesiones activas de un usuario"""
    from db_connector import get_mysql
    
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        cur.execute("""
            SELECT COUNT(*) 
            FROM sesiones 
            WHERE usuario_id = %s AND activa = 1 AND fecha_expiracion > %s
        """, (user_id, datetime.now()))
        
        count = cur.fetchone()[0]
        cur.close()
        
        return count
        
    except Exception as e:
        print(f"Error al contar sesiones activas: {e}")
        return 0

def invalidate_current_session_if_needed(affected_user_id):
    """Invalidar la sesión actual de Flask si el usuario afectado es el usuario actual"""
    from flask import session, request
    
    current_user = get_current_user()
    if current_user and current_user['id'] == affected_user_id:
        # Obtener el token antes de limpiar la sesión
        token = request.cookies.get('session_token')
        
        # Limpiar la sesión de Flask
        session.clear()
        
        # También invalidar el token de la cookie si existe
        if token:
            invalidate_session(token, 'admin_action')
        
        return True
    return False

def recreate_session_after_password_change(user_id, user_data):
    """Recrear sesión después de cambio de contraseña"""
    from flask import session, make_response
    
    # Crear nueva sesión
    nuevo_token = create_session(user_id, False)
    
    if nuevo_token:
        # Establecer nueva sesión de Flask
        session['user_id'] = user_data['id']
        session['usuario'] = user_data['usuario']
        session['correo'] = user_data['correo']
        session['is_admin'] = user_data['is_admin']
        session['rol'] = user_data['rol']
        session['logged_in'] = True
        
        return nuevo_token
    
    return None
