from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from db_connector import get_mysql
from utils import require_login, get_current_user, invalidate_all_user_sessions
from functools import wraps

# Crear el blueprint para administración
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def require_admin():
    """Decorador que requiere que el usuario sea administrador completo (rol 3)"""
    def decorator(f):
        @wraps(f)
        @require_login()
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()
            user_rol = current_user.get('rol', 1)
            
            # Solo usuarios con rol 3 (Administrador completo) pueden acceder
            if not current_user.get('is_admin', False) or user_rol != 3:
                flash('Acceso denegado. Solo administradores completos pueden acceder a esta sección.', 'error')
                return redirect(url_for('blog.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@admin_bp.route('/')
@require_admin()
def dashboard():
    """Panel principal de administración"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener estadísticas
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE estado_aprobacion = 'pendiente'")
        usuarios_pendientes = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE estado_aprobacion = 'aprobado'")
        usuarios_aprobados = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE estado_aprobacion = 'rechazado'")
        usuarios_rechazados = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM eventos")
        total_eventos = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM notificaciones_admin WHERE leida = 0")
        notificaciones_pendientes = cur.fetchone()[0]
        
        # Estadísticas por rol
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 1 AND estado_aprobacion = 'aprobado'")
        participantes = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 2 AND estado_aprobacion = 'aprobado'")
        organizadores = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 3 AND estado_aprobacion = 'aprobado'")
        administradores = cur.fetchone()[0]
        
        cur.close()
        
        estadisticas = {
            'usuarios_pendientes': usuarios_pendientes,
            'usuarios_aprobados': usuarios_aprobados,
            'usuarios_rechazados': usuarios_rechazados,
            'total_eventos': total_eventos,
            'notificaciones_pendientes': notificaciones_pendientes,
            'participantes': participantes,
            'organizadores': organizadores,
            'administradores': administradores
        }
        
        return render_template('admin/dashboard.html', estadisticas=estadisticas)
        
    except Exception as e:
        flash(f'Error al cargar el panel de administración: {str(e)}', 'error')
        return redirect(url_for('blog.index'))

@admin_bp.route('/usuarios_pendientes')
@require_admin()
def usuarios_pendientes():
    """Lista de usuarios pendientes de aprobación"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        cur.execute("""
            SELECT id, nombre, usuario, correo, fecha_registro 
            FROM usuarios 
            WHERE estado_aprobacion = 'pendiente' 
            ORDER BY fecha_registro DESC
        """)
        usuarios = cur.fetchall()
        cur.close()
        
        return render_template('admin/usuarios_pendientes.html', usuarios=usuarios)
        
    except Exception as e:
        flash(f'Error al cargar usuarios pendientes: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/aprobar_usuario/<int:user_id>', methods=['POST'])
@require_admin()
def aprobar_usuario(user_id):
    """Aprobar un usuario"""
    try:
        current_user = get_current_user()
        observaciones = request.form.get('observaciones', '')
        rol = request.form.get('rol')
        
        # Validar que se haya seleccionado un rol
        if not rol or rol not in ['1', '2', '3']:
            flash('Debes seleccionar un rol válido para el usuario', 'error')
            return redirect(url_for('admin.usuarios_pendientes'))
        
        rol = int(rol)
        
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Verificar que el usuario existe y está pendiente
        cur.execute("SELECT usuario, correo FROM usuarios WHERE id = %s AND estado_aprobacion = 'pendiente'", (user_id,))
        usuario_info = cur.fetchone()
        
        if not usuario_info:
            flash('Usuario no encontrado o ya procesado', 'error')
            return redirect(url_for('admin.usuarios_pendientes'))
        
        # Determinar si debe ser admin (rol 2 o 3)
        es_admin = 1 if rol in [2, 3] else 0
        
        # Aprobar usuario con rol
        cur.execute("""
            UPDATE usuarios 
            SET estado_aprobacion = 'aprobado', 
                fecha_aprobacion = NOW(), 
                aprobado_por = %s,
                observaciones_admin = %s,
                rol = %s,
                isAdmin = %s
            WHERE id = %s
        """, (current_user['id'], observaciones, rol, es_admin, user_id))
        
        # Marcar notificaciones relacionadas como leídas
        cur.execute("""
            UPDATE notificaciones_admin 
            SET leida = 1 
            WHERE usuario_relacionado = %s AND tipo = 'nuevo_registro'
        """, (user_id,))
        
        mysql.connection.commit()
        cur.close()
        
        # Mensaje personalizado según el rol
        roles_nombres = {1: 'Participante', 2: 'Organizador', 3: 'Administrador'}
        rol_nombre = roles_nombres.get(rol, 'Usuario')
        
        flash(f'Usuario {usuario_info[0]} aprobado exitosamente como {rol_nombre}', 'success')
        return redirect(url_for('admin.usuarios_pendientes'))
        
    except Exception as e:
        flash(f'Error al aprobar usuario: {str(e)}', 'error')
        return redirect(url_for('admin.usuarios_pendientes'))

@admin_bp.route('/rechazar_usuario/<int:user_id>', methods=['POST'])
@require_admin()
def rechazar_usuario(user_id):
    """Rechazar un usuario"""
    try:
        current_user = get_current_user()
        observaciones = request.form.get('observaciones', '')
        
        if not observaciones.strip():
            flash('Debes proporcionar una razón para rechazar al usuario', 'error')
            return redirect(url_for('admin.usuarios_pendientes'))
        
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Verificar que el usuario existe y está pendiente
        cur.execute("SELECT usuario, correo FROM usuarios WHERE id = %s AND estado_aprobacion = 'pendiente'", (user_id,))
        usuario_info = cur.fetchone()
        
        if not usuario_info:
            flash('Usuario no encontrado o ya procesado', 'error')
            return redirect(url_for('admin.usuarios_pendientes'))
        
        # Rechazar usuario
        cur.execute("""
            UPDATE usuarios 
            SET estado_aprobacion = 'rechazado', 
                fecha_aprobacion = NOW(), 
                aprobado_por = %s,
                observaciones_admin = %s
            WHERE id = %s
        """, (current_user['id'], observaciones, user_id))
        
        # Marcar notificaciones relacionadas como leídas
        cur.execute("""
            UPDATE notificaciones_admin 
            SET leida = 1 
            WHERE usuario_relacionado = %s AND tipo = 'nuevo_registro'
        """, (user_id,))
        
        mysql.connection.commit()
        cur.close()
        
        # Invalidar cualquier sesión que pudiera tener el usuario rechazado
        invalidate_all_user_sessions(user_id, 'usuario_rechazado', current_user['id'])
        
        flash(f'Usuario {usuario_info[0]} rechazado', 'success')
        return redirect(url_for('admin.usuarios_pendientes'))
        
    except Exception as e:
        flash(f'Error al rechazar usuario: {str(e)}', 'error')
        return redirect(url_for('admin.usuarios_pendientes'))

@admin_bp.route('/todos_usuarios')
@require_admin()
def todos_usuarios():
    """Lista de todos los usuarios con sus estados"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        cur.execute("""
            SELECT u.id, u.nombre, u.usuario, u.correo, u.estado_aprobacion, 
                   u.fecha_registro, u.fecha_aprobacion, u.isAdmin, u.rol,
                   admin.usuario as aprobado_por_usuario, u.observaciones_admin
            FROM usuarios u
            LEFT JOIN usuarios admin ON u.aprobado_por = admin.id
            ORDER BY u.fecha_registro DESC
        """)
        usuarios = cur.fetchall()
        cur.close()
        
        return render_template('admin/todos_usuarios.html', usuarios=usuarios)
        
    except Exception as e:
        flash(f'Error al cargar usuarios: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/notificaciones')
@require_admin()
def notificaciones():
    """Ver todas las notificaciones administrativas"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        cur.execute("""
            SELECT n.id, n.tipo, n.titulo, n.mensaje, n.fecha_creacion, n.leida,
                   u.usuario, u.correo
            FROM notificaciones_admin n
            LEFT JOIN usuarios u ON n.usuario_relacionado = u.id
            ORDER BY n.fecha_creacion DESC
            LIMIT 50
        """)
        notificaciones = cur.fetchall()
        cur.close()
        
        return render_template('admin/notificaciones.html', notificaciones=notificaciones)
        
    except Exception as e:
        flash(f'Error al cargar notificaciones: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/marcar_notificacion_leida/<int:notif_id>', methods=['POST'])
@require_admin()
def marcar_notificacion_leida(notif_id):
    """Marcar una notificación como leída"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        cur.execute("UPDATE notificaciones_admin SET leida = 1 WHERE id = %s", (notif_id,))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
