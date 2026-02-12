"""
PURETEGO CRM - Service Package Model
Modelo de pacotes de serviços (Start2GO, Biz2GO, etc.)
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base

class ServicePackage(Base):
    __tablename__ = 'service_packages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True) # Temporarily nullable for migration
    name = Column(String(100), nullable=False)
    price = Column(Numeric(15, 2), nullable=False, default=0.00)
    description = Column(Text)
    html_description = Column(Text, nullable=True)
    features = Column(Text) # JSON or simple text list

    # Relationships
    company = relationship("Company")
    clients = relationship("Client", back_populates="interested_package")

    def __repr__(self):
        return f'<ServicePackage {self.name}>'
