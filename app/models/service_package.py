"""
PURETEGO CRM - Service Package Model
Modelo de pacotes de serviços (Start2GO, Biz2GO, etc.)
"""

from sqlalchemy import Column, Integer, String, Text, Numeric
from sqlalchemy.orm import relationship
from config.database import Base

class ServicePackage(Base):
    __tablename__ = 'service_packages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    price = Column(Numeric(15, 2), nullable=False, default=0.00)
    description = Column(Text)
    features = Column(Text) # JSON or simple text list

    # Relationships
    clients = relationship("Client", back_populates="interested_package")

    def __repr__(self):
        return f'<ServicePackage {self.name}>'
