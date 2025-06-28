from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db_connector import get_mysql
from utils import validate_email, validate_username, validate_password, hash_password, check_password, require_login, get_current_user

# Crear el blueprint para autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario_o_correo = request.form['usuario_o_correo']
        contrasena = request.form['contrasena']
        
        # Validaciones básicas
        if not usuario_o_correo or not contrasena:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('auth/login.html')
        
        try:
            mysql = get_mysql()
            cur = mysql.connection.cursor()
            
            # Buscar usuario por nombre de usuario o correo
            cur.execute("SELECT id, usuario, correo, contrasena, isAdmin FROM usuarios WHERE usuario = %s OR correo = %s", 
                       (usuario_o_correo, usuario_o_correo))
            user = cur.fetchone()
            cur.close()
            
            if not user:
                flash('Usuario o contraseña incorrectos', 'error')
                return render_template('auth/login.html')
            
            # Verificar contraseña
            if not check_password(contrasena, user[3]):  # user[3] es la contraseña hasheada
                flash('Usuario o contraseña incorrectos', 'error')
                return render_template('auth/login.html')
            
            # Login exitoso - crear sesión
            session['user_id'] = user[0]      # id
            session['usuario'] = user[1]      # usuario
            session['correo'] = user[2]       # correo
            session['is_admin'] = bool(user[4])  # isAdmin
            session['logged_in'] = True
            
            flash(f'¡Bienvenido {user[1]}!', 'success')
            
            # Redirigir a la página solicitada o al inicio
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('blog.index'))
            
        except Exception as e:
            flash(f'Error al iniciar sesión: {str(e)}', 'error')
            return render_template('auth/login.html')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        usuario = request.form['usuario']
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']
        
        # Validaciones básicas
        if not usuario or not correo or not contrasena or not confirmar_contrasena:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('auth/register.html')
        
        # Validar nombre de usuario
        valid_user, user_msg = validate_username(usuario)
        if not valid_user:
            flash(user_msg, 'error')
            return render_template('auth/register.html')
        
        # Validar email
        if not validate_email(correo):
            flash('El formato del correo electrónico no es válido', 'error')
            return render_template('auth/register.html')
        
        # Validar contraseña
        valid_pass, pass_msg = validate_password(contrasena)
        if not valid_pass:
            flash(pass_msg, 'error')
            return render_template('auth/register.html')
        
        # Verificar que las contraseñas coincidan
        if contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('auth/register.html')
        
        try:
            mysql = get_mysql()
            cur = mysql.connection.cursor()
            
            # Verificar si el usuario ya existe
            cur.execute("SELECT * FROM usuarios WHERE usuario = %s OR correo = %s", (usuario, correo))
            existing_user = cur.fetchone()
            
            if existing_user:
                flash('El usuario o correo ya existe', 'error')
                cur.close()
                return render_template('auth/register.html')
            
            # Hash de la contraseña
            hashed_password = hash_password(contrasena)
            
            # Insertar nuevo usuario
            cur.execute("INSERT INTO usuarios (usuario, correo, contrasena) VALUES (%s, %s, %s)", 
                       (usuario, correo, hashed_password))
            mysql.connection.commit()
            cur.close()
            
            flash('¡Registro exitoso! Ya puedes iniciar sesión', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'Error al registrar usuario: {str(e)}', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    # Limpiar la sesión
    session.clear()
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('blog.index'))

@auth_bp.route('/perfil')
@require_login()
def perfil():
    """Página de perfil del usuario (requiere login)"""
    user = get_current_user()
    return render_template('auth/perfil.html', user=user)
