from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.routes.auth import login_required
from app.models import Project, ProjectTicket, Client
from app.utils.tenant import filter_by_company
from config.database import get_db
from datetime import datetime
from flask_babel import gettext as _
import logging

bp = Blueprint('projects', __name__, url_prefix='/projects')

@bp.route('/')
@login_required
def index():
    """List of all active projects for the company."""
    with get_db() as db:
        from sqlalchemy.orm import joinedload
        query = db.query(Project).options(joinedload(Project.client))
        query = filter_by_company(query, Project)
        
        # Simple status filter
        status = request.args.get('status', 'active')
        if status:
            query = query.filter(Project.status == status)
            
        projects = query.order_by(Project.created_at.desc()).all()
        
    return render_template('projects/index.html', projects=projects, current_status=status)

@bp.route('/create/<int:client_id>', methods=['GET', 'POST'])
@login_required
def create(client_id):
    """Start a new project for a client."""
    from sqlalchemy.orm import joinedload
    with get_db() as db:
        client = db.query(Client).options(
            joinedload(Client.interested_package)
        ).filter(Client.id == client_id).first()
        
        if not client:
            flash('Cliente não encontrado.', 'error')
            return redirect(url_for('clients.index'))

        if request.method == 'POST':
            try:
                name = request.form.get('name')
                description = request.form.get('description')
                start_date_str = request.form.get('start_date')
                monthly_value = request.form.get('monthly_value', 0)
                
                logging.info(f"Creating project for client {client_id}: {name}")
                
                project = Project(
                    client_id=client_id,
                    company_id=session.get('company_id'),
                    name=name,
                    description=description,
                    start_date=datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None,
                    monthly_value=float(monthly_value) if monthly_value else 0,
                    status='active'
                )
                
                from flask_babel import gettext as _
                db.add(project)
                db.commit()
                
                logging.info(f"Project created successfully: {project.id}")
                flash(_('Projeto "%(name)s" iniciado com sucesso!', name=name), 'success')
                return redirect(url_for('projects.view', project_id=project.id))
            except Exception as e:
                logging.error(f"Error creating project: {str(e)}", exc_info=True)
                flash(_('Erro ao criar projeto: %(error)s', error=str(e)), 'error')
                return redirect(url_for('projects.create', client_id=client_id))

    return render_template(
        'projects/create.html', 
        client=client, 
        now_date=datetime.now().strftime('%Y-%m-%d')
    )

@bp.route('/<int:project_id>')
@login_required
def view(project_id):
    """View project details and tickets."""
    try:
        with get_db() as db:
            from sqlalchemy.orm import joinedload
            project = db.query(Project).options(
                joinedload(Project.client),
                joinedload(Project.tickets)
            ).filter(Project.id == project_id).first()
            
            if not project:
                flash(_('Projeto não encontrado.'), 'error')
                return redirect(url_for('projects.index'))
                
            # Fetch related history for context
            from app.models import HealthCheck, Proposal
            health_checks = db.query(HealthCheck).filter_by(client_id=project.client_id).order_by(HealthCheck.created_at.desc()).limit(5).all()
            proposals = db.query(Proposal).filter_by(client_id=project.client_id).order_by(Proposal.created_at.desc()).limit(5).all()
                
        return render_template('projects/view.html', project=project, health_checks=health_checks, proposals=proposals)
    except Exception as e:
        logging.error(f"Error in projects.view: {str(e)}", exc_info=True)
        flash(_('Erro ao carregar projeto: %(error)s', error=str(e)), 'error')
        return redirect(url_for('projects.index'))

@bp.route('/<int:project_id>/ticket/add', methods=['POST'])
@login_required
def add_ticket(project_id):
    """Add a ticket/task to a project."""
    title = request.form.get('title')
    description = request.form.get('description')
    priority = request.form.get('priority', 'medium')
    due_date_str = request.form.get('due_date')
    
    with get_db() as db:
        ticket = ProjectTicket(
            project_id=project_id,
            title=title,
            description=description,
            priority=priority,
            due_date=datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None,
            status='pending'
        )
        db.add(ticket)
        db.commit()
        flash(_('Tarefa adicionada.'), 'success')
        
    return redirect(url_for('projects.view', project_id=project_id))
@bp.route('/<int:project_id>/upload-contract', methods=['POST'])
@login_required
def upload_contract(project_id):
    """Upload signed contract for a project."""
    if 'contract' not in request.files:
        flash('Nenhum arquivo enviado.', 'error')
        return redirect(url_for('projects.view', project_id=project_id))
    
    file = request.files['contract']
    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(url_for('projects.view', project_id=project_id))

    from flask import current_app
    import os
    from werkzeug.utils import secure_filename
    
    with get_db() as db:
        project = db.query(Project).get(project_id)
        if not project:
            flash('Projeto não encontrado.', 'error')
            return redirect(url_for('projects.index'))

        # Create company folder
        company_id = session.get('company_id')
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f'company_{company_id}', 'contracts')
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = secure_filename(f"contract_p{project_id}_{file.filename}")
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        project.contract_file_path = file_path
        project.signed_at = datetime.utcnow()
        db.commit()
        
        flash('Contrato enviado com sucesso!', 'success')
        
    return redirect(url_for('projects.view', project_id=project_id))

@bp.route('/<int:project_id>/update-status', methods=['POST'])
@login_required
def update_status(project_id):
    """Update project phase or financial status."""
    phase = request.form.get('phase')
    financial_status = request.form.get('financial_status')
    
    with get_db() as db:
        project = db.query(Project).get(project_id)
        if not project:
            flash('Projeto não encontrado.', 'error')
            return redirect(url_for('projects.index'))
            
        if phase:
            project.phase = phase
            # If moving to onboarding, automatically create initial onboarding tasks
            if phase == 'onboarding':
                # Check for existing onboarding tickets
                exists = db.query(ProjectTicket).filter_by(project_id=project_id, is_onboarding=True).count()
                if exists == 0:
                    onboarding_tasks = [
                        ('Reunião de Kickoff', 'Agendar e realizar kickoff com o cliente.'),
                        ('Coleta de Acessos', 'Solicitar e validar acessos ao GMB, Site e Redes Sociais.'),
                        ('Planejamento Editorial', 'Definir linha editorial e cronograma inicial.')
                    ]
                    for title, desc in onboarding_tasks:
                        db.add(ProjectTicket(
                            project_id=project_id,
                            title=title,
                            description=desc,
                            phase='onboarding',
                            is_onboarding=True,
                            status='pending'
                        ))
        
        if financial_status:
            project.financial_status = financial_status
            
        db.commit()
        flash('Status do projeto atualizado.', 'success')
        
    return redirect(url_for('projects.view', project_id=project_id))

@bp.route('/<int:project_id>/renew', methods=['POST'])
@login_required
def renew(project_id):
    """Renovar contrato do projeto (estender prazo)"""
    new_end_date = request.form.get('end_date')
    new_value = request.form.get('monthly_value')
    
    with get_db() as db:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            flash(_('Projeto não encontrado'), 'danger')
            return redirect(url_for('projects.index'))
            
        if new_end_date:
            from datetime import datetime
            project.end_date = datetime.strptime(new_end_date, '%Y-%m-%d').date()
        
        if new_value:
            project.monthly_value = float(new_value)
            
        db.commit()
        flash(_('Projeto renovado com sucesso!'), 'success')
        
    return redirect(url_for('projects.view', project_id=project_id))
