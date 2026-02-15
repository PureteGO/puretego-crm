"""
PURETEGO CRM - Proposal Service
Business logic for creating, approving, and managing proposals
"""

from datetime import datetime, timedelta, date
from app.models import (
    Proposal, QuoteOption, QuoteItem, ProposalTemplate, PaymentPlanPreset,
    Client, Service, ServicePackage, Deal, DealStatus, Project, Receivable,
    HealthCheck, KanbanStage, Company
)
from flask_babel import gettext as _


class ProposalService:
    """Serviço centralizado para lógica de negócio de propostas"""
    
    @staticmethod
    def create_proposal(db, company_id, client_id, user_id, template_id=None, deal_id=None,
                        title=None, currency='Gs', language='es', options_data=None, 
                        notes=None, payment_terms=None, valid_days=30):
        """
        Cria uma proposta completa com opções e itens.
        
        Args:
            options_data: list of {
                'name': str, 'is_default': bool, 'preset_id': int|None,
                'items': [{'service_id': int|None, 'package_id': int|None, 
                           'description': str, 'quantity': int, 'unit_price': float,
                           'discount_pct': float, 'billing_type': str, 'tag': str}]
            }
        """
        today = date.today()
        
        proposal = Proposal(
            company_id=company_id,
            client_id=int(client_id),
            user_id=user_id,
            template_id=template_id,
            deal_id=deal_id,
            title=title,
            currency=currency,
            language=language,
            payment_terms=payment_terms,
            status='draft'
        )
        proposal.issue_date = today
        proposal.valid_until = today + timedelta(days=valid_days)
        
        if notes:
            proposal.notes_json = notes if isinstance(notes, dict) else {'notes': notes}
        
        db.add(proposal)
        db.flush()  # Get proposal.id
        
        # Create options and items
        grand_total = 0
        if options_data:
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
        
        return proposal
    
    @staticmethod
    def create_from_package(db, company_id, client_id, user_id, package_id, 
                           template_id=None, language='es'):
        """Cria proposta automaticamente a partir de um pacote de serviços"""
        package = db.query(ServicePackage).get(package_id)
        if not package:
            raise ValueError("Pacote não encontrado")
        
        client = db.query(Client).get(client_id)
        if not client:
            raise ValueError("Cliente não encontrado")
        
        options_data = [{
            'name': f'Opción: {package.name}',
            'is_default': True,
            'items': [{
                'package_id': package.id,
                'description': package.description,
                'quantity': 1,
                'unit_price': float(package.price),
                'billing_type': 'recurring',
                'tag': 'principal'
            }]
        }]
        
        return ProposalService.create_proposal(
            db=db,
            company_id=company_id,
            client_id=client_id,
            user_id=user_id,
            template_id=template_id,
            title=f"Propuesta — {package.name} — {client.name}",
            currency='Gs',
            language=language,
            options_data=options_data
        )

    @staticmethod
    def approve_proposal(db, proposal_id, session_data):
        """
        Aprova uma proposta e dispara workflows:
        1. Atualiza status para 'approved'
        2. Cria/atualiza Deal no Kanban
        3. Cria Projeto
        4. Gera Receivables baseado no plano de pagamento
        """
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise ValueError("Proposta não encontrada")
        
        if proposal.status == 'approved':
            raise ValueError("Proposta já foi aprovada")
        
        company_id = proposal.company_id or session_data.get('company_id')
        
        # 1. Update proposal status
        proposal.status = 'approved'
        
        # 2. Get default option
        default_option = proposal.get_default_option()
        total_amount = float(default_option.total_amount) if default_option else float(proposal.total_amount)
        
        # 3. Handle Deal
        deal = None
        if proposal.deal_id:
            deal = db.query(Deal).get(proposal.deal_id)
        
        if not deal:
            # Find existing open deal for this client
            deal = db.query(Deal).filter(
                Deal.client_id == proposal.client_id,
                Deal.company_id == company_id,
                Deal.status == DealStatus.OPEN
            ).first()
        
        if not deal:
            # Create a new deal
            deal = Deal(
                title=proposal.title or f"Deal — {proposal.client.name}",
                company_id=company_id,
                client_id=proposal.client_id,
                owner_id=proposal.user_id,
                value=total_amount
            )
            db.add(deal)
            db.flush()
            proposal.deal_id = deal.id
        
        # Move deal to "Ganho"
        ganho_stage = db.query(KanbanStage).filter(
            KanbanStage.company_id == company_id,
            KanbanStage.name.like('%Ganho%')
        ).first()
        if ganho_stage:
            deal.kanban_stage_id = ganho_stage.id
            deal.status = DealStatus.WON
            deal.closed_at = datetime.utcnow()
            deal.value = total_amount
            
            # Sync client stage
            if proposal.client:
                proposal.client.kanban_stage_id = ganho_stage.id
                proposal.client.status = 'active_client'
        
        # 4. Create Project
        existing_project = db.query(Project).filter(
            Project.client_id == proposal.client_id,
            Project.company_id == company_id,
            Project.status == 'active'
        ).first()
        
        if not existing_project:
            project = Project(
                client_id=proposal.client_id,
                company_id=company_id,
                name=f"Projeto: {proposal.client.name}",
                status='active',
                phase='financeiro',
                total_amount=total_amount
            )
            project.deal_id = deal.id
            db.add(project)
            db.flush()
            project_id = project.id
        else:
            project_id = existing_project.id
        
        # 5. Create Receivables from payment plan
        receivables = ProposalService._generate_receivables(
            db, company_id, proposal, default_option, deal, project_id
        )
        
        db.commit()
        
        return {
            'proposal': proposal,
            'deal': deal,
            'project_id': project_id,
            'receivables_count': len(receivables)
        }
    
    @staticmethod
    def _generate_receivables(db, company_id, proposal, option, deal, project_id):
        """Gera receivables baseado no preset de pagamento da opção"""
        receivables = []
        total = float(option.total_amount) if option else float(proposal.total_amount)
        
        if total <= 0:
            return receivables
        
        preset = option.preset if option and option.preset_id else None
        
        if preset and preset.installments_config:
            # Generate from preset installments
            for inst in preset.installments_config:
                pct = float(inst.get('pct', 100))
                days = int(inst.get('days_after_sign', 0))
                amount = round(total * (pct / 100), 2)
                
                receivable = Receivable(
                    company_id=company_id,
                    client_id=proposal.client_id,
                    deal_id=deal.id if deal else None,
                    project_id=project_id,
                    description=f"{proposal.title or 'Propuesta'} — {pct}%",
                    amount=amount,
                    due_date=(date.today() + timedelta(days=days)),
                    status='open'
                )
                db.add(receivable)
                receivables.append(receivable)
        else:
            # Single payment (contado)
            receivable = Receivable(
                company_id=company_id,
                client_id=proposal.client_id,
                deal_id=deal.id if deal else None,
                project_id=project_id,
                description=f"{_('Faturamento -')} {proposal.title or proposal.client.name}",
                amount=total,
                due_date=(date.today() + timedelta(days=5)),
                status='open'
            )
            db.add(receivable)
            receivables.append(receivable)
        
        return receivables
    
    @staticmethod
    def calculate_payment_schedule(option, preset=None):
        """
        Calcula a previsão de parcelas para exibição na UI.
        
        Returns:
            list of {'installment': int, 'pct': float, 'amount': float, 'due_date': str}
        """
        total = float(option.total_amount) if option else 0
        if total <= 0:
            return []
        
        if not preset and option:
            preset = option.preset
        
        schedule = []
        today = date.today()
        
        if preset and preset.installments_config:
            for idx, inst in enumerate(preset.installments_config):
                pct = float(inst.get('pct', 100))
                days = int(inst.get('days_after_sign', 0))
                amount = round(total * (pct / 100), 2)
                due = today + timedelta(days=days)
                
                schedule.append({
                    'installment': idx + 1,
                    'pct': pct,
                    'amount': amount,
                    'due_date': due.isoformat()
                })
        else:
            schedule.append({
                'installment': 1,
                'pct': 100,
                'amount': total,
                'due_date': (today + timedelta(days=5)).isoformat()
            })
        
        return schedule
    
    @staticmethod
    def duplicate_proposal(db, proposal_id, user_id):
        """Duplica uma proposta existente (nova cópia em rascunho)"""
        original = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not original:
            raise ValueError("Proposta não encontrada")
        
        new_proposal = Proposal(
            company_id=original.company_id,
            client_id=original.client_id,
            user_id=user_id,
            template_id=original.template_id,
            title=f"{original.title or 'Propuesta'} (Cópia)",
            currency=original.currency,
            language=original.language,
            payment_terms=original.payment_terms,
            status='draft'
        )
        new_proposal.issue_date = date.today()
        new_proposal.valid_until = date.today() + timedelta(days=30)
        new_proposal.notes_json = original.notes_json
        
        db.add(new_proposal)
        db.flush()
        
        # Duplicate options and items
        for opt in original.options:
            new_opt = QuoteOption(
                proposal_id=new_proposal.id,
                name=opt.name,
                is_default=opt.is_default,
                preset_id=opt.preset_id,
                total_amount=opt.total_amount,
                sort_order=opt.sort_order
            )
            db.add(new_opt)
            db.flush()
            
            for item in opt.items:
                new_item = QuoteItem(
                    option_id=new_opt.id,
                    service_id=item.service_id,
                    service_package_id=item.service_package_id,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount_pct=item.discount_pct,
                    total=item.total,
                    billing_type=item.billing_type,
                    tag=item.tag,
                    sort_order=item.sort_order
                )
                db.add(new_item)
        
        new_proposal.total_amount = original.total_amount
        db.commit()
        
        return new_proposal
    
    @staticmethod
    def get_health_check_for_proposal(db, client_id):
        """Busca o último health check do cliente para incluir na proposta"""
        hc = db.query(HealthCheck).filter(
            HealthCheck.client_id == client_id
        ).order_by(HealthCheck.created_at.desc()).first()
        
        return hc.to_dict() if hc else None
