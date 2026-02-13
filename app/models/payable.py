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
    
    # Category: Foreign Key to PayableCategory
    category_id = Column(Integer, ForeignKey('payable_categories.id'), nullable=True, index=True)
    
    # Status: open, paid, partial, overdue, cancelled
    status = Column(String(50), default='open', index=True)
    paid_amount = Column(Numeric(12, 2), default=0)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship('Company')
    category_obj = relationship('PayableCategory', back_populates='payables')

    def __init__(self, company_id, description, amount, due_date, status='open', category_id=None, notes=None, paid_amount=0):
        self.company_id = company_id
        self.description = description
        self.amount = amount
        self.due_date = due_date
        self.status = status
        self.category_id = category_id
        self.notes = notes
        self.paid_amount = paid_amount

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'amount': float(self.amount),
            'paid_amount': float(self.paid_amount or 0),
            'balance': float(self.amount) - float(self.paid_amount or 0),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'status': self.status,
            'category_id': self.category_id,
            'category_name': self.category_obj.name if self.category_obj else 'Outros',
            'category_color': self.category_obj.color if self.category_obj else '#6c757d',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
