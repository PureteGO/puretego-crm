"""
PURETEGO CRM - Quote Option Model
Opções de proposta (permite comparação A/B entre planos)
"""

from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class QuoteOption(Base):
    """Uma opção dentro de uma proposta (e.g. Opção A: Start2GO, Opção B: Biz2GO)"""
    
    __tablename__ = 'quote_options'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(Integer, ForeignKey('proposals.id', ondelete='CASCADE'), nullable=False, index=True)
    
    name = Column(String(150), nullable=False)  # e.g. "Opción A — Start2GO"
    is_default = Column(Boolean, default=False)
    
    preset_id = Column(Integer, ForeignKey('payment_plan_presets.id', ondelete='SET NULL'), nullable=True)
    
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    proposal = relationship('Proposal', back_populates='options')
    preset = relationship('PaymentPlanPreset')
    items = relationship('QuoteItem', back_populates='option', cascade='all, delete-orphan', order_by='QuoteItem.sort_order')
    
    def calculate_total(self):
        """Calcula o total baseado nos itens"""
        if self.items:
            self.total_amount = sum(
                (item.total or 0) for item in self.items
            )
        return self.total_amount
    
    def get_recurring_total(self):
        """Retorna o total mensal recorrente"""
        if not self.items:
            return 0
        return sum(
            float(item.total or 0) for item in self.items 
            if item.billing_type == 'recurring'
        )
    
    def get_onetime_total(self):
        """Retorna o total de itens únicos"""
        if not self.items:
            return 0
        return sum(
            float(item.total or 0) for item in self.items 
            if item.billing_type == 'one_time'
        )
    
    def to_dict(self, include_items=False):
        """Converte o objeto para dicionário"""
        data = {
            'id': self.id,
            'proposal_id': self.proposal_id,
            'name': self.name,
            'is_default': self.is_default,
            'preset_id': self.preset_id,
            'total_amount': float(self.total_amount) if self.total_amount else 0.00,
            'recurring_total': self.get_recurring_total(),
            'onetime_total': self.get_onetime_total(),
            'sort_order': self.sort_order,
            'items_count': len(self.items) if self.items else 0
        }
        
        if include_items:
            data['items'] = [item.to_dict() for item in self.items] if self.items else []
            data['preset'] = self.preset.to_dict() if self.preset else None
        
        return data
    
    def __repr__(self):
        return f'<QuoteOption {self.name} — {self.total_amount}>'
