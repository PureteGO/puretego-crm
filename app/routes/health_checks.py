import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.routes.auth import login_required
from app.models import HealthCheck, Client
from app.services import SerpApiService
from config.database import get_db
from app.services.health_check_service import HealthCheckService
import json

logger = logging.getLogger(__name__)

bp = Blueprint('health_checks', __name__, url_prefix='/health-checks')

@bp.route('/quick-check', methods=['POST'])
@login_required
def quick_check():
    data = request.get_json()
    business_name = data.get('business_name')
    if not business_name:
        return jsonify({'success': False, 'message': 'Nome obrigatório'}), 400
    
    try:
        # Usar HealthCheckService (sem salvar no banco ainda)
        result = HealthCheckService.perform_public_audit(None, business_name)
        
        if not result['success']:
            return jsonify({'success': False, 'message': result.get('error')}), 404
            
        return jsonify({
            'success': True,
            'score': result['score'],
            'report': result['report']
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'Erro ao processar busca.'}), 500

@bp.route('/')
@login_required
def index():
    with get_db() as db:
        health_checks = db.query(HealthCheck).order_by(HealthCheck.created_at.desc()).all()
        return render_template('health_checks/index.html', health_checks=health_checks)

@bp.route('/official/<int:client_id>', methods=['POST'])
@login_required
def official_check(client_id):
    """Trigger an official health check audit for a linked client."""
    try:
        location_link_id = request.form.get('location_link_id') or request.json.get('location_link_id') if request.is_json else None
        if location_link_id:
            location_link_id = int(location_link_id)
            
        result = HealthCheckService.perform_official_audit(client_id, location_link_id)
        if result['success']:
            flash(_('Auditoria Oficial realizada com sucesso!'), 'success')
            return redirect(url_for('health_checks.view', health_check_id=result['check_id']))
        else:
            flash(_('Erro: %(error)s', error=result.get('error', 'Erro desconhecido')), 'error')
            return redirect(url_for('clients.view', client_id=client_id))
    except Exception as e:
        flash(_('Erro interno ao processar auditoria oficial.'), 'error')
        return redirect(url_for('clients.view', client_id=client_id))


# Health Check Routes

@bp.route('/create/<int:client_id>', methods=['GET', 'POST'])
@login_required
def create(client_id):
    """Criar novo health check para um cliente"""
    with get_db() as db:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            flash('Cliente não encontrado.', 'error')
            return redirect(url_for('clients.index'))
        
        if request.method == 'POST':
            # Se for auditoria pública (manual)
            primary_link = client.get_primary_gmb_link()
            query = request.form.get('business_name') or (primary_link.gmb_location_title if primary_link else None) or client.gmb_profile_name or client.name
            location = request.form.get('location') or (primary_link.gmb_location_address if primary_link else None) or client.address
            
            try:
                # Usar serviço de Health Check (Public Audit)
                result = HealthCheckService.perform_public_audit(client.id, query, location=location)
                
                if result['success']:
                    flash('Health Check realizado com sucesso!', 'success')
                    return redirect(url_for('health_checks.view', health_check_id=result['check_id']))
                else:
                    flash(f"Erro: {result.get('error')}", 'error')
                    
            except Exception as e:
                db.rollback()
                flash(f'Erro ao realizar Health Check: {str(e)}', 'error')
                return render_template('health_checks/create.html', client=client)
                
        return render_template('health_checks/create.html', client=client)

@bp.route('/<int:health_check_id>')
@login_required
def view(health_check_id):
    """Visualizar detalhes do relatório"""
    try:
        with get_db() as db:
            from sqlalchemy.orm import joinedload
            health_check = db.query(HealthCheck).options(joinedload(HealthCheck.client))\
                .filter(HealthCheck.id == health_check_id).first()
            
            if not health_check:
                flash('Relatório não encontrado.', 'error')
                return redirect(url_for('health_checks.index'))
            
            # --- Radar Metrics Backfill (Runtime) ---
            # If report is missing radar data (e.g. from bug), try to fetch it from DB
            report = health_check.report_data
            if isinstance(report, str):
                try:
                    report = json.loads(report)
                except:
                    report = {}
            if not report:
                report = {}
                
            radar = report.get('radar_metrics')
            
            # Check if radar is missing or zeroed out (all 0s)
            is_empty = not radar
            if radar:
                # If all main metrics are 0, likely a failed previous fetch
                if radar.get('visibility') == 0 and radar.get('position') == 0 and radar.get('authority') == 0:
                    is_empty = True
            
            if is_empty:
                try:
                    from app.models.local_search import LocalMetricsAggregated
                    from sqlalchemy import func
                    
                    # Try to find metrics for the same date as the report creation
                    if health_check.created_at:
                        scan_date = health_check.created_at.date()
                        
                        agg = db.query(LocalMetricsAggregated).filter(
                            LocalMetricsAggregated.client_id == health_check.client_id,
                            func.date(LocalMetricsAggregated.scan_date) == scan_date
                        ).first()
                        
                        if agg:
                            report['radar_metrics'] = {
                                'visibility': agg.visibility_score,
                                'position': agg.avg_position_score,
                                'reviews': agg.reviews_score,
                            'authority': agg.local_authority_score,
                            'market_avg': {
                                'visibility': agg.market_avg_visibility,
                                'position': agg.market_avg_position,
                                'reviews': agg.market_avg_reviews,
                                'authority': agg.market_avg_authority
                            }
                        }
                        # Update in-memory object (and potentially save if we commit)
                        health_check.report_data = report
                        # Optional: Persist fixed data
                        # db.commit() 
                except Exception as e:
                    logger.warning(f"Failed to backfill radar metrics: {e}")
            
            return render_template('health_checks/view.html', health_check=health_check)
    except Exception as e:
        logger.exception(f"Error loading health check report {health_check_id}")
        flash(f'Erro ao carregar relatório: {str(e)}', 'error')
        return redirect(url_for('health_checks.index'))

@bp.route('/<int:health_check_id>/delete', methods=['POST'])
@login_required
def delete(health_check_id):
    """Deletar um relatório de health check"""
    with get_db() as db:
        health_check = db.query(HealthCheck).filter(HealthCheck.id == health_check_id).first()
        if not health_check:
            flash('Relatório não encontrado.', 'error')
            return redirect(url_for('health_checks.index'))
        
        client_id = health_check.client_id
        db.delete(health_check)
        db.commit()
        
        flash('Relatório removido com sucesso.', 'success')
        return redirect(url_for('clients.view', client_id=client_id))

@bp.route('/convert-to-lead', methods=['POST'])
@login_required
def convert_to_lead():
    data = request.get_json()
    business_name = data.get('business_name')
    report_data = data.get('report')
    score = data.get('score')
    
    if not business_name or not report_data:
         return jsonify({'success': False, 'message': 'Dados incompletos'}), 400

    user_id = session.get('user_id')
    company_id = session.get('company_id')
    
    if not user_id:
         return jsonify({'success': False, 'message': 'Sessão expirada. Faça login novamente.'}), 401

    with get_db() as db:
        try:
            from app.models import KanbanStage
            # Tentar pegar o primeiro estágio do Kanban da empresa
            first_stage = db.query(KanbanStage).filter(
                KanbanStage.company_id == company_id
            ).order_by(KanbanStage.order).first()
            
            # Fallback se não tiver estágios da empresa (usa global ou id 1)
            if not first_stage:
                first_stage = db.query(KanbanStage).order_by(KanbanStage.order).first()
                
            stage_id = first_stage.id if first_stage else 1
            
            # Extrair endereço corretamente do report_data (que vem do Serper)
            address = report_data.get('address')
            if not address and 'source_data' in report_data:
                address = report_data['source_data'].get('address')
            
            new_client = Client(
                name=business_name,
                gmb_profile_name=business_name,
                address=address,
                kanban_stage_id=stage_id,
                company_id=company_id,
                owner_id=user_id
            )
            db.add(new_client)
            db.commit() # Commit para gerar ID
            
            health_check = HealthCheck(
                client_id=new_client.id,
                score=score,
                report_data=report_data
            )
            # Definir source como 'public' já que veio do Quick Check
            health_check.source = 'public'
            if 'source_data' in report_data:
                health_check.origin_id = report_data['source_data'].get('cid') or report_data['source_data'].get('placeId')
                
            db.add(health_check)
            db.commit()
            
            return jsonify({'success': True, 'client_id': new_client.id, 'message': 'Lead criado!'})
        except Exception as e:
            db.rollback()
            logger.error(f"Error in convert_to_lead: {str(e)}")
            return jsonify({'success': False, 'message': f"Erro ao criar lead: {str(e)}"}), 500

@bp.route('/<int:health_check_id>/ai-generate', methods=['POST'])
@login_required
def generate_ai_content(health_check_id):
    try:
        health_check = db.session.get(HealthCheck, health_check_id)
        if not health_check:
            return jsonify({'error': 'Relatório não encontrado'}), 404

        data = request.get_json()
        action_type = data.get('type')
        
        logger.debug(f"AI Request: Type={action_type}, HealthCheck={health_check_id}")

        try:
            from app.services.gemini_service import GeminiService
            gemini = GeminiService()
        except ImportError as e:
            logger.error(f"AI Error: Dependency missing - {str(e)}")
            return jsonify({'error': 'Biblioteca de IA não instalada. Execute pip install.'}), 500
        except Exception as e:
            logger.error(f"AI Error: Service init failed - {str(e)}")
            return jsonify({'error': f'Erro ao iniciar serviço de IA: {str(e)}'}), 500
        
        if not gemini.model:
            logger.error("AI Error: Google API Key missing")
            return jsonify({'error': 'Chave de API do Google não configurada (GOOGLE_API_KEY).'}), 503

        client_name = health_check.client.name
        address = health_check.report_data.get('address') if health_check.report_data else None
        if not address and health_check.client.address:
            address = health_check.client.address

        result = ""
        try:
            if action_type == 'post-evento':
                result = gemini.generate_post_suggestion(client_name, address)
            elif action_type == 'faq':
                result = gemini.generate_faq_suggestion(client_name)
            else:
                return jsonify({'error': 'Tipo de ação inválido'}), 400
        except Exception as e:
            logger.error(f"AI Error: Generation failed - {str(e)}")
            return jsonify({'error': f'Erro na geração do conteúdo: {str(e)}'}), 500

        return jsonify({'result': result})

    except Exception as e:
        logger.exception(f"Critical AI error in health check {health_check_id}")
        return jsonify({'error': f"Erro interno: {str(e)}"}), 500
