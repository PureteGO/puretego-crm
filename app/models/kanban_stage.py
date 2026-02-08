"""
PURETEGO CRM - Kanban Stage Model
Modelo de etapas do pipeline Kanban com suporte multi-tenant
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class KanbanStage(Base):
    """Modelo de etapas do pipeline de vendas - personalizável por empresa"""
    
    __tablename__ = 'kanban_stages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    order = Column('order', Integer, nullable=False, default=0, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Multi-tenant field
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)  # nullable for migration
    
    # Relationships
    company = relationship('Company', back_populates='kanban_stages')
    deals = relationship('Deal', back_populates='stage')
    
    def __init__(self, name, order=0, company_id=None):
        self.name = name
        self.order = order
        self.company_id = company_id
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'order': self.order,
            'company_id': self.company_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<KanbanStage {self.name}>'

