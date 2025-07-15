# Configuración específica para PythonAnywhere
# Este archivo debe ser colocado en tu directorio de PythonAnywhere

import sys
import os

# Añadir el path de tu proyecto
path = '/home/tuusuario/mysite'  # Cambiar por tu path real
if path not in sys.path:
    sys.path.insert(0, path)

# Configurar variables de entorno para producción
os.environ['FLASK_ENV'] = 'production'

from flask_app import app as application

# Configuración adicional para PythonAnywhere
application.config.update(
    # Configuraciones para optimizar rendimiento
    SEND_FILE_MAX_AGE_DEFAULT=31536000,  # Cache estático por 1 año
    PERMANENT_SESSION_LIFETIME=3600,     # Sesiones expiran en 1 hora
    SESSION_COOKIE_SECURE=True,          # Solo HTTPS
    SESSION_COOKIE_HTTPONLY=True,        # No accesible via JavaScript
    SESSION_COOKIE_SAMESITE='Lax',       # Protección CSRF
    
    # Configuraciones específicas para evitar timeouts
    SQLALCHEMY_ENGINE_OPTIONS={
        'pool_timeout': 20,
        'pool_recycle': 300,  # Reciclar conexiones cada 5 minutos
        'pool_pre_ping': True  # Verificar conexiones antes de usar
    }
)

# Deshabilitar modo debug explícitamente en producción
application.config['DEBUG'] = False

# Función para limpiar recursos al apagar
def cleanup():
    """Limpiar recursos al apagar la aplicación"""
    try:
        # Aquí puedes agregar limpieza adicional si es necesaria
        pass
    except Exception as e:
        print(f"Error durante limpieza: {e}")

import atexit
atexit.register(cleanup)

if __name__ == "__main__":
    application.run()
