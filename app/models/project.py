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
    receivables = relationship('Receivable', back_populates='project', cascade='all, delete-orphan')
    notes = relationship('ProjectNote', back_populates='project', cascade='all, delete-orphan')

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
    assigned_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Verification workflow
    verification_required = Column(Boolean, default=False)
    approved_at = Column(DateTime)
    approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    rejection_comment = Column(Text)
    assigned_comment = Column(Text)
    
    completed_at = Column(DateTime)
    completed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship('Project', back_populates='tickets')
    assignee = relationship('User', foreign_keys=[assigned_to])
    assigned_by = relationship('User', foreign_keys=[assigned_by_id])
    approved_by = relationship('User', foreign_keys=[approved_by_id])
    completer = relationship('User', foreign_keys=[completed_by])

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'assignee': self.assignee.name if self.assignee else None,
            'assigned_by_id': self.assigned_by_id,
            'verification_required': self.verification_required,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejection_comment': self.rejection_comment,
            'assigned_comment': self.assigned_comment,
            'completer': self.completer.name if self.completer else None
        }
