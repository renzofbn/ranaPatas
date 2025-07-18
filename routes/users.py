from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from db_connector import get_mysql
from utils import require_login, get_current_user, invalidate_all_user_sessions, invalidate_current_session_if_needed
from functools import wraps

# Crear el blueprint para gestión de usuarios
users_bp = Blueprint('users', __name__, url_prefix='/users')

def require_admin():
    """Decorador para requerir permisos de administrador completo (rol 3)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()
            if not current_user:
                flash('Necesitas iniciar sesión para acceder a esta página', 'error')
                return redirect(url_for('auth.login', next=request.url))
            
            user_rol = current_user.get('rol', 1)
            if not current_user.get('is_admin', False) or user_rol != 3:
                flash('Solo administradores completos pueden acceder a esta página', 'error')
                return redirect(url_for('blog.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@users_bp.route('/')
@require_admin()
def index():
    """Listar todos los usuarios del sistema"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener todos los usuarios (excluyendo rechazados)
        cur.execute("""
            SELECT id, usuario, correo, isAdmin, rol, cuenta_bloqueada,
                   DATE_FORMAT(fecha_registro, '%Y-%m-%d') as fecha_registro
            FROM usuarios 
            WHERE estado_aprobacion != 'rechazado'
            ORDER BY id DESC
        """)
        
        users = cur.fetchall()
        cur.close()
        
        # Convertir a lista de diccionarios para facilitar el manejo en el template
        users_list = []
        for user in users:
            users_list.append({
                'id': user[0],
                'usuario': user[1],
                'correo': user[2],
                'is_admin': bool(user[3]),
                'rol': user[4] or 1,
                'cuenta_bloqueada': bool(user[5]),
                'fecha_registro': user[6] if user[6] else 'N/A'
            })
        
        return render_template('users/index.html', users=users_list)
        
    except Exception as e:
        flash(f'Error al cargar usuarios: {str(e)}', 'error')
        return redirect(url_for('blog.index'))


@users_bp.route('/bloquear/<int:user_id>', methods=['POST'])
@require_admin()
def bloquear(user_id):
    """Bloquear usuario"""
    try:
        current_user = get_current_user()
        
        # Evitar que el admin se bloquee a sí mismo
        if current_user['id'] == user_id:
            flash('No puedes bloquear tu propia cuenta', 'error')
            return redirect(url_for('users.index'))
        
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Verificar que el usuario existe y no está ya bloqueado
        cur.execute("SELECT id, usuario, cuenta_bloqueada FROM usuarios WHERE id = %s", (user_id,))
        user = cur.fetchone()
        
        if not user:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('users.index'))
        
        if user[2]:  # cuenta_bloqueada
            flash(f'El usuario {user[1]} ya está bloqueado', 'warning')
            return redirect(url_for('users.index'))
        
        # Bloquear usuario
        cur.execute("UPDATE usuarios SET cuenta_bloqueada = 1 WHERE id = %s", (user_id,))
        mysql.connection.commit()
        
        # Invalidar todas las sesiones del usuario
        invalidate_all_user_sessions(user_id, 'cuenta_bloqueada', current_user['id'])
        
        cur.close()
        
        flash(f'Usuario {user[1]} bloqueado correctamente. Sus sesiones han sido invalidadas.', 'success')
        
    except Exception as e:
        flash(f'Error al bloquear usuario: {str(e)}', 'error')
    
    return redirect(url_for('users.index'))

@users_bp.route('/desbloquear/<int:user_id>', methods=['POST'])
@require_admin()
def desbloquear(user_id):
    """Desbloquear usuario"""
    try:
        current_user = get_current_user()
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Verificar que el usuario existe y está bloqueado
        cur.execute("SELECT id, usuario, cuenta_bloqueada FROM usuarios WHERE id = %s", (user_id,))
        user = cur.fetchone()
        
        if not user:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('users.index'))
        
        if not user[2]:  # cuenta_bloqueada
            flash(f'El usuario {user[1]} no está bloqueado', 'warning')
            return redirect(url_for('users.index'))
        
        # Desbloquear usuario
        cur.execute("UPDATE usuarios SET cuenta_bloqueada = 0 WHERE id = %s", (user_id,))
        mysql.connection.commit()
        cur.close()
        
        flash(f'Usuario {user[1]} desbloqueado correctamente.', 'success')
        
    except Exception as e:
        flash(f'Error al desbloquear usuario: {str(e)}', 'error')
    
    return redirect(url_for('users.index'))
    
    return redirect(url_for('users.index'))

# Función toggle_admin eliminada - ahora se usa el sistema de roles

@users_bp.route('/cambiar_rol/<int:user_id>', methods=['POST'])
@require_admin()
def cambiar_rol(user_id):
    """Cambiar el rol de un usuario"""
    try:
        current_user = get_current_user()
        nuevo_rol = request.form.get('nuevo_rol')
        
        # Validar que el rol sea válido
        if not nuevo_rol or nuevo_rol not in ['1', '2', '3']:
            flash('Rol inválido', 'error')
            return redirect(url_for('users.index'))
        
        nuevo_rol = int(nuevo_rol)
        
        # No permitir que se cambien a sí mismos
        if current_user['id'] == user_id:
            flash('No puedes cambiar tu propio rol', 'error')
            return redirect(url_for('users.index'))
        
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener información del usuario
        cur.execute("SELECT usuario, rol FROM usuarios WHERE id = %s", (user_id,))
        usuario_info = cur.fetchone()
        
        if not usuario_info:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('users.index'))
        
        # Determinar si debe ser admin (rol 2 o 3)
        es_admin = 1 if nuevo_rol in [2, 3] else 0
        
        # Actualizar el rol y el campo isAdmin
        cur.execute("""
            UPDATE usuarios 
            SET rol = %s, isAdmin = %s 
            WHERE id = %s
        """, (nuevo_rol, es_admin, user_id))
        
        mysql.connection.commit()
        
        mysql.connection.commit()
        cur.close()
        
        # Invalidar todas las sesiones del usuario usando la función dedicada
        invalidate_all_user_sessions(user_id, 'cambio_rol', current_user['id'])
        
        # Si el usuario afectado es el usuario actual, limpiar su sesión de Flask
        session_invalidated = invalidate_current_session_if_needed(user_id)
        
        # Mensaje personalizado según el rol
        roles_nombres = {1: 'Usuario', 2: 'Organizador', 3: 'Administrador'}
        rol_nombre = roles_nombres.get(nuevo_rol, 'Usuario')
        
        if session_invalidated:
            flash(f'Rol de {usuario_info[0]} cambiado a {rol_nombre}. Has sido deslogueado porque tu propio rol fue modificado.', 'info')
            # Crear respuesta con cookie limpia
            response = redirect(url_for('auth.login'))
            response.set_cookie('session_token', '', expires=0)
            return response
        else:
            flash(f'Rol de {usuario_info[0]} cambiado a {rol_nombre}. Se han cerrado todas sus sesiones.', 'success')
            return redirect(url_for('users.index'))
        
    except Exception as e:
        flash(f'Error al cambiar el rol: {str(e)}', 'error')
        return redirect(url_for('users.index'))

@users_bp.route('/cambiar_contrasena_admin/<int:user_id>', methods=['POST'])
@require_admin()
def cambiar_contrasena_admin(user_id):
    """Cambiar la contraseña de un usuario (solo administradores)"""
    try:
        from utils import hash_password, validate_password
        
        current_user = get_current_user()
        nueva_contrasena = request.form.get('nueva_contrasena')
        
        # Validar la nueva contraseña
        valid_password, password_msg = validate_password(nueva_contrasena)
        if not valid_password:
            flash(f'Error en la contraseña: {password_msg}', 'error')
            return redirect(url_for('users.index'))
        
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener información del usuario
        cur.execute("SELECT usuario FROM usuarios WHERE id = %s", (user_id,))
        usuario_info = cur.fetchone()
        
        if not usuario_info:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('users.index'))
        
        # Hashear la nueva contraseña
        contrasena_hasheada = hash_password(nueva_contrasena)
        
        # Actualizar la contraseña
        cur.execute("""
            UPDATE usuarios 
            SET contrasena = %s 
            WHERE id = %s
        """, (contrasena_hasheada, user_id))
        
        mysql.connection.commit()
        cur.close()
        
        # Invalidar todas las sesiones del usuario
        invalidate_all_user_sessions(user_id, 'cambio_contrasena_admin', current_user['id'])
        
        flash(f'Contraseña de {usuario_info[0]} cambiada correctamente. Se han cerrado todas sus sesiones.', 'success')
        
    except Exception as e:
        flash(f'Error al cambiar la contraseña: {str(e)}', 'error')
    
    return redirect(url_for('users.index'))
