"""
PURETEGO CRM - Proposal Model (v2)
Modelo de proposta/orçamento com suporte a templates, opções e planos de pagamento
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, Date, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Proposal(Base):
    """Modelo de proposta/orçamento para cliente — v2 com opções e templates"""
    
    __tablename__ = 'proposals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Tenant isolation
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # Core references
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    deal_id = Column(Integer, ForeignKey('deals.id', ondelete='SET NULL'), nullable=True, index=True)
    template_id = Column(Integer, ForeignKey('proposal_templates.id', ondelete='SET NULL'), nullable=True)
    
    # Proposal metadata
    title = Column(String(255), nullable=True)  # e.g. "Propuesta Comercial — Start2GO"
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    currency = Column(String(5), default='Gs')
    
    # Dates
    issue_date = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    
    # Status: draft, sent, approved, rejected, expired
    status = Column(String(50), nullable=False, default='draft', index=True)
    
    # Language for PDF generation: 'es', 'pt', 'en'
    language = Column(String(5), default='es')
    
    # Free-form JSON for custom notes, terms, etc.
    # Example: {"notes": "...", "terms": "...", "custom_sections": [...]}
    notes_json = Column(JSON, nullable=True)
    
    # Legacy field kept for backward compat during migration
    payment_terms = Column(Text, nullable=True)
    
    pdf_file_path = Column(String(255))
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship('Company')
    client = relationship('Client', back_populates='proposals')
    user = relationship('User', backref='proposals')
    deal = relationship('Deal')
    template = relationship('ProposalTemplate', back_populates='proposals')
    options = relationship('QuoteOption', back_populates='proposal', cascade='all, delete-orphan', order_by='QuoteOption.sort_order')
    
    # Legacy — kept for migration, will be removed after data migration
    items = relationship('ProposalItem', back_populates='proposal', cascade='all, delete-orphan')
    
    def __init__(self, client_id, user_id, company_id=None, total_amount=0.00, 
                 status='draft', title=None, currency='Gs', language='es',
                 deal_id=None, template_id=None, payment_terms=None):
        self.client_id = client_id
        self.user_id = user_id
        self.company_id = company_id
        self.total_amount = total_amount
        self.status = status
        self.title = title
        self.currency = currency
        self.language = language
        self.deal_id = deal_id
        self.template_id = template_id
        self.payment_terms = payment_terms
    
    def calculate_total(self):
        """Calcula o total baseado na opção padrão ou primeira opção"""
        if self.options:
            default_opt = next((o for o in self.options if o.is_default), self.options[0])
            default_opt.calculate_total()
            self.total_amount = default_opt.total_amount
        elif self.items:
            # Legacy fallback
            self.total_amount = sum(item.price for item in self.items)
        return self.total_amount
    
    def get_default_option(self):
        """Retorna a opção marcada como padrão, ou a primeira"""
        if not self.options:
            return None
        return next((o for o in self.options if o.is_default), self.options[0])
    
    def get_notes(self, key=None):
        """Retorna notas do JSON, ou valor específico por chave"""
        data = self.notes_json or {}
        if key:
            return data.get(key)
        return data
    
    def set_note(self, key, value):
        """Define uma nota no JSON"""
        if not self.notes_json:
            self.notes_json = {}
        self.notes_json[key] = value
    
    def to_dict(self, include_relations=False):
        """Converte o objeto para dicionário"""
        data = {
            'id': self.id,
            'company_id': self.company_id,
            'client_id': self.client_id,
            'user_id': self.user_id,
            'deal_id': self.deal_id,
            'template_id': self.template_id,
            'title': self.title,
            'total_amount': float(self.total_amount) if self.total_amount else 0.00,
            'currency': self.currency,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'status': self.status,
            'language': self.language,
            'payment_terms': self.payment_terms,
            'pdf_file_path': self.pdf_file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relations:
            data['client'] = self.client.to_dict() if self.client else None
            data['user'] = self.user.to_dict() if self.user else None
            data['options'] = [opt.to_dict(include_items=True) for opt in self.options] if self.options else []
            data['template'] = self.template.to_dict() if self.template else None
            # Legacy
            data['items'] = [item.to_dict(include_relations=True) for item in self.items] if self.items else []
        
        return data
    
    def __repr__(self):
        return f'<Proposal {self.id} - Client {self.client_id}>'


class ProposalItem(Base):
    """Modelo LEGACY de item de proposta — mantido para migração"""
    
    __tablename__ = 'proposal_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(Integer, ForeignKey('proposals.id', ondelete='CASCADE'), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    description = Column(Text)
    
    # Relationships
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
