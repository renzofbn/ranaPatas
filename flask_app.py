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
from datetime import datetime, timedelta

def create_app(config_name='default'):
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Configurar logging mejorado
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Aplicación iniciada')
    
    # Inicializar la base de datos
    mysql = init_db(app)
    
    # Variable para tracking de última limpieza
    app.config['LAST_CLEANUP'] = datetime.now()
    
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
        from flask import request, session, redirect, url_for, g, current_app
        from utils import get_current_user, cleanup_expired_sessions_if_needed
        
        # Rutas que no requieren validación de sesión
        exempt_routes = [
            'auth.login', 'auth.register', 'auth.logout', 
            'blog.index', 'static', 'login_redirect', 'register_redirect',
            'logout_redirect', 'perfil_redirect'
        ]
        
        # Si la ruta actual no requiere autenticación, continuar
        if request.endpoint in exempt_routes or request.endpoint is None:
            # Aprovechar requests a rutas públicas para limpieza ocasional
            cleanup_expired_sessions_if_needed()
            return
        
        # Cache del usuario en g para evitar múltiples consultas DB
        if not hasattr(g, 'current_user'):
            # Si el usuario está logueado, validar que su sesión sigue siendo válida
            if session.get('logged_in', False):
                try:
                    current_user = get_current_user()
                    if not current_user:
                        # Sesión inválida, limpiar y redirigir
                        session.clear()
                        return redirect(url_for('auth.login'))
                    g.current_user = current_user
                    
                    # Limpieza ocasional cuando hay actividad de usuarios
                    cleanup_expired_sessions_if_needed()
                    
                except Exception as e:
                    # Error al validar sesión, limpiar y redirigir
                    app.logger.error(f"Error validando sesión: {e}")
                    session.clear()
                    return redirect(url_for('auth.login'))
            else:
                return redirect(url_for('auth.login'))

    return app

# Crear la aplicación
app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    app.run(debug=True)
