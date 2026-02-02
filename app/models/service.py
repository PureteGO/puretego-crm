"""
PURETEGO CRM - Service Model
Modelo de serviço oferecido
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime
from sqlalchemy.sql import func
from config.database import Base


class Service(Base):
    """Modelo de serviço do catálogo Puretego"""
    
    __tablename__ = 'services'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    base_price = Column(Numeric(10, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, server_default=func.now())
    
    def __init__(self, name, description=None, base_price=0.00):
        self.name = name
        self.description = description
        self.base_price = base_price
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'base_price': float(self.base_price) if self.base_price else 0.00,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Service {self.name}>'
