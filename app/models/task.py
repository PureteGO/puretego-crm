"""
PURETEGO CRM - Task Model
Modelo de tarefas para automação de workflow e atribuição entre usuários
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from config.database import Base
from datetime import datetime


class Task(Base):
    """Modelo de tarefas associadas a clientes e negócios"""
    
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status: open, in_progress, done, canceled
    status = Column(String(20), default='open', index=True)
    
    # Type: sdr_followup, sales_meeting, finance_billing, gmb_onboarding, manual, etc.
    type = Column(String(50), index=True)
    
    # Target Role: owner, sdr, sales, finance, gmb_manager, etc.
    role_target = Column(String(50), index=True)
    
    # Priority: low, medium, high
    priority = Column(String(20), default='medium', index=True)
    
    # User Assignment (renamed from user_id for clarity)
    # assigned_to_id = who must do the task
    # assigned_by_id = who created/delegated the task
    assigned_to_id = Column('assigned_to_id', Integer, ForeignKey('users.id'), nullable=True, index=True)
    assigned_by_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    
    # Context Links
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True, index=True)
    deal_id = Column(Integer, ForeignKey('deals.id'), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, index=True)
    
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    # v2: Verification & Project Integration
    verification_required = Column(Boolean, default=False)
    approved_at = Column(DateTime, nullable=True)
    approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    rejection_comment = Column(Text, nullable=True)
    completed_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    assigned_comment = Column(Text, nullable=True)
    
    # Project specific (migration from ProjectTicket)
    phase = Column(String(50), nullable=True)
    is_onboarding = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship('Company')
    assigned_to = relationship('User', foreign_keys=[assigned_to_id], backref='assigned_tasks')
    assigned_by = relationship('User', foreign_keys=[assigned_by_id], backref='created_tasks')
    approved_by = relationship('User', foreign_keys=[approved_by_id])
    completed_by = relationship('User', foreign_keys=[completed_by_id])
    
    client = relationship('Client', backref='tasks')
    deal = relationship('Deal', backref='tasks')
    project = relationship('Project', backref='tasks')
    
    def __repr__(self):
        return f'<Task {self.title} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'type': self.type,
            'role_target': self.role_target,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else None,
            'deal_id': self.deal_id,
            'deal_title': self.deal.title if self.deal else None,
            'project_id': self.project_id,
            'assigned_to_id': self.assigned_to_id,
            'assigned_to_name': self.assigned_to.name if self.assigned_to else None,
            'assigned_by_id': self.assigned_by_id,
            'assigned_by_name': self.assigned_by.name if self.assigned_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'verification_required': self.verification_required,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approved_by_name': self.approved_by.name if self.approved_by else None,
            'completed_by_name': self.completed_by.name if self.completed_by else None,
            'phase': self.phase,
            'rejection_comment': self.rejection_comment,
            'assigned_comment': self.assigned_comment
        }
