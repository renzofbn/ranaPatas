from flask import Blueprint, render_template

# Crear el blueprint para el blog
blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/')
def index():
    return render_template('blog/01-index.html')

@blog_bp.route('/programa')
def programa():
    return render_template('blog/02-programa.html')

@blog_bp.route('/inscripcion')
def inscripcion():
    return render_template('blog/03-inscripcion.html')

@blog_bp.route('/eventos/registro')
def eventos_registro():
    return render_template('blog/04-eventos-registro.html')
