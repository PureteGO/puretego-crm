"""
PURETEGO CRM - Company Model
Modelo de empresa (tenant) para multi-tenancy
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
from app.utils.saas_limits import PLAN_SOLO, get_plan_config

class Company(Base):
    """Modelo de empresa (tenant) - cada empresa tem seus próprios dados isolados"""
    
    __tablename__ = 'companies'
    
    # Available theme styles
    THEME_CHOICES = [
        ('tech-teal', 'Tech Teal', 'Moderno e tecnológico com verde-azulado'),
        ('corporate-blue', 'Corporate Blue', 'Profissional e corporativo'),
        ('innovation-purple', 'Innovation Purple', 'Inovador e criativo'),
        ('energetic-orange', 'Energetic Orange', 'Dinâmico e energético'),
        ('premium-red', 'Premium Red', 'Elegante e premium'),
        ('nature-green', 'Nature Green', 'Natural e sustentável'),
        ('maps2go-official', 'Maps2GO Official', 'Identidade visual oficial Maps2GO'),
    ]
    
    # Workflow Modes
    WORKFLOW_SOLO = 'solo'           # Consultor Solo
    WORKFLOW_LEAN = 'lean'           # Pequena Agência
    WORKFLOW_STRUCTURED = 'structured' # Agência Estruturada
    
    WORKFLOW_MODES = [
        (WORKFLOW_SOLO, 'Solo (Consultor)'),
        (WORKFLOW_LEAN, 'Lean (Pequena Agência)'),
        (WORKFLOW_STRUCTURED, 'Structured (Agência Completa)')
    ]
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(255))
    tax_id = Column(String(50)) # CNPJ, RUC, etc.
    address = Column(Text)
    logo_url = Column(String(500))
    theme_style = Column(String(50), default='tech-teal')  # Company's visual theme
    currency_symbol = Column(String(5), default='Gs') # Currency symbol (e.g., Gs, $, R$)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # SaaS Plan Configuration
    plan_tier = Column(String(50), default=PLAN_SOLO)
    plan_config = Column(JSON, nullable=True) # Overrides or cached config
    
    # Workflow Mode (solo, lean, structured)
    workflow_mode = Column(String(50), default=WORKFLOW_LEAN)
    
    # Commission Rates (Percentages)
    commission_closer_rate = Column(Numeric(5, 2), default=10.0)
    commission_sdr_rate = Column(Numeric(5, 2), default=2.0)
    
    # SMTP Configuration for outgoing emails
    smtp_server = Column(String(255), nullable=True)
    smtp_port = Column(Integer, default=587)
    smtp_use_tls = Column(Boolean, default=True)
    smtp_username = Column(String(255), nullable=True)
    smtp_password = Column(String(255), nullable=True)
    smtp_from_email = Column(String(255), nullable=True)
    smtp_from_name = Column(String(255), nullable=True)
    
    # Relationships
    users = relationship('User', back_populates='company', cascade='all, delete-orphan')
    clients = relationship('Client', back_populates='company', cascade='all, delete-orphan')
    kanban_stages = relationship('KanbanStage', back_populates='company', cascade='all, delete-orphan')
    google_connections = relationship('GoogleConnection', back_populates='company', cascade='all, delete-orphan')
    gmb_location_links = relationship('GMBLocationLink', back_populates='company', cascade='all, delete-orphan')
    
    # SaaS Package (Legacy relationship - keeping for reference if needed, but primary is plan_tier)
    # saas_package_id = Column(Integer, ForeignKey('saas_packages.id'), nullable=True)
    # saas_package = relationship('SaasPackage', back_populates='companies')
    
    def __init__(self, name, slug, email=None, phone=None, address=None, logo_url=None, theme_style='tech-teal', plan_tier=PLAN_SOLO, workflow_mode=WORKFLOW_LEAN):
        self.name = name
        self.slug = slug
        self.email = email
        self.phone = phone
        self.address = address
        self.logo_url = logo_url
        self.theme_style = theme_style
        self.plan_tier = plan_tier
        self.workflow_mode = workflow_mode
        self.plan_config = get_plan_config(plan_tier)
    
    def get_limit(self, limit_key):
        """
        Retorna o limite para um recurso específico baseada no plano.
        Ex: company.get_limit('max_users') -> 5
        """
        if not self.plan_config:
            self.plan_config = get_plan_config(self.plan_tier)
            
        return self.plan_config.get(limit_key, 0)

    def has_smtp_configured(self):
        """Verifica se a empresa tem SMTP configurado"""
        return bool(self.smtp_server and self.smtp_username and self.smtp_password)
    
    def get_smtp_config(self):
        """Retorna configuração SMTP da empresa"""
        if not self.has_smtp_configured():
            return None
        return {
            'server': self.smtp_server,
            'port': self.smtp_port or 587,
            'use_tls': self.smtp_use_tls,
            'username': self.smtp_username,
            'password': self.smtp_password,
            'from_email': self.smtp_from_email or self.smtp_username,
            'from_name': self.smtp_from_name or self.name
        }
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'email': self.email,
            'phone': self.phone,
            'website': self.website,
            'tax_id': self.tax_id,
            'address': self.address,
            'logo_url': self.logo_url,
            'theme_style': self.theme_style or 'tech-teal',
            'is_active': self.is_active,
            'has_smtp': self.has_smtp_configured(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'users_count': len(self.users) if self.users else 0,
            'clients_count': len(self.clients) if self.clients else 0,
            'workflow_mode': self.workflow_mode or self.WORKFLOW_LEAN
        }
    
    def __repr__(self):
        return f'<Company {self.name}>'
