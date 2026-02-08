"""
Script para semear dados da 'Agência Demo' para testes e demonstrações.
"""
import os
from datetime import datetime, timedelta
from config.database import get_db, Base, engine
from app.models import (
    Company, User, Role, Client, Deal, KanbanStage, 
    Interaction, InteractionType, ServicePackage, Proposal,
    Receivable, Project, Task, DealStatus
)

def seed_demo():
    with get_db() as db:
        # 1. Garantir Etapas do Kanban
        stages = [
            ('Novo Lead', 1), ('Primeiro Contato', 2), ('Agendado', 3), 
            ('Reunião Realizada', 4), ('Proposta Enviada', 5), 
            ('Negociação', 6), ('Fechado - Ganho', 7), ('Fechado - Perdido', 8)
        ]
        db_stages = {}
        for name, order in stages:
            stage = db.query(KanbanStage).filter(KanbanStage.name == name).first()
            if not stage:
                stage = KanbanStage(name=name, order=order)
                db.add(stage)
                db.flush()
            db_stages[name] = stage

        # 2. Criar Empresa Demo
        demo_company = db.query(Company).filter(Company.name == 'Agência Demo').first()
        if not demo_company:
            demo_company = Company(
                name='Agência Demo',
                slug='demo',
                workflow_mode='lean',
                email='demo@maps2go.online',
                phone='(11) 99999-9999',
                address='Rua Demo, 123',
                plan_tier='puretego'
            )
            demo_company.currency_symbol = 'R$'
            demo_company.commission_closer_rate = 10
            demo_company.commission_sdr_rate = 2
            db.add(demo_company)
            db.flush()
        
        # 3. Criar Usuários
        roles = {r.name: r.id for r in db.query(Role).all()}
        users_data = [
            ('demo_owner', 'Owner Demo', 'owner'),
            ('demo_sdr', 'SDR Demo', 'sdr'),
            ('demo_sales', 'Vendedor Demo', 'sales'),
            ('demo_finance', 'Financeiro Demo', 'finance'),
            ('demo_gmb', 'GMB Manager Demo', 'gmb_manager')
        ]
        
        demo_users = {}
        for username, name, role_name in users_data:
            email = f'{username}@maps2go.online'
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    name=name,
                    email=email,
                    password='demo123',
                    role_id=roles[role_name],
                    company_id=demo_company.id
                )
                user.receives_commission = True
                db.add(user)
                db.flush()
            demo_users[role_name] = user

        # 4. Criar Clientes e Deals
        clients_data = [
            ('Pizzaria do Bairro', 'Novo Lead', 'demo_sdr'),
            ('Odonto Clean', 'Agendado', 'demo_sdr'),
            ('Auto Mecânica Silva', 'Proposta Enviada', 'demo_sales'),
            ('Restaurante Sabor', 'Fechado - Ganho', 'demo_sales')
        ]

        for client_name, stage_name, owner_username in clients_data:
            owner_email = f'{owner_username}@maps2go.online'
            owner = db.query(User).filter(User.email == owner_email).first()
            client = db.query(Client).filter(Client.name == client_name, Client.company_id == demo_company.id).first()
            if not client:
                client = Client(
                    name=client_name,
                    company_id=demo_company.id,
                    owner_id=owner.id,
                    kanban_stage_id=db_stages[stage_name].id,
                    phone='(11) 99999-9999',
                    address='Rua Demo, 123'
                )
                db.add(client)
                db.flush()
                
                # Criar Deal
                deal = Deal(
                    title=f'GMB Optimization - {client_name}',
                    client_id=client.id,
                    company_id=demo_company.id,
                    owner_id=owner.id,
                    kanban_stage_id=client.kanban_stage_id,
                    value=1500 if stage_name == 'Fechado - Ganho' else 0
                )
                deal.status = DealStatus.WON if stage_name == 'Fechado - Ganho' else DealStatus.OPEN
                db.add(deal)
                db.flush()

                # Se for "Fechado - Ganho", criar projeto e financeiro
                if stage_name == 'Fechado - Ganho':
                    project = Project(
                        client_id=client.id,
                        company_id=demo_company.id,
                        name=f'Projeto GMB: {client_name}',
                        status='active',
                        phase='onboarding'
                    )
                    db.add(project)
                    db.flush()
                    
                    receivable = Receivable(
                        company_id=demo_company.id,
                        client_id=client.id,
                        deal_id=deal.id,
                        project_id=project.id,
                        description='Parcela 01/01',
                        amount=1500,
                        due_date=datetime.utcnow().date() + timedelta(days=5),
                        status='open'
                    )
                    db.add(receivable)
                    
                    # Tarefa para o GMB Manager
                    task = Task(
                        company_id=demo_company.id,
                        title=f'Onboarding GMB: {client_name}',
                        description='Iniciar checklist de verificação e fotos.',
                        status='pending',
                        type='gmb_onboarding',
                        role_target='gmb_manager',
                        client_id=client.id,
                        project_id=project.id,
                        due_date=datetime.utcnow() + timedelta(days=3)
                    )
                    db.add(task)

        # 5. Criar Super Admin (as requested)
        super_admin_email = 'support@maps2go.online'
        super_admin = db.query(User).filter(User.email == super_admin_email).first()
        if not super_admin:
            print(f"Criando Super Admin: {super_admin_email}...")
            super_admin = User(
                name='Maps2GO Support',
                email=super_admin_email,
                password='MeLu_1723$',
                role_id=roles['owner'],
                company_id=demo_company.id
            )
            super_admin.is_superadmin = True
            db.add(super_admin)
            db.flush()

        db.commit()
        print("✅ Dados da 'Agência Demo' semeados com sucesso!")

if __name__ == "__main__":
    seed_demo()
