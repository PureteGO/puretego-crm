"""
PURETEGO CRM - Visits Routes
Rotas de gestão de visitas
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.routes.auth import login_required
from app.models import Visit, Client
from config.database import get_db
from datetime import datetime

bp = Blueprint('visits', __name__, url_prefix='/visits')


@bp.route('/')
@login_required
def index():
    """Lista de visitas"""
    with get_db() as db:
        visits = db.query(Visit).order_by(Visit.visit_date.desc()).all()
    
    return render_template('visits/index.html', visits=visits)


@bp.route('/create', methods=['GET', 'POST'])
@bp.route('/create/<int:client_id>', methods=['GET', 'POST'])
@login_required
def create(client_id=None):
    """Criar nova visita"""
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        visit_date_str = request.form.get('visit_date')
        notes = request.form.get('notes')
        next_step = request.form.get('next_step')
        
        # Converter data
        try:
            visit_date = datetime.strptime(visit_date_str, '%Y-%m-%dT%H:%M')
        except:
            visit_date = datetime.now()
        
        with get_db() as db:
            visit = Visit(
                client_id=int(client_id),
                user_id=session['user_id'],
                visit_date=visit_date,
                notes=notes,
                next_step=next_step
            )
            db.add(visit)
            db.commit()
            
            flash('Visita registrada com sucesso!', 'success')
            return redirect(url_for('clients.view', client_id=client_id))
    
    with get_db() as db:
        clients = db.query(Client).order_by(Client.name).all()
        
        selected_client = None
        if client_id:
            selected_client = db.query(Client).filter(Client.id == client_id).first()
    
    return render_template(
        'visits/create.html',
        clients=clients,
        selected_client=selected_client
    )


@bp.route('/<int:visit_id>')
@login_required
def view(visit_id):
    """Visualizar detalhes da visita"""
    with get_db() as db:
        visit = db.query(Visit).filter(Visit.id == visit_id).first()
        
        if not visit:
            flash('Visita não encontrada.', 'error')
            return redirect(url_for('visits.index'))
    
    return render_template('visits/view.html', visit=visit)


@bp.route('/<int:visit_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(visit_id):
    """Editar visita"""
    with get_db() as db:
        visit = db.query(Visit).filter(Visit.id == visit_id).first()
        
        if not visit:
            flash('Visita não encontrada.', 'error')
            return redirect(url_for('visits.index'))
        
        if request.method == 'POST':
            visit_date_str = request.form.get('visit_date')
            visit.notes = request.form.get('notes')
            visit.next_step = request.form.get('next_step')
            
            # Converter data
            try:
                visit.visit_date = datetime.strptime(visit_date_str, '%Y-%m-%dT%H:%M')
            except:
                pass
            
            db.commit()
            
            flash('Visita atualizada com sucesso!', 'success')
            return redirect(url_for('visits.view', visit_id=visit.id))
    
    return render_template('visits/edit.html', visit=visit)


@bp.route('/<int:visit_id>/delete', methods=['POST'])
@login_required
def delete(visit_id):
    """Deletar visita"""
    with get_db() as db:
        visit = db.query(Visit).filter(Visit.id == visit_id).first()
        
        if not visit:
            flash('Visita não encontrada.', 'error')
            return redirect(url_for('visits.index'))
        
        client_id = visit.client_id
        db.delete(visit)
        db.commit()
        
        flash('Visita deletada com sucesso.', 'success')
    
    return redirect(url_for('clients.view', client_id=client_id))
