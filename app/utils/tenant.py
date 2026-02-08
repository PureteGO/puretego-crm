"""
PURETEGO CRM - Tenant Utilities
Funções utilitárias para isolamento de dados por tenant (empresa)
"""

from flask import session


def get_company_id():
    """
    Obtém o company_id da sessão atual.
    Retorna None se não houver empresa na sessão ou se for superadmin.
    """
    # Superadmins podem ver todos os dados
    if session.get('is_superadmin', False):
        return None
    return session.get('company_id')


def is_superadmin():
    """Verifica se o usuário atual é superadmin PureteGO"""
    return session.get('is_superadmin', False)


def filter_by_company(query, model):
    """
    Adiciona filtro de company_id a uma query SQLAlchemy.
    Superadmins não são filtrados (veem todos os dados).
    
    Args:
        query: Query SQLAlchemy
        model: Modelo que possui o campo company_id
        
    Returns:
        Query filtrada pelo company_id da sessão (ou sem filtro para superadmin)
        
    Uso:
        clients = filter_by_company(db.query(Client), Client).all()
    """
    # Superadmins veem tudo
    if is_superadmin():
        return query
    
    company_id = session.get('company_id')
    if company_id and hasattr(model, 'company_id'):
        return query.filter(model.company_id == company_id)
    return query


def filter_by_owner_or_company(query, model, user_id=None):
    """
    Filtra por owner_id (para vendedores) ou company_id (para admins).
    Usado quando role.can_view_all_clients é False.
    
    Args:
        query: Query SQLAlchemy
        model: Modelo com company_id e owner_id
        user_id: ID do usuário (se None, usa sessão)
        
    Returns:
        Query filtrada
    """
    from sqlalchemy import or_
    
    company_id = get_company_id()
    if user_id is None:
        user_id = session.get('user_id')
    
    if company_id and hasattr(model, 'company_id') and hasattr(model, 'owner_id'):
        # Filtrar por empresa E (owner ou sem owner)
        return query.filter(
            model.company_id == company_id,
            or_(
                model.owner_id == user_id,
                model.owner_id == None  # Clientes sem owner são visíveis
            )
        )
    
    return query


def set_tenant_context(client, user=None):
    """
    Define o contexto de tenant para um novo registro.
    
    Args:
        client: Objeto Client (ou qualquer modelo com company_id)
        user: Usuário atual (opcional, usa sessão se não fornecido)
    """
    company_id = get_company_id()
    user_id = session.get('user_id') if user is None else user.id
    
    if hasattr(client, 'company_id') and client.company_id is None:
        client.company_id = company_id
    
    if hasattr(client, 'owner_id') and client.owner_id is None:
        client.owner_id = user_id
