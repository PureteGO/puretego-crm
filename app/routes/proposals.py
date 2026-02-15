"""
PURETEGO CRM - Proposals Routes (v2)
Rotas de gestão de propostas/orçamentos com suporte a templates, opções e planos
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from app.routes.auth import login_required
from app.models import (
    Proposal, ProposalItem, Client, Service, ServicePackage,
    ProposalTemplate, QuoteOption, QuoteItem, PaymentPlanPreset,
    HealthCheck, Deal, Company
)
from app.services import PDFGenerator
from app.services.proposal_service import ProposalService
from config.database import get_db
from datetime import datetime, timedelta, date
import json

bp = Blueprint('proposals', __name__, url_prefix='/proposals')


@bp.route('/')
@login_required
def index():
    """Lista de propostas com filtros"""
    status_filter = request.args.get('status', '')
    client_filter = request.args.get('client_id', '')
    
    with get_db() as db:
        query = db.query(Proposal)
        
        # Multi-tenant filter
        company_id = session.get('company_id')
        if company_id:
            query = query.filter(Proposal.company_id == company_id)
        
        # Status filter
        if status_filter:
            query = query.filter(Proposal.status == status_filter)
        
        # Client filter
        if client_filter:
            query = query.filter(Proposal.client_id == int(client_filter))
        
        proposals_query = query.order_by(Proposal.created_at.desc()).all()
        
        # Serialize to avoid DetachedInstanceError
        proposals = []
        for p in proposals_query:
            default_opt = p.get_default_option()
            proposals.append({
                'id': p.id,
                'title': p.title or f'Propuesta #{p.id}',
                'client_id': p.client_id,
                'client_name': p.client.name if p.client else 'Cliente removido',
                'total_amount': float(p.total_amount or 0),
                'currency': p.currency or 'Gs',
                'status': p.status,
                'language': p.language or 'es',
                'issue_date': p.issue_date,
                'valid_until': p.valid_until,
                'options_count': len(p.options) if p.options else 0,
                'created_at': p.created_at,
                'pdf_file_path': p.pdf_file_path,
                'template_name': p.template.name if p.template else None
            })
        
        # Get clients for filter dropdown
        clients_query = db.query(Client).filter(Client.company_id == company_id).order_by(Client.name).all()
        clients = [{'id': c.id, 'name': c.name} for c in clients_query]
    
    return render_template(
        'proposals/index.html', 
        proposals=proposals, 
        clients=clients,
        status_filter=status_filter,
        client_filter=client_filter
    )


@bp.route('/create', methods=['GET', 'POST'])
@bp.route('/create/<int:client_id>', methods=['GET', 'POST'])
@login_required
def create(client_id=None):
    """Criar nova proposta com wizard"""
    company_id = session.get('company_id')
    
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        template_id = request.form.get('template_id') or None
        deal_id = request.form.get('deal_id') or None
        title = request.form.get('title', '')
        currency = request.form.get('currency', 'Gs')
        language = request.form.get('language', 'es')
        payment_terms = request.form.get('payment_terms', '')
        notes_text = request.form.get('notes', '')
        
        # Parse options from form
        options_data = _parse_options_from_form(request.form)
        
        notes = {'notes': notes_text} if notes_text else None
        
        with get_db() as db:
            try:
                proposal = ProposalService.create_proposal(
                    db=db,
                    company_id=company_id,
                    client_id=client_id,
                    user_id=session['user_id'],
                    template_id=int(template_id) if template_id else None,
                    deal_id=int(deal_id) if deal_id else None,
                    title=title,
                    currency=currency,
                    language=language,
                    options_data=options_data,
                    notes=notes,
                    payment_terms=payment_terms
                )
                flash(f'Proposta criada com sucesso! Total: {currency} {float(proposal.total_amount):,.0f}', 'success')
                return redirect(url_for('proposals.view', proposal_id=proposal.id))
            except Exception as e:
                flash(f'Erro ao criar proposta: {str(e)}', 'error')
    
    with get_db() as db:
        clients_query = db.query(Client).filter(Client.company_id == company_id).order_by(Client.name).all()
        services_query = db.query(Service).order_by(Service.name).all()
        
        selected_client = None
        if client_id:
            try:
                client_obj = db.query(Client).filter(Client.id == client_id).first()
                if client_obj:
                    selected_client = {
                        'id': client_obj.id, 
                        'name': client_obj.name,
                        'interested_package_id': client_obj.interested_package_id
                    }
            except:
                pass

        clients = [{'id': c.id, 'name': c.name} for c in clients_query]
        services = [{'id': s.id, 'name': s.name, 'base_price': float(s.base_price or 0), 'description': s.description or ''} for s in services_query]
        
        # Get service packages
        packages_query = db.query(ServicePackage).order_by(ServicePackage.name).all()
        packages = [{'id': pkg.id, 'name': pkg.name, 'price': float(pkg.price), 'description': pkg.description} for pkg in packages_query]
        
        # Get templates
        templates_query = db.query(ProposalTemplate).filter(
            ProposalTemplate.is_active == True,
            ((ProposalTemplate.company_id == company_id) | (ProposalTemplate.company_id == None))
        ).order_by(ProposalTemplate.name).all()
        templates = [t.to_dict() for t in templates_query]
        
        # Get payment plan presets
        presets_query = db.query(PaymentPlanPreset).filter(
            PaymentPlanPreset.company_id == company_id,
            PaymentPlanPreset.is_active == True
        ).order_by(PaymentPlanPreset.name).all()
        presets = [p.to_dict() for p in presets_query]
        
        # Get open deals for client (if pre-selected)
        deals = []
        if client_id:
            deals_query = db.query(Deal).filter(
                Deal.client_id == client_id,
                Deal.company_id == company_id
            ).all()
            deals = [{'id': d.id, 'title': d.title, 'value': d.value} for d in deals_query]
    
    return render_template(
        'proposals/create.html',
        clients=clients,
        services=services,
        packages=packages,
        templates=templates,
        presets=presets,
        deals=deals,
        selected_client=selected_client
    )


@bp.route('/<int:proposal_id>')
@login_required
def view(proposal_id):
    """Visualizar detalhes da proposta com opções e health check"""
    with get_db() as db:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            flash('Proposta não encontrada.', 'error')
            return redirect(url_for('proposals.index'))
        
        # Serialize proposal data
        proposal_data = proposal.to_dict(include_relations=True)
        proposal_data['client_name'] = proposal.client.name if proposal.client else 'N/A'
        proposal_data['user_name'] = proposal.user.name if proposal.user else 'N/A'
        
        # Get options with items
        options = []
        for opt in proposal.options:
            opt_data = opt.to_dict(include_items=True)
            # Calculate payment schedule preview
            opt_data['payment_schedule'] = ProposalService.calculate_payment_schedule(opt)
            options.append(opt_data)
        
        # If no v2 options, use legacy items
        if not options and proposal.items:
            legacy_items = []
            for item in proposal.items:
                legacy_items.append({
                    'display_name': item.service.name if item.service else 'N/A',
                    'description': item.description,
                    'total': float(item.price) if item.price else 0,
                    'quantity': 1,
                    'unit_price': float(item.price) if item.price else 0,
                    'discount_pct': 0,
                    'billing_type': 'one_time',
                    'tag': 'principal'
                })
            options = [{
                'name': 'Opción Principal (Legacy)',
                'is_default': True,
                'total_amount': float(proposal.total_amount or 0),
                'items': legacy_items,
                'payment_schedule': []
            }]
        
        # Get health check data
        hc = ProposalService.get_health_check_for_proposal(db, proposal.client_id)
        health_check = hc if isinstance(hc, dict) else None
    
    return render_template(
        'proposals/view.html', 
        proposal=proposal_data, 
        options=options,
        health_check=health_check
    )


@bp.route('/<int:proposal_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(proposal_id):
    """Editar proposta existente"""
    company_id = session.get('company_id')
    
    with get_db() as db:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            flash('Proposta não encontrada.', 'error')
            return redirect(url_for('proposals.index'))
        
        if request.method == 'POST':
            proposal.title = request.form.get('title', proposal.title)
            proposal.template_id = request.form.get('template_id') or proposal.template_id
            proposal.currency = request.form.get('currency', 'Gs')
            proposal.language = request.form.get('language', 'es')
            proposal.payment_terms = request.form.get('payment_terms', '')
            proposal.status = request.form.get('status', 'draft')
            
            notes_text = request.form.get('notes', '')
            if notes_text:
                proposal.set_note('notes', notes_text)
            
            # Remove existing options and items
            for opt in proposal.options:
                for item in opt.items:
                    db.delete(item)
                db.delete(opt)
            db.flush()
            
            # Parse and recreate options
            options_data = _parse_options_from_form(request.form)
            
            grand_total = 0
            for idx, opt_data in enumerate(options_data):
                option = QuoteOption(
                    proposal_id=proposal.id,
                    name=opt_data.get('name', f'Opción {chr(65 + idx)}'),
                    is_default=opt_data.get('is_default', idx == 0),
                    preset_id=opt_data.get('preset_id'),
                    sort_order=idx
                )
                db.add(option)
                db.flush()
                
                option_total = 0
                for item_idx, item_data in enumerate(opt_data.get('items', [])):
                    item = QuoteItem(
                        option_id=option.id,
                        service_id=item_data.get('service_id'),
                        service_package_id=item_data.get('package_id'),
                        description=item_data.get('description'),
                        quantity=item_data.get('quantity', 1),
                        unit_price=float(item_data.get('unit_price', 0)),
                        discount_pct=float(item_data.get('discount_pct', 0)),
                        billing_type=item_data.get('billing_type', 'one_time'),
                        tag=item_data.get('tag', 'principal'),
                        sort_order=item_idx
                    )
                    item.calculate_total()
                    db.add(item)
                    option_total += float(item.total)
                
                option.total_amount = option_total
                if option.is_default:
                    grand_total = option_total
            
            proposal.total_amount = grand_total
            db.commit()
            
            flash('Proposta atualizada com sucesso!', 'success')
            return redirect(url_for('proposals.view', proposal_id=proposal.id))
        
        # GET: Prepare form data
        services_query = db.query(Service).order_by(Service.name).all()
        services = [{'id': s.id, 'name': s.name, 'base_price': float(s.base_price), 'description': s.description} for s in services_query]
        
        packages_query = db.query(ServicePackage).order_by(ServicePackage.name).all()
        packages = [{'id': pkg.id, 'name': pkg.name, 'price': float(pkg.price), 'description': pkg.description} for pkg in packages_query]
        
        templates_query = db.query(ProposalTemplate).filter(
            ProposalTemplate.is_active == True,
            ((ProposalTemplate.company_id == company_id) | (ProposalTemplate.company_id == None))
        ).all()
        templates = [t.to_dict() for t in templates_query]
        
        presets_query = db.query(PaymentPlanPreset).filter(
            PaymentPlanPreset.company_id == company_id,
            PaymentPlanPreset.is_active == True
        ).all()
        presets = [p.to_dict() for p in presets_query]
        
        # Serialize proposal with options
        proposal_data = proposal.to_dict(include_relations=True)
        proposal_data['notes_text'] = proposal.get_notes('notes') or ''
        
        options_json = []
        for opt in proposal.options:
            options_json.append(opt.to_dict(include_items=True))
    
    return render_template(
        'proposals/edit.html',
        proposal=proposal_data,
        options_json=json.dumps(options_json),
        services=services,
        packages=packages,
        templates=templates,
        presets=presets
    )


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
    
    return redirect(url_for('proposals.index'))


@bp.route('/<int:proposal_id>/send', methods=['POST'])
@login_required
def send(proposal_id):
    """Marcar proposta como enviada e gerar PDF"""
    with get_db() as db:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            return jsonify({'success': False, 'message': 'Proposta não encontrada'}), 404
        
        proposal.status = 'sent'
        db.commit()
        
        flash('Proposta marcada como enviada!', 'success')
    
    return jsonify({'success': True, 'redirect': url_for('proposals.view', proposal_id=proposal_id)})


@bp.route('/<int:proposal_id>/approve', methods=['POST'])
@login_required
def approve(proposal_id):
    """Aprovar proposta e disparar workflow"""
    with get_db() as db:
        try:
            result = ProposalService.approve_proposal(db, proposal_id, session)
            flash(
                f'Proposta aprovada! Projeto criado e {result["receivables_count"]} fatura(s) gerada(s) automaticamente.',
                'success'
            )
            return jsonify({
                'success': True, 
                'redirect': url_for('proposals.view', proposal_id=proposal_id)
            })
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500


@bp.route('/<int:proposal_id>/reject', methods=['POST'])
@login_required
def reject(proposal_id):
    """Rejeitar proposta"""
    with get_db() as db:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            return jsonify({'success': False, 'message': 'Proposta não encontrada'}), 404
        
        proposal.status = 'rejected'
        db.commit()
        
        flash('Proposta marcada como rejeitada.', 'warning')
    
    return jsonify({'success': True, 'redirect': url_for('proposals.view', proposal_id=proposal_id)})


@bp.route('/<int:proposal_id>/duplicate', methods=['POST'])
@login_required
def duplicate(proposal_id):
    """Duplicar proposta"""
    with get_db() as db:
        try:
            new_proposal = ProposalService.duplicate_proposal(db, proposal_id, session['user_id'])
            flash('Proposta duplicada com sucesso!', 'success')
            return jsonify({
                'success': True, 
                'redirect': url_for('proposals.edit', proposal_id=new_proposal.id)
            })
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400


@bp.route('/<int:proposal_id>/pdf')
@bp.route('/<int:proposal_id>/generate-pdf')
@login_required
def generate_pdf(proposal_id):
    """Gerar PDF da proposta"""
    language = request.args.get('lang', None)
    
    with get_db() as db:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            flash('Proposta não encontrada.', 'error')
            return redirect(url_for('proposals.index'))
        
        lang = language or proposal.language or 'es'
        
        # Get health check data
        health_check = db.query(HealthCheck).filter(
            HealthCheck.client_id == proposal.client_id
        ).order_by(HealthCheck.created_at.desc()).first()
        
        # Get company branding
        company = db.query(Company).get(proposal.company_id) if proposal.company_id else None
        
        # Build v2 options with items
        options_list = []
        default_option = proposal.get_default_option()
        
        if proposal.options:
            for opt in proposal.options:
                opt_items = []
                for item in opt.items:
                    opt_items.append({
                        'display_name': item.get_display_name(),
                        'description': item.description or '',
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price or 0),
                        'discount_pct': float(item.discount_pct or 0),
                        'total': float(item.total or 0),
                        'billing_type': item.billing_type or 'one_time',
                        'tag': item.tag or 'principal'
                    })
                
                options_list.append({
                    'name': opt.name or f'Opción {chr(65 + len(options_list))}',
                    'is_default': opt.is_default,
                    'total_amount': float(opt.total_amount or 0),
                    'items': opt_items
                })
        elif proposal.items:
            # Legacy fallback
            legacy_items = []
            for item in proposal.items:
                legacy_items.append({
                    'display_name': item.service.name if item.service else 'N/A',
                    'description': item.description or (item.service.description if item.service else ''),
                    'quantity': 1,
                    'unit_price': float(item.price or 0),
                    'discount_pct': 0,
                    'total': float(item.price or 0),
                    'billing_type': 'one_time',
                    'tag': 'principal'
                })
            options_list.append({
                'name': 'Opción Principal',
                'is_default': True,
                'total_amount': float(proposal.total_amount or 0),
                'items': legacy_items
            })
        
        # Payment schedule from default option
        schedule = []
        if default_option:
            schedule = ProposalService.calculate_payment_schedule(default_option)
        
        proposal_data = {
            'client_name': proposal.client.name if proposal.client else 'N/A',
            'title': proposal.title,
            'proposal_date': proposal.issue_date or proposal.created_at,
            'valid_until': proposal.valid_until or (proposal.created_at + timedelta(days=30)),
            'total_amount': float(proposal.total_amount or 0),
            'currency': proposal.currency or 'Gs',
            'payment_terms': proposal.payment_terms or '',
            'options': options_list,
            'payment_schedule': schedule,
            'health_check': health_check.to_dict() if health_check else None,
        }
        
        # Generate PDF
        company_data = company.to_dict() if company else {}
        pdf_generator = PDFGenerator()
        pdf_path = pdf_generator.generate_proposal_pdf(proposal_data, language=lang, company=company_data)
        
        # Save path
        proposal.pdf_file_path = pdf_path
        db.commit()
        
        safe_name = "".join(x for x in (proposal.client.name if proposal.client else 'proposta') if x.isalnum() or x in (' ', '_', '-')).replace(' ', '_')
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f'propuesta_{safe_name}.pdf'
        )


@bp.route('/proposals/<int:id>/preview-pdf')
@login_required
def preview_pdf(id):
    """Gera visualização HTML da proposta (sem salvar PDF)"""
    with get_db() as db:
        proposal = db.query(Proposal).get(id)
        if not proposal:
            flash('Proposta não encontrada.', 'error')
            return redirect(url_for('proposals.index'))

        language = request.args.get('lang')
        
        lang = language or proposal.language or 'es'
        
        # Get health check data
        health_check = db.query(HealthCheck).filter(
            HealthCheck.client_id == proposal.client_id
        ).order_by(HealthCheck.created_at.desc()).first()
        
        # Get company branding
        company = db.query(Company).get(proposal.company_id) if proposal.company_id else None
        
        # Build v2 options with items
        options_list = []
        default_option = proposal.get_default_option()
        
        if proposal.options:
            for opt in proposal.options:
                opt_items = []
                for item in opt.items:
                    opt_items.append({
                        'display_name': item.get_display_name(),
                        'description': item.description or '',
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price or 0),
                        'discount_pct': float(item.discount_pct or 0),
                        'total': float(item.total or 0),
                        'billing_type': item.billing_type or 'one_time',
                        'tag': item.tag or 'principal'
                    })
                
                options_list.append({
                    'name': opt.name or f'Opción {chr(65 + len(options_list))}',
                    'is_default': opt.is_default,
                    'total_amount': float(opt.total_amount or 0),
                    'items': opt_items
                })
        elif proposal.items:
            # Legacy fallback
            legacy_items = []
            for item in proposal.items:
                legacy_items.append({
                    'display_name': item.service.name if item.service else 'N/A',
                    'description': item.description or (item.service.description if item.service else ''),
                    'quantity': 1,
                    'unit_price': float(item.price or 0),
                    'discount_pct': 0,
                    'total': float(item.price or 0),
                    'billing_type': 'one_time',
                    'tag': 'principal'
                })
            options_list.append({
                'name': 'Opción Principal',
                'is_default': True,
                'total_amount': float(proposal.total_amount or 0),
                'items': legacy_items
            })
        
        # Payment schedule from default option
        schedule = []
        if default_option:
            schedule = ProposalService.calculate_payment_schedule(default_option)
        
        proposal_data = {
            'client_name': proposal.client.name if proposal.client else 'N/A',
            'title': proposal.title,
            'proposal_date': proposal.issue_date or proposal.created_at,
            'valid_until': proposal.valid_until or (proposal.created_at + timedelta(days=30)),
            'total_amount': float(proposal.total_amount or 0),
            'currency': proposal.currency or 'Gs',
            'payment_terms': proposal.payment_terms or '',
            'options': options_list,
            'payment_schedule': schedule,
            'health_check': health_check.to_dict() if health_check else None,
        }
        
        # Generate HTML Preview
        company_data = company.to_dict() if company else {}
        pdf_generator = PDFGenerator()
        html_content = pdf_generator.preview_html(proposal_data, language=lang, company=company_data)
        
        return html_content


# ============================
# API Endpoints (AJAX)
# ============================

@bp.route('/api/client/<int:client_id>/deals')
@login_required
def api_client_deals(client_id):
    """Retorna deals de um cliente (para seleção dinâmica no form)"""
    company_id = session.get('company_id')
    with get_db() as db:
        deals = db.query(Deal).filter(
            Deal.client_id == client_id,
            Deal.company_id == company_id
        ).all()
        return jsonify([{'id': d.id, 'title': d.title, 'value': d.value} for d in deals])


@bp.route('/api/package/<int:package_id>/details')
@login_required
def api_package_details(package_id):
    """Retorna detalhes de um pacote para preencher itens automaticamente"""
    with get_db() as db:
        pkg = db.query(ServicePackage).get(package_id)
        if not pkg:
            return jsonify({'error': 'Pacote não encontrado'}), 404
        return jsonify({
            'id': pkg.id,
            'name': pkg.name,
            'price': float(pkg.price),
            'description': pkg.description,
            'html_description': pkg.html_description
        })


@bp.route('/api/preset/<int:preset_id>/schedule')
@login_required
def api_preset_schedule(preset_id):
    """Retorna preview de parcelas para um preset"""
    total = request.args.get('total', 0, type=float)
    with get_db() as db:
        preset = db.query(PaymentPlanPreset).get(preset_id)
        if not preset:
            return jsonify({'error': 'Preset não encontrado'}), 404
        
        # Create a mock option for calculation
        class MockOption:
            total_amount = total
            preset = None
        
        mock = MockOption()
        mock.preset = preset
        
        schedule = ProposalService.calculate_payment_schedule(mock, preset)
        return jsonify(schedule)


# ============================
# Helper Functions
# ============================

def _parse_options_from_form(form):
    """
    Parse options and items from HTML form data.
    Expected form structure:
        options[0][name], options[0][is_default], options[0][preset_id]
        options[0][items][0][service_id], options[0][items][0][unit_price], etc.
    """
    options = []
    opt_idx = 0
    
    while True:
        prefix = f'options[{opt_idx}]'
        name = form.get(f'{prefix}[name]')
        
        if name is None:
            # Try alternative flat format
            if opt_idx == 0 and form.getlist('service_ids[]'):
                # Legacy format: flat service list = single option
                return _parse_legacy_form(form)
            break
        
        preset_id = form.get(f'{prefix}[preset_id]')
        is_default = form.get(f'{prefix}[is_default]', '0')
        
        items = []
        item_idx = 0
        while True:
            item_prefix = f'{prefix}[items][{item_idx}]'
            service_id = form.get(f'{item_prefix}[service_id]')
            package_id = form.get(f'{item_prefix}[package_id]')
            
            if service_id is None and package_id is None:
                break
            
            items.append({
                'service_id': int(service_id) if service_id else None,
                'package_id': int(package_id) if package_id else None,
                'description': form.get(f'{item_prefix}[description]', ''),
                'quantity': int(form.get(f'{item_prefix}[quantity]', 1)),
                'unit_price': float(form.get(f'{item_prefix}[unit_price]', 0)),
                'discount_pct': float(form.get(f'{item_prefix}[discount_pct]', 0)),
                'billing_type': form.get(f'{item_prefix}[billing_type]', 'one_time'),
                'tag': form.get(f'{item_prefix}[tag]', 'principal')
            })
            item_idx += 1
        
        options.append({
            'name': name,
            'is_default': is_default in ('1', 'true', 'on'),
            'preset_id': int(preset_id) if preset_id else None,
            'items': items
        })
        opt_idx += 1
    
    return options


def _parse_legacy_form(form):
    """Parse legacy flat form format (backward compat with old create.html)"""
    service_ids = form.getlist('service_ids[]')
    service_prices = form.getlist('service_prices[]')
    service_descriptions = form.getlist('service_descriptions[]')
    
    items = []
    for i, sid in enumerate(service_ids):
        if sid:
            items.append({
                'service_id': int(sid),
                'description': service_descriptions[i] if i < len(service_descriptions) else None,
                'quantity': 1,
                'unit_price': float(service_prices[i]) if i < len(service_prices) else 0,
                'discount_pct': 0,
                'billing_type': 'one_time',
                'tag': 'principal'
            })
    
    return [{
        'name': 'Opción Principal',
        'is_default': True,
        'items': items
    }]
