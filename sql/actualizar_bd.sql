-- Script para actualizar base de datos existente
-- Ejecutar solo si la tabla eventos ya existe y no tiene la columna torneo_iniciado_por

-- Verificar si la columna existe
SELECT COLUMN_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'eventos' 
AND COLUMN_NAME = 'torneo_iniciado_por';

-- Si la columna no existe, ejecutar estos comandos:
ALTER TABLE eventos ADD COLUMN torneo_iniciado_por INT;
ALTER TABLE eventos ADD FOREIGN KEY (torneo_iniciado_por) REFERENCES usuarios(id);

-- Verificar que la columna fue agregada
DESCRIBE eventos;
