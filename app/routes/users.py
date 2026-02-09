"""
PURETEGO CRM - Users Routes
Rotas de gestão de usuários dentro de uma empresa (multi-tenant)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.routes.auth import login_required
from app.utils.decorators import permission_required
from app.utils.tenant import filter_by_company
from app.models import User, Role, Company
from config.database import get_db
from sqlalchemy.orm import joinedload
from app.utils.saas_limits import PLAN_LEAN, PLAN_PURETEGO

bp = Blueprint('users', __name__, url_prefix='/users')


@bp.route('/')
@login_required
@permission_required('can_manage_users')
def index():
    """Lista de usuários da empresa"""
    with get_db() as db:
        company_id = session.get('company_id')
        
        users_query = db.query(User).options(
            joinedload(User.role),
            joinedload(User.company)
        )
        
        # Superadmins veem todos os usuários
        if not session.get('is_superadmin'):
            users_query = users_query.filter(User.company_id == company_id)
        
        users = users_query.order_by(User.name).all()
        
        # Serialize para evitar DetachedInstanceError
        users_list = [{
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'is_active': u.is_active,
            'is_superadmin': u.is_superadmin,
            'role_name': u.role.display_name if u.role else 'Sem role',
            'company_name': u.company.name if u.company else 'Sem empresa',
            'base_salary': float(u.base_salary or 0),
            'receives_commission': u.receives_commission,
            'created_at': u.created_at
        } for u in users]
        
        roles = db.query(Role).order_by(Role.id).all()
        
        # Filter roles based on plan
        plan = session.get('company_plan')
        if plan not in [PLAN_LEAN, PLAN_PURETEGO]:
             roles = [r for r in roles if r.name != 'gmb_manager']

        roles_list = [{'id': r.id, 'name': r.name, 'display_name': r.display_name} for r in roles]
    
    return render_template('users/index.html', users=users_list, roles=roles_list)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_users')
def create():
    """Criar novo usuário na empresa"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role_id = request.form.get('role_id')
        try:
            base_salary_raw = request.form.get('base_salary', '0').replace(',', '.')
            base_salary = float(base_salary_raw) if base_salary_raw else 0.0
        except (ValueError, TypeError):
            base_salary = 0.0
        
        receives_commission = request.form.get('receives_commission') == 'on'
        
        with get_db() as db:
            # Verificar se email já existe
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                flash('Este email já está em uso.', 'error')
                roles = db.query(Role).order_by(Role.id).all()
                plan = session.get('company_plan')
                if plan not in [PLAN_LEAN, PLAN_PURETEGO]:
                     roles = [r for r in roles if r.name != 'gmb_manager']
                roles_list = [{'id': r.id, 'name': r.name, 'display_name': r.display_name} for r in roles]
                return render_template('users/create.html', roles=roles_list)
            
            # Criar usuário vinculado à empresa do criador
            user = User(
                name=name,
                email=email,
                password=password,
                company_id=session.get('company_id'),
                role_id=int(role_id) if role_id else None,
                base_salary=base_salary,
                receives_commission=receives_commission
            )
            
            db.add(user)
            db.commit()
            
            flash(f'Usuário {name} criado com sucesso!', 'success')
            return redirect(url_for('users.index'))
    
    with get_db() as db:
        roles = db.query(Role).order_by(Role.id).all()
        plan = session.get('company_plan')
        if plan not in [PLAN_LEAN, PLAN_PURETEGO]:
             roles = [r for r in roles if r.name != 'gmb_manager']
        roles_list = [{'id': r.id, 'name': r.name, 'display_name': r.display_name} for r in roles]
    
    return render_template('users/create.html', roles=roles_list)


@bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_users')
def edit(user_id):
    """Editar usuário"""
    with get_db() as db:
        user = db.query(User).options(
            joinedload(User.role),
            joinedload(User.company)
        ).filter(User.id == user_id).first()
        
        if not user:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('users.index'))
        
        # Verificar se pode editar (mesma empresa ou superadmin)
        if not session.get('is_superadmin') and user.company_id != session.get('company_id'):
            flash('Você não pode editar usuários de outra empresa.', 'error')
            return redirect(url_for('users.index'))
        
        if request.method == 'POST':
            user.name = request.form.get('name')
            
            # Só atualiza email se for diferente
            new_email = request.form.get('email')
            if new_email != user.email:
                existing = db.query(User).filter(User.email == new_email).first()
                if existing:
                    flash('Este email já está em uso.', 'error')
                    roles = db.query(Role).order_by(Role.id).all()
                    roles_list = [{'id': r.id, 'name': r.name, 'display_name': r.display_name} for r in roles]
                    return render_template('users/edit.html', user=user, roles=roles_list)
                user.email = new_email
            
            # Atualiza senha só se fornecida
            new_password = request.form.get('password')
            if new_password:
                user.set_password(new_password)
            
            role_id = request.form.get('role_id')
            user.role_id = int(role_id) if role_id else None
            
            user.base_salary = float(request.form.get('base_salary') or 0)
            user.receives_commission = request.form.get('receives_commission') == 'on'
            
            user.is_active = request.form.get('is_active') == 'on'
            
            db.commit()
            
            flash(f'Usuário {user.name} atualizado com sucesso!', 'success')
            return redirect(url_for('users.index'))
        
        roles = db.query(Role).order_by(Role.id).all()
        plan = session.get('company_plan')
        if plan not in [PLAN_LEAN, PLAN_PURETEGO]:
             roles = [r for r in roles if r.name != 'gmb_manager']
        roles_list = [{'id': r.id, 'name': r.name, 'display_name': r.display_name} for r in roles]
        
        return render_template('users/edit.html', user=user, roles=roles_list)


@bp.route('/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@permission_required('can_manage_users')
def toggle_active(user_id):
    """Ativar/desativar usuário"""
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('users.index'))
        
        # Não pode desativar a si mesmo
        if user.id == session.get('user_id'):
            flash('Você não pode desativar sua própria conta.', 'error')
            return redirect(url_for('users.index'))
        
        # Verificar permissão
        if not session.get('is_superadmin') and user.company_id != session.get('company_id'):
            flash('Você não pode modificar usuários de outra empresa.', 'error')
            return redirect(url_for('users.index'))
        
        user.is_active = not user.is_active
        db.commit()
        
        status = 'ativado' if user.is_active else 'desativado'
        flash(f'Usuário {user.name} {status} com sucesso!', 'success')
    
    return redirect(url_for('users.index'))
