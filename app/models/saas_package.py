"""
PURETEGO CRM - SaaS Package Model
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class SaasPackage(Base):
    """Modelo de pacote de serviço SaaS"""
    
    __tablename__ = 'saas_packages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, default=0.0)
    
    # Limits and Quotas
    max_users = Column(Integer, default=1)
    max_clients = Column(Integer, default=50)
    health_check_credits = Column(Integer, default=10) # Monthly or total credits? treating as limit for now.
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    # companies = relationship('Company', back_populates='saas_package')
    
    def __init__(self, name, description=None, price=0.0, max_users=1, max_clients=50, health_check_credits=10, is_active=True):
        self.name = name
        self.description = description
        self.price = price
        self.max_users = max_users
        self.max_clients = max_clients
        self.health_check_credits = health_check_credits
        self.is_active = is_active
        
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'max_users': self.max_users,
            'max_clients': self.max_clients,
            'health_check_credits': self.health_check_credits,
            'is_active': self.is_active
        }
