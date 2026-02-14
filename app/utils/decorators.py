"""
PURETEGO CRM - Authentication and Permission Decorators
Decorators para autenticação e controle de acesso
"""

from functools import wraps
from flask import session, redirect, url_for, flash, g
from flask_babel import _ as gettext
from config.database import get_db
from app.models import User


def get_current_user():
    """
    Obtém o usuário atual da sessão com eager loading de company e role.
    Retorna None se não houver usuário logado.
    O objeto retornado permanece vinculado ao db_session global (scoped_session).
    """
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    # Check if user is already loaded in g
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user
    
    from config.database import db_session
    from sqlalchemy.orm import joinedload
    
    try:
        user = db_session.query(User).options(
            joinedload(User.company),
            joinedload(User.role)
        ).filter(User.id == user_id).first()
        
        if user:
            g.current_user = user
            
        return user
    except Exception as e:
        import logging
        logging.error(f"Error in get_current_user: {e}")
        return None


def login_required(f):
    """
    Decorator para rotas que requerem autenticação.
    Verifica se o usuário está logado e ativo.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash(gettext('You must be logged in to access this page.'), 'warning')
            return redirect(url_for('auth.login'))
        
        user = get_current_user()
        
        if not user:
            session.clear()
            flash(gettext('Session expired. Please log in again.'), 'warning')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            session.clear()
            flash(gettext('Your account is inactive. Contact the administrator.'), 'error')
            return redirect(url_for('auth.login'))
        
        if user.company and not user.company.is_active:
            session.clear()
            flash(gettext('Your company is inactive. Contact support.'), 'error')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def permission_required(permission):
    """
    Decorator para rotas que requerem uma permissão específica.
    Uso: @permission_required('can_manage_users')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Primeiro verifica login
            if 'user_id' not in session:
                flash('Você precisa estar logado para acessar esta página.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Verifica permissão na sessão ou no banco
            permissions = session.get('permissions', {})
            if not permissions.get(permission, False):
                # Double-check no banco
                user = get_current_user()
                if not user or not user.has_permission(permission):
                    flash(gettext('You do not have permission to access this feature.'), 'error')
                    return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def role_required(*allowed_roles):
    """
    Decorator para rotas que requerem roles específicas.
    Uso: @role_required('owner', 'manager')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Você precisa estar logado para acessar esta página.', 'warning')
                return redirect(url_for('auth.login'))
            
            user_role = session.get('role')
            if user_role not in allowed_roles:
                # Superadmin bypass
                if session.get('is_superadmin'):
                    return f(*args, **kwargs)
                
                flash(gettext('You do not have permission to access this feature.'), 'error')
                return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
