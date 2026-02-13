from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class Project(Base):
    """Represents a project or active service contract for a client."""
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    deal_id = Column(Integer, ForeignKey('deals.id'), nullable=True, index=True) # Source of the sale
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    status = Column(String(50), default='active') # active, on_hold, completed, cancelled
    phase = Column(String(50), default='vendas') # vendas, financeiro, onboarding, execucao, manutencao
    financial_status = Column(String(50), default='pending') # pending, awaiting_finance, paid, approved
    
    contract_file_path = Column(String(500))
    signed_at = Column(DateTime)
    
    start_date = Column(Date)
    end_date = Column(Date) # Null for recurring
    
    billing_type = Column(String(20), default='recurring') # recurring, fixed
    billing_base_day = Column(Integer, default=10) # Day of the month for billing
    total_amount = Column(Numeric(12, 2), default=0) # Total value for fixed projects
    
    monthly_value = Column(Numeric(12, 2), default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    client = relationship('Client', back_populates='projects')
    company = relationship('Company')
    deal = relationship('Deal', back_populates='project', uselist=False)
    tickets = relationship('ProjectTicket', back_populates='project', cascade='all, delete-orphan')

class ProjectTicket(Base):
    """Internal tasks or steps for a specific project."""
    __tablename__ = 'project_tickets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    phase = Column(String(50)) # Phase where this ticket belongs
    status = Column(String(50), default='pending') # pending, in_progress, done, cancelled
    priority = Column(String(20), default='medium') # low, medium, high, urgent
    
    is_onboarding = Column(Boolean, default=False)
    
    due_date = Column(Date)
    assigned_to = Column(Integer, ForeignKey('users.id'), nullable=True) # Team member
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship('Project', back_populates='tickets')
    assignee = relationship('User')
