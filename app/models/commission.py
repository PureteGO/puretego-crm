"""
PURETEGO CRM - Commission Model
Modelo de comissões para vendedores e SDRs
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class Commission(Base):
    """Represents a commission earned by a user for a deal or receivable."""
    __tablename__ = 'commissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    deal_id = Column(Integer, ForeignKey('deals.id'), nullable=False, index=True)
    receivable_id = Column(Integer, ForeignKey('receivables.id'), nullable=True, index=True)
    
    amount = Column(Numeric(12, 2), nullable=False)
    
    # Type: closer (Sales), opener (SDR)
    commission_type = Column(String(50), default='closer')
    
    # Status: pending, paid, cancelled
    status = Column(String(50), default='pending', index=True)
    
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship('Company')
    user = relationship('User')
    deal = relationship('Deal', backref='commissions')
    receivable = relationship('Receivable', backref='commissions')

    def __init__(self, company_id, user_id, deal_id, amount, commission_type='closer', receivable_id=None, status='pending'):
        self.company_id = company_id
        self.user_id = user_id
        self.deal_id = deal_id
        self.receivable_id = receivable_id
        self.amount = amount
        self.commission_type = commission_type
        self.status = status

    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user.name if self.user else 'N/A',
            'deal_title': self.deal.title if self.deal else 'N/A',
            'amount': float(self.amount),
            'type': self.commission_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
