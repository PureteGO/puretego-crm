"""
PURETEGO CRM - Email Log Model
Registro de envios de e-mail por tenant
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class EmailLog(Base):
    """Log de e-mails enviados pelo sistema"""
    __tablename__ = 'email_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    
    email_type = Column(String(50), nullable=False) # invoice, proposal, etc.
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255))
    
    status = Column(String(50), default='sent') # sent, error
    error_message = Column(Text, nullable=True)
    
    # Reference to external entity (receivable_id, proposal_id)
    reference_id = Column(Integer, nullable=True)
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # Sender
    
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    company = relationship('Company')
    user = relationship('User')

    def __init__(self, company_id, email_type, recipient, subject=None, status='sent', reference_id=None, user_id=None, error_message=None):
        self.company_id = company_id
        self.email_type = email_type
        self.recipient = recipient
        self.subject = subject
        self.status = status
        self.reference_id = reference_id
        self.user_id = user_id
        self.error_message = error_message
