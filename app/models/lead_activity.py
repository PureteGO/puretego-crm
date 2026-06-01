"""
PURETEGO CRM - Lead Activity Model
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class LeadActivity(Base):
    """Histórico simples de interações e alterações dos Leads de Prospecção"""
    
    __tablename__ = 'lead_activities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Tipo de ação: e.g., "created", "status_change", "note_added", "converted", "contact"
    action = Column(String(255), nullable=False)
    
    notes = Column(Text, nullable=True) # Observações livres da atividade
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    lead = relationship('Lead', back_populates='activities')
    user = relationship('User', backref='lead_activities')

    def __init__(self, lead_id, user_id=None, action="note_added", notes=None):
        self.lead_id = lead_id
        self.user_id = user_id
        self.action = action
        self.notes = notes

    def to_dict(self):
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'action': self.action,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<LeadActivity {self.id} for Lead {self.lead_id}>'
