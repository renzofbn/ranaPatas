-- Script para corregir registros con estado NULL en participante_evaluacion
-- Ejecutar este script si hay participantes con estado NULL

UPDATE participante_evaluacion 
SET estado = 'pendiente' 
WHERE estado IS NULL;

-- Verificar que no queden registros con estado NULL
SELECT COUNT(*) as registros_con_estado_null 
FROM participante_evaluacion 
WHERE estado IS NULL;

-- Corregir fechas NULL en participante_evaluacion
UPDATE participante_evaluacion 
SET fecha_agregacion = CURRENT_TIMESTAMP
WHERE fecha_agregacion IS NULL;

-- Verificar que no queden registros con fecha_agregacion NULL
SELECT COUNT(*) as registros_con_fecha_null 
FROM participante_evaluacion 
WHERE fecha_agregacion IS NULL;
