"""
PURETEGO CRM - Task Model
Modelo de tarefas para automação de workflow entre setores
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
    
    # Status: pending, completed, canceled
    status = Column(String(20), default='pending', index=True)
    
    # Type: sdr_followup, sales_meeting, finance_billing, gmb_onboarding, etc.
    type = Column(String(50), index=True)
    
    # Target Role: owner, sdr, sales, finance, gmb_manager, etc.
    role_target = Column(String(50), index=True)
    
    # User Assignment
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    
    # Context Links
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True, index=True)
    deal_id = Column(Integer, ForeignKey('deals.id'), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, index=True)
    
    due_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship('Company')
    assigned_user = relationship('User', backref='assigned_tasks')
    client = relationship('Client', backref='tasks')
    deal = relationship('Deal', backref='tasks')
    project = relationship('Project', backref='tasks')
    
    def __repr__(self):
        return f'<Task {self.title} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'status': self.status,
            'role_target': self.role_target,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'client_name': self.client.name if self.client else None,
            'type': self.type
        }
