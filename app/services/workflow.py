"""
PURETEGO CRM - Workflow Service
Gerencia gatilhos automáticos entre etapas do CRM
"""

from datetime import datetime, timedelta
from app.models.task import Task
from app.models.client import Client
from app.models.deal import Deal
from app.models.commission import Commission
from app.models.user import User
from flask_babel import gettext as _

class WorkflowService:
    """Serviço de automação de fluxo de trabalho (Eventos -> Tarefas)"""
    
    @staticmethod
    def on_deal_stage_changed(db, company_id, deal, old_stage_name, new_stage_name):
        """
        Acionado quando um negócio muda de etapa no Kanban.
        Cria tarefas automáticas baseadas na transição e no modo de trabalho da empresa.
        """
        company = db.query(Company).get(company_id)
        if not company: return

        mode = company.workflow_mode or Company.WORKFLOW_LEAN

        # --- GATILHOS POR ETAPA ---

        # 1. Agendamento (SDR -> Sales)
        if new_stage_name == 'Agendado' and old_stage_name != 'Agendado':
            if mode in [Company.WORKFLOW_LEAN, Company.WORKFLOW_STRUCTURED]:
                WorkflowService._create_sales_meeting_task(db, company_id, deal)

        # 2. Proposta Enviada (Apenas Structured)
        if new_stage_name == 'Proposta Enviada' and mode == Company.WORKFLOW_STRUCTURED:
            WorkflowService._create_followup_task(db, company_id, deal)

        # 3. Negócio Ganho (Checklist Completo)
        if new_stage_name and 'Ganho' in new_stage_name:
            WorkflowService._handle_won_deal(db, company, deal)

    @staticmethod
    def _create_followup_task(db, company_id, deal):
        """Cria tarefa de follow-up 48h após envio de proposta"""
        task = Task(
            company_id=company_id,
            title=f"Follow-up: {deal.title}",
            description=f"Proposta enviada para o cliente. Realizar acompanhamento para fechamento.",
            status='open',
            type='sales_followup',
            role_target='sales',
            client_id=deal.client_id,
            deal_id=deal.id,
            due_date=datetime.utcnow() + timedelta(hours=48)
        )
        db.add(task)

    @staticmethod
    def _create_sales_meeting_task(db, company_id, deal):
        """Cria uma tarefa de reunião para o time de vendas"""
        client = db.query(Client).get(deal.client_id)
        client_name = client.name if client else _("Cliente Desconhecido")
        
        task = Task(
            company_id=company_id,
            title=f"{_('Reunião agendada com')} {client_name}",
            description=f"{_('Lead qualificado pelo SDR. Preparar apresentação para o negócio:')} {deal.title}",
            status='open',
            type='sales_meeting',
            role_target='sales',
            client_id=deal.client_id,
            deal_id=deal.id,
            due_date=datetime.utcnow() + timedelta(days=1)
        )
        db.add(task)

    @staticmethod
    def _handle_won_deal(db, company, deal):
        """Lógica de automação após fechar negócio baseada no modo"""
        from app.models import Project, ProjectTicket
        company_id = company.id
        mode = company.workflow_mode or Company.WORKFLOW_LEAN

        client = db.query(Client).get(deal.client_id)
        if not client: return

        # 1. Criar Projeto (Obrigatório em Lean/Structured, opcional mas útil em Solo)
        existing_project = db.query(Project).filter(Project.client_id == client.id, Project.status == 'active').first()
        if not existing_project:
            project = Project(
                client_id=client.id,
                company_id=company_id,
                name=f"Projeto: {client.name}",
                status='active',
                phase='financeiro'
            )
            if hasattr(project, 'deal_id'): project.deal_id = deal.id
            db.add(project)
            db.flush()
            project_id = project.id
        else:
            project_id = existing_project.id

        # 2. Checklist Financeiro (Todos os modos)
        receivable = WorkflowService._handle_financials(db, company_id, deal, project_id)
        
        # 3. Comissões (Structured e Lean)
        if mode in [Company.WORKFLOW_LEAN, Company.WORKFLOW_STRUCTURED]:
            WorkflowService._handle_commissions(db, company, deal, receivable)
        
        # Tarefa Financeira: Solo e Lean têm abordagem simples, Structured é mais rigorosa
        finance_title = _('Faturar Cliente:') if mode != Company.WORKFLOW_STRUCTURED else _('Faturamento e Contrato:')
        finance_task = Task(
            company_id=company_id,
            title=f"{finance_title} {client.name}",
            description=f"{_('Negócio fechado ganho. Emitir contrato e cobrança correspondente.')}",
            status='open',
            type='finance_billing',
            role_target='finance',
            client_id=client.id,
            deal_id=deal.id,
            project_id=project_id,
            due_date=datetime.utcnow() + timedelta(days=1 if mode == Company.WORKFLOW_STRUCTURED else 2)
        )
        db.add(finance_task)

        # 3. Checklist de Produção (Apenas Lean e Structured)
        if mode in [Company.WORKFLOW_LEAN, Company.WORKFLOW_STRUCTURED]:
            # Onboarding/Briefing
            gmb_task = Task(
                company_id=company_id,
                title=f"{_('Onboarding GMB:')} {client.name}",
                description=f"{_('Iniciar processo de configuração GMB.')}",
                status='open',
                type='gmb_onboarding',
                role_target='gmb_manager',
                client_id=client.id,
                deal_id=deal.id,
                project_id=project_id,
                due_date=datetime.utcnow() + timedelta(days=3)
            )
            db.add(gmb_task)
            
            # Tarefa extra para Structured: Briefing de Alinhamento
            if mode == Company.WORKFLOW_STRUCTURED:
                briefing_task = Task(
                    company_id=company_id,
                    title=f"Reunião de Briefing: {client.name}",
                    description="Coletar detalhes técnicos com o cliente para início da produção.",
                    status='open',
                    type='briefing_meeting',
                    role_target='sales', # Closer ou Account Manager
                    client_id=client.id,
                    deal_id=deal.id,
                    project_id=project_id,
                    due_date=datetime.utcnow() + timedelta(days=2)
                )
                db.add(briefing_task)

    @staticmethod
    def _handle_financials(db, company_id, deal, project_id=None):
        """Cria os registros financeiros iniciais para um negócio ganho"""
        from app.models.receivable import Receivable
        
        # 1. Tentar pegar o valor do negócio
        amount = deal.value or 0
        
        if amount == 0:
            from app.models.proposal import Proposal
            proposal = db.query(Proposal).filter(
                Proposal.client_id == deal.client_id, 
                Proposal.status == 'accepted'
            ).order_by(Proposal.created_at.desc()).first()
            if proposal:
                amount = proposal.total_amount
            
        if amount > 0:
            receivable = Receivable(
                company_id=company_id,
                client_id=deal.client_id,
                deal_id=deal.id,
                project_id=project_id,
                description=f"{_('Faturamento Inicial -')} {deal.title}",
                amount=amount,
                due_date=(datetime.utcnow() + timedelta(days=5)).date(),
                status='open'
            )
            db.add(receivable)
            db.flush()
            return receivable
        return None

    @staticmethod
    def _handle_commissions(db, company, deal, receivable=None):
        """Calcula e registra comissões automáticas para um negócio ganho"""
        amount = deal.value or (receivable.amount if receivable else 0)
        if amount <= 0: return

        # Regras de Comissionamento baseadas na Empresa:
        closer_rate = float(company.commission_closer_rate or 10.0) / 100.0
        sdr_rate = float(company.commission_sdr_rate or 2.0) / 100.0
        
        commissions = []
        
        # 1. Closer Commission
        if deal.owner_id:
            closer_user = db.query(User).get(deal.owner_id)
            if closer_user and closer_user.receives_commission:
                closer_amount = float(amount) * closer_rate
                comm = Commission(
                    company_id=company.id,
                    user_id=deal.owner_id,
                    deal_id=deal.id,
                    receivable_id=receivable.id if receivable else None,
                    amount=closer_amount,
                    commission_type='closer'
                )
                commissions.append(comm)
            
        # 2. SDR Commission - Se o dono do cliente for diferente do dono do negócio e for SDR
        if deal.client and deal.client.owner_id and deal.client.owner_id != deal.owner_id:
            sdr_user = db.query(User).get(deal.client.owner_id)
            if sdr_user and sdr_user.receives_commission:
                sdr_amount = float(amount) * sdr_rate
                comm = Commission(
                    company_id=company.id,
                    user_id=deal.client.owner_id,
                    deal_id=deal.id,
                    receivable_id=receivable.id if receivable else None,
                    amount=sdr_amount,
                    commission_type='opener'
                )
                commissions.append(comm)
            
        for c in commissions:
            db.add(c)
