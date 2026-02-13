from flask import Blueprint, render_template, session
from app.routes.auth import login_required
from app.models import Client, Visit, Proposal, HealthCheck, KanbanStage, Interaction, Project, ProjectTicket, Deal, Receivable, Company, User
from app.utils.tenant import filter_by_company
from config.database import get_db
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from app.models.task import Task

bp = Blueprint('dashboard', __name__, url_prefix='/')


@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    """Dashboard principal com visão geral - filtrado por empresa e função"""
    # Use session.get('role') consistent with auth.py
    user_role = session.get('role') or 'sales'
    user_id = session.get('user_id')
    is_superadmin = session.get('is_superadmin', False)
    
    with get_db() as db:
        # --- Shared Data ---
        total_clients = filter_by_company(db.query(func.count(Client.id)), Client).scalar() or 0
        
        # --- Role-Based context ---
        data = {
            'role': user_role,
            'total_clients': total_clients,
            'is_superadmin': is_superadmin
        }
        
        # Expanded view for Owners, Managers, Finance or Superadmins
        if user_role in ['owner', 'admin', 'manager', 'finance'] or is_superadmin:
            # Admin/Finance View
            data['total_proposals'] = filter_by_company(db.query(func.count(Proposal.id)).join(Client), Client).scalar() or 0
            
            # --- New Leads Metrics (v1.5) ---
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            fifteen_days_ago = datetime.utcnow() - timedelta(days=15)
            
            # Count clients created/entered funnel in last 7/15 days
            # Use funnel_start_date if available, else created_at
            data['new_leads_7d'] = filter_by_company(db.query(func.count(Client.id)), Client).filter(
                func.coalesce(Client.funnel_start_date, Client.created_at) >= seven_days_ago
            ).scalar() or 0
            
            data['new_leads_15d'] = filter_by_company(db.query(func.count(Client.id)), Client).filter(
                func.coalesce(Client.funnel_start_date, Client.created_at) >= fifteen_days_ago
            ).scalar() or 0

            # REAL FINANCIAL METRICS (Receivable Model)
            data['awaiting_payment'] = filter_by_company(db.query(func.sum(Receivable.amount)), Receivable).filter(Receivable.status == 'open').scalar() or 0
            data['pending_contracts'] = filter_by_company(db.query(func.count(Project.id)), Project).filter(Project.contract_file_path == None).scalar() or 0
            
            # Renewal Alerts (Expiring in 30 days)
            thirty_days_ahead = (datetime.now() + timedelta(days=30)).date()
            data['expiring_projects'] = filter_by_company(db.query(Project).options(joinedload(Project.client)), Project)\
                .filter(Project.end_date != None, Project.end_date <= thirty_days_ahead, Project.status == 'active').all()
            
            # Aggregate Pipeline
            pipeline_query = filter_by_company(
                db.query(KanbanStage.name, func.count(Client.id))\
                .join(Client, Client.kanban_stage_id == KanbanStage.id, isouter=True), Client
            ).group_by(KanbanStage.id, KanbanStage.name).order_by(KanbanStage.order).all()
            
            data['clients_by_stage'] = pipeline_query
            
            # Executive Metrics
            won_stage_name = 'Fechado - Ganho'
            lost_stage_name = 'Fechado - Perdido'
            
            total_active_leads = sum(count for name, count in pipeline_query if name != lost_stage_name)
            won_leads = next((count for name, count in pipeline_query if name == won_stage_name), 0)
            
            data['win_rate'] = (won_leads / total_active_leads * 100) if total_active_leads > 0 else 0
            
            # Proposal Values
            proposals_value_query = filter_by_company(db.query(func.sum(Proposal.total_amount)).join(Client), Client)
            data['total_pipeline_value'] = proposals_value_query.filter(Proposal.status != 'rejected').scalar() or 0
            
            # Unified Sales Metrics (v1.6) - Corrected for Finance/Project integration
            first_day_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # 1. Sum Won Values from Projects (Current month)
            # Use total_amount (fixed) + monthly_value (recurring)
            # 1. Sum Won Values from Projects (Current month)
            # Use total_amount (fixed) + monthly_value (recurring)
            projects_val = filter_by_company(db.query(
                func.sum(func.coalesce(Project.total_amount, 0) + func.coalesce(Project.monthly_value, 0))
            ), Project).filter(
                Project.status != 'cancelled',
                Project.created_at >= first_day_month
            ).scalar() or 0
            
            # 2. Sum Won Values from Deals that DON'T have a Project yet
            # Avoid double counting by checking for unlinked deals
            deals_val = filter_by_company(db.query(func.sum(Deal.value)), Deal).filter(
                Deal.status == 'won',
                Deal.updated_at >= first_day_month,
                ~Deal.id.in_(db.query(Project.deal_id).filter(Project.deal_id != None))
            ).scalar() or 0
            
            data['won_amount'] = float(projects_val) + float(deals_val)
            
            # 3. Won Count (Total unique sales)
            proj_count = filter_by_company(db.query(func.count(Project.id)), Project).filter(
                Project.created_at >= first_day_month,
                Project.status != 'cancelled'
            ).scalar() or 0
            
            deal_count = filter_by_company(db.query(func.count(Deal.id)), Deal).filter(
                Deal.status == 'won',
                Deal.updated_at >= first_day_month,
                Deal.value > 0, # Only count if it adds value or has no project yet
                ~Deal.id.in_(db.query(Project.deal_id).filter(Project.deal_id != None))
            ).scalar() or 0
            
            total_wins = proj_count + deal_count
            data['avg_ticket'] = (float(data['won_amount']) / total_wins) if total_wins > 0 else 0
            
            # 4. Unified Sales Performance Chart (Last 6 months)
            six_months_ago = datetime.now() - timedelta(days=180)
            
            # Projects history
            proj_sales = filter_by_company(
                db.query(
                    func.date_format(Project.created_at, '%Y-%m').label('month'),
                    func.sum(func.coalesce(Project.total_amount, 0) + func.coalesce(Project.monthly_value, 0)).label('total')
                ), Project
            ).filter(Project.created_at >= six_months_ago, Project.status != 'cancelled')\
             .group_by('month').all()

            # Deals history (not linked to projects)
            deal_sales = filter_by_company(
                db.query(
                    func.date_format(Deal.updated_at, '%Y-%m').label('month'),
                    func.sum(Deal.value).label('total')
                ), Deal
            ).filter(Deal.status == 'won', Deal.updated_at >= six_months_ago, 
                     ~Deal.id.in_(db.query(Project.deal_id).filter(Project.deal_id != None)))\
             .group_by('month').all()

            # Combine and sort months
            performance_map = {}
            for s in proj_sales:
                performance_map[s.month] = float(s.total or 0)
            for s in deal_sales:
                performance_map[s.month] = performance_map.get(s.month, 0) + float(s.total or 0)
            
            data['sales_performance'] = [{'month': m, 'total': t} for m, t in sorted(performance_map.items())]
           
        elif user_role in ['gmb_manager', 'traffic', 'creative']:
            # Production/Ops View
            data['onboarding_count'] = filter_by_company(db.query(func.count(Project.id)), Project).filter(Project.phase == 'onboarding').scalar() or 0
            data['execution_count'] = filter_by_company(db.query(func.count(Project.id)), Project).filter(Project.phase == 'execucao').scalar() or 0
            
            # Pending operational tickets
            data['pending_tickets'] = filter_by_company(db.query(ProjectTicket).join(Project), Project)\
                .filter(ProjectTicket.status != 'done').options(joinedload(ProjectTicket.project)).limit(10).all()
        
        else:
            # Sales (SDR/Seller) View
            # Personal stats
            client_query = db.query(Client).filter(Client.owner_id == user_id)
            data['my_clients_count'] = filter_by_company(client_query, Client).count()
            
            data['total_visits'] = filter_by_company(db.query(func.count(Visit.id)).join(Client), Client).filter(Client.owner_id == user_id).scalar() or 0
            
            # Additional metrics for Sales/SDR dashboards
            data['total_proposals'] = filter_by_company(db.query(func.count(Proposal.id)).join(Client), Client).filter(Client.owner_id == user_id).scalar() or 0
            data['total_pipeline_value'] = filter_by_company(db.query(func.sum(Proposal.total_amount)).join(Client), Client).filter(Client.owner_id == user_id, Proposal.status != 'rejected').scalar() or 0
            
            # Shared: Activity history (already done below in shared section)
            
            # Personal Pipeline
            data['clients_by_stage'] = filter_by_company(
                db.query(KanbanStage.name, func.count(Client.id))\
                .join(Client, Client.kanban_stage_id == KanbanStage.id, isouter=True), Client
            ).filter(Client.owner_id == user_id).group_by(KanbanStage.id, KanbanStage.name).order_by(KanbanStage.order).all()

        # Shared: Activity history
        data['recent_leads'] = filter_by_company(
            db.query(Client).order_by(Client.created_at.desc()).limit(10), Client
        ).all()

        data['recent_visits'] = filter_by_company(
            db.query(Visit).join(Client).options(joinedload(Visit.client)), Client
        ).order_by(Visit.visit_date.desc()).limit(5).all()
        
        data['recent_health_checks'] = filter_by_company(
            db.query(HealthCheck).join(Client).options(joinedload(HealthCheck.client)), Client
        ).order_by(HealthCheck.created_at.desc()).limit(5).all()
        
        data['recent_interactions'] = filter_by_company(
            db.query(Interaction).join(Client).options(joinedload(Interaction.client), joinedload(Interaction.type)), Client
        ).filter(Interaction.status == 'done', Interaction.date <= datetime.now()).order_by(Interaction.date.desc()).limit(5).all()

        # --- Lead Follow-up Rule (v1.6) ---
        # "não permita leads que nao tenham seguimento no processo de vendas passar para o outro dia sem ter indicado o próximo passo"
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Clients with interactions done today
        clients_treated_today_sub = db.query(Interaction.client_id).filter(
            Interaction.status == 'done',
            Interaction.date >= today_start
        ).distinct().subquery()
        
        # 2. Clients with future interactions scheduled
        clients_with_future_sub = db.query(Interaction.client_id).filter(
            Interaction.status == 'scheduled',
            Interaction.date > datetime.now()
        ).distinct().subquery()
        
        # 3. Find clients in (1) but NOT in (2)
        data['leads_pending_followup'] = filter_by_company(db.query(Client), Client).filter(
            Client.id.in_(clients_treated_today_sub),
            ~Client.id.in_(clients_with_future_sub)
        ).all()

        # --- Additional Metrics for Deploy v1 ---
        
        # 1. Critical Leads (>48h without contact) for SDR/Sales
        if user_role in ['sdr', 'sales']:
            forty_eight_hours_ago = datetime.utcnow() - timedelta(hours=48)
            # Find clients owned by user where last interaction was >48h ago OR no interaction exists
            # (Simplification: using Client.id for subquery to avoid complex joins in filter_by_company)
            critical_leads_query = filter_by_company(db.query(Client.id), Client).filter(Client.owner_id == user_id)
            
            # Subquery for clients with recent interactions
            recent_interaction_subquery = db.query(Interaction.client_id).filter(
                Interaction.date >= forty_eight_hours_ago
            ).subquery()
            
            data['critical_leads_count'] = critical_leads_query.filter(
                ~Client.id.in_(recent_interaction_subquery)
            ).count()

        # 2. Owner Onboarding Checklist (First Steps)
        if user_role in ['owner', 'admin'] or is_superadmin:
            company = db.query(Company).get(session.get('company_id'))
            if company:
                data['onboarding_guide'] = {
                    'branding_ok': bool(company.logo_url),
                    'smtp_ok': company.has_smtp_configured(),
                    'users_added': db.query(func.count(User.id)).filter(User.company_id == company.id).scalar() > 1,
                    'clients_added': total_clients > 0
                }
                # Total progress
                steps = [data['onboarding_guide']['branding_ok'], data['onboarding_guide']['smtp_ok'], 
                         data['onboarding_guide']['users_added'], data['onboarding_guide']['clients_added']]
                data['onboarding_percent'] = int((sum(steps) / len(steps)) * 100)
    
        # --- Overdue Items for Modal ---
        overdue_items = []
        
        # 1. Overdue Interactions
        overdue_interactions = db.query(Interaction).options(joinedload(Interaction.client), joinedload(Interaction.type)).filter(
            Interaction.user_id == user_id,
            Interaction.status == 'scheduled',
            Interaction.date < datetime.now()
        ).all()
        
        for i in overdue_interactions:
            overdue_items.append({
                'type': 'interaction',
                'id': i.id,
                'title': f"{i.type.name} - {i.client.name}",
                'date': i.date,
                'url': f"/clients/{i.client_id}"  # Direct link to client
            })
            
        # 2. Overdue Tasks
        overdue_tasks = filter_by_company(db.query(Task), Task).filter(
            Task.status == 'pending',
            Task.due_date < datetime.now(),
            or_(Task.user_id == user_id, (Task.user_id == None) & (Task.role_target == user_role))
        ).all()
        
        for t in overdue_tasks:
            overdue_items.append({
                'type': 'task',
                'id': t.id,
                'title': t.title,
                'date': t.due_date,
                'url': '#' # Tasks might need a specific view, for now just show them
            })
            
        # Sort by date (oldest first)
        overdue_items.sort(key=lambda x: x['date'])
        data['overdue_items'] = overdue_items

        return render_template('dashboard/index.html', **data)

