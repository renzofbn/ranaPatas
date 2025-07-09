from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from db_connector import get_mysql
from utils import require_login, get_current_user
from functools import wraps
from datetime import datetime, timezone, timedelta

# Crear el blueprint para evaluaciones
evaluaciones_bp = Blueprint('evaluaciones', __name__, url_prefix='/evaluaciones')

def get_gmt_minus_5_time():
    """Obtener la hora actual en GMT-5"""
    gmt_minus_5 = timezone(timedelta(hours=-5))
    return datetime.now(gmt_minus_5)

def require_admin_evaluaciones():
    """Decorador para requerir permisos de administrador para crear/editar/eliminar evaluaciones (rol 2 o 3)"""
    def decorator(f):
        @wraps(f)
        @require_login()
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()
            user_rol = current_user.get('rol', 1)
            
            # Solo usuarios con rol 2 (Organizador) o 3 (Admin) pueden crear/modificar/eliminar
            if not current_user.get('is_admin', False) or user_rol not in [2, 3]:
                flash('Solo organizadores y administradores pueden realizar esta acción', 'error')
                return redirect(url_for('evaluaciones.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@evaluaciones_bp.route('/')
@require_login()
def index():
    """Listar todas las evaluaciones"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener todas las evaluaciones con información del creador
        cur.execute("""
            SELECT e.id, e.nombre, e.observacion, e.fecha_creada, e.activa,
                   u.usuario as creado_por_usuario, u.nombre as creado_por_nombre, e.creado_por
            FROM evaluaciones e
            JOIN usuarios u ON e.creado_por = u.id
            ORDER BY e.fecha_creada DESC
        """)
        
        evaluaciones = cur.fetchall()
        
        # Obtener estadísticas de participantes por evaluación
        evaluaciones_list = []
        for evaluacion in evaluaciones:
            # Contar participantes por estado
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
                    SUM(CASE WHEN estado = 'en_progreso' THEN 1 ELSE 0 END) as en_progreso,
                    SUM(CASE WHEN estado = 'completada' THEN 1 ELSE 0 END) as completadas,
                    SUM(CASE WHEN estado = 'cancelada' THEN 1 ELSE 0 END) as canceladas
                FROM participante_evaluacion 
                WHERE evaluacion_id = %s
            """, (evaluacion[0],))
            
            stats = cur.fetchone()
            
            evaluaciones_list.append({
                'id': evaluacion[0],
                'nombre': evaluacion[1],
                'observacion': evaluacion[2],
                'fecha_creada': evaluacion[3],
                'activa': bool(evaluacion[4]),
                'creado_por_usuario': evaluacion[5],
                'creado_por_nombre': evaluacion[6],
                'creado_por': evaluacion[7],
                'stats': {
                    'total': stats[0] or 0,
                    'pendientes': stats[1] or 0,
                    'en_progreso': stats[2] or 0,
                    'completadas': stats[3] or 0,
                    'canceladas': stats[4] or 0
                }
            })
        
        cur.close()
        
        # Verificar si el usuario puede crear/editar/eliminar
        current_user = get_current_user()
        can_manage = current_user.get('is_admin', False) and current_user.get('rol', 1) in [2, 3]
        
        return render_template('evaluaciones/index.html', 
                             evaluaciones=evaluaciones_list,
                             can_manage=can_manage)
        
    except Exception as e:
        flash(f'Error al cargar evaluaciones: {str(e)}', 'error')
        return redirect(url_for('blog.index'))

@evaluaciones_bp.route('/crear', methods=['GET', 'POST'])
@require_admin_evaluaciones()
def crear():
    """Crear nueva evaluación"""
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        observacion = request.form.get('observacion', '').strip()
        
        # Validaciones
        if not nombre:
            flash('El nombre de la evaluación es obligatorio', 'error')
            return render_template('evaluaciones/crear.html')
        
        if len(nombre) > 255:
            flash('El nombre no puede tener más de 255 caracteres', 'error')
            return render_template('evaluaciones/crear.html')
        
        try:
            current_user = get_current_user()
            mysql = get_mysql()
            cur = mysql.connection.cursor()
            
            # Verificar que no exista una evaluación con el mismo nombre
            cur.execute("SELECT id FROM evaluaciones WHERE nombre = %s", (nombre,))
            if cur.fetchone():
                flash('Ya existe una evaluación con ese nombre', 'error')
                cur.close()
                return render_template('evaluaciones/crear.html')
            
            # Crear la evaluación
            cur.execute("""
                INSERT INTO evaluaciones (nombre, observacion, creado_por)
                VALUES (%s, %s, %s)
            """, (nombre, observacion, current_user['id']))
            
            mysql.connection.commit()
            evaluacion_id = cur.lastrowid
            cur.close()
            
            flash(f'Evaluación "{nombre}" creada exitosamente', 'success')
            return redirect(url_for('evaluaciones.detalle', evaluacion_id=evaluacion_id))
            
        except Exception as e:
            flash(f'Error al crear evaluación: {str(e)}', 'error')
            return render_template('evaluaciones/crear.html')
    
    return render_template('evaluaciones/crear.html')

@evaluaciones_bp.route('/editar/<int:evaluacion_id>', methods=['GET', 'POST'])
@require_admin_evaluaciones()
def editar(evaluacion_id):
    """Editar evaluación existente"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener la evaluación
        cur.execute("""
            SELECT id, nombre, observacion, activa, creado_por
            FROM evaluaciones 
            WHERE id = %s
        """, (evaluacion_id,))
        
        evaluacion = cur.fetchone()
        if not evaluacion:
            flash('Evaluación no encontrada', 'error')
            return redirect(url_for('evaluaciones.index'))
        
        if request.method == 'POST':
            nombre = request.form.get('nombre', '').strip()
            observacion = request.form.get('observacion', '').strip()
            activa = request.form.get('activa') == 'on'
            
            # Validaciones
            if not nombre:
                flash('El nombre de la evaluación es obligatorio', 'error')
                return render_template('evaluaciones/editar.html', evaluacion={
                    'id': evaluacion[0],
                    'nombre': evaluacion[1],
                    'observacion': evaluacion[2],
                    'activa': bool(evaluacion[3])
                })
            
            if len(nombre) > 255:
                flash('El nombre no puede tener más de 255 caracteres', 'error')
                return render_template('evaluaciones/editar.html', evaluacion={
                    'id': evaluacion[0],
                    'nombre': evaluacion[1],
                    'observacion': evaluacion[2],
                    'activa': bool(evaluacion[3])
                })
            
            # Verificar que no exista otra evaluación con el mismo nombre
            cur.execute("SELECT id FROM evaluaciones WHERE nombre = %s AND id != %s", 
                       (nombre, evaluacion_id))
            if cur.fetchone():
                flash('Ya existe otra evaluación con ese nombre', 'error')
                return render_template('evaluaciones/editar.html', evaluacion={
                    'id': evaluacion[0],
                    'nombre': evaluacion[1],
                    'observacion': evaluacion[2],
                    'activa': bool(evaluacion[3])
                })
            
            # Actualizar la evaluación
            cur.execute("""
                UPDATE evaluaciones 
                SET nombre = %s, observacion = %s, activa = %s
                WHERE id = %s
            """, (nombre, observacion, activa, evaluacion_id))
            
            mysql.connection.commit()
            cur.close()
            
            flash(f'Evaluación "{nombre}" actualizada exitosamente', 'success')
            return redirect(url_for('evaluaciones.detalle', evaluacion_id=evaluacion_id))
        
        cur.close()
        
        return render_template('evaluaciones/editar.html', evaluacion={
            'id': evaluacion[0],
            'nombre': evaluacion[1],
            'observacion': evaluacion[2],
            'activa': bool(evaluacion[3])
        })
        
    except Exception as e:
        flash(f'Error al editar evaluación: {str(e)}', 'error')
        return redirect(url_for('evaluaciones.index'))

@evaluaciones_bp.route('/eliminar/<int:evaluacion_id>', methods=['POST'])
@require_admin_evaluaciones()
def eliminar(evaluacion_id):
    """Eliminar evaluación (solo el creador puede eliminarla)"""
    try:
        current_user = get_current_user()
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener información de la evaluación y verificar el creador
        cur.execute("SELECT nombre, creado_por FROM evaluaciones WHERE id = %s", (evaluacion_id,))
        evaluacion = cur.fetchone()
        
        if not evaluacion:
            flash('Evaluación no encontrada', 'error')
            return redirect(url_for('evaluaciones.index'))
        
        # Verificar que solo el creador pueda eliminar la evaluación
        if evaluacion[1] != current_user['id']:
            flash('Solo el creador de la evaluación puede eliminarla', 'error')
            return redirect(url_for('evaluaciones.index'))
        
        # Verificar si tiene participantes y mostrar información
        cur.execute("SELECT COUNT(*) FROM participante_evaluacion WHERE evaluacion_id = %s", 
                   (evaluacion_id,))
        participantes_count = cur.fetchone()[0]
        
        # Eliminar primero los participantes de la evaluación
        if participantes_count > 0:
            cur.execute("DELETE FROM participante_evaluacion WHERE evaluacion_id = %s", 
                       (evaluacion_id,))
        
        # Eliminar la evaluación
        cur.execute("DELETE FROM evaluaciones WHERE id = %s", (evaluacion_id,))
        mysql.connection.commit()
        cur.close()
        
        message = f'Evaluación "{evaluacion[0]}" eliminada exitosamente'
        if participantes_count > 0:
            message += f' (se eliminaron también {participantes_count} participante(s) asociado(s))'
        flash(message, 'success')
        
    except Exception as e:
        flash(f'Error al eliminar evaluación: {str(e)}', 'error')
    
    return redirect(url_for('evaluaciones.index'))

@evaluaciones_bp.route('/detalle/<int:evaluacion_id>')
@require_login()
def detalle(evaluacion_id):
    """Ver detalle de una evaluación"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener información de la evaluación
        cur.execute("""
            SELECT e.id, e.nombre, e.observacion, e.fecha_creada, e.activa,
                   u.usuario as creado_por_usuario, u.nombre as creado_por_nombre
            FROM evaluaciones e
            JOIN usuarios u ON e.creado_por = u.id
            WHERE e.id = %s
        """, (evaluacion_id,))
        
        evaluacion = cur.fetchone()
        if not evaluacion:
            flash('Evaluación no encontrada', 'error')
            return redirect(url_for('evaluaciones.index'))
        
        # Obtener participantes de la evaluación
        cur.execute("""
            SELECT pe.id, pe.usuario_id, u.usuario, u.nombre, pe.fecha_agregacion,
                   pe.tiempo_inicio, pe.tiempo_final, pe.estado, pe.observaciones,
                   agregador.usuario as agregado_por_usuario,
                   iniciador.usuario as iniciado_por_usuario,
                   terminador.usuario as terminado_por_usuario
            FROM participante_evaluacion pe
            JOIN usuarios u ON pe.usuario_id = u.id
            JOIN usuarios agregador ON pe.agregado_por = agregador.id
            LEFT JOIN usuarios iniciador ON pe.iniciado_por = iniciador.id
            LEFT JOIN usuarios terminador ON pe.terminado_por = terminador.id
            WHERE pe.evaluacion_id = %s
            ORDER BY pe.fecha_agregacion DESC
        """, (evaluacion_id,))
        
        participantes = cur.fetchall()
        cur.close()
        
        # Verificar si el usuario puede gestionar la evaluación
        current_user = get_current_user()
        can_manage = current_user.get('is_admin', False) and current_user.get('rol', 1) in [2, 3]
        
        evaluacion_data = {
            'id': evaluacion[0],
            'nombre': evaluacion[1],
            'observacion': evaluacion[2],
            'fecha_creada': evaluacion[3],
            'activa': bool(evaluacion[4]),
            'creado_por_usuario': evaluacion[5],
            'creado_por_nombre': evaluacion[6]
        }
        
        participantes_list = []
        for p in participantes:
            # Calcular duración si existe
            duracion = None
            if p[5] and p[6]:  # tiempo_inicio y tiempo_final
                duracion_total = p[6] - p[5]
                duracion = str(duracion_total)
            
            participantes_list.append({
                'id': p[0],
                'usuario_id': p[1],
                'usuario': p[2],
                'nombre': p[3],
                'fecha_agregacion': p[4],
                'tiempo_inicio': p[5],
                'tiempo_final': p[6],
                'estado': p[7],
                'observaciones': p[8],
                'agregado_por_usuario': p[9],
                'iniciado_por_usuario': p[10],
                'terminado_por_usuario': p[11],
                'duracion': duracion
            })
        
        return render_template('evaluaciones/detalle.html', 
                             evaluacion=evaluacion_data,
                             participantes=participantes_list,
                             can_manage=can_manage)
        
    except Exception as e:
        flash(f'Error al cargar detalle de evaluación: {str(e)}', 'error')
        return redirect(url_for('evaluaciones.index'))

@evaluaciones_bp.route('/toggle_activa/<int:evaluacion_id>', methods=['POST'])
@require_admin_evaluaciones()
def toggle_activa(evaluacion_id):
    """Activar/desactivar evaluación"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener estado actual
        cur.execute("SELECT activa, nombre FROM evaluaciones WHERE id = %s", (evaluacion_id,))
        evaluacion = cur.fetchone()
        
        if not evaluacion:
            return jsonify({'success': False, 'error': 'Evaluación no encontrada'})
        
        nuevo_estado = not bool(evaluacion[0])
        
        # Actualizar estado
        cur.execute("UPDATE evaluaciones SET activa = %s WHERE id = %s", 
                   (nuevo_estado, evaluacion_id))
        mysql.connection.commit()
        cur.close()
        
        estado_texto = 'activada' if nuevo_estado else 'desactivada'
        flash(f'Evaluación "{evaluacion[1]}" {estado_texto} exitosamente', 'success')
        
        return jsonify({'success': True, 'nuevo_estado': nuevo_estado})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@evaluaciones_bp.route('/agregar_participante/<int:evaluacion_id>', methods=['POST'])
@require_admin_evaluaciones()
def agregar_participante(evaluacion_id):
    """Agregar participante a una evaluación"""
    try:
        usuario_id = request.form.get('usuario_id')
        observaciones = request.form.get('observaciones', '').strip()
        
        if not usuario_id:
            return jsonify({'success': False, 'error': 'Debe seleccionar un usuario'})
        
        current_user = get_current_user()
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Verificar que la evaluación existe
        cur.execute("SELECT id, nombre FROM evaluaciones WHERE id = %s", (evaluacion_id,))
        evaluacion = cur.fetchone()
        
        if not evaluacion:
            return jsonify({'success': False, 'error': 'Evaluación no encontrada'})
        
        # Verificar que el usuario existe y está aprobado
        cur.execute("""
            SELECT id, usuario, nombre FROM usuarios 
            WHERE id = %s AND estado_aprobacion = 'aprobado'
        """, (usuario_id,))
        
        usuario = cur.fetchone()
        if not usuario:
            return jsonify({'success': False, 'error': 'Usuario no encontrado o no aprobado'})
        
        # Verificar que el usuario no esté ya en la evaluación
        cur.execute("""
            SELECT id FROM participante_evaluacion 
            WHERE evaluacion_id = %s AND usuario_id = %s
        """, (evaluacion_id, usuario_id))
        
        if cur.fetchone():
            return jsonify({'success': False, 'error': f'El usuario {usuario[1]} ya está en esta evaluación'})
        
        # Agregar el participante con estado pendiente por defecto
        cur.execute("""
            INSERT INTO participante_evaluacion (evaluacion_id, usuario_id, agregado_por, observaciones, estado)
            VALUES (%s, %s, %s, %s, 'pendiente')
        """, (evaluacion_id, usuario_id, current_user['id'], observaciones))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            'success': True, 
            'message': f'Usuario {usuario[1]} agregado exitosamente a la evaluación'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@evaluaciones_bp.route('/buscar_usuarios')
@require_login()
def buscar_usuarios():
    """Buscar usuarios para autocompletado"""
    try:
        query = request.args.get('q', '').strip()
        evaluacion_id = request.args.get('evaluacion_id')
        
        if not query or len(query) < 2:
            return jsonify([])
        
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Buscar usuarios que no estén ya en la evaluación
        if evaluacion_id:
            cur.execute("""
                SELECT u.id, u.usuario, u.nombre, u.correo
                FROM usuarios u
                WHERE u.estado_aprobacion = 'aprobado' 
                  AND (u.usuario LIKE %s OR u.nombre LIKE %s OR u.correo LIKE %s)
                  AND u.id NOT IN (
                    SELECT pe.usuario_id 
                    FROM participante_evaluacion pe 
                    WHERE pe.evaluacion_id = %s
                  )
                ORDER BY u.usuario
                LIMIT 10
            """, (f'%{query}%', f'%{query}%', f'%{query}%', evaluacion_id))
        else:
            cur.execute("""
                SELECT u.id, u.usuario, u.nombre, u.correo
                FROM usuarios u
                WHERE u.estado_aprobacion = 'aprobado' 
                  AND (u.usuario LIKE %s OR u.nombre LIKE %s OR u.correo LIKE %s)
                ORDER BY u.usuario
                LIMIT 10
            """, (f'%{query}%', f'%{query}%', f'%{query}%'))
        
        usuarios = cur.fetchall()
        cur.close()
        
        # Formatear resultados para el autocompletado
        resultados = []
        for usuario in usuarios:
            resultados.append({
                'id': usuario[0],
                'usuario': usuario[1],
                'nombre': usuario[2] or '',
                'correo': usuario[3],
                'display': f"{usuario[1]} ({usuario[2] or usuario[3]})"
            })
        
        return jsonify(resultados)
        
    except Exception as e:
        return jsonify([])

@evaluaciones_bp.route('/detalle/<int:evaluacion_id>/<int:participante_id>')
@require_login()
def detalle_participante(evaluacion_id, participante_id):
    """Ver detalle de un participante específico en una evaluación"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener información de la evaluación
        cur.execute("""
            SELECT e.id, e.nombre, e.observacion, e.fecha_creada, e.activa,
                   u.usuario as creado_por_usuario, u.nombre as creado_por_nombre
            FROM evaluaciones e
            JOIN usuarios u ON e.creado_por = u.id
            WHERE e.id = %s
        """, (evaluacion_id,))
        
        evaluacion = cur.fetchone()
        if not evaluacion:
            flash('Evaluación no encontrada', 'error')
            return redirect(url_for('evaluaciones.index'))
        
        # Obtener información del participante
        cur.execute("""
            SELECT pe.id, pe.usuario_id, u.usuario, u.nombre, pe.fecha_agregacion,
                   pe.tiempo_inicio, pe.tiempo_final, pe.estado, pe.observaciones,
                   agregador.usuario as agregado_por_usuario,
                   iniciador.usuario as iniciado_por_usuario,
                   terminador.usuario as terminado_por_usuario
            FROM participante_evaluacion pe
            JOIN usuarios u ON pe.usuario_id = u.id
            JOIN usuarios agregador ON pe.agregado_por = agregador.id
            LEFT JOIN usuarios iniciador ON pe.iniciado_por = iniciador.id
            LEFT JOIN usuarios terminador ON pe.terminado_por = terminador.id
            WHERE pe.evaluacion_id = %s AND pe.id = %s
        """, (evaluacion_id, participante_id))
        
        participante = cur.fetchone()
        if not participante:
            flash('Participante no encontrado en esta evaluación', 'error')
            return redirect(url_for('evaluaciones.detalle', evaluacion_id=evaluacion_id))
        
        cur.close()
        
        # Verificar si el usuario puede gestionar cronómetros
        current_user = get_current_user()
        can_manage = current_user.get('is_admin', False) and current_user.get('rol', 1) in [2, 3]
        
        evaluacion_data = {
            'id': evaluacion[0],
            'nombre': evaluacion[1] or '',
            'observacion': evaluacion[2] or '',
            'fecha_creada': evaluacion[3],  # Debería tener valor por DEFAULT CURRENT_TIMESTAMP
            'activa': bool(evaluacion[4]),
            'creado_por_usuario': evaluacion[5] or '',
            'creado_por_nombre': evaluacion[6] or ''
        }
        
        # Calcular duración si existe
        duracion = None
        duracion_segundos = None
        if participante[5] and participante[6]:  # tiempo_inicio y tiempo_final
            duracion_total = participante[6] - participante[5]
            duracion_segundos = duracion_total.total_seconds()
            hours, remainder = divmod(int(duracion_segundos), 3600)
            minutes, seconds = divmod(remainder, 60)
            duracion = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        participante_data = {
            'id': participante[0],
            'usuario_id': participante[1],
            'usuario': participante[2] or '',
            'nombre': participante[3] or '',
            'fecha_agregacion': participante[4],  # Puede ser None, se maneja en el template
            'tiempo_inicio': participante[5],
            'tiempo_final': participante[6],
            'estado': participante[7] or 'pendiente',  # Valor predeterminado si es None
            'observaciones': participante[8] or '',
            'agregado_por_usuario': participante[9] or '',
            'iniciado_por_usuario': participante[10] or '',
            'terminado_por_usuario': participante[11] or '',
            'duracion': duracion,
            'duracion_segundos': duracion_segundos
        }
        
        return render_template('evaluaciones/detalle_participante.html', 
                             evaluacion=evaluacion_data,
                             participante=participante_data,
                             can_manage=can_manage)
        
    except Exception as e:
        flash(f'Error al cargar detalle del participante: {str(e)}', 'error')
        return redirect(url_for('evaluaciones.index'))

@evaluaciones_bp.route('/eliminar_participante/<int:evaluacion_id>/<int:participante_id>', methods=['POST'])
@require_admin_evaluaciones()
def eliminar_participante(evaluacion_id, participante_id):
    """Eliminar participante de una evaluación"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener información del participante antes de eliminarlo
        cur.execute("""
            SELECT pe.id, u.usuario, e.nombre
            FROM participante_evaluacion pe
            JOIN usuarios u ON pe.usuario_id = u.id
            JOIN evaluaciones e ON pe.evaluacion_id = e.id
            WHERE pe.evaluacion_id = %s AND pe.id = %s
        """, (evaluacion_id, participante_id))
        
        participante = cur.fetchone()
        if not participante:
            flash('Participante no encontrado', 'error')
            return redirect(url_for('evaluaciones.detalle', evaluacion_id=evaluacion_id))
        
        # Eliminar el participante
        cur.execute("""
            DELETE FROM participante_evaluacion 
            WHERE evaluacion_id = %s AND id = %s
        """, (evaluacion_id, participante_id))
        
        mysql.connection.commit()
        cur.close()
        
        flash(f'Participante {participante[1]} eliminado de la evaluación {participante[2]}', 'success')
        
    except Exception as e:
        flash(f'Error al eliminar participante: {str(e)}', 'error')
    
    return redirect(url_for('evaluaciones.detalle', evaluacion_id=evaluacion_id))

@evaluaciones_bp.route('/cronometro/<int:evaluacion_id>/<int:participante_id>', methods=['POST'])
@require_admin_evaluaciones()
def cronometro_participante(evaluacion_id, participante_id):
    """Controlar cronómetro del participante (iniciar, terminar, reiniciar)"""
    try:
        accion = request.form.get('accion')
        if not accion or accion not in ['iniciar', 'terminar', 'reiniciar']:
            return jsonify({'success': False, 'error': 'Acción no válida'})
        
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        current_user = get_current_user()
        
        # Verificar que el participante existe
        cur.execute("""
            SELECT pe.id, pe.estado, pe.tiempo_inicio, pe.tiempo_final
            FROM participante_evaluacion pe
            WHERE pe.evaluacion_id = %s AND pe.id = %s
        """, (evaluacion_id, participante_id))
        
        participante = cur.fetchone()
        if not participante:
            return jsonify({'success': False, 'error': 'Participante no encontrado'})
        
        participante_id_db, estado_actual, tiempo_inicio, tiempo_final = participante
        
        # Procesar acción
        if accion == 'iniciar':
            if estado_actual != 'pendiente':
                return jsonify({'success': False, 'error': 'Solo se puede iniciar un cronómetro en estado pendiente'})
            
            # Iniciar cronómetro usando la hora GMT-5
            tiempo_servidor = get_gmt_minus_5_time()
            cur.execute("""
                UPDATE participante_evaluacion 
                SET tiempo_inicio = %s, estado = 'en_progreso', iniciado_por = %s
                WHERE id = %s
            """, (tiempo_servidor, current_user['id'], participante_id))
            
        elif accion == 'terminar':
            if estado_actual != 'en_progreso':
                return jsonify({'success': False, 'error': 'Solo se puede terminar un cronómetro en progreso'})
            
            # Terminar cronómetro usando la hora del servidor
            tiempo_servidor = datetime.now()
            cur.execute("""
                UPDATE participante_evaluacion 
                SET tiempo_final = %s, estado = 'completada', terminado_por = %s
                WHERE id = %s
            """, (tiempo_servidor, current_user['id'], participante_id))
            
        elif accion == 'reiniciar':
            if estado_actual == 'pendiente':
                return jsonify({'success': False, 'error': 'No se puede reiniciar un cronómetro que no ha iniciado'})
            
            # Reiniciar (borrar tiempos y volver a pendiente)
            cur.execute("""
                UPDATE participante_evaluacion 
                SET tiempo_inicio = NULL, tiempo_final = NULL, estado = 'pendiente',
                    iniciado_por = NULL, terminado_por = NULL
                WHERE id = %s
            """, (participante_id,))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': f'Cronómetro {accion}do correctamente'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error al procesar acción del cronómetro: {str(e)}'})
