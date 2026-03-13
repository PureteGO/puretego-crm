from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_babel import _
from app.routes.auth import login_required
from app.models import Interaction, InteractionType, CadenceRule, Client, Visit, Task, Project, ProjectTicket
from config.database import get_db, SessionLocal
from datetime import datetime, timedelta
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

bp = Blueprint('interactions', __name__, url_prefix='/interactions')

@bp.route('/')
@login_required
def index():
    """List all interactions (optional, for main timeline)"""
    with get_db() as db:
        interactions = db.query(Interaction).order_by(Interaction.date.desc()).limit(100).all()
    
    return render_template('interactions/index.html', interactions=interactions) # TODO: Create template if needed

@bp.route('/create', methods=['POST'])
@login_required
def create():
    """Log a new interaction and return next step suggestion"""
    data = request.get_json()
    
    client_id = data.get('client_id')
    deal_id = data.get('deal_id')
    type_id = data.get('type_id')
    date_str = data.get('date') # ISO Format
    notes = data.get('notes', '')
    status = data.get('status', 'done')
    
    if not client_id or not type_id:
        return jsonify({'success': False, 'message': 'Missing fields'}), 400
        
    try:
        date = datetime.fromisoformat(date_str)
    except:
        date = datetime.now()
        
    suggestion = None
    
    with get_db() as db:
        # 1. Create the interaction
        interaction = Interaction(
            client_id=client_id,
            deal_id=deal_id,
            user_id=session['user_id'],
            type_id=type_id,
            date=date,
            status=status,
            notes=notes
        )
        db.add(interaction)
        db.commit()
        
        # Capture ID while attached
        new_interaction_id = interaction.id
        
        # 2. Check for Cadence Rules (only if this was a completed action)
        if status == 'done':
            rule = db.query(CadenceRule).filter_by(trigger_type_id=type_id).first()
            if rule:
                next_date = date + timedelta(days=rule.delay_days)
                suggestion = {
                    'type_id': rule.suggested_next_type.id,
                    'type_name': rule.suggested_next_type.name,
                    'is_call': rule.suggested_next_type.is_call,
                    'date': next_date.isoformat(),
                    'message': f"Sugestão: Agendar {rule.suggested_next_type.name} para {next_date.strftime('%d/%m')}?"
                }
    
    return jsonify({
        'success': True,
        'interaction_id': new_interaction_id,
        'suggestion': suggestion
    })

@bp.route('/agenda')
@login_required
def agenda():
    """Get tasks (scheduled interactions AND visits) formatted for dashboard"""
    now = datetime.now()
    end_of_today = now.replace(hour=23, minute=59, second=59)
    end_of_7_days = (now + timedelta(days=7)).replace(hour=23, minute=59, second=59)
    
    user_id = session.get('user_id')
    user_role = session.get('role') or 'sales'
    company_id = session.get('company_id')
    
    db = SessionLocal()
    try:
        from sqlalchemy.orm import joinedload
        
        # Combine and formatting
        today_list = []
        upcoming_list = []

        # Helper to format items
        def format_item(item, type_label, url, is_call=False, date_field='date', note_field='notes'):
            date_val = getattr(item, date_field)
            if not date_val: date_val = datetime.now() # Fallback
            
            client_name = _('Task')
            if hasattr(item, 'client') and item.client:
                client_name = item.client.name
            elif hasattr(item, 'project') and item.project and item.project.client:
                client_name = item.project.client.name
                
            return {
                'id': f"{type_label}_{item.id}",
                'client_id': getattr(item, 'client_id', None), 
                'client_name': client_name,
                'type_name': type_label,
                'icon': getattr(item.type, 'icon', None) if hasattr(item, 'type') else None,
                'is_call': is_call,
                'date': date_val.isoformat() if date_val else datetime.now().isoformat(),
                'status': getattr(item, 'status', 'scheduled'),
                'notes': getattr(item, note_field, '') or getattr(item, 'title', ''), 
                'url': url
            }
            
        # 1. Interactions
        try:
            # Base query for interactions
            interaction_query = db.query(Interaction).options(joinedload(Interaction.client), joinedload(Interaction.type))\
                .join(Client).filter(
                    Interaction.status == 'scheduled',
                    Client.company_id == company_id
                )
                
            # If not an privileged role, filter by current user only
            if user_role not in ['owner', 'admin', 'manager', 'superadmin']:
                interaction_query = interaction_query.filter(Interaction.user_id == user_id)
                
            # Interactions: Overdue & Today
            urgent_tasks = interaction_query.filter(Interaction.date <= end_of_today)\
                .order_by(Interaction.date).all()
            
            # Interactions: Upcoming (Next 7 Days)
            future_tasks = interaction_query.filter(
                    Interaction.date > end_of_today,
                    Interaction.date <= end_of_7_days
                ).order_by(Interaction.date).all()

            for i in urgent_tasks:
                if not i.type: continue
                # Safe URL generation
                try:
                    client_url = url_for('clients.view', client_id=i.client_id)
                except:
                    client_url = "#"
                today_list.append(format_item(i, i.type.name, client_url, is_call=i.type.is_call))
                
            for i in future_tasks:
                if not i.type: continue
                try:
                    client_url = url_for('clients.view', client_id=i.client_id)
                except:
                    client_url = "#"
                upcoming_list.append(format_item(i, i.type.name, client_url, is_call=i.type.is_call))
        except Exception as e:
            print(f"Error fetching interactions: {e}")

        # 2. Visits
        try:
            company_id = session.get('company_id')
            
            visits_today = db.query(Visit).options(joinedload(Visit.client)).join(Client).filter(
                Visit.visit_date <= end_of_today,
                Visit.visit_date >= now.replace(hour=0, minute=0, second=0),
                Client.company_id == company_id
            ).all()
            
            visits_future = db.query(Visit).options(joinedload(Visit.client)).join(Client).filter(
                Visit.visit_date > end_of_today,
                Visit.visit_date <= end_of_7_days,
                Client.company_id == company_id
            ).all()

            for v in visits_today:
                if not v.client_id: continue
                try:
                    client_url = url_for('clients.view', client_id=v.client_id)
                except:
                    client_url = "#"
                today_list.append(format_item(v, _('Visit'), client_url, is_call=False, date_field='visit_date'))
                
            for v in visits_future:
                if not v.client_id: continue
                try:
                    client_url = url_for('clients.view', client_id=v.client_id)
                except:
                    client_url = "#"
                upcoming_list.append(format_item(v, _('Visit'), client_url, is_call=False, date_field='visit_date'))
        except Exception as e:
            print(f"Error fetching visits: {e}")

        # 3. Tasks
        try:
            task_query = db.query(Task).options(joinedload(Task.client)).filter(
                Task.status.in_(['open', 'in_progress', 'pending_approval']),
                Task.company_id == company_id
            )
            if user_role not in ['owner', 'admin', 'manager', 'superadmin']:
                task_query = task_query.filter(
                    or_(
                        Task.assigned_to_id == user_id,
                        (Task.assigned_to_id.is_(None)) & (Task.assigned_by_id == user_id)
                    )
                )
                
            tasks_today = task_query.filter(Task.due_date <= end_of_today).all()
            tasks_future = task_query.filter(Task.due_date > end_of_today, Task.due_date <= end_of_7_days).all()

            for t in tasks_today:
                today_list.append(format_item(t, _('Task'), url_for('tasks.index'), date_field='due_date', note_field='title'))
            for t in tasks_future:
                upcoming_list.append(format_item(t, _('Task'), url_for('tasks.index'), date_field='due_date', note_field='title'))
        except Exception as e:
             print(f"Error fetching tasks: {e}")

        # 4. Project Tickets
        try:
            ticket_query = db.query(ProjectTicket).join(Project).options(joinedload(ProjectTicket.project)).filter(
                ProjectTicket.status.in_(['pending', 'in_progress', 'pending_approval']),
                Project.status == 'active',
                Project.company_id == company_id
            )
            # For tickets, we filter by assignment usually, or if user is owner of project?
            # Sticking to assignment for agenda to avoid clutter
            ticket_query = ticket_query.filter(ProjectTicket.assigned_to == user_id)
            
            tickets_today = ticket_query.filter(or_(ProjectTicket.due_date <= end_of_today, ProjectTicket.due_date.is_(None))).all()  
            
            tickets_future = ticket_query.filter(ProjectTicket.due_date > end_of_today, ProjectTicket.due_date <= end_of_7_days).all()

            for t in tickets_today:
                if not t.project_id: continue
                try:
                    proj_url = url_for('projects.view', project_id=t.project_id)
                except:
                    proj_url = "#"
                today_list.append(format_item(t, _('Project Task'), proj_url, date_field='due_date', note_field='title'))
                
            for t in tickets_future:
                if not t.project_id: continue
                try:
                    proj_url = url_for('projects.view', project_id=t.project_id)
                except:
                    proj_url = "#"
                upcoming_list.append(format_item(t, _('Project Task'), proj_url, date_field='due_date', note_field='title'))
        except Exception as e:
            print(f"Error fetching tickets: {e}")
            
        # Sort lists by date
        today_list.sort(key=lambda x: x['date'] or '')
        upcoming_list.sort(key=lambda x: x['date'] or '')
        
        return jsonify({
            'today': today_list,
            'upcoming': upcoming_list
        })
    finally:
        db.close()


@bp.route('/types')
@login_required
def get_types():
    """Get all interaction types for dropdowns"""
    with get_db() as db:
        types = db.query(InteractionType).all()
        return jsonify([{
            'id': t.id, 
            'name': t.name, 
            'icon': t.icon, 
            'is_call': t.is_call
        } for t in types])

@bp.route('/<int:interaction_id>/update', methods=['POST'])
@login_required
def update(interaction_id):
    """Update an existing interaction"""
    data = request.get_json()
    
    with get_db() as db:
        interaction = db.query(Interaction).filter_by(id=interaction_id).first()
        
        if not interaction:
            return jsonify({'success': False, 'message': 'Interaction not found'}), 404
            
        # Update fields
        if 'notes' in data:
            interaction.notes = data['notes']
        if 'deal_id' in data:
            interaction.deal_id = data['deal_id']  
        if 'date' in data:
            try:
                interaction.date = datetime.fromisoformat(data['date'])
            except ValueError:
                pass
        if 'status' in data:
            interaction.status = data['status']
        if 'type_id' in data:
            interaction.type_id = data['type_id']
            
        db.commit()
        
        return jsonify({'success': True, 'message': 'Updated successfully'})


@bp.route('/types/create', methods=['POST'])
@login_required
def create_type():
    """Create a new interaction type"""
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({'success': False, 'message': 'Name required'}), 400
    
    with get_db() as db:
        new_type = InteractionType(
            name=name,
            icon=data.get('icon', 'bi bi-circle'),
            is_call=data.get('is_call', False)
        )
        db.add(new_type)
        db.commit()
        return jsonify({'success': True, 'item': {'id': new_type.id, 'name': new_type.name}})


@bp.route('/types/<int:type_id>/update', methods=['POST'])
@login_required
def update_type(type_id):
    """Update an interaction type"""
    data = request.get_json()
    
    with get_db() as db:
        type_obj = db.query(InteractionType).get(type_id)
        if not type_obj:
            return jsonify({'success': False, 'message': 'Type not found'}), 404
            
        if 'name' in data: type_obj.name = data['name']
        if 'icon' in data: type_obj.icon = data['icon']
        if 'is_call' in data: type_obj.is_call = data['is_call']
        
        db.commit()
        return jsonify({'success': True})


@bp.route('/types/<int:type_id>/delete', methods=['POST'])
@login_required
def delete_type(type_id):
    """Delete an interaction type"""
    with get_db() as db:
        type_obj = db.query(InteractionType).get(type_id)
        if not type_obj:
            return jsonify({'success': False, 'message': 'Type not found'}), 404
            
        # Check usage
        count = db.query(Interaction).filter_by(type_id=type_id).count()
        if count > 0:
            return jsonify({'success': False, 'message': f'Cannot delete: Used in {count} interactions'}), 400
            
        db.delete(type_obj)
        db.commit()
        return jsonify({'success': True})
