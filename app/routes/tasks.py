"""
PURETEGO CRM - Tasks Routes
Rotas para gestão de tarefas e API de notificações
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.routes.auth import login_required, get_current_user
from app.models.task import Task
from app.utils.tenant import filter_by_company
from config.database import get_db
from datetime import datetime

bp = Blueprint('tasks', __name__, url_prefix='/tasks')
api_bp = Blueprint('api_tasks', __name__, url_prefix='/api/tasks')

@api_bp.route('/summary')
@login_required
def get_task_summary():
    """API: Retorna resumo de tarefas pendentes para o dashboard"""
    user = get_current_user()
    role_name = user.role.name
    
    with get_db() as db:
        # Filtrar tarefas pendentes para o papel do usuário ou especificamente para o usuário
        query = filter_by_company(db.query(Task), Task).filter(Task.status == 'pending')
        
        # Filtro por Role e/ou UserID
        # Regra: Se a tarefa tem user_id, deve ser para aquele user. 
        # Se não tem, mas tem role_target, deve ser para qualquer um com esse role.
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Task.user_id == user.id,
                (Task.user_id == None) & (Task.role_target == role_name)
            )
        )
        
        tasks = query.order_by(Task.due_date.asc()).all()
        
        # Contadores
        today = datetime.utcnow().date()
        overdue_count = sum(1 for t in tasks if t.due_date.date() < today)
        today_count = sum(1 for t in tasks if t.due_date.date() == today)
        
        return jsonify({
            'success': True,
            'total_pending': len(tasks),
            'overdue_count': overdue_count,
            'today_count': today_count,
            'tasks': [t.to_dict() for t in tasks[:5]] # Retorna as 5 mais urgentes
        })

@bp.route('/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    """Marcar tarefa como concluída"""
    with get_db() as db:
        task = db.query(Task).get(task_id)
        if not task:
            return jsonify({'success': False, 'message': 'Tarefa não encontrada'}), 404
            
        task.status = 'completed'
        db.commit()
        return jsonify({'success': True, 'message': 'Tarefa concluída'})
