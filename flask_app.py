# Flask App - Aplicación principal

from flask import Flask
import os
from config import config
from db_connector import init_db
from routes.auth import auth_bp
from routes.blog import blog_bp
from routes.users import users_bp
from routes.eventos import eventos_bp
from routes.participante import participante_bp
from routes.admin import admin_bp
from routes.evaluaciones import evaluaciones_bp
import atexit
import threading
import time

def cleanup_sessions_periodically(app):
    """Función para limpiar sesiones expiradas periódicamente"""
    while True:
        try:
            with app.app_context():
                from utils import cleanup_expired_sessions
                cleanup_expired_sessions()
            # Ejecutar cada hora
            time.sleep(3600)
        except Exception as e:
            print(f"Error en limpieza de sesiones: {e}")
            time.sleep(3600)

def create_app(config_name='default'):
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar la base de datos
    mysql = init_db(app)
    
    # Iniciar hilo de limpieza de sesiones después de configurar la app
    cleanup_thread = threading.Thread(target=cleanup_sessions_periodically, args=(app,), daemon=True)
    cleanup_thread.start()
    
    # Registrar blueprints
    app.register_blueprint(blog_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(eventos_bp)
    app.register_blueprint(participante_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(evaluaciones_bp)
    
    # Rutas de compatibilidad (para mantener las URLs anteriores)
    @app.route('/login')
    def login_redirect():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    @app.route('/register')
    def register_redirect():
        from flask import redirect, url_for
        return redirect(url_for('auth.register'))
    
    @app.route('/logout')
    def logout_redirect():
        from flask import redirect, url_for
        return redirect(url_for('auth.logout'))

    @app.route('/perfil')
    def perfil_redirect():
        from flask import redirect, url_for
        return redirect(url_for('auth.perfil'))
    
    # Manejador de errores 404
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('404.html'), 404
    
    # Hook para validar sesiones en cada request
    @app.before_request
    def validate_session_on_request():
        from flask import request, session, redirect, url_for
        from utils import get_current_user
        
        # Rutas que no requieren validación de sesión
        exempt_routes = [
            'auth.login', 'auth.register', 'auth.logout', 
            'blog.index', 'static', 'login_redirect', 'register_redirect',
            'logout_redirect', 'perfil_redirect'
        ]
        
        # Si la ruta actual no requiere autenticación, continuar
        if request.endpoint in exempt_routes or request.endpoint is None:
            return
        
        # Si el usuario está logueado, validar que su sesión sigue siendo válida
        if session.get('logged_in', False):
            current_user = get_current_user()
            if not current_user:
                # Sesión inválida, limpiar y redirigir
                session.clear()
                return redirect(url_for('auth.login'))

    return app

# Crear la aplicación
app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    app.run(debug=True)
