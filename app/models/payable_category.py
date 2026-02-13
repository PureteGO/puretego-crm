"""
PURETEGO CRM - Payable Category Model
Modelo de Categorias de Contas a Pagar
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base

class PayableCategory(Base):
    """Categories for expenses (e.g., Marketing, Tools, Rent)"""
    __tablename__ = 'payable_categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(20), default='#6c757d') # Default gray
    
    # Relationships
    company = relationship('Company')
    payables = relationship('Payable', back_populates='category_obj')

    def __init__(self, company_id, name, color='#6c757d'):
        self.company_id = company_id
        self.name = name
        self.color = color

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color
        }

    def __repr__(self):
        return f'<PayableCategory {self.name}>'
