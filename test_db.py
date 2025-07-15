#!/usr/bin/env python3
"""
Script para probar la conexión a la base de datos
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(override=True)

def test_db_connection():
    """Probar conexión a la base de datos"""
    try:
        import MySQLdb
        
        # Obtener credenciales
        host = os.getenv('MYSQL_HOST')
        user = os.getenv('MYSQL_USER') 
        password = os.getenv('MYSQL_PASSWORD')
        database = os.getenv('MYSQL_DB')
        port = int(os.getenv('MYSQL_PORT', 3306))
        
        print(f"Intentando conectar a:")
        print(f"  Host: {host}")
        print(f"  Usuario: {user}")
        print(f"  Base de datos: {database}")
        print(f"  Puerto: {port}")
        
        # Intentar conexión
        connection = MySQLdb.connect(
            host=host,
            user=user,
            passwd=password,
            db=database,
            port=port,
            connect_timeout=10
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        user_count = cursor.fetchone()
        
        print(f"✅ Conexión exitosa!")
        print(f"✅ Versión MySQL: {version[0]}")
        print(f"✅ Usuarios en la tabla: {user_count[0]}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_flask_db():
    """Probar conexión usando Flask-MySQLdb"""
    try:
        # Añadir el path del proyecto
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from flask import Flask
        from db_connector import init_db
        
        app = Flask(__name__)
        
        with app.app_context():
            mysql = init_db(app)
            
            cur = mysql.connection.cursor()
            cur.execute("SELECT VERSION()")
            version = cur.fetchone()
            
            cur.execute("SELECT COUNT(*) FROM usuarios")  
            user_count = cur.fetchone()
            
            print(f"✅ Flask-MySQLdb conexión exitosa!")
            print(f"✅ Versión MySQL: {version[0]}")
            print(f"✅ Usuarios en la tabla: {user_count[0]}")
            
            cur.close()
            
        return True
        
    except Exception as e:
        print(f"❌ Error con Flask-MySQLdb: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Probando conexión directa a MySQL...")
    direct_ok = test_db_connection()
    
    print("\n🔍 Probando conexión con Flask-MySQLdb...")
    flask_ok = test_flask_db()
    
    if direct_ok and flask_ok:
        print("\n🎉 Todas las pruebas exitosas!")
        sys.exit(0)
    else:
        print("\n🚨 Algunas pruebas fallaron!")
        sys.exit(1)
