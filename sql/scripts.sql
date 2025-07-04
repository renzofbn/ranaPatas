CREATE DATABASE IF NOT EXISTS tu_base_de_datos;
USE tu_base_de_datos;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    correo VARCHAR(100) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    isAdmin TINYINT(1) DEFAULT 0
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

    -- Relaciones
    FOREIGN KEY (tiempo_iniciado_por) REFERENCES usuarios(id),
    FOREIGN KEY (tiempo_terminado_por) REFERENCES usuarios(id),
    FOREIGN KEY (participante_agregado_por) REFERENCES usuarios(id),
    FOREIGN KEY (evento_id) REFERENCES eventos(id)
);

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

