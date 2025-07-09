-- Crear tablas para sistema de evaluaciones
-- Ejecutar este script para crear las tablas necesarias

-- Tabla principal de evaluaciones
CREATE TABLE evaluaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    observacion TEXT,
    fecha_creada DATETIME DEFAULT CURRENT_TIMESTAMP,
    creado_por INT NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    
    -- Llave foránea para el usuario que creó la evaluación
    CONSTRAINT fk_evaluaciones_creado_por 
        FOREIGN KEY (creado_por) REFERENCES usuarios(id) ON DELETE RESTRICT
);

-- Tabla de participación en evaluaciones
CREATE TABLE participante_evaluacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    evaluacion_id INT NOT NULL,
    usuario_id INT NOT NULL,
    fecha_agregacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    agregado_por INT NOT NULL,
    tiempo_inicio DATETIME NULL,
    tiempo_final DATETIME NULL,
    iniciado_por INT NULL,
    terminado_por INT NULL,
    observaciones TEXT,
    estado ENUM('pendiente', 'en_progreso', 'completada', 'cancelada') DEFAULT 'pendiente',
    
    -- Llave foránea para la evaluación
    CONSTRAINT fk_participante_evaluacion_evaluacion 
        FOREIGN KEY (evaluacion_id) REFERENCES evaluaciones(id) ON DELETE CASCADE,
    
    -- Llave foránea para el usuario participante
    CONSTRAINT fk_participante_evaluacion_usuario 
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    
    -- Llave foránea para quien agregó al participante
    CONSTRAINT fk_participante_evaluacion_agregado_por 
        FOREIGN KEY (agregado_por) REFERENCES usuarios(id) ON DELETE RESTRICT,
    
    -- Llave foránea para quien inició el cronómetro
    CONSTRAINT fk_participante_evaluacion_iniciado_por 
        FOREIGN KEY (iniciado_por) REFERENCES usuarios(id) ON DELETE SET NULL,
    
    -- Llave foránea para quien terminó el cronómetro
    CONSTRAINT fk_participante_evaluacion_terminado_por 
        FOREIGN KEY (terminado_por) REFERENCES usuarios(id) ON DELETE SET NULL,
    
    -- Constraint único para evitar duplicados
    UNIQUE KEY unique_evaluacion_usuario (evaluacion_id, usuario_id)
);
