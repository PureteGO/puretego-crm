"""
PURETEGO CRM - Calendar Routes
Rotas para visualização e gestão da agenda
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from app.routes.auth import login_required
from app.models import Visit, Interaction, Client, User, InteractionType, KanbanStage
from config.database import get_db
from datetime import datetime, timedelta
from app.models.visit import Visit
from sqlalchemy import or_

bp = Blueprint('calendar', __name__, url_prefix='/calendar')

@bp.route('/')
@login_required
def index():
    """Visualização principal do calendário"""
    with get_db() as db:
        users = db.query(User).all()
        clients = db.query(Client).order_by(Client.name).all()
        interaction_types = db.query(InteractionType).all()
        
        return render_template('calendar/index.html', 
                               users=users, 
                               clients=clients,
                               interaction_types=interaction_types)

@bp.route('/events')
@login_required
def get_events():
    """API para retornar eventos (Visitas e Interações) para o FullCalendar"""
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    
    # Validar datas
    try:
        start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00')).date()
        end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00')).date()
    except:
        start_date = datetime.now().date() - timedelta(days=30)
        end_date = datetime.now().date() + timedelta(days=30)

    events = []

    with get_db() as db:
        # 1. Buscar Visitas
        visits = db.query(Visit).filter(
            Visit.visit_date >= start_date,
            Visit.visit_date <= end_date
        ).all()
        
        for v in visits:
            events.append({
                'id': f'visit_{v.id}',
                'title': f'Visita: {v.client.name}',
                'start': v.visit_date.isoformat(),
                'end': (v.visit_date + timedelta(hours=1)).isoformat(), # Assume 1h
                'backgroundColor': '#0d6efd', # Blue
                'borderColor': '#0d6efd',
                'extendedProps': {
                    'type': 'visit',
                    'client_id': v.client_id,
                    'notes': v.notes
                }
            })
            
        # 2. Buscar Interações (Calls, Emails, etc)
        interactions = db.query(Interaction).filter(
            Interaction.date >= start_date,
            Interaction.date <= end_date
        ).all()
        
        for i in interactions:
            color = '#6c757d' # Grey default
            if i.type.is_call:
                color = '#198754' # Green for calls
            elif 'Email' in i.type.name:
                color = '#ffc107' # Yellow for email
            
            events.append({
                'id': f'interaction_{i.id}',
                'title': f'{i.type.name}: {i.client.name}',
                'start': i.date.isoformat(),
                # Interactions might not have end time, use start
                'allDay': False,
                'backgroundColor': color,
                'borderColor': color,
                'extendedProps': {
                    'type': 'interaction',
                    'client_id': i.client_id,
                    'interaction_type_id': i.type_id,
                    'notes': i.notes,
                    'status': i.status
                }
            })
            
    return jsonify(events)

@bp.route('/save', methods=['POST'])
@login_required
def save_event():
    """Salvar evento (Visita ou Interação) com criação inline de cliente"""
    data = request.get_json()
    
    event_type = data.get('type') # 'visit' or 'interaction'
    client_id = data.get('client_id')
    date_str = data.get('date')
    notes = data.get('notes')
    
    # Parse date
    try:
        event_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        return jsonify({'success': False, 'message': 'Data inválida'}), 400

    with get_db() as db:
        # 1. Handle New Client Creation
        if client_id == 'new':
            new_client_name = data.get('new_client_name')
            new_client_phone = data.get('new_client_phone')
            
            if not new_client_name:
                 return jsonify({'success': False, 'message': 'Nome do cliente é obrigatório'}), 400
                 
            # Default KanBan stage
            try:
                first_stage = db.query(KanbanStage).order_by(KanbanStage.order).first()
                stage_id = first_stage.id if first_stage else 1
            except:
                stage_id = 1

            client = Client(
                name=new_client_name,
                phone=new_client_phone,
                kanban_stage_id=stage_id
            )
            db.add(client)
            db.flush() # Get ID
            client_id = client.id
        else:
            try:
                client_id = int(client_id)
            except:
                return jsonify({'success': False, 'message': 'Cliente inválido'}), 400

        # 2. Create Event
        # Get current user (simple fix: assume user_id 1 or from session if available in future context)
        # Note: In a real app we need `current_user.id`. Assuming session has it or fixed for now.
        from flask import session
        user_id = session.get('user_id')
        if not user_id:
             # Fallback just in case, though login_required checks Session
             user = db.query(User).first()
             user_id = user.id if user else 1

        if event_type == 'visit':
            visit = Visit(
                client_id=client_id,
                user_id=user_id,
                visit_date=event_date,
                notes=notes
            )
            db.add(visit)
            
        elif event_type == 'interaction':
            interaction_type_id = data.get('interaction_type_id')
            if not interaction_type_id:
                 return jsonify({'success': False, 'message': 'Tipo de interação é obrigatório'}), 400
                 
            interaction = Interaction(
                client_id=client_id,
                user_id=user_id,
                type_id=int(interaction_type_id),
                date=event_date,
                status='scheduled', # Created via calendar implies scheduled
                notes=notes
            )
            db.add(interaction)
        else:
            return jsonify({'success': False, 'message': 'Tipo de evento desconhecido'}), 400
            
        db.commit()
        
    return jsonify({'success': True, 'message': 'Agendamento criado!', 'client_id': client_id})

@bp.route('/update/<event_type>/<int:event_id>', methods=['POST'])
@login_required
def update_event(event_type, event_id):
    """Atualiza um agendamento existente"""
    data = request.get_json()
    date_str = data.get('date')
    notes = data.get('notes')
    client_id = data.get('client_id')
    
    try:
        event_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        return jsonify({'success': False, 'message': 'Data inválida'}), 400

    with get_db() as db:
        if event_type == 'visit':
            event = db.query(Visit).filter(Visit.id == event_id).first()
            if event:
                event.visit_date = event_date
                event.notes = notes
                if client_id: event.client_id = int(client_id)
        elif event_type == 'interaction':
            event = db.query(Interaction).filter(Interaction.id == event_id).first()
            if event:
                event.date = event_date
                event.notes = notes
                if client_id: event.client_id = int(client_id)
                if data.get('interaction_type_id'):
                    event.type_id = int(data.get('interaction_type_id'))
                if data.get('status'):
                    event.status = data.get('status')
        else:
            return jsonify({'success': False, 'message': 'Tipo de evento inválido'}), 400
            
        if not event:
            return jsonify({'success': False, 'message': 'Agendamento não encontrado'}), 404
            
        db.commit()
        return jsonify({'success': True, 'message': 'Agendamento atualizado!'})

@bp.route('/delete/<event_type>/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_type, event_id):
    """Remove um agendamento existente"""
    with get_db() as db:
        if event_type == 'visit':
            event = db.query(Visit).filter(Visit.id == event_id).first()
        elif event_type == 'interaction':
            event = db.query(Interaction).filter(Interaction.id == event_id).first()
        else:
            return jsonify({'success': False, 'message': 'Tipo de evento inválido'}), 400
            
        if not event:
            return jsonify({'success': False, 'message': 'Agendamento não encontrado'}), 404
            
        db.delete(event)
        db.commit()
        return jsonify({'success': True, 'message': 'Agendamento removido!'})
