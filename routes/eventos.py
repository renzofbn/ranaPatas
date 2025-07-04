from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db_connector import get_mysql
from utils import require_login, get_current_user, require_admin
from datetime import datetime, timedelta, timezone
import re

# Crear el blueprint para eventos
eventos_bp = Blueprint('eventos', __name__, url_prefix='/eventos')

@eventos_bp.route('/')
def index():
    """Listar todos los eventos"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener todos los eventos con información del usuario creador
        cur.execute("""
            SELECT e.id, e.nombre, e.fecha_creacion, e.creado_por_usuario, 
                   e.id_usuario_creado, e.lugar, e.observaciones, e.fecha_inicio,
                   u.usuario as usuario_creador
            FROM eventos e
            LEFT JOIN usuarios u ON e.id_usuario_creado = u.id
            ORDER BY e.fecha_creacion DESC
        """)
        
        eventos_raw = cur.fetchall()
        cur.close()
        
        # Convertir a lista de diccionarios
        eventos = []
        for evento in eventos_raw:
            eventos.append({
                'id': evento[0],
                'nombre': evento[1],
                'fecha_creacion': evento[2],
                'creado_por_usuario': evento[3],
                'id_usuario_creado': evento[4],
                'lugar': evento[5] or 'No especificado',
                'observaciones': evento[6] or '',
                'fecha_inicio': evento[7],
                'usuario_creador': evento[8] or evento[3]  # Fallback al nombre guardado
            })
        
        return render_template('eventos/index.html', eventos=eventos)
        
    except Exception as e:
        flash(f'Error al cargar eventos: {str(e)}', 'error')
        eventos = []
        return render_template('eventos/index.html', eventos=eventos)

@eventos_bp.route('/nuevo', methods=['GET', 'POST'])
@require_admin()
def nuevo():
    """Crear nuevo evento"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.form.get('nombre', '').strip()
            lugar = request.form.get('lugar', '').strip()
            observaciones = request.form.get('observaciones', '').strip()
            fecha_inicio = request.form.get('fecha_inicio', '').strip()
            
            # Validaciones básicas
            if not nombre:
                flash('El nombre del evento es obligatorio', 'error')
                return render_template('eventos/nuevo.html')
            
            if len(nombre) > 100:
                flash('El nombre del evento no puede tener más de 100 caracteres', 'error')
                return render_template('eventos/nuevo.html')
            
            if lugar and len(lugar) > 150:
                flash('El lugar no puede tener más de 150 caracteres', 'error')
                return render_template('eventos/nuevo.html')
            
            # Validar fecha si se proporciona
            fecha_inicio_obj = None
            if fecha_inicio:
                try:
                    fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%dT%H:%M')
                except ValueError:
                    flash('Formato de fecha inválido', 'error')
                    return render_template('eventos/nuevo.html')
            
            # Obtener información del usuario actual
            current_user = get_current_user()
            
            # Insertar en la base de datos
            mysql = get_mysql()
            cur = mysql.connection.cursor()
            
            cur.execute("""
                INSERT INTO eventos (nombre, creado_por_usuario, id_usuario_creado, lugar, observaciones, fecha_inicio)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                nombre,
                current_user['usuario'],
                current_user['id'],
                lugar if lugar else None,
                observaciones if observaciones else None,
                fecha_inicio_obj
            ))
            
            mysql.connection.commit()
            evento_id = cur.lastrowid
            cur.close()
            
            flash(f'Evento "{nombre}" creado exitosamente', 'success')
            return redirect(url_for('eventos.detalle', nombre_evento=_slug_from_name(nombre)))
            
        except Exception as e:
            flash(f'Error al crear evento: {str(e)}', 'error')
            return render_template('eventos/nuevo.html')
    
    return render_template('eventos/nuevo.html')

@eventos_bp.route('/<string:nombre_evento>')
def detalle(nombre_evento):
    """Ver detalle de un evento específico"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Buscar evento por nombre (usando LIKE para flexibilidad)
        # Convertir el slug de vuelta a un nombre aproximado para buscar
        nombre_busqueda = nombre_evento.replace('-', ' ')

        cur.execute("""
            SELECT e.id, e.nombre, e.fecha_creacion, e.creado_por_usuario, 
                   e.id_usuario_creado, e.lugar, e.observaciones, e.fecha_inicio,
                   u.usuario as usuario_creador
            FROM eventos e
            LEFT JOIN usuarios u ON e.id_usuario_creado = u.id
            WHERE LOWER(e.nombre) LIKE LOWER(%s)
            ORDER BY e.id DESC
            LIMIT 1
        """, (f'%{nombre_busqueda}%',))
        
        evento_raw = cur.fetchone()
        
        if not evento_raw:
            cur.close()
            # Mostrar error 404 si no se encuentra el evento
            from flask import abort
            abort(404)
        
        # Convertir evento a diccionario
        evento = {
            'id': evento_raw[0],
            'nombre': evento_raw[1],
            'fecha_creacion': evento_raw[2],
            'creado_por_usuario': evento_raw[3],
            'id_usuario_creado': evento_raw[4],
            'lugar': evento_raw[5] or 'No especificado',
            'observaciones': evento_raw[6] or 'Sin observaciones',
            'fecha_inicio': evento_raw[7],
            'usuario_creador': evento_raw[8] or evento_raw[3]
        }
        
        # Obtener participantes del evento
        cur.execute("""
            SELECT 
                p.id, p.codigo, p.nombre, p.tiempo_inicio, p.tiempo_llegada, 
                p.tiempo_total, p.usuario_agregado_en,
                u_agregado.usuario as agregado_por,
                u_iniciado.usuario as iniciado_por,
                u_terminado.usuario as terminado_por
            FROM participantes_evento p
            LEFT JOIN usuarios u_agregado ON p.participante_agregado_por = u_agregado.id
            LEFT JOIN usuarios u_iniciado ON p.tiempo_iniciado_por = u_iniciado.id
            LEFT JOIN usuarios u_terminado ON p.tiempo_terminado_por = u_terminado.id
            WHERE p.evento_id = %s
            ORDER BY p.usuario_agregado_en ASC
        """, (evento['id'],))
        
        participantes_raw = cur.fetchall()
        cur.close()
        
        # Convertir participantes a lista de diccionarios y calcular estados
        participantes = []
        stats = {'total': 0, 'completados': 0, 'en_progreso': 0, 'pendientes': 0}
        
        for p in participantes_raw:
            # Determinar estado del participante
            if p[4]:  # tiempo_llegada existe
                estado = 'completado'
                stats['completados'] += 1
            elif p[3]:  # tiempo_inicio existe pero no tiempo_llegada
                estado = 'en_progreso'
                stats['en_progreso'] += 1
            else:  # ni tiempo_inicio ni tiempo_llegada
                estado = 'pendiente'
                stats['pendientes'] += 1
            
            stats['total'] += 1
            
            # Calcular tiempo total si está disponible
            tiempo_total_str = None
            if p[5]:  # tiempo_total existe
                tiempo_total_str = str(p[5])
            
            participante = {
                'id': p[0],
                'codigo': p[1],
                'nombre': p[2],
                'tiempo_inicio': p[3],
                'tiempo_llegada': p[4],
                'tiempo_total': p[5],
                'tiempo_total_str': tiempo_total_str,
                'usuario_agregado_en': p[6],
                'agregado_por': p[7],
                'iniciado_por': p[8],
                'terminado_por': p[9],
                'estado': estado
            }
            participantes.append(participante)
        
        return render_template('eventos/detalle.html', 
                             evento=evento, 
                             participantes=participantes,
                             stats=stats)
        
    except Exception as e:
        if 'abort' in str(e) or '404' in str(e):
            # Re-lanzar el error 404
            from flask import abort
            abort(404)
        flash(f'Error al cargar evento: {str(e)}', 'error')
        return redirect(url_for('eventos.index'))

@eventos_bp.route('/editar/<int:evento_id>', methods=['GET', 'POST'])
@require_admin()
def editar(evento_id):
    """Editar evento existente"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.form.get('nombre', '').strip()
            lugar = request.form.get('lugar', '').strip()
            observaciones = request.form.get('observaciones', '').strip()
            fecha_inicio = request.form.get('fecha_inicio', '').strip()
            
            # Validaciones básicas
            if not nombre:
                flash('El nombre del evento es obligatorio', 'error')
                return redirect(url_for('eventos.editar', evento_id=evento_id))
            
            # Validar fecha si se proporciona
            fecha_inicio_obj = None
            if fecha_inicio:
                try:
                    fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%dT%H:%M')
                except ValueError:
                    flash('Formato de fecha inválido', 'error')
                    return redirect(url_for('eventos.editar', evento_id=evento_id))
            
            # Actualizar en la base de datos
            mysql = get_mysql()
            cur = mysql.connection.cursor()
            
            cur.execute("""
                UPDATE eventos 
                SET nombre = %s, lugar = %s, observaciones = %s, fecha_inicio = %s
                WHERE id = %s
            """, (
                nombre,
                lugar if lugar else None,
                observaciones if observaciones else None,
                fecha_inicio_obj,
                evento_id
            ))
            
            mysql.connection.commit()
            cur.close()
            
            flash(f'Evento "{nombre}" actualizado exitosamente', 'success')
            return redirect(url_for('eventos.detalle', nombre_evento=_slug_from_name(nombre)))
            
        except Exception as e:
            flash(f'Error al actualizar evento: {str(e)}', 'error')
            return redirect(url_for('eventos.editar', evento_id=evento_id))
    
    # GET: Mostrar formulario de edición
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        cur.execute("""
            SELECT id, nombre, lugar, observaciones, fecha_inicio
            FROM eventos 
            WHERE id = %s
        """, (evento_id,))
        
        evento_raw = cur.fetchone()
        cur.close()
        
        if not evento_raw:
            flash('Evento no encontrado', 'error')
            return redirect(url_for('eventos.index'))
        
        evento = {
            'id': evento_raw[0],
            'nombre': evento_raw[1],
            'lugar': evento_raw[2] or '',
            'observaciones': evento_raw[3] or '',
            'fecha_inicio': evento_raw[4].strftime('%Y-%m-%dT%H:%M') if evento_raw[4] else ''
        }
        
        return render_template('eventos/editar.html', evento=evento)
        
    except Exception as e:
        flash(f'Error al cargar evento: {str(e)}', 'error')
        return redirect(url_for('eventos.index'))

@eventos_bp.route('/eliminar/<int:evento_id>', methods=['POST'])
@require_login()
def eliminar(evento_id):
    """Eliminar evento"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener información del evento incluyendo el creador
        cur.execute("SELECT nombre, id_usuario_creado FROM eventos WHERE id = %s", (evento_id,))
        evento = cur.fetchone()
        
        if not evento:
            flash('Evento no encontrado', 'error')
            cur.close()
            return redirect(url_for('eventos.index'))
        
        nombre_evento = evento[0]
        id_usuario_creado = evento[1]
        
        # Verificar que el usuario actual sea quien creó el evento
        usuario_actual = get_current_user()
        
        if not usuario_actual or usuario_actual['id'] != id_usuario_creado:
            flash('Solo el creador del evento puede eliminarlo', 'error')
            cur.close()
            return redirect(url_for('eventos.detalle', nombre_evento=_slug_from_name(nombre_evento)))
        
        # Primero eliminar todos los participantes del evento
        print(f"DEBUG: Eliminando participantes del evento {evento_id}")
        cur.execute("DELETE FROM participantes_evento WHERE evento_id = %s", (evento_id,))
        participantes_eliminados = cur.rowcount
        print(f"DEBUG: Eliminados {participantes_eliminados} participantes")
        
        # Luego eliminar el evento
        print(f"DEBUG: Eliminando evento {evento_id}")
        cur.execute("DELETE FROM eventos WHERE id = %s", (evento_id,))
        eventos_eliminados = cur.rowcount
        print(f"DEBUG: Eliminados {eventos_eliminados} eventos")
        
        if eventos_eliminados == 0:
            print("DEBUG: No se eliminó ningún evento - posible problema de permisos o restricciones")
            flash('No se pudo eliminar el evento. Es posible que ya haya sido eliminado.', 'error')
            cur.close()
            return redirect(url_for('eventos.index'))
        
        mysql.connection.commit()
        cur.close()
        
        print(f"DEBUG: Evento eliminado exitosamente")
        flash(f'Evento "{nombre_evento}" eliminado correctamente', 'success')
        
    except Exception as e:
        flash(f'Error al eliminar evento: {str(e)}', 'error')
    
    return redirect(url_for('eventos.index'))

@eventos_bp.route('/<string:nombre_evento>/agregar-participante', methods=['POST'])
@require_admin()
def agregar_participante(nombre_evento):
    """Agregar un nuevo participante a un evento"""
    try:
        codigo = request.form.get('codigo', '').strip()
        nombre = request.form.get('nombre', '').strip()
        
        if not codigo or not nombre:
            flash('Código y nombre son requeridos', 'error')
            return redirect(url_for('eventos.detalle', nombre_evento=nombre_evento))
        
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Buscar el evento
        nombre_busqueda = nombre_evento.replace('-', ' ')
        cur.execute("""
            SELECT id FROM eventos 
            WHERE LOWER(nombre) LIKE LOWER(%s)
            ORDER BY id DESC LIMIT 1
        """, (f'%{nombre_busqueda}%',))
        
        evento = cur.fetchone()
        if not evento:
            flash('Evento no encontrado', 'error')
            cur.close()
            return redirect(url_for('eventos.index'))
        
        evento_id = evento[0]
        
        # Verificar que el código no exista ya en este evento
        cur.execute("""
            SELECT id FROM participantes_evento 
            WHERE evento_id = %s AND codigo = %s
        """, (evento_id, codigo))
        
        if cur.fetchone():
            flash(f'Ya existe un participante con el código "{codigo}" en este evento', 'error')
            cur.close()
            return redirect(url_for('eventos.detalle', nombre_evento=nombre_evento))
        
        # Obtener ID del usuario actual
        usuario_actual = get_current_user()
        
        # Insertar el nuevo participante
        cur.execute("""
            INSERT INTO participantes_evento 
            (codigo, nombre, participante_agregado_por, evento_id)
            VALUES (%s, %s, %s, %s)
        """, (codigo, nombre, usuario_actual['id'], evento_id))
        
        mysql.connection.commit()
        cur.close()
        
        flash(f'Participante "{nombre}" agregado exitosamente', 'success')
        
    except Exception as e:
        flash(f'Error al agregar participante: {str(e)}', 'error')
    
    return redirect(url_for('eventos.detalle', nombre_evento=nombre_evento))

@eventos_bp.route('/<string:nombre_evento>/eliminar-participante/<int:participante_id>', methods=['POST'])
@require_admin()
def eliminar_participante(nombre_evento, participante_id):
    """Eliminar un participante de un evento"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Obtener información del participante antes de eliminarlo
        cur.execute("""
            SELECT nombre FROM participantes_evento 
            WHERE id = %s
        """, (participante_id,))
        
        participante = cur.fetchone()
        if not participante:
            flash('Participante no encontrado', 'error')
            cur.close()
            return redirect(url_for('eventos.detalle', nombre_evento=nombre_evento))
        
        nombre_participante = participante[0]
        
        # Eliminar el participante
        cur.execute("""
            DELETE FROM participantes_evento 
            WHERE id = %s
        """, (participante_id,))
        
        mysql.connection.commit()
        cur.close()
        
        flash(f'Participante "{nombre_participante}" eliminado correctamente', 'success')
        
    except Exception as e:
        flash(f'Error al eliminar participante: {str(e)}', 'error')
    
    return redirect(url_for('eventos.detalle', nombre_evento=nombre_evento))

@eventos_bp.route('/<string:nombre_evento>/<string:codigo_participante>')
def detalle_participante(nombre_evento, codigo_participante):
    """Ver detalle de un participante específico en un evento"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Buscar el evento primero
        nombre_busqueda = nombre_evento.replace('-', ' ')
        cur.execute("""
            SELECT e.id, e.nombre, e.fecha_creacion, e.creado_por_usuario, 
                   e.id_usuario_creado, e.lugar, e.observaciones, e.fecha_inicio,
                   u.usuario as usuario_creador
            FROM eventos e
            LEFT JOIN usuarios u ON e.id_usuario_creado = u.id
            WHERE LOWER(e.nombre) LIKE LOWER(%s)
            ORDER BY e.id DESC LIMIT 1
        """, (f'%{nombre_busqueda}%',))
        
        evento_raw = cur.fetchone()
        
        if not evento_raw:
            cur.close()
            flash('Evento no encontrado', 'error')
            return redirect(url_for('eventos.index'))
        
        # Convertir evento a diccionario
        evento = {
            'id': evento_raw[0],
            'nombre': evento_raw[1],
            'fecha_creacion': evento_raw[2],
            'creado_por_usuario': evento_raw[3],
            'id_usuario_creado': evento_raw[4],
            'lugar': evento_raw[5] or 'No especificado',
            'observaciones': evento_raw[6] or 'Sin observaciones',
            'fecha_inicio': evento_raw[7],
            'usuario_creador': evento_raw[8] or evento_raw[3]
        }
        
        # Buscar el participante específico
        cur.execute("""
            SELECT 
                p.id, p.codigo, p.nombre, p.tiempo_inicio, p.tiempo_llegada, 
                p.tiempo_total, p.usuario_agregado_en,
                u_agregado.usuario as agregado_por,
                u_iniciado.usuario as iniciado_por,
                u_terminado.usuario as terminado_por,
                p.participante_agregado_por, p.tiempo_iniciado_por, p.tiempo_terminado_por
            FROM participantes_evento p
            LEFT JOIN usuarios u_agregado ON p.participante_agregado_por = u_agregado.id
            LEFT JOIN usuarios u_iniciado ON p.tiempo_iniciado_por = u_iniciado.id
            LEFT JOIN usuarios u_terminado ON p.tiempo_terminado_por = u_terminado.id
            WHERE p.evento_id = %s AND UPPER(p.codigo) = UPPER(%s)
            LIMIT 1
        """, (evento['id'], codigo_participante))
        
        participante_raw = cur.fetchone()
        
        if not participante_raw:
            cur.close()
            # Mostrar error 404 si no se encuentra el participante
            from flask import abort
            abort(404)
        
        # Determinar estado del participante
        if participante_raw[4]:  # tiempo_llegada existe
            estado = 'completado'
        elif participante_raw[3]:  # tiempo_inicio existe pero no tiempo_llegada
            estado = 'en_progreso'
        else:  # ni tiempo_inicio ni tiempo_llegada
            estado = 'pendiente'
        
        # Calcular tiempo total si está disponible
        tiempo_total_str = None
        tiempo_transcurrido = None
        if participante_raw[5]:  # tiempo_total existe
            tiempo_total_str = str(participante_raw[5])
        elif participante_raw[3] and not participante_raw[4]:  # En progreso
            # Calcular tiempo transcurrido desde el inicio hasta ahora
            from datetime import datetime
            tiempo_actual = datetime.now()
            tiempo_inicio = participante_raw[3]
            if isinstance(tiempo_inicio, datetime):
                diferencia = tiempo_actual - tiempo_inicio
                horas = int(diferencia.total_seconds() // 3600)
                minutos = int((diferencia.total_seconds() % 3600) // 60)
                segundos = int(diferencia.total_seconds() % 60)
                tiempo_transcurrido = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        
        participante = {
            'id': participante_raw[0],
            'codigo': participante_raw[1],
            'nombre': participante_raw[2],
            'tiempo_inicio': participante_raw[3],
            'tiempo_llegada': participante_raw[4],
            'tiempo_total': participante_raw[5],
            'tiempo_total_str': tiempo_total_str,
            'tiempo_transcurrido': tiempo_transcurrido,
            'usuario_agregado_en': participante_raw[6],
            'agregado_por': participante_raw[7],
            'iniciado_por': participante_raw[8],
            'terminado_por': participante_raw[9],
            'participante_agregado_por_id': participante_raw[10],
            'tiempo_iniciado_por_id': participante_raw[11],
            'tiempo_terminado_por_id': participante_raw[12],
            'estado': estado
        }
        
        # Obtener estadísticas del evento para contexto
        cur.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN tiempo_llegada IS NOT NULL THEN 1 ELSE 0 END) as completados,
                   SUM(CASE WHEN tiempo_inicio IS NOT NULL AND tiempo_llegada IS NULL THEN 1 ELSE 0 END) as en_progreso,
                   SUM(CASE WHEN tiempo_inicio IS NULL THEN 1 ELSE 0 END) as pendientes
            FROM participantes_evento 
            WHERE evento_id = %s
        """, (evento['id'],))
        
        stats_raw = cur.fetchone()
        stats = {
            'total': stats_raw[0] or 0,
            'completados': stats_raw[1] or 0,
            'en_progreso': stats_raw[2] or 0,
            'pendientes': stats_raw[3] or 0
        }
        
        cur.close()
        
        return render_template('eventos/detalle_participante.html', 
                             evento=evento, 
                             participante=participante,
                             stats=stats)
        
    except Exception as e:
        if 'abort' in str(e) or '404' in str(e):
            # Re-lanzar el error 404
            from flask import abort
            abort(404)
        flash(f'Error al cargar participante: {str(e)}', 'error')
        return redirect(url_for('eventos.detalle', nombre_evento=nombre_evento))

@eventos_bp.route('/<nombre_evento>/participante/<codigo_participante>/iniciar-cronometro', methods=['POST'])
@require_admin()
def iniciar_cronometro(nombre_evento, codigo_participante):
    """Iniciar el cronómetro de un participante"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Verificar que el evento existe
        cur.execute("SELECT id FROM eventos WHERE nombre = %s", (nombre_evento.replace('-', ' '),))
        evento = cur.fetchone()
        if not evento:
            cur.close()
            return {'success': False, 'error': 'Evento no encontrado'}, 404
        
        evento_id = evento[0]
        
        # Verificar que el participante existe
        cur.execute("""
            SELECT id, tiempo_inicio 
            FROM participantes_evento 
            WHERE codigo = %s AND evento_id = %s
        """, (codigo_participante, evento_id))
        participante = cur.fetchone()
        
        if not participante:
            cur.close()
            return {'success': False, 'error': 'Participante no encontrado'}, 404
        
        participante_id = participante[0]
        tiempo_inicio_actual = participante[1]
        
        # Verificar que no tenga ya un tiempo de inicio
        if tiempo_inicio_actual:
            cur.close()
            return {'success': False, 'error': 'El participante ya tiene un tiempo de inicio registrado'}, 400
        
        # Obtener el usuario actual
        usuario_actual = get_current_user()
        if not usuario_actual:
            cur.close()
            return {'success': False, 'error': 'Usuario no autenticado'}, 401
        
        # Actualizar el participante con el tiempo de inicio y usuario
        # Configurar timezone GMT-5 (UTC-5)
        gmt_minus_5 = timezone(timedelta(hours=-5))
        ahora = datetime.now(gmt_minus_5)
        cur.execute("""
            UPDATE participantes_evento 
            SET tiempo_inicio = %s, tiempo_iniciado_por = %s
            WHERE id = %s
        """, (ahora, usuario_actual['id'], participante_id))
        
        mysql.connection.commit()
        cur.close()
        
        return {
            'success': True, 
            'message': 'Cronómetro iniciado correctamente',
            'tiempo_inicio': ahora.isoformat(),
            'iniciado_por': usuario_actual['usuario']
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Error al iniciar cronómetro: {str(e)}'}, 500

@eventos_bp.route('/<nombre_evento>/participante/<codigo_participante>/finalizar-cronometro', methods=['POST'])
@require_admin()
def finalizar_cronometro(nombre_evento, codigo_participante):
    """Finalizar el cronómetro de un participante"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Verificar que el evento existe
        cur.execute("SELECT id FROM eventos WHERE nombre = %s", (nombre_evento.replace('-', ' '),))
        evento = cur.fetchone()
        if not evento:
            cur.close()
            return {'success': False, 'error': 'Evento no encontrado'}, 404
        
        evento_id = evento[0]
        
        # Verificar que el participante existe
        cur.execute("""
            SELECT id, tiempo_inicio, tiempo_llegada 
            FROM participantes_evento 
            WHERE codigo = %s AND evento_id = %s
        """, (codigo_participante, evento_id))
        participante = cur.fetchone()
        
        if not participante:
            cur.close()
            return {'success': False, 'error': 'Participante no encontrado'}, 404
        
        participante_id = participante[0]
        tiempo_inicio = participante[1]
        tiempo_llegada_actual = participante[2]
        
        # Verificar que tenga tiempo de inicio
        if not tiempo_inicio:
            cur.close()
            return {'success': False, 'error': 'El participante no tiene un tiempo de inicio registrado'}, 400
        
        # Verificar que no tenga ya un tiempo de llegada
        if tiempo_llegada_actual:
            cur.close()
            return {'success': False, 'error': 'El participante ya tiene un tiempo de llegada registrado'}, 400
        
        # Obtener el usuario actual
        usuario_actual = get_current_user()
        if not usuario_actual:
            cur.close()
            return {'success': False, 'error': 'Usuario no autenticado'}, 401
        
        # Primero guardar el tiempo de llegada
        # Configurar timezone GMT-5 (UTC-5)
        gmt_minus_5 = timezone(timedelta(hours=-5))
        ahora = datetime.now(gmt_minus_5)
        cur.execute("""
            UPDATE participantes_evento 
            SET tiempo_llegada = %s, tiempo_terminado_por = %s
            WHERE id = %s
        """, (ahora, usuario_actual['id'], participante_id))
        
        mysql.connection.commit()
        
        # Ahora consultar los tiempos exactos para calcular la diferencia
        cur.execute("""
            SELECT tiempo_inicio, tiempo_llegada 
            FROM participantes_evento 
            WHERE id = %s
        """, (participante_id,))
        
        tiempos = cur.fetchone()
        tiempo_inicio_exacto = tiempos[0]
        tiempo_llegada_exacto = tiempos[1]
        
        # Calcular el tiempo total usando los tiempos exactos de la base de datos
        tiempo_transcurrido = tiempo_llegada_exacto - tiempo_inicio_exacto
        tiempo_total_segundos = int(tiempo_transcurrido.total_seconds())
        
        # Convertir segundos a formato TIME
        horas = tiempo_total_segundos // 3600
        minutos = (tiempo_total_segundos % 3600) // 60
        segundos = tiempo_total_segundos % 60
        tiempo_total_str = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        
        # Actualizar con el tiempo total calculado
        cur.execute("""
            UPDATE participantes_evento 
            SET tiempo_total = %s
            WHERE id = %s
        """, (tiempo_total_str, participante_id))
        
        mysql.connection.commit()
        cur.close()
        
        return {
            'success': True, 
            'message': 'Cronómetro finalizado correctamente',
            'tiempo_llegada': tiempo_llegada_exacto.strftime('%Y-%m-%d %H:%M:%S'),
            'tiempo_total': tiempo_total_str,
            'terminado_por': usuario_actual['usuario']
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Error al finalizar cronómetro: {str(e)}'}, 500

def _slug_from_name(nombre):
    """Convertir nombre de evento a slug para URL"""
    # Convertir a minúsculas y reemplazar espacios con guiones
    slug = nombre.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remover caracteres especiales
    slug = re.sub(r'[-\s]+', '-', slug)   # Reemplazar espacios y múltiples guiones
    return slug.strip('-')