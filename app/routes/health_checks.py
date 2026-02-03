"""
PURETEGO CRM - Health Checks Routes
Rotas de gestão de Health Checks do GMB
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.routes.auth import login_required
from app.models import HealthCheck, Client
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
            # Usar o nome do perfil GMB ou o nome do cliente
            business_name = client.gmb_profile_name or client.name
            
            # Executar análise via SerpApi
            serpapi = SerpApiService()
            result = serpapi.analyze_gmb_profile(business_name)
            
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
    """Health check rápido via API (para uso durante visitas)"""
    data = request.get_json()
    business_name = data.get('business_name')
    client_id = data.get('client_id')
    
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
    
    # Se client_id foi fornecido, salvar no banco
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
        'report': result['report']
    })
