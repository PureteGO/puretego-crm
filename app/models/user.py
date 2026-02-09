"""
PURETEGO CRM - User Model
Modelo de usuário do sistema com suporte multi-tenant
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
import bcrypt
import secrets
from datetime import datetime, timedelta


class User(Base):
    """Modelo de usuário para autenticação e controle de acesso multi-tenant"""
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Multi-tenant fields
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    is_superadmin = Column(Boolean, default=False, index=True)
    
    # Financial fields
    base_salary = Column(Numeric(10, 2), default=0.0)
    receives_commission = Column(Boolean, default=True)
    
    # Password reset fields
    reset_token = Column(String(100), nullable=True, index=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # Relationships
    company = relationship('Company', back_populates='users')
    role = relationship('Role', back_populates='users')
    interactions = relationship('Interaction', back_populates='user')
    owned_clients = relationship('Client', foreign_keys='Client.owner_id', back_populates='owner')
    
    def __init__(self, name, email, password, company_id=None, role_id=None, base_salary=0.0, receives_commission=True):
        self.name = name
        self.email = email
        self.set_password(password)
        self.company_id = company_id
        self.role_id = role_id
        self.base_salary = base_salary
        self.receives_commission = receives_commission
    
    def set_password(self, password):
        """Criptografa e define a senha do usuário"""
        salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        """Verifica se a senha fornecida está correta"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
    def generate_reset_token(self, expires_hours=24):
        """Gera um token seguro para reset de senha"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=expires_hours)
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verifica se o token de reset é válido"""
        if not self.reset_token or not self.reset_token_expires:
            return False
        if self.reset_token != token:
            return False
        if datetime.utcnow() > self.reset_token_expires:
            return False
        return True
    
    def clear_reset_token(self):
        """Limpa o token de reset após uso"""
        self.reset_token = None
        self.reset_token_expires = None
    
    def has_permission(self, permission):
        """Verifica se o usuário tem determinada permissão"""
        if not self.role:
            return False
        return getattr(self.role, permission, False)
    
    def can_view_client(self, client):
        """Verifica se o usuário pode ver determinado cliente"""
        if self.is_superadmin:
            return True
        if not self.role:
            return False
        # Owner, Manager, Admin, GMB Manager podem ver todos
        if self.role.can_view_all_clients or self.role.name == 'gmb_manager':
            return True
        # Sales/SDR só veem seus próprios clientes
        return client.owner_id == self.id
    
    def can_edit_client(self, client):
        """Verifica se o usuário pode editar determinado cliente"""
        if self.is_superadmin:
            return True
        if not self.role:
            return False
        if self.role.can_edit_all_clients:
            return True
        return client.owner_id == self.id

    def can_manage_gmb_for(self, client):
        """Verifica se o usuário pode gerenciar o GMB (editar/vincular) de um cliente"""
        if self.is_superadmin:
            return True
        if not self.role or not getattr(self.role, 'can_manage_gmb', False):
            return False
        # Se puder editar todos, pode gerenciar GMB de todos
        if self.role.can_edit_all_clients:
            return True
        # Se for GMB Manager, só pode gerenciar os que "somente dele" (owner_id)
        # Se for Sales, também só os dele.
        return client.owner_id == self.id

    def can_manage_healthcheck_for(self, client):
        """Verifica se o usuário pode gerenciar healthchecks de um cliente"""
        if self.is_superadmin:
            return True
        if not self.role or not getattr(self.role, 'can_manage_healthchecks', False):
            return False
        # GMB Manager pode rodar para QUALQUER cliente
        if self.role.name == 'gmb_manager':
            return True
        if self.role.can_edit_all_clients:
            return True
        return client.owner_id == self.id

    def can_manage_tickets(self):
        """Verifica se o usuário tem permissão básica de tickets"""
        if not self.role:
            return False
        return getattr(self.role, 'can_manage_tickets', True)
    
    def to_dict(self, include_relations=False):
        """Converte o objeto para dicionário"""
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'is_active': self.is_active,
            'is_superadmin': self.is_superadmin,
            'company_id': self.company_id,
            'role_id': self.role_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relations:
            data['company_name'] = self.company.name if self.company else None
            data['role_name'] = self.role.display_name if self.role else None
            data['permissions'] = self.role.get_permissions_dict() if self.role else {}
        
        return data
    
    def __repr__(self):
        return f'<User {self.email}>'
