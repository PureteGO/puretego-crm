"""
PURETEGO CRM - Authentication Routes
Rotas de autenticação (login/logout)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import User
from config.database import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        with get_db() as db:
            user = db.query(User).filter(User.email == email).first()
            
            if user and user.check_password(password):
                # Login bem-sucedido
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['user_email'] = user.email
                session.permanent = True
                
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard.index'))
            else:
                flash('Email ou senha inválidos.', 'error')
    
    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    """Logout do usuário"""
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))


def login_required(f):
    """Decorator para rotas que requerem autenticação"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    
    return decorated_function
