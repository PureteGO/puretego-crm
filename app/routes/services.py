from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_babel import gettext as _
from app.utils.decorators import login_required, permission_required
from app.models import Service, ServicePackage
from config.database import get_db
from app.utils.tenant import filter_by_company

bp = Blueprint('services', __name__, url_prefix='/services')

@bp.route('/')
@login_required
@permission_required('can_manage_company')
def index():
    """List all services and packages for the current company"""
    company_id = session.get('company_id')
    
    with get_db() as db:
        # Use db_session directly to keep instances attached during rendering
        services = db.query(Service).filter(
            (Service.company_id == company_id) | (Service.company_id == None)
        ).all()
        
        packages = db.query(ServicePackage).filter(
            (ServicePackage.company_id == company_id) | (ServicePackage.company_id == None)
        ).all()
        
        return render_template('services/index.html', services=services, packages=packages)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_company')
def create_service():
    """Create a new service"""
    if request.method == 'POST':
        with get_db() as db:
            service = Service(
                name=request.form.get('name'),
                description=request.form.get('description'),
                html_description=request.form.get('html_description'),
                base_price=float(request.form.get('base_price') or 0)
            )
            service.company_id = session.get('company_id')
            db.add(service)
            db.commit()
            flash(_('Service created successfully!'), 'success')
            return redirect(url_for('services.index'))
            
    return render_template('services/edit_service.html', service=None)

@bp.route('/<int:service_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_company')
def edit_service(service_id):
    """Edit an existing service"""
    with get_db() as db:
        service = filter_by_company(db.query(Service), Service).filter(Service.id == service_id).first()
        if not service:
            flash(_('Service not found or permission denied.'), 'error')
            return redirect(url_for('services.index'))
            
        if request.method == 'POST':
            service.name = request.form.get('name')
            service.description = request.form.get('description')
            service.html_description = request.form.get('html_description')
            service.base_price = float(request.form.get('base_price') or 0)
            db.commit()
            flash(_('Service updated successfully!'), 'success')
            return redirect(url_for('services.index'))
        return render_template('services/edit_service.html', service=service)

@bp.route('/packages/create', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_company')
def create_package():
    """Create a new service package"""
    if request.method == 'POST':
        with get_db() as db:
            package = ServicePackage(
                name=request.form.get('name'),
                description=request.form.get('description'),
                html_description=request.form.get('html_description'),
                price=float(request.form.get('price') or 0),
                features=request.form.get('features')
            )
            package.company_id = session.get('company_id')
            db.add(package)
            db.commit()
            flash(_('Package created successfully!'), 'success')
            return redirect(url_for('services.index'))
            
    return render_template('services/edit_package.html', package=None)

@bp.route('/packages/<int:package_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('can_manage_company')
def edit_package(package_id):
    """Edit an existing service package"""
    with get_db() as db:
        package = filter_by_company(db.query(ServicePackage), ServicePackage).filter(ServicePackage.id == package_id).first()
        if not package:
            flash(_('Package not found or permission denied.'), 'error')
            return redirect(url_for('services.index'))
            
        if request.method == 'POST':
            package.name = request.form.get('name')
            package.description = request.form.get('description')
            package.html_description = request.form.get('html_description')
            package.price = float(request.form.get('price') or 0)
            package.features = request.form.get('features')
            db.commit()
            flash(_('Package updated successfully!'), 'success')
            return redirect(url_for('services.index'))
        return render_template('services/edit_package.html', package=package)
