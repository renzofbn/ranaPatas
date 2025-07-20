from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response, jsonify, jsonify
from db_connector import get_mysql
from utils import (validate_email, validate_username, validate_password, hash_password, 
                  check_password, require_login, get_current_user, create_session, 
                  invalidate_session, invalidate_all_user_sessions, invalidate_current_session_if_needed,
                  recreate_session_after_password_change)
from datetime import datetime, timezone

# Crear el blueprint para autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario_o_correo = request.form['usuario_o_correo']
        contrasena = request.form['contrasena']
        remember_me = request.form.get('remember_me', False)
        
        # Validaciones básicas
        if not usuario_o_correo or not contrasena:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('auth/login.html')
        
        try:
            mysql = get_mysql()
            if not mysql:
                flash('Error de conexión a la base de datos', 'error')
                return render_template('auth/login.html')
                
            cur = mysql.connection.cursor()
            
            # Buscar usuario por nombre de usuario o correo
            cur.execute("SELECT id, usuario, correo, contrasena, isAdmin, estado_aprobacion, rol, cuenta_bloqueada FROM usuarios WHERE usuario = %s OR correo = %s", 
                       (usuario_o_correo, usuario_o_correo))
            user = cur.fetchone()
            cur.close()
            
            if not user:
                flash('Usuario o contraseña incorrectos', 'error')
                return render_template('auth/login.html')
            
            # Manejar tanto tuplas como diccionarios dependiendo de la configuración
            if isinstance(user, dict):
                user_id = user['id']
                username = user['usuario'] 
                email = user['correo']
                password_hash = user['contrasena']
                is_admin = user['isAdmin']
                estado = user['estado_aprobacion']
                rol = user['rol']
                bloqueada = user['cuenta_bloqueada']
            else:
                user_id = user[0]
                username = user[1]
                email = user[2] 
                password_hash = user[3]
                is_admin = user[4]
                estado = user[5]
                rol = user[6]
                bloqueada = user[7]
            
            # Verificar si la cuenta está bloqueada
            if bloqueada:
                flash('Tu cuenta ha sido bloqueada por un administrador. Contacta al administrador para más información.', 'error')
                return render_template('auth/login.html')
            
            # Verificar estado de aprobación
            if estado == 'pendiente':
                flash('Tu cuenta está pendiente de aprobación por un administrador.', 'error')
                return render_template('auth/login.html')
            elif estado == 'rechazado':
                flash('Tu cuenta ha sido rechazada. Contacta al administrador para más información.', 'error')
                return render_template('auth/login.html')
            
            # Verificar contraseña
            if not check_password(contrasena, password_hash):
                flash('Usuario o contraseña incorrectos', 'error')
                return render_template('auth/login.html')
            
            # Login exitoso - actualizar último login
            cur = mysql.connection.cursor()
            cur.execute("UPDATE usuarios SET ultimo_login = NOW() WHERE id = %s", (user_id,))
            mysql.connection.commit()
            cur.close()
            
            # Crear sesión tradicional
            session['user_id'] = user_id
            session['usuario'] = username
            session['correo'] = email
            session['is_admin'] = bool(is_admin)
            session['rol'] = rol or 1
            session['logged_in'] = True
            
            # Crear token de sesión
            token = create_session(user_id, remember_me)
            
            flash(f'¡Bienvenido {username}!', 'success')
            
            # Crear respuesta y establecer cookie del token
            next_page = request.args.get('next')
            if next_page:
                response = make_response(redirect(next_page))
            else:
                response = make_response(redirect(url_for('blog.index')))
            
            if token:
                # Configurar cookie del token
                max_age = 30*24*60*60 if remember_me else 24*60*60  # 30 días o 24 horas
                response.set_cookie('session_token', token, 
                                  max_age=max_age, 
                                  httponly=True, 
                                  secure=False,  # Cambiar a True en producción con HTTPS
                                  samesite='Lax')
            
            return response
            
        except Exception as e:
            # Log detallado del error para debugging
            import traceback
            error_details = traceback.format_exc()
            print(f"Error en login: {str(e)}")
            print(f"Detalles del error: {error_details}")
            
            # Error más específico para el usuario
            if "1045" in str(e):
                flash('Error de autenticación con la base de datos', 'error')
            elif "2003" in str(e):
                flash('No se puede conectar con la base de datos', 'error') 
            elif "1146" in str(e):
                flash('Tabla de usuarios no encontrada', 'error')
            else:
                flash(f'Error al iniciar sesión. Código: {str(e)[:50]}', 'error')
            
            return render_template('auth/login.html')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        usuario = request.form['usuario']
        correo = request.form['correo']
        sexo = request.form.get('sexo') or None  # Puede ser None si no se selecciona
        fecha_nacimiento = request.form.get('fecha_nacimiento') or None  # Puede ser None si no se proporciona
        contrasena = request.form['contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']
        
        # Validaciones básicas
        if not nombre or not usuario or not correo or not contrasena or not confirmar_contrasena:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('auth/register.html')
        
        # Validar nombre (solo letras y espacios)
        if not nombre.replace(' ', '').replace('-', '').isalpha() or len(nombre.strip()) < 2:
            flash('El nombre debe contener solo letras y tener al menos 2 caracteres', 'error')
            return render_template('auth/register.html')
        
        # Validar nombre de usuario
        valid_user, user_msg = validate_username(usuario)
        if not valid_user:
            flash(user_msg, 'error')
            return render_template('auth/register.html')
        
        # Validar email
        if not validate_email(correo):
            flash('El formato del correo electrónico no es válido', 'error')
            return render_template('auth/register.html')
        
        # Validar fecha de nacimiento (opcional, pero si se proporciona debe ser válida)
        if fecha_nacimiento:
            try:
                from datetime import datetime
                fecha_nacimiento_obj = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
                fecha_actual = datetime.now().date()
                if fecha_nacimiento_obj > fecha_actual:
                    flash('La fecha de nacimiento no puede ser una fecha futura', 'error')
                    return render_template('auth/register.html')
                # Verificar que la persona tenga al menos 13 años (opcional)
                edad = fecha_actual.year - fecha_nacimiento_obj.year - ((fecha_actual.month, fecha_actual.day) < (fecha_nacimiento_obj.month, fecha_nacimiento_obj.day))
                if edad < 13:
                    flash('Debes tener al menos 13 años para registrarte', 'error')
                    return render_template('auth/register.html')
            except ValueError:
                flash('Formato de fecha de nacimiento inválido', 'error')
                return render_template('auth/register.html')
        
        # Validar sexo (opcional, pero si se proporciona debe ser válido)
        if sexo and sexo not in ['M', 'F']:
            flash('Valor de sexo inválido', 'error')
            return render_template('auth/register.html')
        
        # Validar contraseña
        valid_pass, pass_msg = validate_password(contrasena)
        if not valid_pass:
            flash(pass_msg, 'error')
            return render_template('auth/register.html')
        
        # Verificar que las contraseñas coincidan
        if contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('auth/register.html')
        
        try:
            mysql = get_mysql()
            cur = mysql.connection.cursor()
            
            # Verificar si el usuario ya existe
            cur.execute("SELECT * FROM usuarios WHERE usuario = %s OR correo = %s", (usuario, correo))
            existing_user = cur.fetchone()
            
            if existing_user:
                flash('El usuario o correo ya existe', 'error')
                cur.close()
                return render_template('auth/register.html')
            
            # Hash de la contraseña
            hashed_password = hash_password(contrasena)
            
            # Insertar nuevo usuario con estado pendiente y rol por defecto (Usuario)
            cur.execute("""INSERT INTO usuarios (nombre, usuario, correo, sexo, fecha_nacimiento, contrasena, estado_aprobacion, rol) 
                           VALUES (%s, %s, %s, %s, %s, %s, 'pendiente', 1)""", 
                       (nombre.strip(), usuario, correo, sexo, fecha_nacimiento, hashed_password))
            mysql.connection.commit()
            
            # Crear notificación para administradores
            user_id = cur.lastrowid
            mensaje_notificacion = f"El usuario {usuario} ({correo}) se ha registrado y está pendiente de aprobación."
            cur.execute("""INSERT INTO notificaciones_admin (tipo, titulo, mensaje, usuario_relacionado) 
                           VALUES (%s, %s, %s, %s)""",
                       ('nuevo_registro', 'Nuevo usuario pendiente de aprobación', mensaje_notificacion, user_id))
            mysql.connection.commit()
            cur.close()
            
            flash('¡Registro exitoso! Tu cuenta está pendiente de aprobación por un administrador. Te notificaremos cuando sea aprobada.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'Error al registrar usuario: {str(e)}', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    from utils import cleanup_expired_sessions_if_needed
    
    # Obtener token antes de limpiar la sesión
    token = request.cookies.get('session_token')
    
    # Invalidar token de sesión
    if token:
        invalidate_session(token, 'logout_manual')
    
    # Limpiar la sesión tradicional
    session.clear()
    
    # Aprovechar el logout para hacer limpieza ocasional
    cleanup_expired_sessions_if_needed()
    
    # Crear respuesta y eliminar cookie
    response = make_response(redirect(url_for('blog.index')))
    response.set_cookie('session_token', '', expires=0)
    
    flash('Has cerrado sesión exitosamente', 'success')
    return response

@auth_bp.route('/perfil')
@require_login()
def perfil():
    """Página de perfil del usuario (requiere login)"""
    try:
        current_user = get_current_user()
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener información completa del usuario
        cur.execute("""
            SELECT id, usuario, correo, nombre, isAdmin, fecha_registro, ultimo_login, rol, sexo, fecha_nacimiento
            FROM usuarios 
            WHERE id = %s
        """, (current_user['id'],))
        
        usuario_completo = cur.fetchone()
        
        # Obtener estadísticas de participaciones
        cur.execute("""
            SELECT 
                COUNT(*) as total_participaciones,
                SUM(CASE WHEN tiempo_llegada IS NOT NULL THEN 1 ELSE 0 END) as eventos_completados,
                SUM(CASE WHEN tiempo_inicio IS NOT NULL AND tiempo_llegada IS NULL THEN 1 ELSE 0 END) as eventos_en_progreso
            FROM participantes_evento 
            WHERE usuario_id = %s
        """, (current_user['id'],))
        
        estadisticas = cur.fetchone()
        cur.close()
        
        if usuario_completo:
            user = {
                'id': usuario_completo[0],
                'usuario': usuario_completo[1],
                'correo': usuario_completo[2],
                'nombre': usuario_completo[3],
                'is_admin': bool(usuario_completo[4]),
                'fecha_registro': usuario_completo[5],
                'ultimo_login': usuario_completo[6],
                'rol': usuario_completo[7] or 1,
                'sexo': usuario_completo[8],
                'fecha_nacimiento': usuario_completo[9],
                'total_participaciones': estadisticas[0] if estadisticas else 0,
                'eventos_completados': estadisticas[1] if estadisticas else 0,
                'eventos_en_progreso': estadisticas[2] if estadisticas else 0
            }
        else:
            # Fallback a datos básicos si hay algún problema
            user = current_user.copy()
            user['nombre'] = None
            user['fecha_registro'] = None
            user['ultimo_login'] = None
            user['sexo'] = None
            user['fecha_nacimiento'] = None
            user['rol'] = current_user.get('rol', 1)
            user['total_participaciones'] = 0
            user['eventos_completados'] = 0
            user['eventos_en_progreso'] = 0
            user['ultimo_login'] = None
            user['total_participaciones'] = 0
            user['eventos_completados'] = 0
            user['eventos_en_progreso'] = 0
        
        return render_template('auth/perfil.html', user=user)
        
    except Exception as e:
        # En caso de error, usar datos básicos
        user = get_current_user()
        user['nombre'] = None
        user['fecha_registro'] = None
        user['ultimo_login'] = None
        user['total_participaciones'] = 0
        user['eventos_completados'] = 0
        user['eventos_en_progreso'] = 0
        return render_template('auth/perfil.html', user=user)

@auth_bp.route('/cambiar_contrasena', methods=['GET', 'POST'])
@require_login()
def cambiar_contrasena():
    """Cambiar contraseña del usuario actual"""
    if request.method == 'POST':
        contrasena_actual = request.form['contrasena_actual']
        nueva_contrasena = request.form['nueva_contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']
        
        # Validaciones básicas
        if not contrasena_actual or not nueva_contrasena or not confirmar_contrasena:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('auth/cambiar_contrasena.html')
        
        # Verificar que las nuevas contraseñas coincidan
        if nueva_contrasena != confirmar_contrasena:
            flash('Las contraseñas nuevas no coinciden', 'error')
            return render_template('auth/cambiar_contrasena.html')
        
        # Validar nueva contraseña
        valid_pass, pass_msg = validate_password(nueva_contrasena)
        if not valid_pass:
            flash(pass_msg, 'error')
            return render_template('auth/cambiar_contrasena.html')
        
        try:
            user = get_current_user()
            mysql = get_mysql()
            cur = mysql.connection.cursor()
            
            # Verificar contraseña actual
            cur.execute("SELECT contrasena FROM usuarios WHERE id = %s", (user['id'],))
            current_password_hash = cur.fetchone()[0]
            
            if not check_password(contrasena_actual, current_password_hash):
                flash('La contraseña actual es incorrecta', 'error')
                cur.close()
                return render_template('auth/cambiar_contrasena.html')
            
            # Hash de la nueva contraseña
            new_password_hash = hash_password(nueva_contrasena)
            
            # Actualizar contraseña en la base de datos
            from datetime import datetime
            cur.execute("""
                UPDATE usuarios 
                SET contrasena = %s, password_cambiado_en = %s 
                WHERE id = %s
            """, (new_password_hash, datetime.now(timezone.utc), user['id']))
            
            mysql.connection.commit()
            cur.close()
            
            # Invalidar todas las sesiones del usuario (incluyendo la actual)
            invalidate_all_user_sessions(user['id'], 'cambio_password', user['id'])
            
            # Limpiar la sesión actual de Flask
            session.clear()
            
            # Recrear sesión para el usuario actual
            nuevo_token = recreate_session_after_password_change(user['id'], user)
            
            flash('Contraseña cambiada exitosamente. Se han cerrado todas las sesiones por seguridad. Has sido relogueado automáticamente.', 'success')
            
            # Crear respuesta con nuevo token y sesión limpia
            response = make_response(redirect(url_for('auth.perfil')))
            
            # Limpiar cookie anterior y establecer nueva
            response.set_cookie('session_token', '', expires=0)
            
            if nuevo_token:
                response.set_cookie('session_token', nuevo_token, 
                                  max_age=24*60*60,  # 24 horas
                                  httponly=True, 
                                  secure=False,
                                  samesite='Lax')
            
            return response
            
        except Exception as e:
            flash(f'Error al cambiar contraseña: {str(e)}', 'error')
            return render_template('auth/cambiar_contrasena.html')
    
    return render_template('auth/cambiar_contrasena.html')

@auth_bp.route('/mis_sesiones')
@require_login()
def mis_sesiones():
    """Ver y gestionar las sesiones activas del usuario"""
    from utils import get_user_sessions
    user = get_current_user()
    sessions = get_user_sessions(user['id'])
    current_token = request.cookies.get('session_token')
    
    return render_template('auth/mis_sesiones.html', sessions=sessions, current_token=current_token)

@auth_bp.route('/cerrar_sesion/<token>')
@require_login()
def cerrar_sesion_especifica(token):
    """Cerrar una sesión específica"""
    user = get_current_user()
    current_token = request.cookies.get('session_token')
    
    # No permitir cerrar la sesión actual de esta manera
    if token == current_token:
        flash('No puedes cerrar la sesión actual desde aquí. Usa el botón de logout.', 'error')
    else:
        # Verificar que el token pertenece al usuario actual
        from utils import validate_session_token
        token_user = validate_session_token(token)
        if token_user and token_user['id'] == user['id']:
            if invalidate_session(token, 'logout_manual'):
                flash('Sesión cerrada exitosamente', 'success')
            else:
                flash('Error al cerrar la sesión', 'error')
        else:
            flash('Token de sesión inválido', 'error')
    
    return redirect(url_for('auth.mis_sesiones'))

@auth_bp.route('/api/usuarios', methods=['GET'])
@require_login()
def api_usuarios():
    """API para obtener usuarios disponibles (para autocompletado)"""
    try:
        query = request.args.get('q', '').strip()
        
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        if query:
            # Buscar usuarios que coincidan con el query y que no estén rechazados ni bloqueados
            cur.execute("""
                SELECT id, nombre, usuario 
                FROM usuarios 
                WHERE (nombre LIKE %s OR usuario LIKE %s)
                AND estado_aprobacion != 'rechazado'
                AND cuenta_bloqueada = 0
                ORDER BY nombre ASC 
                LIMIT 10
            """, (f'%{query}%', f'%{query}%'))
        else:
            # Obtener todos los usuarios que no estén rechazados ni bloqueados
            cur.execute("""
                SELECT id, nombre, usuario 
                FROM usuarios 
                WHERE estado_aprobacion != 'rechazado'
                AND cuenta_bloqueada = 0
                ORDER BY nombre ASC 
                LIMIT 20
            """)
        
        usuarios = cur.fetchall()
        cur.close()
        
        # Formatear respuesta
        usuarios_lista = []
        for usuario in usuarios:
            usuarios_lista.append({
                'id': usuario[0],
                'nombre': usuario[1],
                'usuario': usuario[2],
                'display': f"{usuario[1]} (@{usuario[2]})"
            })
        
        return jsonify(usuarios_lista)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
