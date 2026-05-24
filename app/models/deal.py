"""
PURETEGO CRM - Deal Model
Modelo de oportunidades/negócios no pipeline de vendas
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
import enum
from datetime import datetime

class DealStatus(enum.Enum):
    OPEN = "open"
    WON = "won"
    LOST = "lost"
    INACTIVE = "inactive"

class Deal(Base):
    """Modelo de Negócio (Oportunidade) no CRM"""
    
    __tablename__ = 'deals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    value = Column(Float, default=0.0)
    currency = Column(String(3), default='Gs')
    probability = Column(Integer, default=50) # 0-100%
    expected_close_date = Column(DateTime, nullable=True)
    status = Column(Enum(DealStatus, values_callable=lambda x: [e.value for e in x]), default=DealStatus.OPEN, index=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    stage_updated_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime, nullable=True)
    
    # Foreign Keys
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    kanban_stage_id = Column(Integer, ForeignKey('kanban_stages.id'), nullable=True, index=True)
    
    # Relationships
    company = relationship('Company', backref='deals')
    client = relationship('Client', back_populates='deals')
    owner = relationship('User', backref='deals')
    stage = relationship('KanbanStage', back_populates='deals')
    interactions = relationship('Interaction', back_populates='deal', cascade='all, delete-orphan')
    project = relationship('Project', back_populates='deal', uselist=False)
    
    def __init__(self, title, company_id, client_id, owner_id=None, kanban_stage_id=None, value=0.0):
        self.title = title
        self.company_id = company_id
        self.client_id = client_id
        self.owner_id = owner_id
        self.kanban_stage_id = kanban_stage_id
        self.value = value
        self.stage_updated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'value': self.value,
            'currency': self.currency,
            'probability': self.probability,
            'status': self.status.value,
            'company_id': self.company_id,
            'client_id': self.client_id,
            'owner_id': self.owner_id,
            'kanban_stage_id': self.kanban_stage_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'stage_updated_at': self.stage_updated_at.isoformat() if self.stage_updated_at else None,
            'expected_close_date': self.expected_close_date.isoformat() if self.expected_close_date else None
        }

    def __repr__(self):
        return f'<Deal {self.title} - {self.value}>'
