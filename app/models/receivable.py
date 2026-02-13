"""
PURETEGO CRM - Receivable Model
Modelo de Contas a Receber (Financeiro 1.0)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class Receivable(Base):
    """Represents a payment to be received from a client."""
    __tablename__ = 'receivables'

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    deal_id = Column(Integer, ForeignKey('deals.id'), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, index=True)
    
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    paid_at = Column(DateTime, nullable=True) # Actual payment date
    
    # Status: open, paid, partial, overdue, cancelled
    status = Column(String(50), default='open', index=True)
    paid_amount = Column(Numeric(12, 2), default=0)
    
    # Payment method used (for reference after paid)
    payment_method = Column(String(50), nullable=True) # boleto, transfer, card, cash
    
    # External reference (e.g., Stripe/Asaas ID)
    external_id = Column(String(255), nullable=True)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship('Company')
    client = relationship('Client', backref='receivables')
    deal = relationship('Deal', backref='receivables')
    project = relationship('Project', backref='receivables')

    def __init__(self, company_id, client_id, description, amount, due_date, deal_id=None, project_id=None, status='open', paid_amount=0):
        self.company_id = company_id
        self.client_id = client_id
        self.description = description
        self.amount = amount
        self.due_date = due_date
        self.deal_id = deal_id
        self.project_id = project_id
        self.status = status
        self.paid_amount = paid_amount

    def to_dict(self):
        """Converts object to dictionary for API responses"""
        return {
            'id': self.id,
            'client_name': self.client.name if self.client else 'N/A',
            'description': self.description,
            'amount': float(self.amount),
            'paid_amount': float(self.paid_amount or 0),
            'balance': float(self.amount) - float(self.paid_amount or 0),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'status': self.status,
            'payment_method': self.payment_method,
            'deal_id': self.deal_id,
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Receivable {self.id} - {self.description} - {self.amount}>'
