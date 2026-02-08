"""
PURETEGO CRM - Prospecting Routes
Rotas para busca e captação de leads via Serper.dev
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from app.services.serper_service import SerperService
from app.utils.decorators import login_required, role_required
from app.models import Client, Deal, DealStatus, KanbanStage, Interaction
from config.database import get_db

bp = Blueprint('prospecting', __name__, url_prefix='/prospecting')

@bp.route('/search', methods=['GET'])
@login_required
@role_required('owner', 'manager', 'sdr', 'sales', 'gmb_manager')
def search():
    """Tela de busca de prospecção"""
    query = request.args.get('q', '')
    location = request.args.get('location', '')
    
    results = []
    error = None
    
    if query:
        service = SerperService()
        if not service.api_key:
             flash('API Key do Serper não configurada. Contate o admin.', 'error')
        else:
            response = service.search_places(query, location=location)
            if response.get('success'):
                results = response.get('places', [])
            else:
                error = response.get('error')
                flash(f'Erro na busca: {error}', 'error')
    
    return render_template('prospecting/search.html', results=results, query=query, location=location)

@bp.route('/add-lead', methods=['POST'])
@login_required
@role_required('owner', 'manager', 'sdr', 'sales', 'gmb_manager')
def add_lead():
    """Converte um resultado da busca em Lead (Cliente + Deal)"""
    data = request.form
    
    # Extrair dados do form
    name = data.get('name')
    address = data.get('address')
    phone = data.get('phone')
    website = data.get('website')
    place_id = data.get('place_id')
    
    company_id = session.get('company_id')
    user_id = session.get('user_id')
    
    if not name:
        flash('Nome é obrigatório.', 'error')
        return redirect(url_for('prospecting.search'))
        
    with get_db() as db:
        # Verificar se cliente já existe pelo nome (simples deduplication)
        # TODO: Melhorar deduplicação por telefone ou place_id
        existing = db.query(Client).filter(Client.company_id == company_id, Client.name == name).first()
        
        if existing:
            flash(f'Cliente {name} já existe na base.', 'warning')
            return redirect(url_for('prospecting.search', q=request.args.get('q')))
            
        # 1. Criar Cliente
        new_client = Client(
            name=name,
            address=address,
            phone=phone,
            email=None, # Serper geralmente não dá email
            company_id=company_id,
            owner_id=user_id,
            status='lead'
        )
        new_client.notes = f"Prospectado via Serper. Website: {website}"
        db.add(new_client)
        db.flush() # Para ter o ID
        
        # 2. Criar Deal
        # Buscar estágio inicial (ex: "Lead" ou primeiro da ordem)
        first_stage = db.query(KanbanStage).filter(KanbanStage.company_id == company_id).order_by(KanbanStage.order).first()
        
        deal = Deal(
            title=f"Oportunidade {name}",
            company_id=company_id,
            client_id=new_client.id,
            owner_id=user_id,
            kanban_stage_id=first_stage.id if first_stage else None,
            value=0.0
        )
        db.add(deal)
        
        db.commit()
        
        flash(f'Lead {name} capturado com sucesso!', 'success')
        
    return redirect(url_for('prospecting.search', q=request.args.get('q'), location=request.args.get('location')))
