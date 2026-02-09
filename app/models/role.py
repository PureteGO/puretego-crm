"""
PURETEGO CRM - Role Model
Modelo de permissões e roles de usuário
"""

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from config.database import Base


class Role(Base):
    """Modelo de role/permissões para controle de acesso"""
    
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(String(255))
    
    # Permission flags
    can_manage_users = Column(Boolean, default=False)       # Criar/editar/deletar usuários
    can_manage_company = Column(Boolean, default=False)     # Editar dados da empresa
    can_view_all_clients = Column(Boolean, default=True)    # Ver todos os clientes da empresa
    can_edit_all_clients = Column(Boolean, default=True)    # Editar qualquer cliente
    can_delete_clients = Column(Boolean, default=False)     # Deletar clientes
    can_generate_proposals = Column(Boolean, default=True)  # Criar orçamentos
    can_view_reports = Column(Boolean, default=True)        # Ver relatórios
    can_export_data = Column(Boolean, default=False)        # Exportar dados
    
    # GMB & Operations specific permissions
    can_manage_gmb = Column(Boolean, default=False)         # Otimizar/Editar GMB Profile
    can_manage_healthchecks = Column(Boolean, default=False) # Criar/Rodar HealthChecks
    can_manage_tickets = Column(Boolean, default=True)      # Criar/Ver tickets operacionais
    can_manage_finance = Column(Boolean, default=False)     # Acesso ao módulo financeiro
    
    # Relationships
    users = relationship('User', back_populates='role')
    
    def __init__(self, name, display_name, description=None, **permissions):
        self.name = name
        self.display_name = display_name
        self.description = description
        
        # Set permissions from kwargs
        for perm, value in permissions.items():
            if hasattr(self, perm):
                setattr(self, perm, value)
    
    def get_permissions_dict(self):
        """Retorna dicionário com todas as permissões"""
        return {
            'can_manage_users': self.can_manage_users,
            'can_manage_company': self.can_manage_company,
            'can_view_all_clients': self.can_view_all_clients,
            'can_edit_all_clients': self.can_edit_all_clients,
            'can_delete_clients': self.can_delete_clients,
            'can_generate_proposals': self.can_generate_proposals,
            'can_view_reports': self.can_view_reports,
            'can_export_data': self.can_export_data,
            'can_manage_gmb': self.can_manage_gmb,
            'can_manage_healthchecks': self.can_manage_healthchecks,
            'can_manage_tickets': self.can_manage_tickets,
            'can_manage_finance': self.can_manage_finance
        }
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        data = {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description
        }
        data.update(self.get_permissions_dict())
        return data
    
    def __repr__(self):
        return f'<Role {self.name}>'


# Default roles configuration
DEFAULT_ROLES = [
    {
        'name': 'owner',
        'display_name': 'Proprietário',
        'description': 'Acesso total à empresa e gestão de usuários',
        'can_manage_users': True,
        'can_manage_company': True,
        'can_view_all_clients': True,
        'can_edit_all_clients': True,
        'can_delete_clients': True,
        'can_generate_proposals': True,
        'can_view_reports': True,
        'can_export_data': True,
        'can_manage_gmb': True,
        'can_manage_healthchecks': True,
        'can_manage_finance': True
    },
    {
        'name': 'manager',
        'display_name': 'Gerente',
        'description': 'Gerencia equipe e tem acesso total aos dados',
        'can_manage_users': True,
        'can_manage_company': False,
        'can_view_all_clients': True,
        'can_edit_all_clients': True,
        'can_delete_clients': True,
        'can_generate_proposals': True,
        'can_view_reports': True,
        'can_export_data': True,
        'can_manage_gmb': True,
        'can_manage_healthchecks': True,
        'can_manage_finance': True
    },
    {
        'name': 'sales',
        'display_name': 'Vendedor (Closer)',
        'description': 'Vendedor externo - vê todos os clientes, edita apenas os seus e fecha negócios',
        'can_manage_users': False,
        'can_manage_company': False,
        'can_view_all_clients': True,   # Vê todos clientes
        'can_edit_all_clients': False,  # Só edita seus
        'can_delete_clients': False,
        'can_generate_proposals': True,
        'can_view_reports': False,
        'can_export_data': False,
        'can_manage_finance': False
    },
    {
        'name': 'sdr',
        'display_name': 'SDR',
        'description': 'Sales Development - prospecção, qualificação e criação de oportunidades',
        'can_manage_users': False,
        'can_manage_company': False,
        'can_view_all_clients': True,
        'can_edit_all_clients': False,
        'can_delete_clients': False,
        'can_generate_proposals': False,
        'can_view_reports': False,
        'can_export_data': False,
        'can_manage_finance': False
    },
    {
        'name': 'traffic',
        'display_name': 'Gestor de Tráfego',
        'description': 'Responsável por campanhas e anúncios',
        'can_manage_users': False,
        'can_manage_company': False,
        'can_view_all_clients': True,
        'can_edit_all_clients': False,
        'can_delete_clients': False,
        'can_generate_proposals': False,
        'can_view_reports': True,
        'can_export_data': False,
        'can_manage_finance': False
    },
    {
        'name': 'creative',
        'display_name': 'Criativos',
        'description': 'Responsável por design e peças criativas',
        'can_manage_users': False,
        'can_manage_company': False,
        'can_view_all_clients': True,
        'can_edit_all_clients': False,
        'can_delete_clients': False,
        'can_generate_proposals': False,
        'can_view_reports': False,
        'can_export_data': False,
        'can_manage_finance': False
    },
    {
        'name': 'finance',
        'display_name': 'Admin/Financeiro',
        'description': 'Gestão de contratos e faturamento',
        'can_manage_users': False,
        'can_manage_company': False,
        'can_view_all_clients': True,
        'can_edit_all_clients': True,
        'can_delete_clients': False,
        'can_generate_proposals': True,
        'can_view_reports': True,
        'can_export_data': True,
        'can_manage_finance': True
    },
    {
        'name': 'gmb_manager',
        'display_name': 'Gestor de Perfil GMB',
        'description': 'Responsável por otimizar e manter continuamente o perfil Google Business Profile',
        'can_manage_users': False,
        'can_manage_company': False,
        'can_view_all_clients': True,
        'can_edit_all_clients': False, # Edit own (implementation logic in routes/models)
        'can_delete_clients': False,
        'can_generate_proposals': False,
        'can_view_reports': True,
        'can_export_data': False,
        'can_manage_gmb': True,
        'can_manage_healthchecks': True,
        'can_manage_tickets': True,
        'can_manage_finance': False
    },
    {
        'name': 'partner',
        'display_name': 'Sócio / Investidor',
        'description': 'Acesso total para sócios e investidores - Sem remuneração fixa ou comissões',
        'can_manage_users': True,
        'can_manage_company': True,
        'can_view_all_clients': True,
        'can_edit_all_clients': True,
        'can_delete_clients': True,
        'can_generate_proposals': True,
        'can_view_reports': True,
        'can_export_data': True,
        'can_manage_gmb': True,
        'can_manage_healthchecks': True,
        'can_manage_tickets': True,
        'can_manage_finance': True
    }
]
