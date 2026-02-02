"""
PURETEGO CRM - Proposal Model
Modelo de proposta/orçamento
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Proposal(Base):
    """Modelo de proposta/orçamento para cliente"""
    
    __tablename__ = 'proposals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    payment_terms = Column(Text)
    status = Column(String(50), nullable=False, default='draft', index=True)
    pdf_file_path = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    client = relationship('Client', back_populates='proposals')
    user = relationship('User', backref='proposals')
    items = relationship('ProposalItem', back_populates='proposal', cascade='all, delete-orphan')
    
    def __init__(self, client_id, user_id, total_amount=0.00, payment_terms=None, status='draft'):
        self.client_id = client_id
        self.user_id = user_id
        self.total_amount = total_amount
        self.payment_terms = payment_terms
        self.status = status
    
    def calculate_total(self):
        """Calcula o total baseado nos itens"""
        if self.items:
            self.total_amount = sum(item.price for item in self.items)
        return self.total_amount
    
    def to_dict(self, include_relations=False):
        """Converte o objeto para dicionário"""
        data = {
            'id': self.id,
            'client_id': self.client_id,
            'user_id': self.user_id,
            'total_amount': float(self.total_amount) if self.total_amount else 0.00,
            'payment_terms': self.payment_terms,
            'status': self.status,
            'pdf_file_path': self.pdf_file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relations:
            data['client'] = self.client.to_dict() if self.client else None
            data['user'] = self.user.to_dict() if self.user else None
            data['items'] = [item.to_dict(include_relations=True) for item in self.items] if self.items else []
        
        return data
    
    def __repr__(self):
        return f'<Proposal {self.id} - Client {self.client_id}>'


class ProposalItem(Base):
    """Modelo de item de proposta"""
    
    __tablename__ = 'proposal_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(Integer, ForeignKey('proposals.id', ondelete='CASCADE'), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    description = Column(Text)
    
    # Relacionamentos
    proposal = relationship('Proposal', back_populates='items')
    service = relationship('Service', backref='proposal_items')
    
    def __init__(self, proposal_id, service_id, price, description=None):
        self.proposal_id = proposal_id
        self.service_id = service_id
        self.price = price
        self.description = description
    
    def to_dict(self, include_relations=False):
        """Converte o objeto para dicionário"""
        data = {
            'id': self.id,
            'proposal_id': self.proposal_id,
            'service_id': self.service_id,
            'price': float(self.price) if self.price else 0.00,
            'description': self.description
        }
        
        if include_relations:
            data['service'] = self.service.to_dict() if self.service else None
        
        return data
    
    def __repr__(self):
        return f'<ProposalItem {self.id} - Proposal {self.proposal_id}>'
