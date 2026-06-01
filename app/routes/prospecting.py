"""
PURETEGO CRM - Prospecting & Leads Routes
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from app.services.serper_service import SerperService
from app.utils.decorators import login_required, role_required
from app.models import Client, Deal, DealStatus, KanbanStage, Interaction, Lead, LeadActivity, User
from config.database import get_db
from flask_babel import gettext as _
from datetime import datetime

bp = Blueprint('prospecting', __name__, url_prefix='/prospecting')

# =========================================================================
# Google Maps (Serper.dev) search and lead capture
# =========================================================================

@bp.route('/search', methods=['GET'])
@login_required
@role_required('owner', 'manager', 'sdr', 'sales', 'gmb_manager')
def search():
    """Tela de busca de prospecção via Google Maps"""
    query = request.args.get('q', '')
    location = request.args.get('location', '')
    
    results = []
    error = None
    
    if query:
        service = SerperService()
        if not service.api_key:
             flash(_('API Key do Serper não configurada. Contate o admin.'), 'error')
        else:
            response = service.search_places(query, location=location)
            if response.get('success'):
                results = response.get('places', [])
            else:
                error = response.get('error')
                flash(f"{_('Erro na busca:')} {error}", 'error')
    
    return render_template('prospecting/search.html', results=results, query=query, location=location)


@bp.route('/add-lead', methods=['POST'])
@login_required
@role_required('owner', 'manager', 'sdr', 'sales', 'gmb_manager')
def add_lead():
    """Converte um resultado da busca do Google Maps em Lead para Prospecção"""
    data = request.form
    
    name = data.get('name')
    address = data.get('address')
    phone = data.get('phone')
    website = data.get('website')
    place_id = data.get('place_id')
    
    company_id = session.get('company_id')
    user_id = session.get('user_id')
    
    if not name:
        flash(_('Nome é obrigatório.'), 'error')
        return redirect(url_for('prospecting.search'))
        
    with get_db() as db:
        # Verificar se lead já existe pelo nome ou link/place
        existing = db.query(Lead).filter(
            Lead.company_id == company_id, 
            Lead.company_name == name
        ).first()
        
        if existing:
            flash(f"{_('Lead')} {name} {_('já existe na base de prospecção.')}", 'warning')
            return redirect(url_for('prospecting.search', q=request.args.get('q'), location=request.args.get('location')))
            
        # Determina o link maps do place_id se não fornecido
        maps_link = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else None
        if website and not maps_link:
            maps_link = website if "google.com/maps" in website else None

        # Criar Lead
        lead = Lead(
            company_name=name,
            company_id=company_id,
            owner_id=user_id,
            source='google_maps',
            maps_link=maps_link,
            address=address,
            qualification='cold',
            prospecting_method='phone_call',
            status='new',
            observations=f"Prospectado via Google Maps. Tel: {phone or ''}. Web: {website or ''}"
        )
        db.add(lead)
        db.flush()
        
        # Registrar atividade inicial
        activity = LeadActivity(
            lead_id=lead.id,
            user_id=user_id,
            action='created',
            notes=_('Lead prospectado e adicionado via busca do Google Maps.')
        )
        db.add(activity)
        db.commit()
        
        flash(f"{_('Lead')} {name} {_('capturado com sucesso para prospecção!')}", 'success')
        
    return redirect(url_for('prospecting.search', q=request.args.get('q'), location=request.args.get('location')))


# =========================================================================
# Prospecting Leads CRUD
# =========================================================================

@bp.route('/leads', methods=['GET'])
@login_required
@role_required('owner', 'manager', 'sdr', 'sales', 'gmb_manager')
def leads():
    """Listagem de leads de prospecção com filtros e busca"""
    company_id = session.get('company_id')
    
    # Query parameters
    search_q = request.args.get('q', '').strip()
    filter_city = request.args.get('city', '').strip()
    filter_neighborhood = request.args.get('neighborhood', '').strip()
    filter_source = request.args.get('source', '').strip()
    filter_method = request.args.get('prospecting_method', '').strip()
    filter_status = request.args.get('status', '').strip()
    
    with get_db() as db:
        query = db.query(Lead).filter(Lead.company_id == company_id)
        
        # Apply filters
        if search_q:
            query = query.filter(Lead.company_name.ilike(f"%{search_q}%"))
        if filter_city:
            query = query.filter(Lead.city.ilike(f"%{filter_city}%"))
        if filter_neighborhood:
            query = query.filter(Lead.neighborhood.ilike(f"%{filter_neighborhood}%"))
        if filter_source:
            query = query.filter(Lead.source == filter_source)
        if filter_method:
            query = query.filter(Lead.prospecting_method == filter_method)
        if filter_status:
            query = query.filter(Lead.status == filter_status)
            
        leads_list = query.order_by(Lead.created_at.desc()).all()
        
        # Get unique cities & neighborhoods for filter dropdowns
        cities = [r[0] for r in db.query(Lead.city).filter(Lead.company_id == company_id, Lead.city.isnot(None)).distinct().all() if r[0]]
        neighborhoods = [r[0] for r in db.query(Lead.neighborhood).filter(Lead.company_id == company_id, Lead.neighborhood.isnot(None)).distinct().all() if r[0]]
        
        return render_template(
            'prospecting/index.html',
            leads=leads_list,
            cities=cities,
            neighborhoods=neighborhoods,
            q=search_q,
            selected_city=filter_city,
            selected_neighborhood=filter_neighborhood,
            selected_source=filter_source,
            selected_method=filter_method,
            selected_status=filter_status
        )


@bp.route('/leads/create', methods=['GET', 'POST'])
@login_required
@role_required('owner', 'manager', 'sdr', 'sales', 'gmb_manager')
def leads_create():
    """Criação manual de um Lead de Prospecção"""
    company_id = session.get('company_id')
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        name = request.form.get('company_name')
        source = request.form.get('source', 'field_visit')
        maps_link = request.form.get('maps_link')
        address = request.form.get('address')
        city = request.form.get('city')
        neighborhood = request.form.get('neighborhood')
        qualification = request.form.get('qualification', 'cold')
        business_health = request.form.get('business_health')
        prospecting_method = request.form.get('prospecting_method', 'phone_call')
        status = request.form.get('status', 'new')
        observations = request.form.get('observations')
        
        if not name:
            flash(_('Nome da empresa é obrigatório.'), 'error')
            return render_template('prospecting/create.html')
            
        with get_db() as db:
            lead = Lead(
                company_name=name,
                company_id=company_id,
                owner_id=user_id,
                source=source,
                maps_link=maps_link,
                address=address,
                city=city,
                neighborhood=neighborhood,
                qualification=qualification,
                business_health=business_health,
                prospecting_method=prospecting_method,
                status=status,
                observations=observations
            )
            db.add(lead)
            db.flush()
            
            # Registrar atividade de criação
            activity = LeadActivity(
                lead_id=lead.id,
                user_id=user_id,
                action='created',
                notes=_('Lead cadastrado manualmente.')
            )
            db.add(activity)
            db.commit()
            
            flash(f"{_('Lead')} {name} {_('cadastrado com sucesso!')}", 'success')
            return redirect(url_for('prospecting.leads'))
            
    return render_template('prospecting/create.html')


@bp.route('/leads/<int:lead_id>', methods=['GET'])
@login_required
@role_required('owner', 'manager', 'sdr', 'sales', 'gmb_manager')
def leads_view(lead_id):
    """Visualização de detalhes da ficha de um Lead"""
    company_id = session.get('company_id')
    
    with get_db() as db:
        lead = db.query(Lead).filter(Lead.id == lead_id, Lead.company_id == company_id).first()
        if not lead:
            flash(_('Lead não encontrado.'), 'error')
            return redirect(url_for('prospecting.leads'))
            
        # Obter o histórico de atividades ordenado
        activities = db.query(LeadActivity).filter(LeadActivity.lead_id == lead_id).order_by(LeadActivity.created_at.desc()).all()
        
        return render_template('prospecting/view.html', lead=lead, activities=activities)


@bp.route('/leads/<int:lead_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('owner', 'manager', 'sdr', 'sales', 'gmb_manager')
def leads_edit(lead_id):
    """Edição dos dados de um Lead"""
    company_id = session.get('company_id')
    user_id = session.get('user_id')
    
    with get_db() as db:
        lead = db.query(Lead).filter(Lead.id == lead_id, Lead.company_id == company_id).first()
        if not lead:
            flash(_('Lead não encontrado.'), 'error')
            return redirect(url_for('prospecting.leads'))
            
        if request.method == 'POST':
            name = request.form.get('company_name')
            source = request.form.get('source')
            maps_link = request.form.get('maps_link')
            address = request.form.get('address')
            city = request.form.get('city')
            neighborhood = request.form.get('neighborhood')
            qualification = request.form.get('qualification')
            business_health = request.form.get('business_health')
            prospecting_method = request.form.get('prospecting_method')
            status = request.form.get('status')
            observations = request.form.get('observations')
            
            if not name:
                flash(_('Nome da empresa é obrigatório.'), 'error')
                return render_template('prospecting/edit.html', lead=lead)
                
            old_status = lead.status
            
            lead.company_name = name
            lead.source = source
            lead.maps_link = maps_link
            lead.address = address
            lead.city = city
            lead.neighborhood = neighborhood
            lead.qualification = qualification
            lead.business_health = business_health
            lead.prospecting_method = prospecting_method
            lead.status = status
            lead.observations = observations
            
            # Registrar alteração de status se houver mudança
            if old_status != status:
                activity = LeadActivity(
                    lead_id=lead.id,
                    user_id=user_id,
                    action='status_change',
                    notes=f"{_('Status atualizado de')} '{old_status}' {_('para')} '{status}'."
                )
                db.add(activity)
            else:
                activity = LeadActivity(
                    lead_id=lead.id,
                    user_id=user_id,
                    action='updated',
                    notes=_('Informações da ficha atualizadas.')
                )
                db.add(activity)
                
            db.commit()
            
            flash(f"{_('Lead')} {name} {_('atualizado com sucesso!')}", 'success')
            return redirect(url_for('prospecting.leads_view', lead_id=lead_id))
            
        return render_template('prospecting/edit.html', lead=lead)


@bp.route('/leads/<int:lead_id>/delete', methods=['POST'])
@login_required
@role_required('owner', 'manager', 'sdr', 'sales', 'gmb_manager')
def leads_delete(lead_id):
    """Exclusão de um Lead de Prospecção"""
    company_id = session.get('company_id')
    
    with get_db() as db:
        lead = db.query(Lead).filter(Lead.id == lead_id, Lead.company_id == company_id).first()
        if not lead:
            flash(_('Lead não encontrado.'), 'error')
            return redirect(url_for('prospecting.leads'))
            
        name = lead.company_name
        db.delete(lead)
        db.commit()
        
        flash(f"{_('Lead')} {name} {_('removido com sucesso!')}", 'success')
        
    return redirect(url_for('prospecting.leads'))


@bp.route('/leads/<int:lead_id>/activity', methods=['POST'])
@login_required
@role_required('owner', 'manager', 'sdr', 'sales', 'gmb_manager')
def leads_activity(lead_id):
    """Adiciona uma anotação de histórico/atividade para o Lead"""
    company_id = session.get('company_id')
    user_id = session.get('user_id')
    
    notes = request.form.get('notes')
    action = request.form.get('action', 'note_added')
    
    if not notes:
        flash(_('Descrição da atividade é obrigatória.'), 'error')
        return redirect(url_for('prospecting.leads_view', lead_id=lead_id))
        
    with get_db() as db:
        lead = db.query(Lead).filter(Lead.id == lead_id, Lead.company_id == company_id).first()
        if not lead:
            flash(_('Lead não encontrado.'), 'error')
            return redirect(url_for('prospecting.leads'))
            
        activity = LeadActivity(
            lead_id=lead_id,
            user_id=user_id,
            action=action,
            notes=notes
        )
        db.add(activity)
        db.commit()
        
        flash(_('Atividade registrada com sucesso!'), 'success')
        
    return redirect(url_for('prospecting.leads_view', lead_id=lead_id))


@bp.route('/leads/<int:lead_id>/convert', methods=['POST'])
@login_required
@role_required('owner', 'manager', 'sdr', 'sales', 'gmb_manager')
def leads_convert(lead_id):
    """Converte o Lead em Cliente Ativo + Oportunidade no Kanban"""
    company_id = session.get('company_id')
    user_id = session.get('user_id')
    
    with get_db() as db:
        lead = db.query(Lead).filter(Lead.id == lead_id, Lead.company_id == company_id).first()
        if not lead:
            flash(_('Lead não encontrado.'), 'error')
            return redirect(url_for('prospecting.leads'))
            
        if lead.status == 'converted':
            flash(_('Este lead já foi convertido anteriormente.'), 'warning')
            return redirect(url_for('prospecting.leads_view', lead_id=lead_id))
            
        # 1. Obter o primeiro estágio do Kanban da empresa
        first_stage = db.query(KanbanStage).filter(
            KanbanStage.company_id == company_id
        ).order_by(KanbanStage.order).first()
        
        if not first_stage:
            # Fallback se não houver estágios específicos
            first_stage = db.query(KanbanStage).order_by(KanbanStage.order).first()
            
        # 2. Criar registro de Client
        # Combina endereço físico com bairro e cidade
        full_address = lead.address or ''
        parts = []
        if lead.neighborhood:
            parts.append(lead.neighborhood)
        if lead.city:
            parts.append(lead.city)
        if parts:
            extra = ", ".join(parts)
            full_address = f"{full_address}\n{extra}".strip()

        new_client = Client(
            name=lead.company_name,
            company_id=company_id,
            owner_id=lead.owner_id or user_id,
            address=full_address,
            kanban_stage_id=first_stage.id if first_stage else None
        )
        new_client.status = 'lead'  # Kanban active workflow starts as 'lead'
        
        # Build comprehensive observations from prospecting lead data
        obs_parts = [f"Convertido a partir de Lead de Prospecção ID {lead.id}."]
        if lead.maps_link:
            obs_parts.append(f"Google Maps Link: {lead.maps_link}")
            if not new_client.website:
                new_client.website = lead.maps_link
        if lead.business_health:
            obs_parts.append(f"Análise de Saúde: {lead.business_health}")
        if lead.observations:
            obs_parts.append(f"Observações de Prospecção:\n{lead.observations}")
            
        new_client.observations = "\n\n".join(obs_parts)
        db.add(new_client)
        db.flush() # Gerar ID do Cliente

        # 4. Criar Deal associado
        deal = Deal(
            title=f"Oportunidade {lead.company_name}",
            company_id=company_id,
            client_id=new_client.id,
            owner_id=lead.owner_id or user_id,
            kanban_stage_id=first_stage.id if first_stage else None,
            value=0.0
        )
        db.add(deal)
        
        # 5. Atualizar o status do Lead de Prospecção para 'converted'
        lead.status = 'converted'
        
        # 6. Registrar atividade de conversão
        activity = LeadActivity(
            lead_id=lead.id,
            user_id=user_id,
            action='converted',
            notes=f"{_('Lead convertido com sucesso em Cliente Ativo.')} ID: {new_client.id}."
        )
        db.add(activity)
        db.commit()
        client_id = new_client.id
        
        flash(f"{_('Lead')} {lead.company_name} {_('convertido com sucesso em Cliente e inserido no Kanban!')}", 'success')
        
    return redirect(url_for('clients.view', client_id=client_id))
