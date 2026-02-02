"""
PURETEGO CRM - Kanban Stage Model
Modelo de etapas do pipeline Kanban
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from config.database import Base


class KanbanStage(Base):
    """Modelo de etapas do pipeline de vendas"""
    
    __tablename__ = 'kanban_stages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    order = Column('order', Integer, nullable=False, default=0, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    def __init__(self, name, order=0):
        self.name = name
        self.order = order
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'order': self.order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<KanbanStage {self.name}>'
