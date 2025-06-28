# Flask App - Aplicación principal

from flask import Flask
import os
from config import config
from db_connector import init_db
from routes.auth import auth_bp
from routes.blog import blog_bp
from routes.users import users_bp
from routes.eventos import eventos_bp

def create_app(config_name='default'):
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar la base de datos
    mysql = init_db(app)
    
    # Registrar blueprints
    app.register_blueprint(blog_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(eventos_bp)
    
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
    
    return app

# Crear la aplicación
app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    app.run(debug=True)
