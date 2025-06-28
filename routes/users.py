from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from db_connector import get_mysql
from utils import require_login, get_current_user
from functools import wraps

# Crear el blueprint para gestión de usuarios
users_bp = Blueprint('users', __name__, url_prefix='/users')

def require_admin():
    """Decorador para requerir permisos de administrador"""
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

@users_bp.route('/')
@require_admin()
def index():
    """Listar todos los usuarios del sistema"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener todos los usuarios
        cur.execute("""
            SELECT id, usuario, correo, isAdmin, 
                   DATE_FORMAT(NOW(), '%Y-%m-%d') as fecha_registro
            FROM usuarios 
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
                'fecha_registro': user[4] if len(user) > 4 else 'N/A'
            })
        
        return render_template('users/index.html', users=users_list)
        
    except Exception as e:
        flash(f'Error al cargar usuarios: {str(e)}', 'error')
        return redirect(url_for('blog.index'))


@users_bp.route('/delete/<int:user_id>', methods=['POST'])
@require_admin()
def delete(user_id):
    """Eliminar usuario"""
    try:
        current_user = get_current_user()
        
        # Evitar que el admin se elimine a sí mismo
        if current_user['id'] == user_id:
            flash('No puedes eliminar tu propia cuenta', 'error')
            return redirect(url_for('users.index'))
        
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Verificar que el usuario existe
        cur.execute("SELECT id, usuario FROM usuarios WHERE id = %s", (user_id,))
        user = cur.fetchone()
        
        if not user:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('users.index'))
        
        # Eliminar usuario
        cur.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
        mysql.connection.commit()
        cur.close()
        
        flash(f'Usuario {user[1]} eliminado correctamente', 'success')
        
    except Exception as e:
        flash(f'Error al eliminar usuario: {str(e)}', 'error')
    
    return redirect(url_for('users.index'))

@users_bp.route('/toggle-admin/<int:user_id>', methods=['POST'])
@require_admin()
def toggle_admin(user_id):
    """Cambiar permisos de administrador"""
    try:
        current_user = get_current_user()
        
        # Evitar que el admin se quite sus propios permisos
        if current_user['id'] == user_id:
            flash('No puedes cambiar tus propios permisos de administrador', 'error')
            return redirect(url_for('users.index'))
        
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener estado actual del usuario
        cur.execute("SELECT id, usuario, isAdmin FROM usuarios WHERE id = %s", (user_id,))
        user = cur.fetchone()
        
        if not user:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('users.index'))
        
        # Cambiar estado de admin
        new_admin_status = not bool(user[2])
        cur.execute("UPDATE usuarios SET isAdmin = %s WHERE id = %s", (new_admin_status, user_id))
        mysql.connection.commit()
        cur.close()
        
        status_text = "administrador" if new_admin_status else "usuario regular"
        flash(f'{user[1]} ahora es {status_text}', 'success')
        
    except Exception as e:
        flash(f'Error al cambiar permisos: {str(e)}', 'error')
    
    return redirect(url_for('users.index'))
