# Prueba de la funcionalidad de iniciar tiempo

## Resumen de los cambios implementados:

### 1. Backend (routes/eventos.py)
- ✅ Agregada nueva ruta `/<string:nombre_evento>/iniciar-tiempo` (POST) solo para administradores
- ✅ Actualizada función `detalle()` para incluir campos `torneo_empezado_en` y `torneo_iniciado_por`
- ✅ Actualizadas funciones `index()` y `todos()` para incluir los nuevos campos
- ✅ Configuración de timezone GMT-5 para el tiempo de inicio
- ✅ Al iniciar tiempo: 
  - Cambia estado del evento a "enCurso"
  - Registra `torneo_empezado_en` y `torneo_iniciado_por`
  - Asigna tiempo de inicio a todos los participantes existentes

### 2. Frontend (templates/eventos/detalle.html)
- ✅ Agregado botón "Iniciar Tiempo del Evento" solo para administradores
- ✅ Botón solo visible si `evento.torneo_empezado_en` es null
- ✅ Confirmación antes de iniciar el tiempo
- ✅ Ocultado botón "Agregar Participante" si el evento ya fue iniciado
- ✅ Mostrado mensaje informativo cuando no se pueden agregar participantes
- ✅ Agregada sección "Información del Torneo" mostrando:
  - Fecha/hora de inicio del torneo
  - Usuario que inició el torneo
- ✅ Modal de agregar participante solo se muestra si el evento no ha sido iniciado

### 3. Base de datos (sql/scripts.sql)
- ✅ Agregada columna `torneo_iniciado_por INT` en tabla `eventos`
- ✅ Agregada foreign key constraint para `torneo_iniciado_por`
- ✅ Agregado script ALTER TABLE para bases de datos existentes

### 4. Funcionalidad implementada:
1. **Botón "Iniciar Tiempo"**: Solo visible para administradores y solo si el evento no ha sido iniciado
2. **Restricción de participantes**: No se pueden agregar participantes después de iniciar el evento
3. **Zona horaria GMT-5**: Todos los tiempos se registran en GMT-5
4. **Registro del iniciador**: Se guarda qué usuario inició el evento
5. **Tiempo automático**: Al iniciar el evento, todos los participantes existentes reciben el tiempo de inicio

### 5. Validaciones:
- ✅ Solo administradores pueden iniciar eventos
- ✅ No se puede iniciar un evento que ya fue iniciado
- ✅ Confirmación antes de iniciar el tiempo
- ✅ Mensajes de error y éxito apropiados
- ✅ Redirección correcta después de la acción

## Para probar:
1. Ejecutar el script SQL para agregar la columna `torneo_iniciado_por` si la tabla ya existe
2. Iniciar la aplicación Flask
3. Entrar como administrador
4. Ir a la vista de detalle de un evento
5. Verificar que aparece el botón "Iniciar Tiempo del Evento"
6. Hacer click y confirmar
7. Verificar que:
   - El estado del evento cambió a "En Curso"
   - El botón de iniciar tiempo desaparece
   - No se puede agregar participantes
   - Se muestra la información del torneo iniciado
   - Los participantes existentes tienen tiempo de inicio
