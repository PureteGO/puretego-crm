"""
PURETEGO CRM - Notifications Routes
API para notificações in-app
"""

from flask import Blueprint, jsonify, session
from flask_babel import gettext as _
from app.routes.auth import login_required, get_current_user
from app.services.notification_service import NotificationService
from config.database import get_db

bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@bp.route('/')
@login_required
def get_notifications():
    """Retorna as últimas notificações do usuário"""
    user = get_current_user()
    company_id = session.get('company_id')
    
    with get_db() as db:
        notifications = NotificationService.get_recent(db, user.id, company_id, limit=20)
        unread_count = NotificationService.get_unread_count(db, user.id, company_id)
        
        return jsonify({
            'success': True,
            'unread_count': unread_count,
            'notifications': [n.to_dict() for n in notifications]
        })


@bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Marca uma notificação como lida"""
    user = get_current_user()
    
    with get_db() as db:
        notif = NotificationService.mark_as_read(db, notification_id, user.id)
        if not notif:
            return jsonify({'success': False, 'message': _('Notification not found')}), 404
        
        db.commit()
        return jsonify({'success': True})


@bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Marca todas as notificações como lidas"""
    user = get_current_user()
    company_id = session.get('company_id')
    
    with get_db() as db:
        NotificationService.mark_all_read(db, user.id, company_id)
        db.commit()
        return jsonify({'success': True})


@bp.route('/count')
@login_required
def unread_count():
    """Retorna apenas a contagem de não lidas (para polling leve)"""
    user = get_current_user()
    company_id = session.get('company_id')
    
    with get_db() as db:
        count = NotificationService.get_unread_count(db, user.id, company_id)
        return jsonify({'success': True, 'count': count})
