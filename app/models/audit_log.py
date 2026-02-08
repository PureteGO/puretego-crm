"""
AuditLog Model - Maps2GO CRM

Tracks all important actions performed by users for security auditing
and compliance in multi-tenant environment.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from config.database import Base


class AuditLog(Base):
    """
    Audit log for tracking user actions across the system.
    
    Captured actions include:
    - Client CRUD operations
    - User management
    - Package changes
    - SuperAdmin impersonation
    - Authentication events
    """
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    
    # Tenant context
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    
    # Actor
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    
    # Action details
    action = Column(String(50), nullable=False, index=True)  # CREATE, UPDATE, DELETE, LOGIN, IMPERSONATE, etc.
    entity_type = Column(String(50), nullable=False, index=True)  # Client, User, Proposal, HealthCheck, etc.
    entity_id = Column(Integer, nullable=True)  # ID of affected entity
    
    # Change tracking
    old_values = Column(JSON, nullable=True)  # Previous state (for updates)
    new_values = Column(JSON, nullable=True)  # New state (for creates/updates)
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    
    # Optional description
    description = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    company = relationship('Company', backref='audit_logs')
    user = relationship('User', backref='audit_logs')
    
    # Action constants
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_LOGIN = 'LOGIN'
    ACTION_LOGOUT = 'LOGOUT'
    ACTION_LOGIN_FAILED = 'LOGIN_FAILED'
    ACTION_PASSWORD_RESET = 'PASSWORD_RESET'
    ACTION_IMPERSONATE = 'IMPERSONATE'
    ACTION_PACKAGE_CHANGE = 'PACKAGE_CHANGE'
    ACTION_HEALTH_CHECK = 'HEALTH_CHECK'
    ACTION_PROPOSAL_GENERATED = 'PROPOSAL_GENERATED'
    
    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action} on {self.entity_type} by user {self.user_id}>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'user_id': self.user_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
