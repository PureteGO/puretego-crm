"""
PURETEGO CRM - Payable Model
Modelo de Contas a Pagar (Custos da Agência)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class Payable(Base):
    """Represents a cost or expense of the agency."""
    __tablename__ = 'payables'

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    paid_at = Column(DateTime, nullable=True)
    
    # Status: open, paid, overdue, cancelled
    status = Column(String(50), default='open', index=True)
    
    # Category: tools, ads, office, payroll, other
    category = Column(String(50), default='other', index=True)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship('Company')

    def __init__(self, company_id, description, amount, due_date, status='open', category='other', notes=None):
        self.company_id = company_id
        self.description = description
        self.amount = amount
        self.due_date = due_date
        self.status = status
        self.category = category
        self.notes = notes

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'amount': float(self.amount),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'status': self.status,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
