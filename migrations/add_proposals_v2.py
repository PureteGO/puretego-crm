"""
PURETEGO CRM — Migration: Proposals v2
Adiciona novas colunas à tabela proposals e cria tabelas para templates, opções, itens e presets.
Executa com: python migrations/add_proposals_v2.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import get_db, engine
from sqlalchemy import text


def run_migration():
    """Executa a migração de Proposals v2"""
    
    with engine.connect() as conn:
        # ============================
        # 1. ALTER proposals table
        # ============================
        alter_columns = {
            'company_id': "ALTER TABLE proposals ADD COLUMN company_id INT NULL, ADD CONSTRAINT fk_proposals_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE",
            'deal_id': "ALTER TABLE proposals ADD COLUMN deal_id INT NULL, ADD CONSTRAINT fk_proposals_deal FOREIGN KEY (deal_id) REFERENCES deals(id) ON DELETE SET NULL",
            'template_id': "ALTER TABLE proposals ADD COLUMN template_id INT NULL",
            'title': "ALTER TABLE proposals ADD COLUMN title VARCHAR(255) NULL",
            'currency': "ALTER TABLE proposals ADD COLUMN currency VARCHAR(5) DEFAULT 'Gs'",
            'issue_date': "ALTER TABLE proposals ADD COLUMN issue_date DATE NULL",
            'valid_until': "ALTER TABLE proposals ADD COLUMN valid_until DATE NULL",
            'language': "ALTER TABLE proposals ADD COLUMN language VARCHAR(5) DEFAULT 'es'",
            'notes_json': "ALTER TABLE proposals ADD COLUMN notes_json JSON NULL",
        }
        
        for col_name, sql in alter_columns.items():
            try:
                conn.execute(text(sql))
                print(f"  ✓ Added column: proposals.{col_name}")
            except Exception as e:
                if 'Duplicate column' in str(e) or 'already exists' in str(e):
                    print(f"  ⏭ Column already exists: proposals.{col_name}")
                else:
                    print(f"  ⚠ Error adding proposals.{col_name}: {e}")
        
        # Widen total_amount precision
        try:
            conn.execute(text("ALTER TABLE proposals MODIFY COLUMN total_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00"))
            print("  ✓ Widened proposals.total_amount to DECIMAL(12,2)")
        except Exception as e:
            print(f"  ⏭ total_amount already correct: {e}")

        # ============================
        # 2. CREATE proposal_templates
        # ============================
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS proposal_templates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company_id INT NULL,
                name VARCHAR(150) NOT NULL,
                code VARCHAR(50) NOT NULL,
                type VARCHAR(20) NOT NULL DEFAULT 'long',
                layout_config JSON NULL,
                is_default BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_pt_company (company_id),
                INDEX idx_pt_code (code),
                INDEX idx_pt_active (is_active),
                CONSTRAINT fk_pt_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        print("  ✓ Created table: proposal_templates")
        
        # Add FK from proposals to proposal_templates
        try:
            conn.execute(text("ALTER TABLE proposals ADD CONSTRAINT fk_proposals_template FOREIGN KEY (template_id) REFERENCES proposal_templates(id) ON DELETE SET NULL"))
            print("  ✓ Added FK: proposals.template_id → proposal_templates")
        except Exception as e:
            if 'Duplicate' in str(e) or 'already exists' in str(e):
                print("  ⏭ FK proposals→proposal_templates already exists")
            else:
                print(f"  ⚠ FK error: {e}")

        # ============================
        # 3. CREATE payment_plan_presets
        # ============================
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payment_plan_presets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company_id INT NOT NULL,
                name VARCHAR(150) NOT NULL,
                code VARCHAR(50) NOT NULL,
                installments_config JSON NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_ppp_company (company_id),
                INDEX idx_ppp_code (code),
                INDEX idx_ppp_active (is_active),
                CONSTRAINT fk_ppp_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        print("  ✓ Created table: payment_plan_presets")

        # ============================
        # 4. CREATE quote_options
        # ============================
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS quote_options (
                id INT AUTO_INCREMENT PRIMARY KEY,
                proposal_id INT NOT NULL,
                name VARCHAR(150) NOT NULL,
                is_default BOOLEAN DEFAULT FALSE,
                preset_id INT NULL,
                total_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
                sort_order INT DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_qo_proposal (proposal_id),
                CONSTRAINT fk_qo_proposal FOREIGN KEY (proposal_id) REFERENCES proposals(id) ON DELETE CASCADE,
                CONSTRAINT fk_qo_preset FOREIGN KEY (preset_id) REFERENCES payment_plan_presets(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        print("  ✓ Created table: quote_options")

        # ============================
        # 5. CREATE quote_items
        # ============================
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS quote_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                option_id INT NOT NULL,
                service_package_id INT NULL,
                service_id INT NULL,
                description TEXT NULL,
                quantity INT NOT NULL DEFAULT 1,
                unit_price DECIMAL(12,2) NOT NULL DEFAULT 0.00,
                discount_pct DECIMAL(5,2) NOT NULL DEFAULT 0.00,
                total DECIMAL(12,2) NOT NULL DEFAULT 0.00,
                billing_type VARCHAR(20) NOT NULL DEFAULT 'one_time',
                tag VARCHAR(20) NOT NULL DEFAULT 'principal',
                sort_order INT DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_qi_option (option_id),
                CONSTRAINT fk_qi_option FOREIGN KEY (option_id) REFERENCES quote_options(id) ON DELETE CASCADE,
                CONSTRAINT fk_qi_package FOREIGN KEY (service_package_id) REFERENCES service_packages(id) ON DELETE SET NULL,
                CONSTRAINT fk_qi_service FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        print("  ✓ Created table: quote_items")

        conn.commit()
        print("\n✅ Schema migration complete!")

    # ============================
    # 6. Migrate existing proposal_items → quote_options + quote_items
    # ============================
    print("\n📦 Migrating existing proposal data...")
    with get_db() as db:
        from app.models import Proposal, ProposalItem, QuoteOption, QuoteItem
        
        proposals_with_items = db.query(Proposal).filter(Proposal.items.any()).all()
        migrated = 0
        
        for proposal in proposals_with_items:
            # Skip if already has options
            if proposal.options:
                continue
            
            # Create a single default option from legacy items
            option = QuoteOption(
                proposal_id=proposal.id,
                name="Opción Principal",
                is_default=True,
                total_amount=float(proposal.total_amount or 0),
                sort_order=0
            )
            db.add(option)
            db.flush()
            
            for idx, item in enumerate(proposal.items):
                qi = QuoteItem(
                    option_id=option.id,
                    service_id=item.service_id,
                    description=item.description,
                    quantity=1,
                    unit_price=float(item.price or 0),
                    discount_pct=0,
                    total=float(item.price or 0),
                    billing_type='one_time',
                    tag='principal',
                    sort_order=idx
                )
                db.add(qi)
            
            # Set company_id from client if missing
            if not proposal.company_id and proposal.client and proposal.client.company_id:
                proposal.company_id = proposal.client.company_id
            
            migrated += 1
        
        db.commit()
        print(f"  ✓ Migrated {migrated} proposals to quote_options/quote_items")

    # ============================
    # 7. Seed default templates & presets
    # ============================
    print("\n🌱 Seeding default templates and presets...")
    with get_db() as db:
        from app.models import ProposalTemplate, PaymentPlanPreset, Company
        import json
        
        # Get first company for seeding
        company = db.query(Company).first()
        if not company:
            print("  ⚠ No company found, skipping seeds")
            return
        
        # Seed templates (global)
        existing = db.query(ProposalTemplate).filter(ProposalTemplate.code == 'long_premium').first()
        if not existing:
            templates = [
                ProposalTemplate(
                    company_id=None,
                    name="Propuesta Completa (Long)",
                    code="long_premium",
                    type="long",
                    layout_config={"sections": ["header", "audit", "services", "payment", "terms", "footer"], "show_audit": True},
                    is_default=True,
                    is_active=True
                ),
                ProposalTemplate(
                    company_id=None,
                    name="Presupuesto Express (Short)",
                    code="short_express",
                    type="short",
                    layout_config={"sections": ["header", "services", "payment", "footer"], "show_audit": False},
                    is_default=False,
                    is_active=True
                ),
            ]
            for t in templates:
                db.add(t)
            print("  ✓ Seeded 2 global proposal templates")
        else:
            print("  ⏭ Templates already seeded")
        
        # Seed payment plan presets for first company
        existing_preset = db.query(PaymentPlanPreset).filter(PaymentPlanPreset.company_id == company.id).first()
        if not existing_preset:
            presets = [
                PaymentPlanPreset(
                    company_id=company.id,
                    name="Contado (100%)",
                    code="contado_100",
                    installments_config=[{"pct": 100, "days_after_sign": 0}],
                    is_active=True
                ),
                PaymentPlanPreset(
                    company_id=company.id,
                    name="2 Cuotas (50/50)",
                    code="2_cuotas_50_50",
                    installments_config=[
                        {"pct": 50, "days_after_sign": 0},
                        {"pct": 50, "days_after_sign": 30}
                    ],
                    is_active=True
                ),
                PaymentPlanPreset(
                    company_id=company.id,
                    name="3 Cuotas (50/30/20)",
                    code="3_cuotas_50_30_20",
                    installments_config=[
                        {"pct": 50, "days_after_sign": 0},
                        {"pct": 30, "days_after_sign": 30},
                        {"pct": 20, "days_after_sign": 60}
                    ],
                    is_active=True
                ),
            ]
            for p in presets:
                db.add(p)
            print(f"  ✓ Seeded 3 payment plan presets for company '{company.name}'")
        else:
            print("  ⏭ Presets already seeded")
        
        db.commit()
    
    print("\n🎉 Proposals v2 migration complete!")


if __name__ == '__main__':
    run_migration()
