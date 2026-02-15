"""
PURETEGO CRM - Payment Plan Preset Model
Presets de planos de pagamento reutilizáveis
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class PaymentPlanPreset(Base):
    """Preset de plano de pagamento reutilizável (e.g. 50/30/20 em 3 parcelas)"""
    
    __tablename__ = 'payment_plan_presets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    
    name = Column(String(150), nullable=False)  # e.g. "3 Parcelas (50/30/20)"
    code = Column(String(50), nullable=False, index=True)  # e.g. "3_parcelas_50_30_20"
    
    # JSON array of installment rules
    # Example: [{"pct": 50, "days_after_sign": 0}, {"pct": 30, "days_after_sign": 30}, {"pct": 20, "days_after_sign": 60}]
    installments_config = Column(JSON, nullable=False)
    
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship('Company')
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'code': self.code,
            'installments_config': self.installments_config or [],
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_installment_count(self):
        """Retorna quantidade de parcelas"""
        return len(self.installments_config) if self.installments_config else 0
    
    def __repr__(self):
        return f'<PaymentPlanPreset {self.name}>'
