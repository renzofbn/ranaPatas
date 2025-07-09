-- Agregar sistema de roles a usuarios
-- Ejecutar este script para agregar la columna de roles

-- Agregar columna de rol a la tabla usuarios
ALTER TABLE usuarios 
ADD COLUMN rol INT DEFAULT 1 COMMENT '1=Participante, 2=Organizador, 3=Admin';

-- Crear tabla de referencia para roles (opcional, para mejor gestión)
CREATE TABLE roles (
    id INT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    descripcion TEXT,
    permisos TEXT COMMENT 'JSON con permisos específicos'
);

-- Insertar los roles básicos
INSERT INTO roles (id, nombre, descripcion) VALUES 
(1, 'Participante', 'Usuario básico que puede participar en eventos'),
(2, 'Organizador', 'Usuario que puede crear y gestionar eventos'),
(3, 'Administrador', 'Usuario con acceso completo al sistema');

-- Agregar índice para mejorar consultas
CREATE INDEX idx_usuarios_rol ON usuarios(rol);

-- Agregar llave foránea (opcional)
ALTER TABLE usuarios 
ADD CONSTRAINT fk_usuarios_rol 
FOREIGN KEY (rol) REFERENCES roles(id);

-- Actualizar usuarios existentes que sean admin para que tengan rol 3
UPDATE usuarios SET rol = 3 WHERE isAdmin = 1;

-- Actualizar otros usuarios existentes como participantes (por defecto ya es 1)
-- UPDATE usuarios SET rol = 1 WHERE isAdmin = 0 AND rol IS NULL;
