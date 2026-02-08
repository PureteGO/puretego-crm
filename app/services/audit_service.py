"""
Audit Service - Maps2GO CRM

Provides centralized logging for all auditable actions in the system.
"""

from datetime import datetime
from flask import request, session
from sqlalchemy.exc import SQLAlchemyError
from config.database import get_db
from app.models.audit_log import AuditLog


class AuditService:
    """Service for logging auditable actions"""
    
    @staticmethod
    def log(action: str, entity_type: str, entity_id: int = None,
            old_values: dict = None, new_values: dict = None,
            description: str = None, user_id: int = None, company_id: int = None):
        """
        Log an auditable action.
        
        Args:
            action: Action type (CREATE, UPDATE, DELETE, LOGIN, etc.)
            entity_type: Type of entity being acted upon
            entity_id: ID of the entity (optional)
            old_values: Previous state for updates (optional)
            new_values: New state for creates/updates (optional)
            description: Human-readable description (optional)
            user_id: Override user ID (optional, defaults to session)
            company_id: Override company ID (optional, defaults to session)
        """
        try:
            # Get user context from session if not provided
            if user_id is None:
                user_id = session.get('user_id')
            if company_id is None:
                company_id = session.get('company_id')
            
            # Get request metadata
            ip_address = None
            user_agent = None
            if request:
                ip_address = request.remote_addr
                # Handle proxied requests
                if request.headers.get('X-Forwarded-For'):
                    ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()
                user_agent = request.headers.get('User-Agent', '')[:500]
            
            # Create audit log entry
            audit_log = AuditLog(
                company_id=company_id,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent,
                description=description,
                created_at=datetime.utcnow()
            )
            
            with get_db() as db:
                db.add(audit_log)
                db.commit()
                
            return True
            
        except SQLAlchemyError as e:
            # Don't let audit logging failures break the application
            print(f"[AUDIT ERROR] Failed to log action: {e}")
            return False
    
    @staticmethod
    def log_login(user_id: int, company_id: int, success: bool = True):
        """Log login attempt"""
        action = AuditLog.ACTION_LOGIN if success else AuditLog.ACTION_LOGIN_FAILED
        AuditService.log(
            action=action,
            entity_type='User',
            entity_id=user_id,
            user_id=user_id,
            company_id=company_id,
            description=f"User {'logged in successfully' if success else 'failed login attempt'}"
        )
    
    @staticmethod
    def log_logout(user_id: int, company_id: int):
        """Log logout"""
        AuditService.log(
            action=AuditLog.ACTION_LOGOUT,
            entity_type='User',
            entity_id=user_id,
            user_id=user_id,
            company_id=company_id,
            description="User logged out"
        )
    
    @staticmethod
    def log_impersonation(admin_user_id: int, target_user_id: int, target_company_id: int):
        """Log superadmin impersonation"""
        AuditService.log(
            action=AuditLog.ACTION_IMPERSONATE,
            entity_type='User',
            entity_id=target_user_id,
            user_id=admin_user_id,
            company_id=target_company_id,
            description=f"SuperAdmin {admin_user_id} impersonated user {target_user_id}"
        )
    
    @staticmethod
    def log_create(entity_type: str, entity_id: int, new_values: dict = None, description: str = None):
        """Log entity creation"""
        AuditService.log(
            action=AuditLog.ACTION_CREATE,
            entity_type=entity_type,
            entity_id=entity_id,
            new_values=new_values,
            description=description or f"Created {entity_type} #{entity_id}"
        )
    
    @staticmethod
    def log_update(entity_type: str, entity_id: int, old_values: dict = None, new_values: dict = None, description: str = None):
        """Log entity update"""
        AuditService.log(
            action=AuditLog.ACTION_UPDATE,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            description=description or f"Updated {entity_type} #{entity_id}"
        )
    
    @staticmethod
    def log_delete(entity_type: str, entity_id: int, old_values: dict = None, description: str = None):
        """Log entity deletion"""
        AuditService.log(
            action=AuditLog.ACTION_DELETE,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            description=description or f"Deleted {entity_type} #{entity_id}"
        )
    
    @staticmethod
    def get_logs(company_id: int = None, user_id: int = None, 
                 entity_type: str = None, action: str = None,
                 limit: int = 100, offset: int = 0):
        """
        Retrieve audit logs with optional filters.
        
        Returns list of AuditLog entries.
        """
        with get_db() as db:
            query = db.query(AuditLog)
            
            if company_id:
                query = query.filter(AuditLog.company_id == company_id)
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if entity_type:
                query = query.filter(AuditLog.entity_type == entity_type)
            if action:
                query = query.filter(AuditLog.action == action)
                
            logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
            
            return [log.to_dict() for log in logs]
