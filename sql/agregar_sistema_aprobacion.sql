-- Agregar sistema de aprobación de usuarios
-- Ejecutar este script para agregar las columnas necesarias

-- Agregar campo nombre si no existe (para usuarios existentes)
ALTER TABLE usuarios 
ADD COLUMN nombre VARCHAR(100) AFTER id;

-- Agregar columnas de estado de aprobación a la tabla usuarios
ALTER TABLE usuarios 
ADD COLUMN estado_aprobacion ENUM('pendiente', 'aprobado', 'rechazado') DEFAULT 'pendiente',
ADD COLUMN fecha_aprobacion DATETIME NULL,
ADD COLUMN aprobado_por INT NULL,
ADD COLUMN observaciones_admin TEXT NULL;

-- Agregar llave foránea para el administrador que aprobó
ALTER TABLE usuarios 
ADD CONSTRAINT fk_usuarios_aprobado_por 
FOREIGN KEY (aprobado_por) REFERENCES usuarios(id);

-- Índice para mejorar consultas por estado
CREATE INDEX idx_usuarios_estado_aprobacion ON usuarios(estado_aprobacion);

-- Actualizar usuarios existentes como aprobados (opcional)
-- Si ya tienes usuarios registrados y quieres que sigan funcionando
UPDATE usuarios SET estado_aprobacion = 'aprobado', fecha_aprobacion = NOW() WHERE estado_aprobacion = 'pendiente';

-- Crear tabla de notificaciones para administradores (opcional)
CREATE TABLE notificaciones_admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(50) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    usuario_relacionado INT,
    leida TINYINT(1) DEFAULT 0,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_relacionado) REFERENCES usuarios(id) ON DELETE CASCADE
);
