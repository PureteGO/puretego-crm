"""
PURETEGO CRM - Authentication Routes
Rotas de autenticação (login/logout/register) com suporte multi-tenant
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from sqlalchemy.orm import joinedload
from app.models import User, Company, Role
from config.database import get_db
from app.services.audit_service import AuditService
from flask_babel import _

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login com suporte multi-tenant"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        with get_db() as db:
            # Carregar usuário com company e role em uma única query
            user = db.query(User).options(
                joinedload(User.company),
                joinedload(User.role)
            ).filter(User.email == email).first()
            
            if user and user.check_password(password):
                # Verificar se usuário está ativo
                if not user.is_active:
                    flash(_('Your account is inactive. Please contact the administrator.'), 'error')
                    return render_template('auth/login.html')
                
                # Verificar se empresa está ativa
                if user.company and not user.company.is_active:
                    flash(_('Your company is inactive. Please contact support.'), 'error')
                    return render_template('auth/login.html')
                
                # Login bem-sucedido - armazenar dados na sessão
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['user_email'] = user.email
                
                # Dados de multi-tenancy
                if user.company:
                    session['company_id'] = user.company_id
                    session['company_name'] = user.company.name
                    session['company_slug'] = user.company.slug
                    session['company_logo'] = user.company.logo_url
                    session['company_theme'] = user.company.theme_style or 'tech-teal'
                    session['company_plan'] = user.company.plan_tier
                    session['company_currency'] = user.company.currency_symbol or 'Gs'
                    session['workflow_mode'] = user.company.workflow_mode or Company.WORKFLOW_LEAN
                
                # Dados de role e permissões
                if user.role:
                    session['role'] = user.role.name
                    session['role_display'] = user.role.display_name
                    session['permissions'] = user.role.get_permissions_dict()
                else:
                    session['role'] = None
                    session['permissions'] = {}
                
                # Superadmin PureteGO (suporte técnico)
                session['is_superadmin'] = user.is_superadmin
                
                session.permanent = True
                
                # Audit log - successful login
                AuditService.log_login(user.id, user.company_id, success=True)
                
                flash(_('Welcome, %(name)s!', name=user.name), 'success')
                return redirect(url_for('dashboard.index'))
            else:
                # Audit log - failed login
                if user:
                    AuditService.log_login(user.id, user.company_id, success=False)
                flash(_('Invalid email or password.'), 'error')
    
    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    """Logout do usuário - limpa toda a sessão"""
    # Audit log - logout
    user_id = session.get('user_id')
    company_id = session.get('company_id')
    if user_id:
        AuditService.log_logout(user_id, company_id)
    
    session.clear()
    flash(_('You have logged out.'), 'info')
    return redirect(url_for('auth.login'))


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Solicitar recuperação de senha por email"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        with get_db() as db:
            user = db.query(User).filter(User.email == email).first()
            
            if user and user.is_active:
                # Gerar token
                token = user.generate_reset_token()
                db.commit()
                
                # Construir URL de reset
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                
                # Enviar email
                from app.services.email_service import send_password_reset_email
                if send_password_reset_email(user, reset_url):
                    flash(_('Recovery instructions were sent to your email.'), 'success')
                else:
                    flash(_('Error sending email. Please try again later.'), 'error')
            else:
                # Não revelar se o email existe ou não (segurança)
                flash('Se enviaron instrucciones de recuperación a tu email.', 'success')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Resetar senha usando token"""
    with get_db() as db:
        # Buscar usuário pelo token
        user = db.query(User).filter(User.reset_token == token).first()
        
        if not user or not user.verify_reset_token(token):
            flash(_('Invalid or expired recovery link.'), 'error')
            return redirect(url_for('auth.forgot_password'))
        
        if request.method == 'POST':
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if len(password) < 6:
                flash(_('Password must have at least 6 characters.'), 'error')
                return render_template('auth/reset_password.html', token=token)
            
            if password != confirm_password:
                flash(_('Passwords do not match.'), 'error')
                return render_template('auth/reset_password.html', token=token)
            
            # Atualizar senha
            user.set_password(password)
            user.clear_reset_token()
            db.commit()
            
            flash(_('Password updated successfully! You can now log in.'), 'success')
            return redirect(url_for('auth.login'))
        
        return render_template('auth/reset_password.html', token=token)


# Re-export decorators para compatibilidade com código existente
from app.utils.decorators import login_required, permission_required, role_required, get_current_user

