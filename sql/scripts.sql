CREATE DATABASE IF NOT EXISTS tu_base_de_datos;
USE tu_base_de_datos;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    correo VARCHAR(100) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    isAdmin TINYINT(1) DEFAULT 0,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE eventos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    creado_por_usuario VARCHAR(50) NOT NULL,
    id_usuario_creado INT NOT NULL,
    lugar VARCHAR(150),
    observaciones TEXT,
    fecha_inicio DATETIME,
    estado VARCHAR(50),
    torneo_empezado_en DATETIME,
    torneo_iniciado_por INT,
    FOREIGN KEY (id_usuario_creado) REFERENCES usuarios(id),
    FOREIGN KEY (torneo_iniciado_por) REFERENCES usuarios(id)
);

-- Script para actualizar tablas existentes (ejecutar solo si la tabla ya existe)
-- ALTER TABLE eventos ADD COLUMN torneo_iniciado_por INT;
-- ALTER TABLE eventos ADD FOREIGN KEY (torneo_iniciado_por) REFERENCES usuarios(id);

CREATE TABLE participantes_evento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,

    tiempo_inicio DATETIME,
    tiempo_llegada DATETIME,
    tiempo_total TIME,

    tiempo_iniciado_por INT,
    tiempo_terminado_por INT,
    participante_agregado_por INT NOT NULL,
    evento_id INT NOT NULL,
    usuario_agregado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    detalles TEXT,

    -- Relaciones
    FOREIGN KEY (tiempo_iniciado_por) REFERENCES usuarios(id),
    FOREIGN KEY (tiempo_terminado_por) REFERENCES usuarios(id),
    FOREIGN KEY (participante_agregado_por) REFERENCES usuarios(id),
    FOREIGN KEY (evento_id) REFERENCES eventos(id)
);

-- ALTER TABLE participantes_evento ADD COLUMN detalles TEXT;

-- Datos de ejemplo para participantes (opcional - solo para pruebas)
-- Asume que ya existen usuarios y eventos en la base de datos

-- Ejemplo de inserción de participantes para evento con ID 1
-- INSERT INTO participantes_evento (codigo, nombre, participante_agregado_por, evento_id) VALUES 
-- ('P001', 'Juan Pérez', 1, 1),
-- ('P002', 'María García', 1, 1),
-- ('P003', 'Carlos López', 1, 1);

-- Ejemplo de participante con tiempos completos
-- UPDATE participantes_evento SET 
--     tiempo_inicio = '2024-01-15 14:30:15',
--     tiempo_llegada = '2024-01-15 14:45:23',
--     tiempo_total = '00:15:08',
--     tiempo_iniciado_por = 1,
--     tiempo_terminado_por = 1
-- WHERE codigo = 'P001';

-- Ejemplo de participante en progreso
-- UPDATE participantes_evento SET 
--     tiempo_inicio = '2024-01-15 14:32:45',
--     tiempo_iniciado_por = 1
-- WHERE codigo = 'P002';

CREATE TABLE sesiones (
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
CREATE TABLE invalidaciones_sesion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    motivo ENUM('cambio_password', 'eliminacion_usuario', 'logout_manual', 'admin_action') NOT NULL,
    fecha_invalidacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    invalidado_por INT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (invalidado_por) REFERENCES usuarios(id)
);

-- Agregar campos para control de sesiones
ALTER TABLE usuarios ADD COLUMN ultimo_login DATETIME;
ALTER TABLE usuarios ADD COLUMN password_cambiado_en DATETIME;
ALTER TABLE usuarios ADD COLUMN cuenta_bloqueada TINYINT(1) DEFAULT 0;
ALTER TABLE usuarios ADD COLUMN intentos_fallidos INT DEFAULT 0;
ALTER TABLE usuarios ADD COLUMN bloqueado_hasta DATETIME;
ALTER TABLE usuarios ADD COLUMN fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP;


-- Agregar columna usuario_id a participantes_evento
ALTER TABLE participantes_evento ADD COLUMN usuario_id INT;

-- Agregar la llave foránea
ALTER TABLE participantes_evento ADD FOREIGN KEY (usuario_id) REFERENCES usuarios(id);

-- Opcional: Agregar índice para mejorar rendimiento
CREATE INDEX idx_participante_usuario ON participantes_evento(usuario_id);


-- Eliminar todos los datos de participantes_evento
DELETE FROM participantes_evento;

-- Eliminar todos los datos de eventos
DELETE FROM eventos;

-- Opcional: Reiniciar los contadores AUTO_INCREMENT
ALTER TABLE participantes_evento AUTO_INCREMENT = 1;
ALTER TABLE eventos AUTO_INCREMENT = 1;