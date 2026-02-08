"""
PURETEGO CRM - Email Templates Model
Modelos de e-mail personalizáveis por tenant
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class EmailTemplate(Base):
    """Template de e-mail personalizável por empresa"""
    __tablename__ = 'email_templates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True) # Null means global default
    
    code = Column(String(100), nullable=False, index=True) # proposal_send, invoice, etc.
    name = Column(String(255), nullable=False)
    area = Column(String(50), default='general') # sales, finance, general
    
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    
    locale = Column(String(10), default='es') # pt_BR, es, en
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship('Company')

    def __init__(self, code, name, subject, body, company_id=None, area='general', locale='es'):
        self.code = code
        self.name = name
        self.subject = subject
        self.body = body
        self.company_id = company_id
        self.area = area
        self.locale = locale

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'area': self.area,
            'subject': self.subject,
            'body': self.body,
            'company_id': self.company_id,
            'is_active': self.is_active
        }
