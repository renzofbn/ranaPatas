-- Script simple para poblar tabla roles vacía

USE patas_de_rana;

-- Verificar que la tabla roles existe pero está vacía
SELECT 'Estado actual de roles:' as info;
SELECT COUNT(*) as total_roles FROM roles;

-- Insertar roles básicos (usar INSERT en lugar de INSERT IGNORE para ver errores)
INSERT INTO roles (id, nombre, descripcion) VALUES
(1, 'Usuario', 'Usuario básico que puede participar en eventos'),
(2, 'Organizador', 'Usuario que puede crear y gestionar eventos'),
(3, 'Administrador', 'Usuario con permisos completos del sistema');

-- Verificar que se insertaron correctamente
SELECT 'Roles insertados:' as info;
SELECT * FROM roles;

-- Si hay usuarios existentes sin rol, asignarles rol de participante
UPDATE usuarios SET rol = 1 WHERE rol IS NULL;

-- Verificar usuarios
SELECT 'Estado de usuarios:' as info;
SELECT COUNT(*) as total_usuarios FROM usuarios;
SELECT COUNT(*) as usuarios_con_rol FROM usuarios WHERE rol IS NOT NULL;

SELECT 'FIX COMPLETADO: Ahora puedes registrar usuarios nuevos' as resultado;
