"""
PURETEGO CRM - Health Checks Routes
Rotas de gestão de Health Checks do GMB
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.routes.auth import login_required
from app.models import HealthCheck, Client
from app.models.quick_check_log import QuickCheckLog
from app.services import SerpApiService
from config.database import get_db

bp = Blueprint('health_checks', __name__, url_prefix='/health-checks')


@bp.route('/')
@login_required
def index():
    """Lista de health checks"""
    with get_db() as db:
        health_checks = db.query(HealthCheck).order_by(HealthCheck.created_at.desc()).all()
        return render_template('health_checks/index.html', health_checks=health_checks)


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
            try:
                # Usar o nome do perfil GMB ou o nome do cliente
                business_name = request.form.get('business_name') or client.gmb_profile_name or client.name
                
                # Executar análise via SerpApi
                serpapi = SerpApiService()
                # Passar o endereço do cliente como contexto de localização, se disponível
                location_context = client.address if client.address else None
                result = serpapi.analyze_gmb_profile(business_name, location=location_context)
                
                if result['score'] == 0 and 'error' in result['report']:
                    flash(f'Erro ao analisar perfil: {result["report"]["error"]}', 'error')
                    return redirect(url_for('clients.view', client_id=client_id))
                
                # Salvar health check
                health_check = HealthCheck(
                    client_id=client_id,
                    score=result['score'],
                    report_data=result['report']
                )
                db.add(health_check)
                db.commit()
                
                flash(f'Health Check realizado! Pontuação: {result["score"]}/100', 'success')
                return redirect(url_for('health_checks.view', health_check_id=health_check.id))
                
            except Exception as e:
                import traceback
                traceback.print_exc() # Print to console/stderr
                db.rollback()
                flash(f'Erro interno ao realizar Health Check: {str(e)}', 'error')
                return redirect(url_for('clients.view', client_id=client_id))
    
        return render_template('health_checks/create.html', client=client)


@bp.route('/<int:health_check_id>')
@login_required
def view(health_check_id):
    """Visualizar detalhes do health check"""
    with get_db() as db:
        health_check = db.query(HealthCheck).filter(HealthCheck.id == health_check_id).first()
        
        if not health_check:
            flash('Health Check não encontrado.', 'error')
            return redirect(url_for('health_checks.index'))
    
        return render_template('health_checks/view.html', health_check=health_check)


@bp.route('/<int:health_check_id>/delete', methods=['POST'])
@login_required
def delete(health_check_id):
    """Deletar health check"""
    with get_db() as db:
        health_check = db.query(HealthCheck).filter(HealthCheck.id == health_check_id).first()
        
        if not health_check:
            flash('Health Check não encontrado.', 'error')
            return redirect(url_for('health_checks.index'))
        
        client_id = health_check.client_id
        db.delete(health_check)
        db.commit()
        
        flash('Health Check deletado com sucesso.', 'success')
    
    return redirect(url_for('clients.view', client_id=client_id))


@bp.route('/quick-check', methods=['POST'])
@login_required
def quick_check():
    """Health check rápido via API (salva LOG, mas não Lead)"""
    data = request.get_json()
    business_name = data.get('business_name')
    client_id = data.get('client_id')
    lat = data.get('lat')
    lon = data.get('lon')
    
    if not business_name:
        return jsonify({'success': False, 'message': 'Nome do negócio é obrigatório'}), 400
    
    # Executar análise
    serpapi = SerpApiService()
    result = serpapi.analyze_gmb_profile(business_name)
    
    if result['score'] == 0 and 'error' in result['report']:
        return jsonify({
            'success': False,
            'message': result['report']['error']
        }), 404
    
    # Se client_id foi fornecido, salvar no banco (fluxo antigo de "re-check")
    if client_id:
        with get_db() as db:
            health_check = HealthCheck(
                client_id=int(client_id),
                score=result['score'],
                report_data=result['report']
            )
            db.add(health_check)
            db.commit()
            result['health_check_id'] = health_check.id
            return jsonify({
                'success': True,
                'score': result['score'],
                'report': result['report'],
                'health_check_id': result['health_check_id']
            })
    
    # SALVAR NO LOG (Histórico)
    log_id = None
    with get_db() as db:
        new_log = QuickCheckLog(
            user_id=session.get('user_id'),
            business_name=result['report'].get('business_name', business_name),
            search_term=business_name,
            location_lat=lat,
            location_lon=lon,
            score=result['score'],
            report_data=result['report']
        )
        db.add(new_log)
        db.commit()
        log_id = new_log.id
    
    return jsonify({
        'success': True,
        'score': result['score'],
        'report': result['report'],
        'log_id': log_id # Retornar ID do Log para conversão futura
    })

@bp.route('/convert-to-lead', methods=['POST'])
@login_required
def convert_to_lead():
    """Converte um resultado de Quick Check (Log) em um Lead"""
    data = request.get_json()
    business_name = data.get('business_name')
    report_data = data.get('report')
    score = data.get('score')
    log_id = data.get('log_id')
    
    if not business_name or not report_data:
         return jsonify({'success': False, 'message': 'Dados incompletos'}), 400

    with get_db() as db:
        # Criar novo cliente (Lead)
        # Tentar pegar o primeiro estágio do Kanban (ex: Novo / Prospecção)
        try:
            from app.models import KanbanStage
            first_stage = db.query(KanbanStage).order_by(KanbanStage.order).first()
            stage_id = first_stage.id if first_stage else None
        except:
            stage_id = 1 # Fallback
        
        # Verificar se já existe cliente com este nome para evitar duplicatas óbvias
        existing_client = db.query(Client).filter(Client.name == business_name).first()
        if existing_client:
            return jsonify({'success': False, 'message': 'Cliente já existe!'}), 409

        new_client = Client(
            name=business_name,
            gmb_profile_name=business_name,
            address=report_data.get('address', None),
            kanban_stage_id=stage_id
        )
        db.add(new_client)
        db.flush() 
        
        # Criar o Health Check
        health_check = HealthCheck(
            client_id=new_client.id,
            score=score,
            report_data=report_data
        )
        db.add(health_check)
        
        # Atualizar Log se existir
        if log_id:
            try:
                log = db.query(QuickCheckLog).filter(QuickCheckLog.id == log_id).first()
                if log:
                    log.converted_client_id = new_client.id
            except Exception as e:
                print(f"Erro ao vincular Log: {e}")
                # Não falhar a request por isso
        
        db.commit()
        
        return jsonify({
            'success': True, 
            'client_id': new_client.id,
            'health_check_id': health_check.id,
            'message': 'Lead criado com sucesso!'
        })
