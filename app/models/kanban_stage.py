"""
PURETEGO CRM - Kanban Stage Model
Modelo de etapas do pipeline Kanban com suporte multi-tenant
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class KanbanStage(Base):
    """Modelo de etapas do pipeline de vendas - personalizável por empresa"""
    
    __tablename__ = 'kanban_stages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    order = Column('order', Integer, nullable=False, default=0, index=True)
    
    # Stage classification
    stage_type = Column(String(20), default='open', index=True)  # 'open', 'won', 'lost'
    color = Column(String(7), default='#6c757d')  # Hex color for UI
    is_active = Column(Boolean, default=True)
    include_in_funnel = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Multi-tenant field
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    
    # Relationships
    company = relationship('Company', back_populates='kanban_stages')
    deals = relationship('Deal', back_populates='stage')
    
    def __init__(self, name, order=0, company_id=None, stage_type='open', color='#6c757d', is_active=True):
        self.name = name
        self.order = order
        self.company_id = company_id
        self.stage_type = stage_type
        self.color = color
        self.is_active = is_active
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'order': self.order,
            'stage_type': self.stage_type,
            'color': self.color,
            'is_active': self.is_active,
            'include_in_funnel': self.include_in_funnel,
            'company_id': self.company_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<KanbanStage {self.name}>'
