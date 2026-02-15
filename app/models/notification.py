"""
PURETEGO CRM - Notification Model
Modelo de notificações in-app para atribuição de tarefas e eventos do pipeline
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Notification(Base):
    """Notificação in-app para um usuário específico"""
    
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)  # Destinatário
    
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    
    # Type: info, task_assigned, task_completed, deal_moved, deal_won, deal_lost
    notification_type = Column(String(50), default='info', index=True)
    
    # Contextual link (what entity generated this notification)
    reference_type = Column(String(50), nullable=True)  # 'task', 'deal', 'client'
    reference_id = Column(Integer, nullable=True)
    
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship('User', backref='notifications')
    company = relationship('Company')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Notification {self.title} -> User {self.user_id}>'
