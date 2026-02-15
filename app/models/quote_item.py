"""
PURETEGO CRM - Quote Item Model
Itens individuais dentro de uma opção de proposta
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class QuoteItem(Base):
    """Linha de serviço dentro de uma opção de proposta"""
    
    __tablename__ = 'quote_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    option_id = Column(Integer, ForeignKey('quote_options.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Source: either a service_package OR a standalone service
    service_package_id = Column(Integer, ForeignKey('service_packages.id', ondelete='SET NULL'), nullable=True)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='SET NULL'), nullable=True)
    
    description = Column(Text)  # Override or custom description
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0.00)
    discount_pct = Column(Numeric(5, 2), nullable=False, default=0.00)
    total = Column(Numeric(12, 2), nullable=False, default=0.00)
    
    # Billing: 'one_time' (setup, implementation) or 'recurring' (monthly service)
    billing_type = Column(String(20), nullable=False, default='one_time')
    
    # Tag: 'principal' (core service), 'optional' (add-on), 'gift' (free bonus)
    tag = Column(String(20), nullable=False, default='principal')
    
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    option = relationship('QuoteOption', back_populates='items')
    service_package = relationship('ServicePackage')
    service = relationship('Service')
    
    def calculate_total(self):
        """Calcula total considerando quantidade e desconto"""
        subtotal = float(self.quantity or 1) * float(self.unit_price or 0)
        discount = subtotal * (float(self.discount_pct or 0) / 100)
        self.total = round(subtotal - discount, 2)
        return self.total
    
    def get_display_name(self):
        """Retorna nome para exibição (do pacote, serviço ou descrição)"""
        if self.service_package:
            return self.service_package.name
        if self.service:
            return self.service.name
        return self.description or 'Item sem nome'
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'option_id': self.option_id,
            'service_package_id': self.service_package_id,
            'service_id': self.service_id,
            'display_name': self.get_display_name(),
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price) if self.unit_price else 0.00,
            'discount_pct': float(self.discount_pct) if self.discount_pct else 0.00,
            'total': float(self.total) if self.total else 0.00,
            'billing_type': self.billing_type,
            'tag': self.tag,
            'sort_order': self.sort_order
        }
    
    def __repr__(self):
        return f'<QuoteItem {self.get_display_name()} — {self.total}>'
