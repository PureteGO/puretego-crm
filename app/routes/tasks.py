"""
PURETEGO CRM - Tasks Routes
Rotas para gestão de tarefas internas com atribuição, prioridade e notificações
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_babel import gettext as _
from app.routes.auth import login_required, get_current_user
from app.models.task import Task
from app.models.user import User
from app.models.client import Client
from app.models.project import Project
from app.utils.tenant import filter_by_company
from config.database import get_db
from datetime import datetime
from sqlalchemy import or_

bp = Blueprint('tasks', __name__, url_prefix='/tasks')
api_bp = Blueprint('api_tasks', __name__, url_prefix='/api/tasks')


# ─────────────────────────────────────────────
# WEB ROUTES
# ─────────────────────────────────────────────

@bp.route('/')
@login_required
def index():
    """Lista de tarefas - com filtros por status, prioridade e tabs"""
    user = get_current_user()
    tab = request.args.get('tab', 'my')  # my, created, all
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    
    with get_db() as db:
        from sqlalchemy.orm import joinedload
        
        base_query = filter_by_company(
            db.query(Task).options(
                joinedload(Task.assigned_to),
                joinedload(Task.assigned_by),
                joinedload(Task.client),
                joinedload(Task.deal)
            ), Task
        )
        
        # Tab filter
        if tab == 'my':
            base_query = base_query.filter(
                or_(
                    Task.assigned_to_id == user.id,
                    (Task.assigned_to_id.is_(None)) & (Task.role_target == (user.role.name if user.role else 'sales'))
                )
            )
        elif tab == 'created':
            base_query = base_query.filter(Task.assigned_by_id == user.id)
        else:  # 'all' - only for managers/owners
            if not user.role or user.role.name not in ['owner', 'manager', 'admin', 'partner']:
                base_query = base_query.filter(Task.assigned_to_id == user.id)
        
        # Status filter
        if status_filter:
            base_query = base_query.filter(Task.status == status_filter)
        else:
            # By default, show active tasks (not done/canceled)
            base_query = base_query.filter(Task.status.in_(['open', 'in_progress']))
        
        # Priority filter
        if priority_filter:
            base_query = base_query.filter(Task.priority == priority_filter)
        
        tasks = base_query.order_by(Task.due_date.is_(None), Task.due_date.asc(), Task.priority.desc()).all()
        
        # Get team members for assignment dropdown
        team_members = filter_by_company(db.query(User).filter(User.is_active == True), User).all()
        clients = filter_by_company(db.query(Client).order_by(Client.name), Client).all()
        projects = filter_by_company(
            db.query(Project).options(joinedload(Project.client)).filter(Project.status == 'active').order_by(Project.name), 
            Project
        ).all()
        
        # Serialize
        tasks_data = []
        for t in tasks:
            tasks_data.append({
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'priority': t.priority,
                'type': t.type,
                'due_date': t.due_date,
                'completed_at': t.completed_at,
                'created_at': t.created_at,
                'client_id': t.client_id,
                'client_name': t.client.name if t.client else None,
                'deal_id': t.deal_id,
                'deal_title': t.deal.title if t.deal else None,
                'project_id': t.project_id,
                'project_name': t.project.name if t.project else None,
                'assigned_to_id': t.assigned_to_id,
                'assigned_to_name': t.assigned_to.name if t.assigned_to else None,
                'assigned_by_id': t.assigned_by_id,
                'assigned_by_name': t.assigned_by.name if t.assigned_by else None,
                'verification_required': t.verification_required,
                'approved_at': t.approved_at,
                'rejection_comment': t.rejection_comment
            })
        
        # Serialize dropdown data to avoid DetachedInstanceError
        team = [{'id': u.id, 'name': u.name} for u in team_members]
        clients_data = [{'id': c.id, 'name': c.name} for c in clients]
        projects_data = [
            {
                'id': p.id, 
                'name': p.name, 
                'client_name': p.client.name if p.client else None
            } for p in projects
        ]
    
    return render_template('tasks/index.html',
        tasks=tasks_data,
        team=team,
        clients=clients_data,
        projects=projects_data,
        current_tab=tab,
        status_filter=status_filter,
        priority_filter=priority_filter,
        now=datetime.utcnow()
    )


@bp.route('/create', methods=['POST'])
@login_required
def create():
    """Criar nova tarefa"""
    user = get_current_user()
    
    with get_db() as db:

        assigned_to_id = int(request.form['assigned_to_id']) if request.form.get('assigned_to_id') else None
        client_id = int(request.form['client_id']) if request.form.get('client_id') else None
        project_id = int(request.form['project_id']) if request.form.get('project_id') else None
        deal_id = int(request.form['deal_id']) if request.form.get('deal_id') else None

        company_id = session.get('company_id')

        # Validate Associations (Strict Tenant Isolation)
        if assigned_to_id:
             # Force check against session company_id, avoiding superadmin bypass
            valid_user = db.query(User).filter(User.id == assigned_to_id)
            if company_id:
                valid_user = valid_user.filter(User.company_id == company_id)
            
            if not valid_user.first():
                assigned_to_id = None
        
        if client_id:
             valid_client = db.query(Client).filter(Client.id == client_id)
             if company_id:
                 valid_client = valid_client.filter(Client.company_id == company_id)
             if not valid_client.first():
                 client_id = None
                 
        if project_id:
             valid_project = db.query(Project).filter(Project.id == project_id)
             if company_id:
                 valid_project = valid_project.filter(Project.company_id == company_id)
             if not valid_project.first():
                 project_id = None

        task = Task(
            company_id=session.get('company_id'),
            title=request.form.get('title', '').strip(),
            description=request.form.get('description', '').strip() or None,
            status='open',

            priority=request.form.get('priority', 'medium'),
            role_target=request.form.get('role_target', ''),
            assigned_to_id=assigned_to_id,
            assigned_by_id=user.id,
            client_id=client_id,
            deal_id=deal_id,
            project_id=project_id,
            verification_required=True if request.form.get('verification_required') == 'on' else False,
            type=request.form.get('type', 'operational'), # Default to operational as per req
        )
        
        # Parse due_date
        due_date_str = request.form.get('due_date', '')
        if due_date_str:
            try:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                try:
                    task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                except ValueError:
                    task.due_date = None
        
        db.add(task)
        db.flush()
        
        # Send notification to assigned user
        if task.assigned_to_id:
            from app.services.notification_service import NotificationService
            NotificationService.on_task_assigned(db, task)
        
        db.commit()
        flash(_('Task created successfully'), 'success')
    
    # Redirect back to referrer or tasks list
    next_url = request.form.get('next', url_for('tasks.index'))
    return redirect(next_url)


@bp.route('/<int:task_id>/update', methods=['POST'])
@login_required
def update(task_id):
    """Atualizar detalhes da tarefa"""
    user = get_current_user()
    
    with get_db() as db:
        task = filter_by_company(db.query(Task), Task).filter(Task.id == task_id).first()
        
        if not task:
            flash(_('Task not found'), 'error')
            return redirect(url_for('tasks.index'))
            
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.priority = request.form.get('priority')
        task.verification_required = True if request.form.get('verification_required') == 'on' else False
        task.assigned_comment = request.form.get('assigned_comment')
        
        if request.form.get('assigned_to_id'):
            aid = int(request.form.get('assigned_to_id'))
            if filter_by_company(db.query(User), User).filter(User.id == aid).first():
                task.assigned_to_id = aid
            else:
                 task.assigned_to_id = None # Invalid user
        else:
            task.assigned_to_id = None
            
        if request.form.get('client_id'):
            cid = int(request.form.get('client_id'))
            if filter_by_company(db.query(Client), Client).filter(Client.id == cid).first():
                task.client_id = cid
            else:
                task.client_id = None
        else:
            task.client_id = None
            
        if request.form.get('project_id'):
            pid = int(request.form.get('project_id'))
            if filter_by_company(db.query(Project), Project).filter(Project.id == pid).first():
                task.project_id = pid
            else:
                task.project_id = None
        
        due_date_str = request.form.get('due_date')
        if due_date_str:
            try:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                try:
                     task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                except ValueError:
                    pass
        else:
            task.due_date = None
            
        db.commit()
        flash(_('Task updated'), 'success')
        
    return redirect(request.referrer or url_for('tasks.index'))



@bp.route('/<int:task_id>/status', methods=['POST'])
@login_required
def update_status(task_id):
    """Atualizar status da tarefa"""
    user = get_current_user()
    new_status = request.form.get('status', request.json.get('status') if request.is_json else None)
    
    if new_status not in ['open', 'in_progress', 'done', 'canceled']:
        return jsonify({'success': False, 'message': _('Invalid status')}), 400
    
    with get_db() as db:
        task = filter_by_company(db.query(Task), Task).filter(Task.id == task_id).first()
        if not task:
            return jsonify({'success': False, 'message': _('Task not found')}), 404
        
        old_status = task.status
        
        # Verification Logic
        if new_status == 'done' and old_status != 'done':
            if task.verification_required:
                task.status = 'pending_approval' # Intercept 'done'
                # Notify creator about review
                from app.services.notification_service import NotificationService
                NotificationService.on_task_pending_approval(db, task)
                message = _('Task submitted for approval')
            else:
                task.status = 'done'
                task.completed_at = datetime.utcnow()
                task.completed_by_id = user.id
                # Notify creator about completion
                from app.services.notification_service import NotificationService
                NotificationService.on_task_completed(db, task)
                message = _('Task completed')
        else:
            task.status = new_status
            if new_status != 'done':
                task.completed_at = None
                task.completed_by_id = None
            message = _('Task updated')
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': message,
            'task': task.to_dict()
        })


@bp.route('/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    """Atalho para marcar tarefa como concluída"""
    with get_db() as db:
        task = filter_by_company(db.query(Task), Task).filter(Task.id == task_id).first()
        if not task:
            return jsonify({'success': False, 'message': _('Task not found')}), 404
        
        if task.verification_required:
            task.status = 'pending_approval'
            # Notify creator
            from app.services.notification_service import NotificationService
            NotificationService.on_task_pending_approval(db, task)
            message = _('Task submitted for approval')
        else:
            task.status = 'done'
            task.completed_at = datetime.utcnow()
            task.completed_by_id = get_current_user().id
            # Notify creator
            from app.services.notification_service import NotificationService
            NotificationService.on_task_completed(db, task)
            message = _('Task completed')
        
        db.commit()
        return jsonify({'success': True, 'message': message})


@bp.route('/<int:task_id>/approve', methods=['POST'])
@login_required
def approve_task(task_id):
    """Aprova a conclusão de uma tarefa"""
    user = get_current_user()
    with get_db() as db:
        task = filter_by_company(db.query(Task), Task).filter(Task.id == task_id).first()
        if not task:
            return jsonify({'success': False, 'message': _('Task not found')}), 404
            
        if task.status != 'pending_approval':
            return jsonify({'success': False, 'message': _('Task is not awaiting approval')}), 400
            
        task.status = 'done'
        task.approved_at = datetime.utcnow()
        task.approved_by_id = user.id
        task.completed_at = datetime.utcnow() # Final actual completion
        
        # Notify assignee
        from app.services.notification_service import NotificationService
        NotificationService.on_task_approved(db, task)
        
        db.commit()
        return jsonify({'success': True, 'message': _('Task approved')})


@bp.route('/<int:task_id>/reject', methods=['POST'])
@login_required
def reject_task(task_id):
    """Rejeita a conclusão de uma tarefa com comentário"""
    user = get_current_user()
    data = request.json or {}
    comment = data.get('comment', '').strip()
    
    if not comment:
        return jsonify({'success': False, 'message': _('Rejection comment is required')}), 400
        
    with get_db() as db:
        task = filter_by_company(db.query(Task), Task).filter(Task.id == task_id).first()
        if not task:
            return jsonify({'success': False, 'message': _('Task not found')}), 404
            
        if task.status != 'pending_approval':
            return jsonify({'success': False, 'message': _('Task is not awaiting approval')}), 400
            
        task.status = 'in_progress' # Return to work
        task.rejection_comment = comment
        task.completed_at = None
        
        # Notify assignee
        from app.services.notification_service import NotificationService
        NotificationService.on_task_rejected(db, task)
        
        db.commit()
        return jsonify({'success': True, 'message': _('Task returned for revision')})


@bp.route('/<int:task_id>/details')
@login_required
def details(task_id):
    """Retorna detalhes da tarefa para edição (JSON)"""
    with get_db() as db:
        task = filter_by_company(db.query(Task), Task).filter(Task.id == task_id).first()
        if not task:
            return jsonify({'success': False, 'message': _('Task not found')}), 404
            
        return jsonify({
            'success': True,
            'task': task.to_dict()
        })


# ─────────────────────────────────────────────
# API ROUTES (JSON)
# ─────────────────────────────────────────────

@api_bp.route('/summary')
@login_required
def get_task_summary():
    """API: Retorna resumo de tarefas pendentes para o dashboard"""
    user = get_current_user()
    role_name = user.role.name if user.role else 'sales'
    
    with get_db() as db:
        query = filter_by_company(db.query(Task), Task).filter(
            Task.status.in_(['open', 'in_progress', 'pending_approval'])
        )
        
        query = query.filter(
            or_(
                Task.assigned_to_id == user.id,
                (Task.assigned_to_id.is_(None)) & (Task.role_target == role_name)
            )
        )
        
        tasks = query.order_by(Task.due_date.is_(None), Task.due_date.asc()).all()
        
        today = datetime.utcnow().date()
        overdue_count = sum(1 for t in tasks if t.due_date and t.due_date.date() < today)
        today_count = sum(1 for t in tasks if t.due_date and t.due_date.date() == today)
        
        return jsonify({
            'success': True,
            'total_pending': len(tasks),
            'overdue_count': overdue_count,
            'today_count': today_count,
            'tasks': [t.to_dict() for t in tasks[:5]]
        })


@api_bp.route('/my')
@login_required
def my_tasks():
    """API: Retorna tarefas do usuário logado (para widget do dashboard)"""
    user = get_current_user()
    role_name = user.role.name if user.role else 'sales'
    
    with get_db() as db:
        from sqlalchemy.orm import joinedload
        
        tasks = filter_by_company(
            db.query(Task).options(joinedload(Task.client), joinedload(Task.assigned_by)), Task
        ).filter(
            Task.status.in_(['open', 'in_progress']),
            or_(
                Task.assigned_to_id == user.id,
                (Task.assigned_to_id.is_(None)) & (Task.role_target == role_name)
            )
        ).order_by(Task.due_date.is_(None), Task.due_date.asc(), Task.priority.desc()).limit(10).all()
        
        return jsonify({
            'success': True,
            'tasks': [t.to_dict() for t in tasks]
        })


@api_bp.route('/quick-create', methods=['POST'])
@login_required
def api_quick_create():
    """API: Criar tarefa rápida via AJAX (de qualquer página)"""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    
    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'success': False, 'message': _('Task title is required')}), 400
    
    with get_db() as db:
        task = Task(
            company_id=session.get('company_id'),
            title=title,
            description=(data.get('description') or '').strip() or None,
            status='open',
            type='operational', # Default for quick add
            verification_required=True if data.get('verification_required') else False,

            assigned_by_id=user.id,
        )
        
        # Validation (Strict)
        company_id = session.get('company_id')
        
        aid = int(data['assigned_to_id']) if data.get('assigned_to_id') else None
        if aid:
            q = db.query(User).filter(User.id == aid)
            if company_id:
                q = q.filter(User.company_id == company_id)
            if q.first():
                task.assigned_to_id = aid
        
        pid = int(data['project_id']) if data.get('project_id') else None
        if pid:
            q = db.query(Project).filter(Project.id == pid)
            if company_id:
                q = q.filter(Project.company_id == company_id)
            if q.first():
                task.project_id = pid
            
        cid = int(data['client_id']) if data.get('client_id') else None
        if cid:
            q = db.query(Client).filter(Client.id == cid)
            if company_id:
                q = q.filter(Client.company_id == company_id)
            if q.first():
                task.client_id = cid
        
        # Parse due_date
        due_date_str = data.get('due_date', '')
        if due_date_str:
            try:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                try:
                    task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                except ValueError:
                    task.due_date = None
        
        db.add(task)
        db.flush()
        
        # Notify assigned user
        if task.assigned_to_id and task.assigned_to_id != user.id:
            from app.services.notification_service import NotificationService
            NotificationService.on_task_assigned(db, task)
        
        db.commit()
        
        return jsonify({'success': True, 'message': _('Task created successfully'), 'task_id': task.id})


@api_bp.route('/team')
@login_required
def api_team_list():
    """API: Lista membros ativos da equipe (para dropdown de assign)"""
    with get_db() as db:
        # Enforce filtering by current session company, even for Super Admins
        # This ensures the dropdown only shows relevant users for the current context
        query = db.query(User).filter(User.is_active == True)
        company_id = session.get('company_id')
        
        if company_id:
            query = query.filter(User.company_id == company_id)
            
        users = query.order_by(User.name).all()
        
        return jsonify([
            {'id': u.id, 'name': u.name, 'is_me': u.id == session.get('user_id')}
            for u in users
        ])
