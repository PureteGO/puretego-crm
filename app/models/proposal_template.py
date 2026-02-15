"""
PURETEGO CRM - Proposal Template Model
Templates de proposta com layouts configuráveis por tenant
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class ProposalTemplate(Base):
    """Template reutilizável para gerar propostas com layouts diferentes"""
    
    __tablename__ = 'proposal_templates'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=True, index=True)  # NULL = global
    
    name = Column(String(150), nullable=False)
    code = Column(String(50), nullable=False, index=True)  # e.g. 'long_premium', 'short_express'
    type = Column(String(20), nullable=False, default='long')  # 'long' or 'short'
    
    # JSON layout config: sections order, visibility, custom blocks
    # Example: {"sections": ["header", "audit", "services", "payment", "footer"], "show_audit": true}
    layout_config = Column(JSON, nullable=True)
    
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship('Company')
    proposals = relationship('Proposal', back_populates='template')
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'code': self.code,
            'type': self.type,
            'layout_config': self.layout_config or {},
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ProposalTemplate {self.name} ({self.code})>'
