from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.routes.auth import login_required
from app.models import Interaction, InteractionType, CadenceRule, Client
from config.database import get_db
from datetime import datetime, timedelta
from sqlalchemy import or_

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
    """Get tasks (scheduled interactions) formatted for dashboard"""
    now = datetime.now()
    end_of_today = now.replace(hour=23, minute=59, second=59)
    
    with get_db() as db:
        # 1. Overdue & Today
        urgent_tasks = db.query(Interaction).filter(
            Interaction.status == 'scheduled',
            Interaction.date <= end_of_today,
            Interaction.user_id == session['user_id']
        ).order_by(Interaction.date).all()
        
        # 2. Upcoming (Future)
        future_tasks = db.query(Interaction).filter(
            Interaction.status == 'scheduled',
            Interaction.date > end_of_today,
            Interaction.user_id == session['user_id']
        ).order_by(Interaction.date).limit(50).all()
        
        return jsonify({
            'today': [t.to_dict() for t in urgent_tasks],
            'upcoming': [t.to_dict() for t in future_tasks]
        })


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
