from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.routes.auth import login_required
from app.models import HealthCheck, Client
from app.services import SerpApiService
from config.database import get_db
import json

bp = Blueprint('health_checks', __name__, url_prefix='/health-checks')

@bp.route('/quick-check', methods=['POST'])
@login_required
def quick_check():
    data = request.get_json()
    business_name = data.get('business_name')
    if not business_name:
        return jsonify({'success': False, 'message': 'Nome obrigatório'}), 400
    
    try:
        serpapi = SerpApiService()
        result = serpapi.analyze_gmb_profile(business_name)
        
        if result.get('score') == 0 and 'error' in result.get('report', {}):
            return jsonify({'success': False, 'message': 'Não encontrado.'}), 404
            
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
            business_name = request.form.get('business_name')
            
            try:
                serpapi = SerpApiService()
                result = serpapi.analyze_gmb_profile(business_name)
                
                health_check = HealthCheck(
                    client_id=client.id,
                    score=result['score'],
                    report_data=result['report']
                )
                db.add(health_check)
                db.commit()
                
                flash('Health Check realizado com sucesso!', 'success')
                return redirect(url_for('clients.view', client_id=client.id))
            except Exception as e:
                db.rollback()
                flash(f'Erro ao realizar Health Check: {str(e)}', 'error')
                return render_template('health_checks/create.html', client=client)
                
        return render_template('health_checks/create.html', client=client)

@bp.route('/<int:health_check_id>')
@login_required
def view(health_check_id):
    with get_db() as db:
        health_check = db.query(HealthCheck).filter(HealthCheck.id == health_check_id).first()
        if not health_check:
            flash('Relatório não encontrado.', 'error')
            return redirect(url_for('health_checks.index'))
        return render_template('health_checks/view.html', health_check=health_check)

@bp.route('/convert-to-lead', methods=['POST'])
@login_required
def convert_to_lead():
    data = request.get_json()
    business_name = data.get('business_name')
    report_data = data.get('report')
    score = data.get('score')
    
    if not business_name or not report_data:
         return jsonify({'success': False, 'message': 'Dados incompletos'}), 400

    with get_db() as db:
        try:
            from app.models import KanbanStage
            first_stage = db.query(KanbanStage).order_by(KanbanStage.order).first()
            stage_id = first_stage.id if first_stage else 1
        except:
            stage_id = 1
        
        new_client = Client(
            name=business_name,
            gmb_profile_name=business_name,
            address=report_data.get('address', None),
            kanban_stage_id=stage_id
        )
        db.add(new_client)
        db.flush() 
        
        health_check = HealthCheck(
            client_id=new_client.id,
            score=score,
            report_data=report_data
        )
        db.add(health_check)
        db.commit()
        
        return jsonify({'success': True, 'client_id': new_client.id, 'message': 'Lead criado!'})
