from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.routes.auth import login_required
from app.models import Project, ProjectTicket, Client, ProjectNote
from app.utils.tenant import filter_by_company
from config.database import get_db
from datetime import datetime
from sqlalchemy.orm import joinedload
from flask_babel import gettext as _
import logging

bp = Blueprint('projects', __name__, url_prefix='/projects')

@bp.route('/')
@login_required
def index():
    """List of all active projects for the company."""
    with get_db() as db:
        from sqlalchemy.orm import joinedload
        from app.models import Receivable
        query = db.query(Project).options(joinedload(Project.client))
        query = filter_by_company(query, Project)
        
        # Simple status filter
        status = request.args.get('status', 'active')
        if status:
            query = query.filter(Project.status == status)
            
        projects = query.order_by(Project.created_at.desc()).all()
        
        # Calculate contract values from receivables for each project
        project_ids = [p.id for p in projects]
        contract_values = {}
        if project_ids:
            receivables = db.query(Receivable).filter(
                Receivable.project_id.in_(project_ids),
                Receivable.status != 'cancelled'
            ).all()
            for r in receivables:
                contract_values[r.project_id] = contract_values.get(r.project_id, 0) + float(r.amount or 0)
        
        return render_template('projects/index.html', projects=projects, current_status=status, contract_values=contract_values)

@bp.route('/api/list')
@login_required
def api_list():
    """Simple API to list active projects for dropdowns."""
    with get_db() as db:
        query = db.query(Project).options(joinedload(Project.client)).filter(Project.status == 'active')
        query = filter_by_company(query, Project)
        projects = query.order_by(Project.name).all()
        return jsonify([
            {
                'id': p.id,
                'name': p.name,
                'client_name': p.client.name if p.client else None
            } for p in projects
        ])

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
            flash(_('Cliente não encontrado.'), 'error')
            return redirect(url_for('clients.index'))

        if request.method == 'POST':
            try:
                name = request.form.get('name')
                description = request.form.get('description')
                start_date_str = request.form.get('start_date')
                billing_type = request.form.get('billing_type', 'recurring')
                billing_base_day = request.form.get('billing_base_day', 10)
                total_amount = request.form.get('total_amount', 0)
                monthly_value = request.form.get('monthly_value', 0)
                
                logging.info(f"Creating project for client {client_id}: {name}")
                
                project = Project(
                    client_id=client_id,
                    company_id=session.get('company_id'),
                    name=name,
                    description=description,
                    start_date=datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None,
                    billing_type=billing_type,
                    billing_base_day=int(billing_base_day) if billing_base_day else 10,
                    total_amount=float(total_amount) if total_amount else 0,
                    monthly_value=float(monthly_value) if monthly_value else 0,
                    status='active'
                )
                
                from flask_babel import gettext as _
                db.add(project)
                db.commit()
                
                logging.info(f"Project created successfully: {project.id}")
                flash(_('Project "%(name)s" launched successfully!', name=name), 'success')
                return redirect(url_for('projects.view', project_id=project.id))
            except Exception as e:
                logging.error(f"Error creating project: {str(e)}", exc_info=True)
                flash(_('Error creating project: %(error)s', error=str(e)), 'error')
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
            from app.models import HealthCheck, Proposal, User, Receivable
            project = db.query(Project).options(
                joinedload(Project.client),
                joinedload(Project.tickets)
            ).filter(Project.id == project_id).first()
            
            if not project:
                flash(_('Project not found.'), 'error')
                return redirect(url_for('projects.index'))
                
            # Fetch related history for context
            health_checks = db.query(HealthCheck).filter_by(client_id=project.client_id).order_by(HealthCheck.created_at.desc()).limit(5).all()
            proposals = db.query(Proposal).filter_by(client_id=project.client_id).order_by(Proposal.created_at.desc()).limit(5).all()
            
            # Fetch company users for assignment
            users = db.query(User).filter_by(company_id=project.company_id).all()
            
            # Calculate contract value from receivables (Setup + Recurring)
            receivables = db.query(Receivable).filter(
                Receivable.project_id == project.id,
                Receivable.status != 'cancelled'
            ).all()
            
            contract_value = sum(float(r.amount or 0) for r in receivables)
            contract_value = sum(float(r.amount or 0) for r in receivables)
            receivables_paid = sum(float(r.paid_amount or 0) for r in receivables)
            
            # Fetch Notes for Memory Tab
            notes = db.query(ProjectNote).filter_by(project_id=project_id).order_by(ProjectNote.created_at.desc()).all()
            
            # Build Timeline Data
            timeline_events = []
            
            # Add notes to timeline
            for n in notes:
                timeline_events.append({
                    'type': 'note',
                    'date': n.created_at,
                    'user': n.author.name if n.author else 'Unknown',
                    'content': n.content,
                    'data': n
                })
                
            # Add tickets to timeline
            for t in project.tickets:
                # Ticket Creation
                timeline_events.append({
                    'type': 'ticket_created',
                    'date': t.created_at,
                    'user': t.assignee.name if t.assignee else 'Unassigned',  # actually creator is not tracked, usually system
                    'content': f"Task created: {t.title}",
                    'data': t
                })
                
                # Ticket Completion
                if t.status == 'done':
                    date_completed = t.completed_at or t.updated_at
                    user_completed = t.completer.name if t.completer else (t.assignee.name if t.assignee else 'Unknown')
                    timeline_events.append({
                        'type': 'ticket_completed',
                        'date': date_completed,
                        'user': user_completed,
                        'content': f"Task completed: {t.title}",
                        'data': t
                    })

            # Sort by date desc
            timeline_events.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)
                
            return render_template('projects/view.html',
                project=project,
                health_checks=health_checks,
                proposals=proposals,
                users=users,
                contract_value=contract_value,
                receivables_paid=receivables_paid,
                timeline_events=timeline_events,
                notes=notes
            )
    except Exception as e:
        logging.error(f"Error in projects.view: {str(e)}", exc_info=True)
        flash(_('Error loading project: %(error)s', error=str(e)), 'error')
        return redirect(url_for('projects.index'))

@bp.route('/<int:project_id>/ticket/add', methods=['POST'])
@login_required
def add_ticket(project_id):
    """Add a ticket/task to a project."""
    title = request.form.get('title')
    description = request.form.get('description')
    priority = request.form.get('priority', 'medium')
    due_date_str = request.form.get('due_date')
    assigned_to = request.form.get('assigned_to')
    
    with get_db() as db:
        ticket = ProjectTicket(
            project_id=project_id,
            title=title,
            description=description,
            priority=priority,
            due_date=datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None,
            assigned_to=int(assigned_to) if assigned_to and assigned_to != "" else None,
            assigned_by_id=session.get('user_id'),
            verification_required=True if request.form.get('verification_required') else False,
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
        flash(_('Nenhum arquivo enviado.'), 'error')
        return redirect(url_for('projects.view', project_id=project_id))
    
    file = request.files['contract']
    if file.filename == '':
        flash(_('Nenhum arquivo selecionado.'), 'error')
        return redirect(url_for('projects.view', project_id=project_id))

    from flask import current_app
    import os
    from werkzeug.utils import secure_filename
    
    with get_db() as db:
        project = db.query(Project).get(project_id)
        if not project:
            flash(_('Project not found.'), 'error')
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
        
        flash(_('Contract uploaded successfully!'), 'success')
        
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
            flash(_('Project not found.'), 'error')
            return redirect(url_for('projects.index'))
            
        if phase:
            project.phase = phase
            # If moving to onboarding, automatically create initial onboarding tasks
            if phase == 'onboarding':
                # Check for existing onboarding tickets
                exists = db.query(ProjectTicket).filter_by(project_id=project_id, is_onboarding=True).count()
                if exists == 0:
                    onboarding_tasks = [
                        (_('Kickoff Meeting'), _('Schedule and perform kickoff with the client.')),
                        (_('Access Collection'), _('Request and validate accesses to GMB, Website and Social Media.')),
                        (_('Editorial Planning'), _('Define editorial line and initial schedule.'))
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
        flash(_('Project status updated.'), 'success')
        
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
            
        if new_end_date and new_end_date.strip():
            from datetime import datetime
            project.end_date = datetime.strptime(new_end_date, '%Y-%m-%d').date()
        
        if new_value:
            project.monthly_value = float(new_value)
            
        db.commit()
        flash(_('Projeto renovado com sucesso!'), 'success')
        
    return redirect(url_for('projects.view', project_id=project_id))

@bp.route('/<int:project_id>/launch-installments', methods=['POST'])
@login_required
def launch_installments(project_id):
    """Lançar parcelas de pagamento para um projeto."""
    from app.models import Receivable
    from datetime import timedelta
    
    amount_total = float(request.form.get('total_amount', 0))
    installments = int(request.form.get('installments', 1))
    first_due_date_str = request.form.get('first_due_date')
    description = request.form.get('description', 'Pagamento de Projeto')
    
    if amount_total <= 0 or not first_due_date_str:
        flash(_('Invalid data for installments.'), 'error')
        return redirect(url_for('projects.view', project_id=project_id))
        
    with get_db() as db:
        project = db.query(Project).get(project_id)
        if not project:
            flash(_('Project not found.'), 'error')
            return redirect(url_for('projects.index'))
            
        first_due_date = datetime.strptime(first_due_date_str, '%Y-%m-%d').date()
        installment_amount = amount_total / installments
        
        for i in range(1, installments + 1):
            due_date = first_due_date + timedelta(days=30 * (i - 1))
            new_receivable = Receivable(
                company_id=project.company_id,
                client_id=project.client_id,
                project_id=project_id,
                description=f"{description} ({i}/{installments})",
                amount=installment_amount,
                due_date=due_date,
                status='open'
            )
            db.add(new_receivable)
        
        db.commit()
        flash(_('%(count)d installments launched successfully!', count=installments), 'success')
        
    return redirect(url_for('projects.view', project_id=project_id))

@bp.route('/<int:project_id>/launch-recurring', methods=['POST'])
@login_required
def launch_recurring(project_id):
    """Lançar mensalidades recorrentes para um projeto."""
    from app.models import Receivable
    from datetime import timedelta
    
    amount = float(request.form.get('monthly_amount', 0))
    count = int(request.form.get('count', 1))
    first_due_date_str = request.form.get('first_due_date')
    description = request.form.get('description', _('Recurring Payment'))
    
    if amount <= 0 or not first_due_date_str:
        flash(_('Invalid data for recurring payments.'), 'error')
        return redirect(url_for('projects.view', project_id=project_id))
        
    with get_db() as db:
        project = db.query(Project).get(project_id)
        if not project:
            flash(_('Project not found.'), 'error')
            return redirect(url_for('projects.index'))
            
        first_due_date = datetime.strptime(first_due_date_str, '%Y-%m-%d').date()
        
        for i in range(1, count + 1):
            # 30 days logic for simplicity and consistency with launch_installments
            due_date = first_due_date + timedelta(days=30 * (i - 1))
            new_receivable = Receivable(
                company_id=project.company_id,
                client_id=project.client_id,
                project_id=project_id,
                description=f"{description} ({i}/{count})",
                amount=amount,
                due_date=due_date,
                status='open'
            )
            db.add(new_receivable)
        
        db.commit()
        flash(_('%(count)d recurring payments launched successfully!', count=count), 'success')
        
    return redirect(url_for('projects.view', project_id=project_id))


@bp.route('/<int:project_id>/note/add', methods=['POST'])
@login_required
def add_note(project_id):
    """Add a note/chat message to the project memory."""
    content = request.form.get('content')
    if not content:
        flash(_('Message cannot be empty.'), 'warning')
        return redirect(url_for('projects.view', project_id=project_id))
        
    with get_db() as db:
        project = db.query(Project).get(project_id)
        if not project:
            return redirect(url_for('projects.index'))
            
        note = ProjectNote(
            project_id=project_id,
            user_id=session.get('user_id'),
            content=content
        )
        db.add(note)
        db.commit()
        flash(_('Note added.'), 'success')
        
    return redirect(url_for('projects.view', project_id=project_id))

@bp.route('/<int:project_id>/ticket/<int:ticket_id>/complete', methods=['POST'])
@login_required
def complete_ticket(project_id, ticket_id):
    """Mark a ticket as completed."""
    with get_db() as db:
        ticket = db.query(ProjectTicket).filter_by(id=ticket_id, project_id=project_id).first()
        if not ticket:
            flash(_('Task not found.'), 'error')
        else:
            if ticket.verification_required:
                ticket.status = 'pending_approval'
                # Notify creator/assigner
                from app.services.notification_service import NotificationService
                NotificationService.on_task_pending_approval(db, ticket)
                flash(_('Task submitted for approval'), 'info')
            else:
                ticket.status = 'done'
                ticket.completed_at = datetime.now()
                ticket.completed_by = session.get('user_id')
                # Notify creator/assigner
                from app.services.notification_service import NotificationService
                NotificationService.on_task_completed(db, ticket)
                flash(_('Task completed!'), 'success')
            db.commit()


@bp.route('/<int:project_id>/ticket/<int:ticket_id>/approve', methods=['POST'])
@login_required
def approve_ticket(project_id, ticket_id):
    """Approve a project task."""
    with get_db() as db:
        ticket = db.query(ProjectTicket).filter_by(id=ticket_id, project_id=project_id).first()
        if not ticket:
            flash(_('Task not found.'), 'error')
        elif ticket.status != 'pending_approval':
            flash(_('Task not awaiting approval.'), 'warning')
        else:
            ticket.status = 'done'
            ticket.approved_at = datetime.utcnow()
            ticket.approved_by_id = session.get('user_id')
            ticket.completed_at = datetime.utcnow()
            
            # Notify assignee
            from app.services.notification_service import NotificationService
            NotificationService.on_task_approved(db, ticket)
            
            db.commit()
            flash(_('Task approved!'), 'success')
            
    return redirect(url_for('projects.view', project_id=project_id))


@bp.route('/<int:project_id>/ticket/<int:ticket_id>/reject', methods=['POST'])
@login_required
def reject_ticket(project_id, ticket_id):
    """Reject a project task with a comment."""
    comment = request.form.get('comment', '').strip()
    if not comment:
        flash(_('Rejection comment is required.'), 'error')
        return redirect(url_for('projects.view', project_id=project_id))
        
    with get_db() as db:
        ticket = db.query(ProjectTicket).filter_by(id=ticket_id, project_id=project_id).first()
        if not ticket:
            flash(_('Task not found.'), 'error')
        elif ticket.status != 'pending_approval':
            flash(_('Task not awaiting approval.'), 'warning')
        else:
            ticket.status = 'in_progress'
            ticket.rejection_comment = comment
            ticket.completed_at = None
            
            # Notify assignee
            from app.services.notification_service import NotificationService
            NotificationService.on_task_rejected(db, ticket)
            
            db.commit()
            flash(_('Task returned for revision.'), 'info')
            
    return redirect(url_for('projects.view', project_id=project_id))
            
    return redirect(url_for('projects.view', project_id=project_id))

@bp.route('/<int:project_id>/note/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(project_id, note_id):
    """Delete a note from the project memory (Super Admin/Owner only)."""
    if not (session.get('is_superadmin') or session.get('role') == 'owner'):
        flash(_('Permission denied.'), 'error')
        return redirect(url_for('projects.view', project_id=project_id))
        
    with get_db() as db:
        note = db.query(ProjectNote).filter_by(id=note_id, project_id=project_id).first()
        if note:
            db.delete(note)
            db.commit()
            flash(_('Note deleted.'), 'success')
        else:
            flash(_('Note not found.'), 'error')
            
    return redirect(url_for('projects.view', project_id=project_id))
