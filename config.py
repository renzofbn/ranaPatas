"""
Configuración de la aplicación Flask
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(override=True)

class Config:
    """Configuración base"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'tu_clave_secreta_aqui')
    
    # Configuración de MySQL
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_DB = os.getenv('MYSQL_DB')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    
    # Configuraciones adicionales para evitar timeouts
    MYSQL_AUTOCOMMIT = True
    MYSQL_CONNECT_TIMEOUT = 10
    MYSQL_READ_TIMEOUT = 10
    MYSQL_WRITE_TIMEOUT = 10

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False

# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
