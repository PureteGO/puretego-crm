"""
PURETEGO CRM - Dashboard Routes
Rotas do dashboard principal
"""

from flask import Blueprint, render_template, session
from app.routes.auth import login_required
from app.models import Client, Visit, Proposal, HealthCheck, KanbanStage
from config.database import get_db
from sqlalchemy import func

bp = Blueprint('dashboard', __name__, url_prefix='/')


@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    """Dashboard principal com visão geral"""
    try:
        with get_db() as db:
            from sqlalchemy.orm import joinedload
            # Estatísticas gerais
            total_clients = db.query(func.count(Client.id)).scalar()
            total_visits = db.query(func.count(Visit.id)).scalar()
            total_proposals = db.query(func.count(Proposal.id)).scalar()
            total_health_checks = db.query(func.count(HealthCheck.id)).scalar()
            
            # Propostas por status
            proposals_by_status = db.query(
                Proposal.status,
                func.count(Proposal.id)
            ).group_by(Proposal.status).all()
            
            # Clientes por etapa do Kanban
            clients_by_stage = db.query(
                KanbanStage.name,
                func.count(Client.id)
            ).join(Client, Client.kanban_stage_id == KanbanStage.id, isouter=True)\
             .group_by(KanbanStage.id, KanbanStage.name)\
             .order_by(KanbanStage.order).all()
            
            # Últimas visitas
            recent_visits = db.query(Visit).options(joinedload(Visit.client))\
                .order_by(Visit.visit_date.desc())\
                .limit(5)\
                .all()
            
            # Últimos health checks
            recent_health_checks = db.query(HealthCheck).options(joinedload(HealthCheck.client))\
                .order_by(HealthCheck.created_at.desc())\
                .limit(5)\
                .all()
        
            return render_template(
                'dashboard/index.html',
                total_clients=total_clients,
                total_visits=total_visits,
                total_proposals=total_proposals,
                total_health_checks=total_health_checks,
                proposals_by_status=dict(proposals_by_status),
                clients_by_stage=clients_by_stage,
                recent_visits=recent_visits,
                recent_health_checks=recent_health_checks
            )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"DEBUG ERROR DASHBOARD: {error_details}")
        return f"<h1>Erro de Depuração Dashboard</h1><pre>{error_details}</pre>", 500
