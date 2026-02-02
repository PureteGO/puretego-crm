"""
PURETEGO CRM - Client Model
Modelo de cliente
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Client(Base):
    """Modelo de cliente prospectado"""
    
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    gmb_profile_name = Column(String(255))
    contact_name = Column(String(255))
    phone = Column(String(50))
    email = Column(String(255))
    address = Column(Text)
    kanban_stage_id = Column(Integer, ForeignKey('kanban_stages.id', ondelete='SET NULL'), index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    kanban_stage = relationship('KanbanStage', backref='clients')
    visits = relationship('Visit', back_populates='client', cascade='all, delete-orphan')
    health_checks = relationship('HealthCheck', back_populates='client', cascade='all, delete-orphan')
    proposals = relationship('Proposal', back_populates='client', cascade='all, delete-orphan')
    
    def __init__(self, name, gmb_profile_name=None, contact_name=None, 
                 phone=None, email=None, address=None, kanban_stage_id=None):
        self.name = name
        self.gmb_profile_name = gmb_profile_name
        self.contact_name = contact_name
        self.phone = phone
        self.email = email
        self.address = address
        self.kanban_stage_id = kanban_stage_id
    
    def to_dict(self, include_relations=False):
        """Converte o objeto para dicionário"""
        data = {
            'id': self.id,
            'name': self.name,
            'gmb_profile_name': self.gmb_profile_name,
            'contact_name': self.contact_name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'kanban_stage_id': self.kanban_stage_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relations:
            data['kanban_stage'] = self.kanban_stage.to_dict() if self.kanban_stage else None
            data['visits_count'] = len(self.visits) if self.visits else 0
            data['health_checks_count'] = len(self.health_checks) if self.health_checks else 0
            data['proposals_count'] = len(self.proposals) if self.proposals else 0
        
        return data
    
    def __repr__(self):
        return f'<Client {self.name}>'
