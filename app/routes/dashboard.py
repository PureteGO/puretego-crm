from flask import Blueprint, render_template, session
from app.routes.auth import login_required
from app.models import Client, Visit, Proposal, HealthCheck, KanbanStage, Interaction, Project, ProjectTicket, Deal, Receivable, Company, User
from app.utils.tenant import filter_by_company
from config.database import get_db
from sqlalchemy import func, or_, extract
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from app.models.task import Task

bp = Blueprint('dashboard', __name__, url_prefix='/')


@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    """Dashboard principal com visão geral - filtrado por empresa e função"""
    try:
        # Use session.get('role') consistent with auth.py
        user_role = session.get('role') or 'sales'
        user_id = session.get('user_id')
        is_superadmin = session.get('is_superadmin', False)
        
        with get_db() as db:
            # --- Shared Data ---
            total_clients = filter_by_company(db.query(func.count(Client.id)), Client).scalar() or 0
            
        # --- Metrics Initialization (Avoids 500 errors for roles with less data) ---
        data = {
            'role': user_role,
            'total_clients': total_clients,
            'is_superadmin': is_superadmin,
            'new_leads_7d': 0,
            'new_leads_15d': 0,
            'won_amount': 0.0,
            'monthly_revenue': 0.0,
            'avg_ticket': 0.0,
            'total_wins': 0,
            'total_pipeline_value': 0.0,
            'total_proposals': 0,
            'awaiting_payment': 0,
            'pending_contracts': 0,
            'expiring_projects': [],
            'clients_by_stage': [],
            'win_rate': 0,
            'sales_performance': [],
            'recent_leads': [],
            'recent_interactions': [],
            'recent_visits': [],
            'recent_health_checks': [],
            'overdue_count': 0,
            'overdue_items': [],
            'onboarding_guide': None,
            'onboarding_percent': 0,
            'onboarding_count': 0,
            'execution_count': 0,
            'pending_tickets': [],
            'my_clients_count': 0,
            'critical_leads_count': 0,
            'leads_pending_followup': [],
            'month_name': datetime.now().strftime('%B')
        }

        with get_db() as db:
            # --- Common Calculations for Owners/Admins/Finance ---
            if user_role in ['owner', 'admin', 'manager', 'superadmin', 'finance'] or is_superadmin:
                # Timeframes
                seven_days_ago = datetime.utcnow() - timedelta(days=7)
                fifteen_days_ago = datetime.utcnow() - timedelta(days=15)
                first_day_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                # Lead Velocity
                # Count clients created/entered funnel in last 7/15 days
                # Use funnel_start_date if available, else created_at
                data['new_leads_7d'] = filter_by_company(db.query(func.count(Client.id)), Client).filter(
                    func.coalesce(Client.funnel_start_date, Client.created_at) >= seven_days_ago
                ).scalar() or 0
                
                data['new_leads_15d'] = filter_by_company(db.query(func.count(Client.id)), Client).filter(
                    func.coalesce(Client.funnel_start_date, Client.created_at) >= fifteen_days_ago
                ).scalar() or 0

                # Finance/Sales data (Shared by Owner, Admin, Manager, Superadmin, Finance)
                data['total_proposals'] = filter_by_company(db.query(func.count(Proposal.id)).join(Client), Client).scalar() or 0

                if user_role == 'finance' or is_superadmin: # Finance specific metrics
                    data['awaiting_payment'] = filter_by_company(db.query(func.sum(Receivable.amount)), Receivable).filter(Receivable.status == 'open').scalar() or 0
                    data['pending_contracts'] = filter_by_company(db.query(func.count(Project.id)), Project).filter(Project.contract_file_path.is_(None)).scalar() or 0

                # Renewal Alerts (Expiring in 30 days)
                thirty_days_ahead = (datetime.now() + timedelta(days=30)).date()
                data['expiring_projects'] = filter_by_company(db.query(Project).options(joinedload(Project.client)), Project)\
                    .filter(Project.end_date.isnot(None), Project.end_date <= thirty_days_ahead, Project.status == 'active').all()
                
                # Aggregate Pipeline
                pipeline_query = filter_by_company(
                    db.query(KanbanStage.name, func.count(Client.id))\
                    .join(Client, (Client.kanban_stage_id == KanbanStage.id) & (Client.is_active == True), isouter=True), Client
                ).group_by(KanbanStage.id, KanbanStage.name).order_by(KanbanStage.order).all()
                
                # Defensive mapping to ensure labels are strings and data is consistent for JS charts
                from flask_babel import _
                data['clients_by_stage'] = [
                    {'name': str(name or _('Unknown')), 'count': int(count or 0)} 
                    for name, count in pipeline_query
                ]
                
                # Executive Metrics
                won_stage_name = 'Fechado - Ganho'
                lost_stage_name = 'Fechado - Perdido'
                
                total_active_leads = sum(count for name, count in pipeline_query if name != lost_stage_name)
                won_leads = next((count for name, count in pipeline_query if name == won_stage_name), 0)
                
                data['win_rate'] = (won_leads / total_active_leads * 100) if total_active_leads > 0 else 0
                
                # Proposals value
                data['total_pipeline_value'] = filter_by_company(db.query(func.sum(Proposal.total_amount)).join(Client), Client).filter(Proposal.status != 'rejected').scalar() or 0
                
                # Closed Sales (Monthly)
                projects_val = filter_by_company(db.query(func.sum(func.coalesce(Project.total_amount, 0))), Project).filter(
                    Project.status != 'cancelled', Project.created_at >= first_day_month
                ).scalar() or 0
                
                deals_val = filter_by_company(db.query(func.sum(Deal.value)), Deal).filter(
                    Deal.status == 'won', Deal.updated_at >= first_day_month,
                    ~Deal.id.in_(db.query(Project.deal_id).filter(Project.deal_id.isnot(None)))
                ).scalar() or 0
                
                data['won_amount'] = float(projects_val) + float(deals_val)
                
                # Monthly Revenue (Receivables)
                monthly_rev = filter_by_company(db.query(func.sum(Receivable.amount)), Receivable).filter(
                    extract('month', Receivable.due_date) == datetime.now().month,
                    extract('year', Receivable.due_date) == datetime.now().year,
                    Receivable.status != 'cancelled'
                ).scalar() or 0
                data['monthly_revenue'] = float(monthly_rev)

                # Avg Ticket calculations
                proj_count = filter_by_company(db.query(func.count(Project.id)), Project).filter(
                    Project.created_at >= first_day_month, Project.status != 'cancelled'
                ).scalar() or 0
                
                deal_count = filter_by_company(db.query(func.count(Deal.id)), Deal).filter(
                    Deal.status == 'won', Deal.updated_at >= first_day_month,
                    ~Deal.id.in_(db.query(Project.deal_id).filter(Project.deal_id.isnot(None)))
                ).scalar() or 0
                
                total_wins = proj_count + deal_count
                data['total_wins'] = total_wins
                data['avg_ticket'] = (data['won_amount'] / total_wins) if total_wins > 0 else 0
                
                # Performance History Chart (Last 6 months)
                six_months_ago = datetime.now() - timedelta(days=180)
                
                # Using specific column expressions for group_by to satisfy strict SQL modes and dialects
                month_expr_proj = func.date_format(Project.created_at, '%Y-%m')
                proj_sales = filter_by_company(db.query(
                    month_expr_proj.label('month'),
                    func.sum(func.coalesce(Project.total_amount, 0)).label('total')
                ), Project).filter(Project.created_at >= six_months_ago, Project.status != 'cancelled')\
                 .group_by(month_expr_proj).all()

                # Deals history (not linked to projects)
                month_expr_deal = func.date_format(Deal.updated_at, '%Y-%m')
                deal_sales = filter_by_company(
                    db.query(
                        month_expr_deal.label('month'),
                        func.sum(Deal.value).label('total')
                    ), Deal
                ).filter(Deal.status == 'won', Deal.updated_at >= six_months_ago, 
                         ~Deal.id.in_(db.query(Project.deal_id).filter(Project.deal_id.isnot(None))))\
                 .group_by(month_expr_deal).all()

                # Combine and sort months
                performance_map = {}
                for s in proj_sales:
                    m = s.month
                    if m:
                        performance_map[m] = performance_map.get(m, 0) + float(s.total or 0)
                
                for s in deal_sales:
                    m = s.month
                    if m:
                        performance_map[m] = performance_map.get(m, 0) + float(s.total or 0)
                
                # Sort by month key (filter out None just in case)
                sorted_months = sorted([item for item in performance_map.items() if item[0] is not None])
                
                data['sales_performance'] = [
                    {'month': m, 'total': t} for m, t in sorted_months
                ]
               
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
                pipeline_query = filter_by_company(
                    db.query(KanbanStage.name, func.count(Client.id))\
                    .join(Client, (Client.kanban_stage_id == KanbanStage.id) & (Client.is_active == True), isouter=True), Client
                ).filter(Client.owner_id == user_id).group_by(KanbanStage.id, KanbanStage.name).order_by(KanbanStage.order).all()

                from flask_babel import _
                data['clients_by_stage'] = [
                    {'name': str(name or _('Unknown')), 'count': int(count or 0)} 
                    for name, count in pipeline_query
                ]

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
                Task.status.in_(['open', 'in_progress']),
                Task.due_date < datetime.now(),
                or_(Task.assigned_to_id == user_id, (Task.assigned_to_id.is_(None)) & (Task.role_target == user_role))
            ).all()
            
            for t in overdue_tasks:
                overdue_items.append({
                    'type': 'task',
                    'id': t.id,
                    'title': t.title,
                    'date': t.due_date,
                    'url': '/tasks/'
                })
                
            # Sort by date (oldest first)
            # Filter out items with None dates to avoid TypeError during sorting
            overdue_items_to_sort = [x for x in overdue_items if x.get('date') is not None]
            overdue_items_to_sort.sort(key=lambda x: x['date'])
            
            data['overdue_items'] = overdue_items_to_sort
            data['overdue_count'] = len(overdue_items_to_sort)

            # Dropdown data for New Task modal
            clients = filter_by_company(db.query(Client).order_by(Client.name), Client).all()
            projects = filter_by_company(
                db.query(Project).options(joinedload(Project.client)).filter(Project.status == 'active').order_by(Project.name), 
                Project
            ).all()
            
            data['clients_data'] = [{'id': c.id, 'name': c.name} for c in clients]
            data['projects_data'] = [
                {
                    'id': p.id, 
                    'name': p.name, 
                    'client_name': p.client.name if p.client else None
                } for p in projects
            ]

            return render_template('dashboard/index.html', **data)
    except Exception as e:
        import logging
        logging.exception("Error in dashboard route")
        return f"<h1>Internal Server Error (Dashboard)</h1><p>Ocorreu um erro ao processar os dados do dashboard. Por favor, tente novamente mais tarde ou contate o suporte.</p><p><small>{str(e)}</small></p>", 500

