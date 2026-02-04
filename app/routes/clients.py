"""
PURETEGO CRM - Clients Routes
Rotas de gestão de clientes e pipeline Kanban
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.routes.auth import login_required
from app.routes.auth import login_required
from app.models import Client, KanbanStage, Visit, HealthCheck, Proposal, Interaction, ServicePackage
from config.database import get_db
from datetime import datetime

bp = Blueprint('clients', __name__, url_prefix='/clients')


@bp.route('/')
@login_required
def index():
    """Lista de clientes"""
    with get_db() as db:
        from sqlalchemy.orm import joinedload
        clients_query = db.query(Client).options(
            joinedload(Client.kanban_stage),
            joinedload(Client.interested_package)
        ).order_by(Client.created_at.desc()).all()
        stages_query = db.query(KanbanStage).order_by(KanbanStage.order).all()
        
        # Serialize to avoid DetachedInstanceError
        clients = [{
            'id': c.id,
            'name': c.name,
            'gmb_profile_name': c.gmb_profile_name,
            'contact_name': c.contact_name,
            'phone': c.phone,
            'email': c.email,
            'created_at': c.created_at,
            'kanban_stage': {'name': c.kanban_stage.name, 'color': 'primary'} if c.kanban_stage else None,
            'interested_package': c.interested_package.name if c.interested_package else None
        } for c in clients_query]
        
        stages = [{'id': s.id, 'name': s.name} for s in stages_query]
    
    return render_template('clients/index.html', clients=clients, stages=stages)


@bp.route('/kanban')
@login_required
def kanban():
    """Visualização Kanban do pipeline de vendas"""
    with get_db() as db:
        stages = db.query(KanbanStage).order_by(KanbanStage.order).all()
        first_stage_id = stages[0].id if stages else -1
        
        # Organizar clientes por etapa
        kanban_data = []
        for stage in stages:
            from sqlalchemy.orm import joinedload
            clients = db.query(Client).options(joinedload(Client.interested_package))\
                .filter(Client.kanban_stage_id == stage.id).all()
            
            # Calculate Total Value (Exclude first stage)
            stage_value = 0
            if stage.id != first_stage_id:
                for client in clients:
                    if client.interested_package:
                        stage_value += client.interested_package.price

            # Serialize data to avoid DetachedInstanceError after session closes
            stage_dict = {
                'id': stage.id,
                'name': stage.name,
                'order': stage.order,
                'total_value': float(stage_value)
            }
            
            clients_list = []
            for client in clients:
                clients_list.append({
                    'id': client.id,
                    'name': client.name,
                    'contact_name': client.contact_name,
                    'package_name': client.interested_package.name if client.interested_package else None
                })

            kanban_data.append({
                'stage': stage_dict,
                'clients': clients_list
            })
    
    return render_template('clients/kanban.html', kanban_data=kanban_data)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Criar novo cliente"""
    if request.method == 'POST':
        name = request.form.get('name')
        gmb_profile_name = request.form.get('gmb_profile_name')
        contact_name = request.form.get('contact_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        kanban_stage_id = request.form.get('kanban_stage_id')
        package_id = request.form.get('interested_package_id')
        
        with get_db() as db:
            client = Client(
                name=name,
                gmb_profile_name=gmb_profile_name,
                contact_name=contact_name,
                phone=phone,
                email=email,
                address=address,
                kanban_stage_id=int(kanban_stage_id) if kanban_stage_id else None
            )
            if package_id:
                client.interested_package_id = int(package_id)
                
            db.add(client)
            db.commit()
            
            flash(f'Cliente {name} criado com sucesso!', 'success')
            return redirect(url_for('clients.view', client_id=client.id))
    
    with get_db() as db:
        stages_query = db.query(KanbanStage).order_by(KanbanStage.order).all()
        packages_query = db.query(ServicePackage).order_by(ServicePackage.price).all()
        
        stages = [{'id': s.id, 'name': s.name} for s in stages_query]
        packages = [{'id': p.id, 'name': p.name, 'price': float(p.price)} for p in packages_query]
    
    return render_template('clients/create.html', stages=stages, packages=packages)


@bp.route('/<int:client_id>')
@login_required
def view(client_id):
    """Visualizar detalhes do cliente"""
    with get_db() as db:
        from sqlalchemy.orm import joinedload
        client = db.query(Client).options(
            joinedload(Client.kanban_stage),
            joinedload(Client.interested_package)
        ).filter(Client.id == client_id).first()
        
        if not client:
            flash('Cliente não encontrado.', 'error')
            return redirect(url_for('clients.index'))
            
        # Buscar visitas, health checks e propostas
        visits = db.query(Visit).filter(Visit.client_id == client_id)\
            .order_by(Visit.visit_date.desc()).all()
        
        health_checks = db.query(HealthCheck).filter(HealthCheck.client_id == client_id)\
            .order_by(HealthCheck.created_at.desc()).all()
        
        proposals = db.query(Proposal).filter(Proposal.client_id == client_id)\
            .order_by(Proposal.created_at.desc()).all()
        
        stages = db.query(KanbanStage).order_by(KanbanStage.order).all()
        
        from sqlalchemy.orm import joinedload
        interactions = db.query(Interaction).options(joinedload(Interaction.type), joinedload(Interaction.user))\
            .filter(Interaction.client_id == client_id)\
            .order_by(Interaction.date.desc()).all()
    
        return render_template(
            'clients/view.html',
            client=client,
            visits=visits,
            health_checks=health_checks,
            proposals=proposals,
            stages=stages,
            interactions=interactions
        )


@bp.route('/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(client_id):
    """Editar cliente"""
    with get_db() as db:
        from sqlalchemy.orm import joinedload
        client = db.query(Client).options(
            joinedload(Client.kanban_stage),
            joinedload(Client.interested_package)
        ).filter(Client.id == client_id).first()
        
        if not client:
            flash('Cliente não encontrado.', 'error')
            return redirect(url_for('clients.index'))
        
        if request.method == 'POST':
            client.name = request.form.get('name')
            client.gmb_profile_name = request.form.get('gmb_profile_name')
            client.contact_name = request.form.get('contact_name')
            client.phone = request.form.get('phone')
            client.email = request.form.get('email')
            client.address = request.form.get('address')
            
            # New Fields
            client.receptionist_name = request.form.get('receptionist_name')
            client.decision_maker_name = request.form.get('decision_maker_name')
            client.decision_factors = request.form.get('decision_factors')
            client.best_contact_time = request.form.get('best_contact_time')
            client.preferred_contact_method = request.form.get('preferred_contact_method')
            client.observations = request.form.get('observations')
            
            kanban_stage_id = request.form.get('kanban_stage_id')
            client.kanban_stage_id = int(kanban_stage_id) if kanban_stage_id else None
            
            package_id = request.form.get('interested_package_id')
            client.interested_package_id = int(package_id) if package_id else None
            
            try:
                db.commit()
                flash(f'Cliente {client.name} atualizado com sucesso!', 'success')
                return redirect(url_for('clients.view', client_id=client.id))
            except Exception as e:
                db.rollback()
                flash(f'Erro ao salvar alterações: {str(e)}', 'error')
                # Keep user on edit page to try again or see error
                stages_query = db.query(KanbanStage).order_by(KanbanStage.order).all()
                packages_query = db.query(ServicePackage).order_by(ServicePackage.price).all()
                stages = [{'id': s.id, 'name': s.name} for s in stages_query]
                packages = [{'id': p.id, 'name': p.name, 'price': float(p.price)} for p in packages_query]
                return render_template('clients/edit.html', client=client, stages=stages, packages=packages)
        
        stages_query = db.query(KanbanStage).order_by(KanbanStage.order).all()
        packages_query = db.query(ServicePackage).order_by(ServicePackage.price).all()
        
        stages = [{'id': s.id, 'name': s.name} for s in stages_query]
        packages = [{'id': p.id, 'name': p.name, 'price': float(p.price)} for p in packages_query]
    
        return render_template('clients/edit.html', client=client, stages=stages, packages=packages)


@bp.route('/<int:client_id>/delete', methods=['POST'])
@login_required
def delete(client_id):
    """Deletar cliente"""
    with get_db() as db:
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if not client:
            flash('Cliente não encontrado.', 'error')
            return redirect(url_for('clients.index'))
        
        client_name = client.name
        db.delete(client)
        db.commit()
        
        flash(f'Cliente {client_name} deletado com sucesso.', 'success')
    
    return redirect(url_for('clients.index'))


@bp.route('/<int:client_id>/move', methods=['POST'])
@login_required
def move_stage(client_id):
    """Mover cliente para outra etapa do Kanban (API)"""
    data = request.get_json()
    new_stage_id = data.get('stage_id')
    
    with get_db() as db:
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if not client:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        client.kanban_stage_id = int(new_stage_id) if new_stage_id else None
        db.commit()
        
        return jsonify({'success': True, 'message': 'Cliente movido com sucesso'})


@bp.route('/stages', methods=['GET'])
@login_required
def get_stages():
    """Obter lista de etapas do Kanban (API)"""
    with get_db() as db:
        stages = db.query(KanbanStage).order_by(KanbanStage.order).all()
        return jsonify([stage.to_dict() for stage in stages])


@bp.route('/stages/create', methods=['POST'])
@login_required
def create_stage():
    """Criar nova etapa do Kanban"""
    name = request.form.get('name')
    order = request.form.get('order', 0)
    
    with get_db() as db:
        stage = KanbanStage(name=name, order=int(order))
        db.add(stage)
        db.commit()
        
        flash(f'Etapa {name} criada com sucesso!', 'success')
    
    return redirect(url_for('clients.kanban'))


@bp.route('/stages/<int:stage_id>/edit', methods=['POST'])
@login_required
def edit_stage(stage_id):
    """Editar etapa do Kanban"""
    with get_db() as db:
        stage = db.query(KanbanStage).filter(KanbanStage.id == stage_id).first()
        
        if not stage:
            flash('Etapa não encontrada.', 'error')
            return redirect(url_for('clients.kanban'))
        
        stage.name = request.form.get('name')
        stage.order = int(request.form.get('order', 0))
        db.commit()
        
        flash(f'Etapa {stage.name} atualizada com sucesso!', 'success')
    
    return redirect(url_for('clients.kanban'))


@bp.route('/stages/<int:stage_id>/delete', methods=['POST'])
@login_required
def delete_stage(stage_id):
    """Deletar etapa do Kanban"""
    with get_db() as db:
        stage = db.query(KanbanStage).filter(KanbanStage.id == stage_id).first()
        
        if not stage:
            flash('Etapa não encontrada.', 'error')
            return redirect(url_for('clients.kanban'))
        
        # Verificar se há clientes nesta etapa
        clients_count = db.query(Client).filter(Client.kanban_stage_id == stage_id).count()
        
        if clients_count > 0:
            flash(f'Não é possível deletar esta etapa pois há {clients_count} cliente(s) associado(s).', 'error')
            return redirect(url_for('clients.kanban'))
        
        stage_name = stage.name
        db.delete(stage)
        db.commit()
        
        flash(f'Etapa {stage_name} deletada com sucesso.', 'success')
    
    return redirect(url_for('clients.kanban'))
