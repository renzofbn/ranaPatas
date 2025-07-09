-- Script de actualización para sistema de sesiones
-- Ejecutar este script después de tener las tablas básicas creadas

-- Tabla de sesiones
CREATE TABLE IF NOT EXISTS sesiones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion DATETIME NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    activa TINYINT(1) DEFAULT 1,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_usuario_activa (usuario_id, activa)
);

-- Tabla para registrar eventos de invalidación
CREATE TABLE IF NOT EXISTS invalidaciones_sesion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    motivo ENUM('cambio_password', 'eliminacion_usuario', 'logout_manual', 'admin_action') NOT NULL,
    fecha_invalidacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    invalidado_por INT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (invalidado_por) REFERENCES usuarios(id)
);

-- Agregar campos para control de sesiones a la tabla usuarios
-- Usar IF NOT EXISTS para evitar errores si ya existen

SET @sql = IF((SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE table_name = 'usuarios' 
               AND table_schema = DATABASE()
               AND column_name = 'ultimo_login') = 0,
             'ALTER TABLE usuarios ADD COLUMN ultimo_login DATETIME',
             'SELECT "Column ultimo_login already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF((SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE table_name = 'usuarios' 
               AND table_schema = DATABASE()
               AND column_name = 'password_cambiado_en') = 0,
             'ALTER TABLE usuarios ADD COLUMN password_cambiado_en DATETIME',
             'SELECT "Column password_cambiado_en already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF((SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE table_name = 'usuarios' 
               AND table_schema = DATABASE()
               AND column_name = 'cuenta_bloqueada') = 0,
             'ALTER TABLE usuarios ADD COLUMN cuenta_bloqueada TINYINT(1) DEFAULT 0',
             'SELECT "Column cuenta_bloqueada already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF((SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE table_name = 'usuarios' 
               AND table_schema = DATABASE()
               AND column_name = 'intentos_fallidos') = 0,
             'ALTER TABLE usuarios ADD COLUMN intentos_fallidos INT DEFAULT 0',
             'SELECT "Column intentos_fallidos already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF((SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE table_name = 'usuarios' 
               AND table_schema = DATABASE()
               AND column_name = 'bloqueado_hasta') = 0,
             'ALTER TABLE usuarios ADD COLUMN bloqueado_hasta DATETIME',
             'SELECT "Column bloqueado_hasta already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Mensaje de confirmación
SELECT 'Sistema de sesiones actualizado correctamente' as mensaje;
