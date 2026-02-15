"""
PURETEGO CRM - Notification Service
Serviço centralizado para criação de notificações in-app e integração com email
"""

from datetime import datetime
from flask import current_app
from flask_babel import gettext as _
from app.models.notification import Notification


class NotificationService:
    """Serviço para criar e gerenciar notificações"""

    @staticmethod
    def notify(db, company_id, user_id, title, message=None, ntype='info', ref_type=None, ref_id=None, send_email=False):
        """
        Cria uma notificação in-app e opcionalmente envia email.
        
        Args:
            db: Database session
            company_id: Company ID (multi-tenant)
            user_id: Target user ID (recipient)
            title: Notification title
            message: Optional detailed message
            ntype: Notification type (info, task_assigned, task_completed, deal_moved, etc.)
            ref_type: Reference entity type ('task', 'deal', 'client')
            ref_id: Reference entity ID
            send_email: Whether to also send an email notification
        """
        notif = Notification(
            company_id=company_id,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=ntype,
            reference_type=ref_type,
            reference_id=ref_id
        )
        db.add(notif)
        
        # Optionally send email
        if send_email:
            try:
                from app.services.email_service import EmailService
                from app.models.user import User
                user = db.query(User).get(user_id)
                if user and user.email:
                    EmailService.send_transactional_email(
                        company_id=company_id,
                        template_code='notification_generic',
                        recipient=user.email,
                        placeholders={
                            'user_name': user.name,
                            'notification_title': title,
                            'notification_message': message or '',
                        },
                        reference_id=ref_id,
                        user_id=user_id
                    )
            except Exception as e:
                current_app.logger.error(f"Failed to send notification email: {e}")
        
        return notif

    @staticmethod
    def on_task_assigned(db, task):
        """Notifica o assigned_to quando recebe nova tarefa"""
        if not task.assigned_to_id:
            return
        
        # Don't notify if user assigned task to themselves
        if task.assigned_by_id and task.assigned_by_id == task.assigned_to_id:
            return
        
        assigner_name = task.assigned_by.name if task.assigned_by else _('System')
        
        NotificationService.notify(
            db=db,
            company_id=task.company_id,
            user_id=task.assigned_to_id,
            title=_('New task assigned to you'),
            message=f"{assigner_name}: {task.title}",
            ntype='task_assigned',
            ref_type='task',
            ref_id=task.id,
            send_email=True
        )

    @staticmethod
    def on_task_completed(db, task):
        """Notifica o assigned_by quando a tarefa é concluída"""
        if not task.assigned_by_id:
            return
        
        # Don't notify if user completed their own assigned task
        if task.assigned_to_id == task.assigned_by_id:
            return
        
        completer_name = task.assigned_to.name if task.assigned_to else _('Someone')
        
        NotificationService.notify(
            db=db,
            company_id=task.company_id,
            user_id=task.assigned_by_id,
            title=_('Task completed'),
            message=f"{completer_name}: {task.title}",
            ntype='task_completed',
            ref_type='task',
            ref_id=task.id,
            send_email=False
        )

    @staticmethod
    def on_task_pending_approval(db, task):
        """Notifica o assigned_by que a tarefa precisa de aprovação"""
        if not task.assigned_by_id:
            return
            
        completer_name = task.assigned_to.name if task.assigned_to else _('Someone')

        NotificationService.notify(
            db=db,
            company_id=task.company_id,
            user_id=task.assigned_by_id,
            title=_('Task awaiting approval'),
            message=f"{completer_name} {_('marked task as completed. Review required.')}: {task.title}",
            ntype='task_approval_needed',
            ref_type='task',
            ref_id=task.id,
            send_email=True
        )

    @staticmethod
    def on_task_approved(db, task):
        """Notifica o assigned_to que a tarefa foi aprovada"""
        if not task.assigned_to_id:
            return
            
        approver_name = task.approved_by.name if task.approved_by else _('Manager')

        NotificationService.notify(
            db=db,
            company_id=task.company_id,
            user_id=task.assigned_to_id,
            title=_('Task approved'),
            message=f"{approver_name} {_('approved your work on')}: {task.title}",
            ntype='task_approved',
            ref_type='task',
            ref_id=task.id,
            send_email=False
        )

    @staticmethod
    def on_task_rejected(db, task):
        """Notifica o assigned_to que a tarefa foi rejeitada"""
        if not task.assigned_to_id:
            return
            
        rejector_name = task.assigned_by.name if task.assigned_by else _('Manager')

        NotificationService.notify(
            db=db,
            company_id=task.company_id,
            user_id=task.assigned_to_id,
            title=_('Task returned for revision'),
            message=f"{rejector_name} {_('returned task')}: {task.title}. {_('Comment')}: {task.rejection_comment}",
            ntype='task_rejected',
            ref_type='task',
            ref_id=task.id,
            send_email=True
        )

    @staticmethod
    def on_deal_stage_changed(db, deal, old_stage, new_stage):
        """Notifica o owner do deal quando o estágio muda"""
        if not deal.owner_id:
            return
        
        NotificationService.notify(
            db=db,
            company_id=deal.company_id,
            user_id=deal.owner_id,
            title=_('Deal stage updated'),
            message=f"{deal.title}: {old_stage} → {new_stage}",
            ntype='deal_moved',
            ref_type='deal',
            ref_id=deal.id,
            send_email=False
        )

    @staticmethod
    def get_unread_count(db, user_id, company_id):
        """Retorna contagem de notificações não lidas"""
        from sqlalchemy import func
        return db.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id,
            Notification.company_id == company_id,
            Notification.is_read == False
        ).scalar() or 0

    @staticmethod
    def get_recent(db, user_id, company_id, limit=20):
        """Retorna as notificações mais recentes do usuário"""
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.company_id == company_id
        ).order_by(Notification.created_at.desc()).limit(limit).all()

    @staticmethod
    def mark_as_read(db, notification_id, user_id):
        """Marca uma notificação como lida (com verificação de ownership)"""
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if notif:
            notif.is_read = True
        return notif

    @staticmethod
    def mark_all_read(db, user_id, company_id):
        """Marca todas as notificações do usuário como lidas"""
        db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.company_id == company_id,
            Notification.is_read == False
        ).update({Notification.is_read: True})
