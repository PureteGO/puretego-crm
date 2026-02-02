"""
PURETEGO CRM - Proposals Routes
Rotas de gestão de propostas/orçamentos
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from app.routes.auth import login_required
from app.models import Proposal, ProposalItem, Client, Service
from app.services import PDFGenerator
from config.database import get_db
from datetime import datetime, timedelta

bp = Blueprint('proposals', __name__, url_prefix='/proposals')


@bp.route('/')
@login_required
def index():
    """Lista de propostas"""
    with get_db() as db:
        proposals_query = db.query(Proposal).order_by(Proposal.created_at.desc()).all()
        
        # Serialize to avoid DetachedInstanceError
        proposals = []
        for p in proposals_query:
            proposals.append({
                'id': p.id,
                'client_id': p.client_id,
                'client_name': p.client.name if p.client else 'Cliente removido',
                'total_amount': p.total_amount,
                'status': p.status,
                'created_at': p.created_at,
                'pdf_file_path': p.pdf_file_path
            })
    
    return render_template('proposals/index.html', proposals=proposals)


@bp.route('/create', methods=['GET', 'POST'])
@bp.route('/create/<int:client_id>', methods=['GET', 'POST'])
@login_required
def create(client_id=None):
    """Criar nova proposta"""
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        payment_terms = request.form.get('payment_terms')
        status = request.form.get('status', 'draft')
        
        # Obter serviços selecionados
        service_ids = request.form.getlist('service_ids[]')
        service_prices = request.form.getlist('service_prices[]')
        service_descriptions = request.form.getlist('service_descriptions[]')
        
        with get_db() as db:
            # Criar proposta
            proposal = Proposal(
                client_id=int(client_id),
                user_id=session['user_id'],
                payment_terms=payment_terms,
                status=status
            )
            db.add(proposal)
            db.flush()  # Para obter o ID da proposta
            
            # Adicionar itens
            total = 0
            for i, service_id in enumerate(service_ids):
                if service_id:
                    price = float(service_prices[i]) if i < len(service_prices) else 0
                    description = service_descriptions[i] if i < len(service_descriptions) else None
                    
                    item = ProposalItem(
                        proposal_id=proposal.id,
                        service_id=int(service_id),
                        price=price,
                        description=description
                    )
                    db.add(item)
                    total += price
            
            proposal.total_amount = total
            db.commit()
            
            flash(f'Proposta criada com sucesso! Total: GS {total:,.0f}', 'success')
            return redirect(url_for('proposals.view', proposal_id=proposal.id))
    
    with get_db() as db:
        clients_query = db.query(Client).order_by(Client.name).all()
        services_query = db.query(Service).order_by(Service.name).all()
        
        selected_client = None
        if client_id:
            try:
                client_obj = db.query(Client).filter(Client.id == client_id).first()
                if client_obj:
                    selected_client = {'id': client_obj.id, 'name': client_obj.name}
            except:
                pass

        # Serialize to avoid DetachedInstanceError
        clients = [{'id': c.id, 'name': c.name} for c in clients_query]
        services = [{'id': s.id, 'name': s.name, 'base_price': float(s.base_price), 'description': s.description} for s in services_query]
    
    return render_template(
        'proposals/create.html',
        clients=clients,
        services=services,
        selected_client=selected_client
    )


@bp.route('/<int:proposal_id>')
@login_required
def view(proposal_id):
    """Visualizar detalhes da proposta"""
    with get_db() as db:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            flash('Proposta não encontrada.', 'error')
            return redirect(url_for('proposals.index'))
    
        return render_template('proposals/view.html', proposal=proposal)


@bp.route('/<int:proposal_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(proposal_id):
    """Editar proposta"""
    with get_db() as db:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            flash('Proposta não encontrada.', 'error')
            return redirect(url_for('proposals.index'))
        
        if request.method == 'POST':
            proposal.payment_terms = request.form.get('payment_terms')
            proposal.status = request.form.get('status', 'draft')
            
            # Remover itens existentes
            for item in proposal.items:
                db.delete(item)
            
            # Adicionar novos itens
            service_ids = request.form.getlist('service_ids[]')
            service_prices = request.form.getlist('service_prices[]')
            service_descriptions = request.form.getlist('service_descriptions[]')
            
            total = 0
            for i, service_id in enumerate(service_ids):
                if service_id:
                    price = float(service_prices[i]) if i < len(service_prices) else 0
                    description = service_descriptions[i] if i < len(service_descriptions) else None
                    
                    item = ProposalItem(
                        proposal_id=proposal.id,
                        service_id=int(service_id),
                        price=price,
                        description=description
                    )
                    db.add(item)
                    total += price
            
            proposal.total_amount = total
            db.commit()
            
            flash('Proposta atualizada com sucesso!', 'success')
            return redirect(url_for('proposals.view', proposal_id=proposal.id))
        
        services_query = db.query(Service).order_by(Service.name).all()
        # Serialize services
        services = [{'id': s.id, 'name': s.name, 'base_price': float(s.base_price), 'description': s.description} for s in services_query]
    
    return render_template('proposals/edit.html', proposal=proposal, services=services)


@bp.route('/<int:proposal_id>/delete', methods=['POST'])
@login_required
def delete(proposal_id):
    """Deletar proposta"""
    with get_db() as db:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            flash('Proposta não encontrada.', 'error')
            return redirect(url_for('proposals.index'))
        
        client_id = proposal.client_id
        db.delete(proposal)
        db.commit()
        
        flash('Proposta deletada com sucesso.', 'success')
    
    return redirect(url_for('clients.view', client_id=client_id))


@bp.route('/<int:proposal_id>/generate-pdf')
@login_required
def generate_pdf(proposal_id):
    """Gerar PDF da proposta"""
    language = request.args.get('lang', 'es')
    
    with get_db() as db:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            flash('Proposta não encontrada.', 'error')
            return redirect(url_for('proposals.index'))
        
        # Preparar dados para o PDF
        proposal_data = {
            'client_name': proposal.client.name,
            'proposal_date': proposal.created_at,
            'valid_until': proposal.created_at + timedelta(days=30),
            'items': [],
            'total_amount': float(proposal.total_amount),
            'payment_terms': proposal.payment_terms or ''
        }
        
        for item in proposal.items:
            proposal_data['items'].append({
                'name': item.service.name,
                'description': item.description or item.service.description,
                'price': float(item.price)
            })
        
        # Gerar PDF
        pdf_generator = PDFGenerator()
        pdf_path = pdf_generator.generate_proposal_pdf(proposal_data, language=language)
        
        # Salvar caminho no banco
        proposal.pdf_file_path = pdf_path
        db.commit()
        
        # Enviar arquivo para download
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f'propuesta_{proposal.client.name}.pdf'
        )
