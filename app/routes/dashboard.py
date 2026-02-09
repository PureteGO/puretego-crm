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
            
            # Won amount = total sum of accepted proposals this month
            first_day_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            data['won_amount'] = filter_by_company(db.query(func.sum(Proposal.total_amount)).join(Client), Client).filter(
                Proposal.status == 'accepted',
                Proposal.updated_at >= first_day_month
            ).scalar() or 0
            
            # Count accepted proposals
            won_proposals_count = filter_by_company(db.query(func.count(Proposal.id)).join(Client), Client).filter(Proposal.status == 'accepted').scalar() or 0
            data['avg_ticket'] = (float(data['won_amount']) / won_proposals_count) if won_proposals_count > 0 else 0
            
            # Sales Performance Chart (Accepted Proposals by Month - Last 6 months)
            six_months_ago = datetime.now() - timedelta(days=180)
            sales_performance = filter_by_company(
                db.query(
                    func.date_format(Proposal.created_at, '%Y-%m').label('month'),
                    func.sum(Proposal.total_amount).label('total')
                ).join(Client), Client
            ).filter(Proposal.status == 'accepted', Proposal.created_at >= six_months_ago)\
             .group_by('month').order_by('month').all()
            
            data['sales_performance'] = [{'month': s.month, 'total': float(s.total or 0)} for s in sales_performance]
            
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
        data['recent_visits'] = filter_by_company(
            db.query(Visit).join(Client).options(joinedload(Visit.client)), Client
        ).order_by(Visit.visit_date.desc()).limit(5).all()
        
        data['recent_health_checks'] = filter_by_company(
            db.query(HealthCheck).join(Client).options(joinedload(HealthCheck.client)), Client
        ).order_by(HealthCheck.created_at.desc()).limit(5).all()
        
        data['recent_interactions'] = filter_by_company(
            db.query(Interaction).join(Client).options(joinedload(Interaction.client), joinedload(Interaction.type)), Client
        ).filter(Interaction.status == 'done').order_by(Interaction.date.desc()).limit(5).all()

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

