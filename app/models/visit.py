"""
PURETEGO CRM - Visit Model
Modelo de visita a cliente
"""

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Visit(Base):
    """Modelo de visita realizada a um cliente"""
    
    __tablename__ = 'visits'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    notes = Column(Text)
    next_step = Column(Text)
    visit_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relacionamentos
    client = relationship('Client', back_populates='visits')
    user = relationship('User', backref='visits')
    
    def __init__(self, client_id, user_id, visit_date, notes=None, next_step=None):
        self.client_id = client_id
        self.user_id = user_id
        self.visit_date = visit_date
        self.notes = notes
        self.next_step = next_step
    
    def to_dict(self, include_relations=False):
        """Converte o objeto para dicionário"""
        data = {
            'id': self.id,
            'client_id': self.client_id,
            'user_id': self.user_id,
            'notes': self.notes,
            'next_step': self.next_step,
            'visit_date': self.visit_date.isoformat() if self.visit_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_relations:
            data['client'] = self.client.to_dict() if self.client else None
            data['user'] = self.user.to_dict() if self.user else None
        
        return data
    
    def __repr__(self):
        return f'<Visit {self.id} - Client {self.client_id}>'
