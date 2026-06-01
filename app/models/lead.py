"""
PURETEGO CRM - Lead Model for Prospecting
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
from datetime import datetime

class Lead(Base):
    """Modelo para empresas potenciais em prospecção inicial"""
    
    __tablename__ = 'leads'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False, index=True)
    
    # Origem do Lead: visita em campo (field_visit), redes sociais (social_media), 
    # Google Maps (google_maps), indicação (referral), outro (other)
    source = Column(String(100), default='field_visit') 
    
    maps_link = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    neighborhood = Column(String(100), nullable=True) # Bairro/Região
    
    # Qualificação: cold, warm, hot
    qualification = Column(String(50), default='cold') 
    
    business_health = Column(Text, nullable=True) # Saúde do Cliente / Perfil Digital
    
    # Forma de Prospecção: visita de abertura (opening_visit), chamada telefônica (phone_call), 
    # WhatsApp (whatsapp), e-mail (email), outro (other)
    prospecting_method = Column(String(100), default='phone_call')
    
    # Status: new (Novo), analyzing (Em análise), qualified (Qualificado), 
    # contacting (Em contato), converted (Convertido), lost (Perdido)
    status = Column(String(50), default='new', index=True)
    
    observations = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Multi-tenant fields
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True) # Vendedor responsável
    
    # Relationships
    company = relationship('Company', backref='leads')
    owner = relationship('User', foreign_keys=[owner_id], backref='owned_leads')
    activities = relationship('LeadActivity', back_populates='lead', cascade='all, delete-orphan')

    def __init__(self, company_name, company_id=None, owner_id=None, source='field_visit',
                 maps_link=None, address=None, city=None, neighborhood=None,
                 qualification='cold', business_health=None, prospecting_method='phone_call',
                 status='new', observations=None):
        self.company_name = company_name
        self.company_id = company_id
        self.owner_id = owner_id
        self.source = source
        self.maps_link = maps_link
        self.address = address
        self.city = city
        self.neighborhood = neighborhood
        self.qualification = qualification
        self.business_health = business_health
        self.prospecting_method = prospecting_method
        self.status = status
        self.observations = observations

    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'source': self.source,
            'maps_link': self.maps_link,
            'address': self.address,
            'city': self.city,
            'neighborhood': self.neighborhood,
            'qualification': self.qualification,
            'business_health': self.business_health,
            'prospecting_method': self.prospecting_method,
            'status': self.status,
            'observations': self.observations,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'company_id': self.company_id,
            'owner_id': self.owner_id
        }

    def __repr__(self):
        return f'<Lead {self.company_name} [{self.status}]>'
