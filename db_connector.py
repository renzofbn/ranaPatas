import os
from flask import Flask
from flask_mysqldb import MySQL
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(override=True)

# Variable global para MySQL
mysql = None

def init_db(app):
    """Inicializar la base de datos con la aplicación Flask"""
    global mysql
    
    # Configuración de MySQL desde variables de entorno
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
    app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))
    
    # Configuraciones adicionales para optimización
    app.config['MYSQL_AUTOCOMMIT'] = True
    app.config['MYSQL_CONNECT_TIMEOUT'] = 10
    app.config['MYSQL_READ_TIMEOUT'] = 10
    app.config['MYSQL_WRITE_TIMEOUT'] = 10
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
    
    mysql = MySQL(app)
    return mysql

def get_mysql():
    """Obtener la instancia de MySQL"""
    return mysql
