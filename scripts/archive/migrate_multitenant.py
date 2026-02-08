"""
PURETEGO CRM - Multi-Tenant Migration Script
Script para executar a migração para multi-tenancy
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import get_db, init_db
from app.models import Company, Role, User, KanbanStage, Client, DEFAULT_ROLES


def run_migration():
    """Executa a migração para multi-tenancy"""
    
    print("=" * 50)
    print("PURETEGO CRM - Multi-Tenant Migration")
    print("=" * 50)
    
    with get_db() as db:
        # 1. Criar roles padrão
        print("\n[1/5] Criando roles padrão...")
        for role_data in DEFAULT_ROLES:
            existing = db.query(Role).filter(Role.name == role_data['name']).first()
            if not existing:
                role = Role(**role_data)
                db.add(role)
                print(f"  [OK] Role '{role_data['name']}' criada")
            else:
                print(f"  - Role '{role_data['name']}' já existe")
        db.commit()
        
        # 2. Criar empresa padrão PureteGO
        print("\n[2/5] Criando empresa padrão PureteGO...")
        default_company = db.query(Company).filter(Company.slug == 'puretego').first()
        if not default_company:
            default_company = Company(
                name='PureteGO',
                slug='puretego',
                email='contacto@puretego.online',
                phone='+595 983 500 802'
            )
            db.add(default_company)
            db.commit()
            print(f"  [OK] Empresa 'PureteGO' criada com ID: {default_company.id}")
        else:
            print(f"  - Empresa 'PureteGO' já existe com ID: {default_company.id}")
        
        # 3. Migrar usuários existentes
        print("\n[3/5] Migrando usuários existentes...")
        owner_role = db.query(Role).filter(Role.name == 'owner').first()
        users_without_company = db.query(User).filter(User.company_id == None).all()
        
        for user in users_without_company:
            user.company_id = default_company.id
            user.role_id = owner_role.id if owner_role else None
            print(f"  [OK] Usuario '{user.email}' vinculado a PureteGO como Owner")
        
        if not users_without_company:
            print("  - Nenhum usuário para migrar")
        db.commit()
        
        # 4. Migrar clientes existentes
        print("\n[4/5] Migrando clientes existentes...")
        clients_without_company = db.query(Client).filter(Client.company_id == None).all()
        
        for client in clients_without_company:
            client.company_id = default_company.id
            print(f"  [OK] Cliente '{client.name}' vinculado a PureteGO")
        
        if not clients_without_company:
            print("  - Nenhum cliente para migrar")
        db.commit()
        
        # 5. Migrar kanban stages
        print("\n[5/5] Migrando etapas do Kanban...")
        stages_without_company = db.query(KanbanStage).filter(KanbanStage.company_id == None).all()
        
        for stage in stages_without_company:
            stage.company_id = default_company.id
            print(f"  [OK] Etapa '{stage.name}' vinculada a PureteGO")
        
        if not stages_without_company:
            print("  - Nenhuma etapa para migrar")
        db.commit()
        
        # Resumo
        print("\n" + "=" * 50)
        print("MIGRAÇÃO CONCLUÍDA!")
        print("=" * 50)
        
        total_users = db.query(User).count()
        total_clients = db.query(Client).count()
        total_companies = db.query(Company).count()
        total_roles = db.query(Role).count()
        
        print(f"\nResumo:")
        print(f"  - {total_companies} empresa(s)")
        print(f"  - {total_roles} role(s)")
        print(f"  - {total_users} usuário(s)")
        print(f"  - {total_clients} cliente(s)")
        print("\n")


if __name__ == '__main__':
    # Inicializa o banco (cria tabelas se não existirem)
    print("Inicializando banco de dados...")
    init_db()
    
    # Executa migração
    run_migration()
