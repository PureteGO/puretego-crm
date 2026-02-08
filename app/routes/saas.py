from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_babel import _
from app.routes.auth import login_required, permission_required
from app.models import Company, User, Role, SaasPackage
from config.database import get_db
from app.services.audit_service import AuditService
import uuid
import os
from flask import current_app

bp = Blueprint('saas', __name__, url_prefix='/saas')

@bp.before_request
@login_required
def require_superadmin():
    """Ensure only superadmins can access this area"""
    if not session.get('is_superadmin'):
        flash(_('Acceso denegado. Área restringida para Super Administradores.'), 'error')
        return redirect(url_for('dashboard.index'))

@bp.route('/')
def dashboard():
    """SaaS Admin Dashboard"""
    with get_db() as db:
        # Get all companies with stats
        companies = db.query(Company).order_by(Company.created_at.desc()).all()
        
        companies_data = []
        for c in companies:
            companies_data.append({
                'id': c.id,
                'name': c.name,
                'slug': c.slug,
                'email': c.email,
                'is_active': c.is_active,
                'created_at': c.created_at,
                'users_count': len(c.users),
                'clients_count': len(c.clients)
            })
            
    return render_template('saas/dashboard.html', companies=companies_data)

@bp.route('/companies/create', methods=['POST'])
def create_company():
    """Create a new company (tenant)"""
    name = request.form.get('name')
    email = request.form.get('email')
    
    if not name:
        flash(_('Nombre de la empresa es obligatorio.'), 'error')
        return redirect(url_for('saas.dashboard'))
        
    # Generate slug from name
    slug = name.lower().replace(' ', '-').replace('.', '').replace(',', '')
    # Ensure uniqueness (simple check)
    slug = f"{slug}-{uuid.uuid4().hex[:4]}"
    
    with get_db() as db:
        new_company = Company(
            name=name,
            slug=slug,
            email=email
        )
        db.add(new_company)
        db.commit()
        
        # Audit log - company creation
        AuditService.log_create('Company', new_company.id, 
                                new_values={'name': name, 'email': email, 'slug': slug})
        
        flash(_('Empresa %(name)s creada con éxito!', name=name), 'success')
        
    return redirect(url_for('saas.dashboard'))

@bp.route('/companies/<int:company_id>/edit', methods=['GET', 'POST'])
def edit_company(company_id):
    """Edit company configuration as SuperAdmin"""
    with get_db() as db:
        company = db.query(Company).get(company_id)
        
        if not company:
            flash(_('Empresa no encontrada'), 'error')
            return redirect(url_for('saas.dashboard'))
            
        if request.method == 'POST':
            company.name = request.form.get('name')
            company.email = request.form.get('email')
            company.phone = request.form.get('phone')
            company.address = request.form.get('address')
            company.theme_style = request.form.get('theme_style')
            company.currency_symbol = request.form.get('currency_symbol')
            company.is_active = request.form.get('is_active') == 'on'
            
            db.commit()
            
            # Audit log - company update
            AuditService.log_update('Company', company.id, description=f'Updated company {company.name}')
            
            flash(_('Empresa actualizada con éxito!'), 'success')
            return redirect(url_for('saas.dashboard'))
            
        return render_template('saas/edit_company.html', company=company, theme_choices=Company.THEME_CHOICES)

@bp.route('/companies/<int:company_id>/impersonate')
def impersonate(company_id):
    """Log in as admin of this company (Impersonation)"""
    with get_db() as db:
        company = db.query(Company).get(company_id)
        if not company:
            return redirect(url_for('saas.dashboard'))
            
        # Find an admin user or the first user of this company
        # Ideally we impersonate a specific user, but for now let's just switch context if possible
        # Since auth relies on user, let's find the first user of this company
        target_user = db.query(User).filter(User.company_id == company.id).first()
        
        if target_user:
            # Update session
            session['user_id'] = target_user.id
            session['user_name'] = f"{target_user.name} (Impersonated)"
            session['user_email'] = target_user.email
            session['company_id'] = company.id
            session['company_name'] = company.name
            session['company_logo'] = company.logo_url
            session['company_theme'] = company.theme_style
            session['company_currency'] = company.currency_symbol or 'Gs'
            
            # Keep superadmin flag
            session['is_superadmin'] = True
            
            # Audit log - impersonation (CRITICAL for security)
            AuditService.log_impersonation(
                admin_user_id=session.get('user_id'),
                target_user_id=target_user.id,
                target_company_id=company.id
            )
            
            flash(_('Ahora estás accediendo como %(name)s', name=company.name), 'info')
            return redirect(url_for('dashboard.index'))
        else:
            flash(_('Esta empresa no tiene usuarios para impersonar.'), 'warning')
            return redirect(url_for('saas.dashboard'))

# --- SaaS Package Routes ---

@bp.route('/packages')
def packages_list():
    """List all SaaS Packages"""
    with get_db() as db:
        packages = db.query(SaasPackage).all()
        return render_template('saas/packages/index.html', packages=packages)

@bp.route('/packages/create', methods=['GET', 'POST'])
def create_package():
    """Create a new SaaS Package"""
    if request.method == 'POST':
        with get_db() as db:
            pkg = SaasPackage(
                name=request.form.get('name'),
                description=request.form.get('description'),
                price=float(request.form.get('price') or 0),
                max_users=int(request.form.get('max_users') or 1),
                max_clients=int(request.form.get('max_clients') or 50),
                health_check_credits=int(request.form.get('health_check_credits') or 0),
                is_active=request.form.get('is_active') == 'on'
            )
            db.add(pkg)
            db.commit()
            flash(_('Paquete creado con éxito!'), 'success')
            return redirect(url_for('saas.packages_list'))
            
    return render_template('saas/packages/edit.html', package=None)

@bp.route('/packages/<int:package_id>/edit', methods=['GET', 'POST'])
def edit_package(package_id):
    """Edit an existing SaaS Package"""
    with get_db() as db:
        pkg = db.query(SaasPackage).get(package_id)
        if not pkg:
            return redirect(url_for('saas.packages_list'))
            
        if request.method == 'POST':
            pkg.name = request.form.get('name')
            pkg.description = request.form.get('description')
            pkg.price = float(request.form.get('price') or 0)
            pkg.max_users = int(request.form.get('max_users') or 1)
            pkg.max_clients = int(request.form.get('max_clients') or 50)
            pkg.health_check_credits = int(request.form.get('health_check_credits') or 0)
            pkg.is_active = request.form.get('is_active') == 'on'
            
            db.commit()
            flash(_('Paquete actualizado con éxito!'), 'success')
            return redirect(url_for('saas.packages_list'))
            
        return render_template('saas/packages/edit.html', package=pkg)
