from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from db_connector import get_mysql
from utils import require_login, get_current_user
from datetime import datetime
import re
import re

# Crear el blueprint para participantes
participante_bp = Blueprint('participante', __name__, url_prefix='/participante')

@participante_bp.route('/<string:nombre_usuario>')
def perfil_participante(nombre_usuario):
    """Mostrar el perfil de un participante con su historial de eventos"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Buscar el usuario por nombre de usuario
        cur.execute("""
            SELECT id, nombre, usuario, fecha_registro, sexo, fecha_nacimiento
            FROM usuarios 
            WHERE usuario = %s
        """, (nombre_usuario,))
        
        usuario_info = cur.fetchone()
        if not usuario_info:
            abort(404)
        
        usuario_id = usuario_info[0]
        
        # Obtener todos los eventos en los que ha participado
        cur.execute("""
            SELECT 
                e.id,
                e.nombre as evento_nombre,
                e.lugar,
                e.fecha_inicio,
                e.fecha_creacion,
                e.estado as evento_estado,
                pe.codigo,
                pe.tiempo_inicio,
                pe.tiempo_llegada,
                pe.usuario_agregado_en as fecha_agregado,
                u_creador.usuario as evento_creador,
                u_agregado.usuario as agregado_por
            FROM participantes_evento pe
            INNER JOIN eventos e ON pe.evento_id = e.id
            LEFT JOIN usuarios u_creador ON e.id_usuario_creado = u_creador.id
            LEFT JOIN usuarios u_agregado ON pe.participante_agregado_por = u_agregado.id
            WHERE pe.usuario_id = %s
            ORDER BY e.fecha_inicio DESC, e.fecha_creacion DESC
        """, (usuario_id,))
        
        participaciones_raw = cur.fetchall()
        
        # Procesar las participaciones
        participaciones = []
        stats = {
            'total_eventos': 0,
            'completados': 0,
            'en_progreso': 0,
            'pendientes': 0,
            'mejor_tiempo': None,
            'tiempo_promedio': None,
            'eventos_ganados': 0
        }
        
        tiempos_completados = []
        
        for part in participaciones_raw:
            # Determinar estado del participante basado en los tiempos
            if part[8]:  # tiempo_llegada existe
                participante_estado = 'completado'
                stats['completados'] += 1
            elif part[7]:  # tiempo_inicio existe pero no tiempo_llegada
                participante_estado = 'en_progreso'
                stats['en_progreso'] += 1
            else:  # ni tiempo_inicio ni tiempo_llegada
                participante_estado = 'pendiente'
                stats['pendientes'] += 1
            
            # Calcular tiempo total si ambos tiempos existen
            tiempo_total_str = None
            tiempo_total_segundos = None
            
            if part[7] and part[8]:  # tiempo_inicio y tiempo_llegada
                tiempo_inicio = part[7]
                tiempo_llegada = part[8]
                
                # Calcular diferencia
                diferencia = tiempo_llegada - tiempo_inicio
                tiempo_total_segundos = diferencia.total_seconds()
                
                # Formatear tiempo
                horas = int(tiempo_total_segundos // 3600)
                minutos = int((tiempo_total_segundos % 3600) // 60)
                segundos = int(tiempo_total_segundos % 60)
                
                if horas > 0:
                    tiempo_total_str = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
                else:
                    tiempo_total_str = f"{minutos:02d}:{segundos:02d}"
                
                tiempos_completados.append(tiempo_total_segundos)
            
            participacion = {
                'evento_id': part[0],
                'evento_nombre': part[1],
                'lugar': part[2] or 'No especificado',
                'fecha_inicio': part[3],
                'fecha_creacion': part[4],
                'evento_estado': part[5],
                'codigo': part[6],
                'tiempo_inicio': part[7],
                'tiempo_llegada': part[8],
                'participante_estado': participante_estado,
                'fecha_agregado': part[9],
                'evento_creador': part[10],
                'agregado_por': part[11],
                'tiempo_total_str': tiempo_total_str,
                'tiempo_total_segundos': tiempo_total_segundos
            }
            
            participaciones.append(participacion)
            
            # Actualizar estadísticas
            stats['total_eventos'] += 1
        
        # Calcular estadísticas de tiempo
        if tiempos_completados:
            stats['mejor_tiempo'] = min(tiempos_completados)
            stats['tiempo_promedio'] = sum(tiempos_completados) / len(tiempos_completados)
            
            # Formatear mejor tiempo
            mejor_segundos = stats['mejor_tiempo']
            horas = int(mejor_segundos // 3600)
            minutos = int((mejor_segundos % 3600) // 60)
            segundos = int(mejor_segundos % 60)
            
            if horas > 0:
                stats['mejor_tiempo_str'] = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
            else:
                stats['mejor_tiempo_str'] = f"{minutos:02d}:{segundos:02d}"
            
            # Formatear tiempo promedio
            promedio_segundos = stats['tiempo_promedio']
            horas = int(promedio_segundos // 3600)
            minutos = int((promedio_segundos % 3600) // 60)
            segundos = int(promedio_segundos % 60)
            
            if horas > 0:
                stats['tiempo_promedio_str'] = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
            else:
                stats['tiempo_promedio_str'] = f"{minutos:02d}:{segundos:02d}"
         # Obtener evaluaciones del usuario
        cur.execute("""
            SELECT 
                e.id,
                e.nombre as evaluacion_nombre,
                e.observacion,
                e.fecha_creada,
                pe.id as participacion_id,
                pe.fecha_agregacion,
                pe.tiempo_inicio,
                pe.tiempo_final,
                pe.estado,
                pe.observaciones as participacion_observaciones,
                u_agregado.usuario as agregado_por,
                u_iniciado.usuario as iniciado_por,
                u_terminado.usuario as terminado_por
            FROM participante_evaluacion pe
            INNER JOIN evaluaciones e ON pe.evaluacion_id = e.id
            LEFT JOIN usuarios u_agregado ON pe.agregado_por = u_agregado.id
            LEFT JOIN usuarios u_iniciado ON pe.iniciado_por = u_iniciado.id
            LEFT JOIN usuarios u_terminado ON pe.terminado_por = u_terminado.id
            WHERE pe.usuario_id = %s
            ORDER BY e.fecha_creada DESC, pe.fecha_agregacion DESC
        """, (usuario_id,))
        
        evaluaciones_raw = cur.fetchall()
        
        # Procesar las evaluaciones
        evaluaciones = []
        for eval_data in evaluaciones_raw:
            # Calcular tiempo total si ambos tiempos existen
            tiempo_total_str = None
            tiempo_total_segundos = None
            
            if eval_data[6] and eval_data[7]:  # tiempo_inicio y tiempo_final
                tiempo_inicio = eval_data[6]
                tiempo_final = eval_data[7]
                
                # Calcular diferencia
                diferencia = tiempo_final - tiempo_inicio
                tiempo_total_segundos = diferencia.total_seconds()
                
                # Formatear tiempo
                horas = int(tiempo_total_segundos // 3600)
                minutos = int((tiempo_total_segundos % 3600) // 60)
                segundos = int(tiempo_total_segundos % 60)
                
                if horas > 0:
                    tiempo_total_str = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
                else:
                    tiempo_total_str = f"{minutos:02d}:{segundos:02d}"
            
            evaluacion = {
                'evaluacion_id': eval_data[0],
                'evaluacion_nombre': eval_data[1],
                'observacion': eval_data[2],
                'fecha_creada': eval_data[3],
                'participacion_id': eval_data[4],
                'fecha_agregacion': eval_data[5],
                'tiempo_inicio': eval_data[6],
                'tiempo_final': eval_data[7],
                'estado': eval_data[8],
                'participacion_observaciones': eval_data[9],
                'agregado_por': eval_data[10],
                'iniciado_por': eval_data[11],
                'terminado_por': eval_data[12],
                'tiempo_total_str': tiempo_total_str,
                'tiempo_total_segundos': tiempo_total_segundos
            }
            
            evaluaciones.append(evaluacion)

        # Verificar si es el propio usuario
        usuario_actual = get_current_user() if session.get('logged_in') else None
        es_propio_perfil = usuario_actual and usuario_actual['id'] == usuario_id

        cur.close()

        # Preparar información del usuario
        usuario = {
            'id': usuario_info[0],
            'nombre': usuario_info[1],
            'usuario': usuario_info[2],
            'fecha_registro': usuario_info[3],
            'sexo': usuario_info[4],
            'fecha_nacimiento': usuario_info[5]
        }

        return render_template('participante/perfil.html', 
                             usuario=usuario,
                             participaciones=participaciones,
                             evaluaciones=evaluaciones,
                             stats=stats,
                             es_propio_perfil=es_propio_perfil)
        
    except Exception as e:
        flash(f'Error al cargar el perfil del participante: {str(e)}', 'error')
        return redirect(url_for('eventos.index'))

@participante_bp.route('/<string:nombre_usuario>/evento/<int:evento_id>')
def detalle_participacion(nombre_usuario, evento_id):
    """Mostrar detalles específicos de la participación en un evento"""
    try:
        mysql = get_mysql()
        cur = mysql.connection.cursor()
        
        # Buscar el usuario
        cur.execute("""
            SELECT id, nombre, usuario, sexo, fecha_nacimiento 
            FROM usuarios 
            WHERE usuario = %s
        """, (nombre_usuario,))
        
        usuario_info = cur.fetchone()
        if not usuario_info:
            abort(404)
        
        usuario_id = usuario_info[0]
        
        # Obtener detalles de la participación específica
        cur.execute("""
            SELECT 
                e.id,
                e.nombre as evento_nombre,
                e.lugar,
                e.fecha_inicio,
                e.observaciones,
                e.estado as evento_estado,
                pe.codigo,
                pe.tiempo_inicio,
                pe.tiempo_llegada,
                pe.usuario_agregado_en as fecha_agregado,
                u_creador.usuario as evento_creador,
                u_agregado.usuario as agregado_por,
                pe.nombre as participante_nombre
            FROM participantes_evento pe
            INNER JOIN eventos e ON pe.evento_id = e.id
            LEFT JOIN usuarios u_creador ON e.id_usuario_creado = u_creador.id
            LEFT JOIN usuarios u_agregado ON pe.participante_agregado_por = u_agregado.id
            WHERE pe.usuario_id = %s AND e.id = %s
        """, (usuario_id, evento_id))
        
        participacion_raw = cur.fetchone()
        if not participacion_raw:
            abort(404)
        
        # Calcular tiempo total y determinar estado
        tiempo_total_str = None
        participante_estado = 'pendiente'
        
        if participacion_raw[7] and participacion_raw[8]:  # tiempo_inicio y tiempo_llegada
            tiempo_inicio = participacion_raw[7]
            tiempo_llegada = participacion_raw[8]
            
            diferencia = tiempo_llegada - tiempo_inicio
            tiempo_total_segundos = diferencia.total_seconds()
            
            horas = int(tiempo_total_segundos // 3600)
            minutos = int((tiempo_total_segundos % 3600) // 60)
            segundos = int(tiempo_total_segundos % 60)
            
            if horas > 0:
                tiempo_total_str = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
            else:
                tiempo_total_str = f"{minutos:02d}:{segundos:02d}"
                
            participante_estado = 'completado'
        elif participacion_raw[7]:  # solo tiempo_inicio
            participante_estado = 'en_progreso'
        
        # Obtener estadísticas del evento (ranking)
        cur.execute("""
            SELECT 
                pe.codigo,
                pe.nombre,
                pe.tiempo_inicio,
                pe.tiempo_llegada
            FROM participantes_evento pe
            WHERE pe.evento_id = %s 
            AND pe.tiempo_inicio IS NOT NULL AND pe.tiempo_llegada IS NOT NULL
            ORDER BY (pe.tiempo_llegada - pe.tiempo_inicio) ASC
        """, (evento_id,))
        
        ranking = cur.fetchall()
        
        # Encontrar posición del usuario
        posicion_usuario = None
        for i, rank in enumerate(ranking):
            if rank[0] == participacion_raw[6]:  # código del participante
                posicion_usuario = i + 1
                break
        
        cur.close()
        
        participacion = {
            'evento_id': participacion_raw[0],
            'evento_nombre': participacion_raw[1],
            'lugar': participacion_raw[2] or 'No especificado',
            'fecha_inicio': participacion_raw[3],
            'observaciones': participacion_raw[4],
            'evento_estado': participacion_raw[5],
            'codigo': participacion_raw[6],
            'tiempo_inicio': participacion_raw[7],
            'tiempo_llegada': participacion_raw[8],
            'participante_estado': participante_estado,
            'fecha_agregado': participacion_raw[9],
            'evento_creador': participacion_raw[10],
            'agregado_por': participacion_raw[11],
            'participante_nombre': participacion_raw[12],
            'tiempo_total_str': tiempo_total_str,
            'posicion': posicion_usuario,
            'total_completados': len(ranking)
        }
        
        usuario = {
            'id': usuario_info[0],
            'nombre': usuario_info[1],
            'usuario': usuario_info[2],
            'sexo': usuario_info[3],
            'fecha_nacimiento': usuario_info[4]
        }
        
        return render_template('participante/detalle_participacion.html',
                             usuario=usuario,
                             participacion=participacion,
                             ranking=ranking[:10])  # Solo mostrar top 10
        
    except Exception as e:
        flash(f'Error al cargar los detalles de participación: {str(e)}', 'error')
        return redirect(url_for('participante.perfil_participante', nombre_usuario=nombre_usuario))

def _slug_from_name(nombre, evento_id=None):
    """Generar slug de URL desde el nombre del evento"""
    # Convertir a minúsculas y reemplazar caracteres especiales
    slug = re.sub(r'[^a-zA-Z0-9\s]', '', nombre.lower())
    # Reemplazar espacios con guiones
    slug = re.sub(r'\s+', '-', slug.strip())
    # Remover guiones múltiples
    slug = re.sub(r'-+', '-', slug)
    # Remover guiones al inicio y final
    slug = slug.strip('-')
    
    if evento_id:
        slug = f"{evento_id}-{slug}"
    
    return slug

def _evento_url_slug(evento_id, nombre):
    """Generar slug de URL para un evento"""
    return _slug_from_name(nombre, evento_id)

# Hacer la función disponible para las plantillas
@participante_bp.context_processor
def inject_evento_url_slug():
    return dict(evento_url_slug=_evento_url_slug)
