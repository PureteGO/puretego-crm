"""
PURETEGO CRM - Client Model
Modelo de cliente com suporte multi-tenant
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Client(Base):
    """Modelo de cliente prospectado - isolado por empresa"""
    
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    gmb_profile_name = Column(String(255))
    contact_name = Column(String(255))
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))
    address = Column(Text)
    kanban_stage_id = Column(Integer, ForeignKey('kanban_stages.id', ondelete='SET NULL'), index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, index=True, nullable=False, server_default=text('1'))

    # Multi-tenant fields
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)  # nullable for migration
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)  # Vendedor responsável
    
    # Relacionamentos
    company = relationship('Company', back_populates='clients')
    owner = relationship('User', foreign_keys=[owner_id], back_populates='owned_clients')
    kanban_stage = relationship('KanbanStage', backref='clients')
    visits = relationship('Visit', back_populates='client', cascade='all, delete-orphan')
    health_checks = relationship('HealthCheck', back_populates='client', cascade='all, delete-orphan')
    proposals = relationship('Proposal', back_populates='client', cascade='all, delete-orphan')
    interactions = relationship('Interaction', back_populates='client', cascade='all, delete-orphan')
    deals = relationship('Deal', back_populates='client', cascade='all, delete-orphan')
    gmb_location_links = relationship('GMBLocationLink', back_populates='client', cascade='all, delete-orphan')
    rankings = relationship('KeywordRanking', back_populates='client', cascade='all, delete-orphan')
    projects = relationship('Project', back_populates='client', cascade='all, delete-orphan')
    
    # Detailed Info Fields
    receptionist_name = Column(String(255))
    decision_maker_name = Column(String(255))
    decision_factors = Column(Text)
    best_contact_time = Column(String(100))
    preferred_contact_method = Column(String(100))
    observations = Column(Text)
    
    # New Package Relationship
    interested_package_id = Column(Integer, ForeignKey('service_packages.id', ondelete='SET NULL'), nullable=True)
    interested_package = relationship("ServicePackage", back_populates="clients")
    
    def __init__(self, name, company_id=None, owner_id=None, gmb_profile_name=None, contact_name=None, 
                 phone=None, email=None, website=None, address=None, kanban_stage_id=None,
                 receptionist_name=None, decision_maker_name=None,
                 decision_factors=None, best_contact_time=None,
                 preferred_contact_method=None, observations=None):
        self.name = name
        self.company_id = company_id
        self.owner_id = owner_id
        self.gmb_profile_name = gmb_profile_name
        self.contact_name = contact_name
        self.phone = phone
        self.email = email
        self.website = website
        self.address = address
        self.kanban_stage_id = kanban_stage_id
        
        # Detailed info fields
        self.receptionist_name = receptionist_name
        self.decision_maker_name = decision_maker_name
        self.decision_factors = decision_factors
        self.best_contact_time = best_contact_time
        self.preferred_contact_method = preferred_contact_method
        self.observations = observations
    
    def to_dict(self, include_relations=False):
        """Converte o objeto para dicionário"""
        data = {
            'id': self.id,
            'name': self.name,
            'company_id': self.company_id,
            'owner_id': self.owner_id,
            'gmb_profile_name': self.gmb_profile_name,
            'contact_name': self.contact_name,
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
            'address': self.address,
            'kanban_stage_id': self.kanban_stage_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # Detailed info fields
            'receptionist_name': self.receptionist_name,
            'decision_maker_name': self.decision_maker_name,
            'decision_factors': self.decision_factors,
            'best_contact_time': self.best_contact_time,
            'preferred_contact_method': self.preferred_contact_method,
            'observations': self.observations
        }
        
        if include_relations:
            data['kanban_stage'] = self.kanban_stage.to_dict() if self.kanban_stage else None
            data['visits_count'] = len(self.visits) if self.visits else 0
            data['health_checks_count'] = len(self.health_checks) if self.health_checks else 0
            data['proposals_count'] = len(self.proposals) if self.proposals else 0
        
        return data
    
    def get_primary_gmb_link(self):
        """Returns the primary GMB location link or the first one if none is primary."""
        if not self.gmb_location_links:
            return None
        
        # Try to find primary
        for link in self.gmb_location_links:
            if link.is_primary:
                return link
        
        # Fallback to first
        return self.gmb_location_links[0]

    def __repr__(self):
        return f'<Client {self.name}>'
